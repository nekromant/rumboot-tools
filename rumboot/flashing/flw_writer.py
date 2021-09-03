#Newer FlashWriter SPL thingie
import io
import time
from parse import parse
from .base import PartitionBase, FlashDeviceBase

class WriterFLW():
    devices = {}
    version = 0
    next_buffer = 0

    def __init__(self, terminal):
        self.terminal = terminal
        r = self.terminal.wait("FlashWriter ({}) (help for useless info)", timeout=100)
        self.version = r[0]

    def edcl_send_data(self, fd, length, cb):
        self.next_buffer = 0
        total = length
        while length:
            self.edcl_sync_wait(0)
            sent = self.edcl_submit_buffer(fd, length)
            length -= sent
            if cb:
                cb(total, total - length, sent)

    def edcl_read_data(self, fd, length, cb):
        self.next_buffer = 0
        self.edcl_sync_wait(0)
        curbuf = self.edcl_get_buffer()
        self.edcl_sync(curbuf)
        total = length
        while length > 0:
            last = not length > self.buffer_length
            data = self.edcl_fetch_buffer(last)
            if len(data) > length:
                data = data[:length]
            fd.write(data)
            length -= len(data)
            if cb:
                cb(total, total - length, len(data))


    def edcl_get_buffer(self):
        return self.addr_buffers[self.next_buffer]

    def edcl_next(self):
        self.next_buffer += 1
        self.next_buffer &= 1

    buffers_count = 0

    def edcl_fetch_buffer(self, is_last):
        self.edcl_sync_wait(0)
        curbuf = self.edcl_get_buffer()
        #print(f"Read buffer {curbuf:x} cnt: {self.buffers_count}")
        self.edcl_next()
        data = self.terminal.xfer.read(curbuf, self.buffer_length)
        if not is_last:
            self.edcl_sync(self.edcl_get_buffer())
        return data

    def edcl_submit_buffer(self, fd, maxlength):
        index = self.next_buffer & 1
        toread = self.buffer_length
        if maxlength < self.buffer_length:
            toread = maxlength 

        data = fd.read(toread)
        #print(f"Filling buffer {index} with {len(data)} bytes addr {self.addr_buffers[index]:x} pos {fd.tell()} cnt: {self.buffers_count}")
        if len(data) > 0:
            self.terminal.xfer.write(self.addr_buffers[index], data)
            self.buffers_count += 1
            self.edcl_sync(self.edcl_get_buffer())
            self.edcl_next()
            return toread
        raise Exception("Out of bounds reading input stream")

    def swap32(self, x):
        return int.from_bytes(x.to_bytes(4, byteorder='little'), byteorder='big', signed=False)

    def dumpuart(self):
        # Debug only
        #if self.terminal.ser.inWaiting():
        #    print(self.terminal.ser.readline())
        pass

    oops = 0
    def edcl_sync(self, value=None):
        if value == None:
            ret = self.terminal.xfer.read32(self.addr_sync)
            ret = self.swap32(ret)
        else:
            while True: 
                self.terminal.xfer.write32(self.addr_sync, self.swap32(value))
                tmp = self.terminal.xfer.read32(self.addr_sync_ack)
                tmp = self.swap32(tmp)
                if tmp == value:
                    self.terminal.xfer.write32(self.addr_sync_ack, 0)                    
                    break
            ret = value
        return ret

    def edcl_sync_wait(self, val, tout=5):
        value = 0
        start = time.monotonic()
        while time.monotonic() - start < 15:
            value = self.edcl_sync()
            if  value == val:
                return
        raise Exception(f"EDCL Sync timeout, last value {value:x}, want {val:x}")

    def __getitem__(self, key):
        self.select(key)
        return self.devices[key]
    
    def select(self, device):
        return self.terminal.cmd(f"select {device}", "Device {} selected")

    def discover(self):
        devices = {}
        ret,lines = self.terminal.cmd("bufptr", "buffers {:x} {:x} sync {:x} ack {:x} length {:x}")
        self.addr_buffers = [ ret[0], ret[1] ]
        self.addr_sync = ret[2]
        self.addr_sync_ack = ret[3]
        self.buffer_length = ret[4]

        ret, lines = self.terminal.cmd("list", "completed")
        for l in lines:
            ret = parse("id: {} part: {} size: {:x} erasesize: {:x} writesize: {:x}", l)
            if ret:
                devices[ret[0]] = {                
                    "part" :        ret[1],
                    "size" :        ret[2],
                    "write_size" :  ret[3],
                    "read_size" :   ret[4],
                    "erase_size" :  ret[3]
                }
        return devices

class FlashDeviceFLW(FlashDeviceBase):
    writer = None
    skip_erase_before_write = True
    def __init__(self, terminal, device):
        self.name = device["device"]
        super().__init__()
        self.writer = WriterFLW(terminal)
        devices = self.writer.discover()
        if not self.name in devices:
            raise Exception(f"Failed to find device {self.name} in devices list")
        for key, value in devices[self.name].items():
            setattr(self, key, value)
        self.writer.select(self.name)

    def switchbaud(self, newbaud):
        self.terminal.cmd(f"baudrate {newbaud:d}", "Baudrate: current={:d},new={:d}")
        self.terminal.reopen(speed=newbaud)

    def _read_edcl(self, fd, offset, length, cb):
        self.terminal.cmd(f"duplicate E {offset:x} {length:x}", "ready", timeout=120)
        return self.writer.edcl_read_data(fd, length, cb)

    def _read_xmodem(self, fd, offset, length, cb):
        self.terminal.cmd(f"duplicate X {offset:x} {length:x}", "ready", timeout=120)
        return self.terminal.xfer.to_file(0, length, fd, callback = cb)

    def _read(self, fd, offset, length, cb):
        if self.terminal.xfer.how == "xmodem":
            return self._read_xmodem(fd, offset, length, cb)
        elif self.terminal.xfer.how == "edcl":
            return self._read_edcl(fd, offset, length, cb) 

    def _write_xmodem(self, fd, offset, length, cb):
        self.terminal.cmd(f"program X {offset:x} {length:x}", "completed", timeout=120)
        self.terminal.xfer.from_file(0, fd, cb, -1, length)

    def _write_edcl(self, fd, offset, length, cb):
        self.terminal.cmd(f"program E {offset:x} {length:x}", "completed", timeout=120)
        self.writer.edcl_send_data(fd, length, cb)

    def _write(self, fd, offset, length, callback = None):
        if self.terminal.xfer.how == "xmodem":
            return self._write_xmodem(fd, offset, length, callback)
        elif self.terminal.xfer.how == "edcl":
            return self._write_edcl(fd, offset, length, callback) 

    def _erase(self, offset, length, callback = None):
        self.terminal.cmd(f"erase {offset:x} {length:x}", "completed")

    def __str__(self):
        return f'FlashWriter Device {self.name} part: {self.part} size {self.size} erase_size: {self.erase_size} write_size: {self.write_size}'


#TODO: MBR Partitions
class FlasherFlwMMC(PartitionBase, FlashDeviceFLW):
    device = "mmc{}"
    protocol = "flashwriter"
    def __init__(self, terminal, device):
        PartitionBase.__init__(self, terminal)
        FlashDeviceFLW.__init__(self, terminal, device)

#TODO: DTB Partitions
class FlasherFlwSF(PartitionBase, FlashDeviceFLW):
    device = "sf{}"
    protocol = "flashwriter"
    def __init__(self, terminal, device):
        PartitionBase.__init__(self, terminal)
        FlashDeviceFLW.__init__(self, terminal, device)

class FlasherFlwNOR(PartitionBase, FlashDeviceFLW):
    device = "nor{}"
    protocol = "flashwriter"
    def __init__(self, terminal, device):
        PartitionBase.__init__(self, terminal)
        FlashDeviceFLW.__init__(self, terminal, device)

class FlasherFlwI2C(PartitionBase, FlashDeviceFLW):
    device = "i2c{:d}-{:x}"
    protocol = "flashwriter"
    def __init__(self, terminal, device):
        PartitionBase.__init__(self, terminal)
        FlashDeviceFLW.__init__(self, terminal, device)

class FlasherFlwNAND(PartitionBase, FlashDeviceFLW):
    device = "nand{}"
    protocol = "flashwriter"
    def __init__(self, terminal, device):
        PartitionBase.__init__(self, terminal)
        FlashDeviceFLW.__init__(self, terminal, device)
