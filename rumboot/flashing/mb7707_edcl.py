#NAND on MB7705. Legacy 10+ year stuff, but we're all about LTS

import time
import io
import hexdump
import humanfriendly
from parse import parse
from .base import PartitionBase, FlashDeviceBase

class PartitionMboot(PartitionBase):
    partitions_synced = False

    def __init__(self, terminal, name, size=None):
        super().__init__(terminal)
        self.name = name

        #Let's register internal partitions
        #This logic as the same, as in mboot
        bootsz = 256 * 1024
        if self.erase_size > bootsz:
            bootsz = self.erase_size

        self.add_partition("boot", 0, bootsz)
        self.add_partition("env",  bootsz, self.erase_size)
        self.add_partition("dtb",  bootsz + self.erase_size, self.erase_size)
        self.add_partition("firmware", 0, self.size)

    def get_real_offset(self):
        return self.__offset

    def commit(self, save=False):
        if self.partitions_synced:
            return

        parts=""
        sizes = []
        for k,v in self.partitions.items():
            if k == "boot":
                continue
            if k == "env":
                continue
            if k == "dtb":
                continue
            if k == "firmware":
                continue
            parts = f"{parts}{k},"
            sizes.append(f"setenv {k}_size {v.size}")

        self.mboot_cmd(f"setenv parts {parts}")
        for s in sizes:
            self.mboot_cmd(s)
        self.mboot_cmd("partscan")
        if save:
            self.mboot_cmd("saveenv")

class FlashDeviceMB7707(FlashDeviceBase):
    cmdaddr    = 0
    magic_addr = 0x00100000
    mbootoffs  = 0x00100010
    TEXT_BASE  = 0x00100014
    RUNPTR     = 0x00100010
    RAM_BASE   = 0x40100000


    def extract_nand_info(self):
        fmt = "mnand_read_id: CS{:d} NAND {} {} {} size({:d}) writesize({:d}) oobsize({:d}) erasesize({:d})"
        chips = []
        _id, lines = self.terminal.wait("mnand_read_id: flash id {:x}")

        if _id[0] > 0:
            params, lines = self.terminal.wait(fmt)
            chips.append(params)

        _id, lines = self.terminal.wait("mnand_read_id: flash id {:x}")
        if _id[0] > 0:
            params, lines = self.terminal.wait(fmt)
            chips.append(params)
        
        size = 0
        part = ""
        for c in chips:
            size += humanfriendly.parse_size(c[1])

        if len(chips) > 1:
            l = "(x2)"
        else:
            l = "(x1)"
        attrs = {
            "size" : size,
            "part" : f"NAND {chips[0][1]} {chips[0][2]} {chips[0][3]} {l}",
            "read_size" : chips[0][4],
            "write_size" : chips[0][5],
            "oob_size" : chips[0][6],
            "erase_size" : chips[0][7],
        }
        self.nand_chips = chips
        return attrs

    def __init__(self, terminal, device):
        self.name = device
        super().__init__()
        self.magic(0xdeadc0de) # Enable slave mode
        
        self.wait_nmagic(0xdeadc0de);
        self.cmdaddr = self.magic()

        layout = self.extract_nand_info()
        for key, value in layout.items():
            setattr(self, key, value)

    def magic(self, value = None):
        if value != None:
            self.terminal.xfer.write32(self.magic_addr, value)
        else:
            value = -1
        ret = self.terminal.xfer.read32(self.magic_addr)
        return ret

    def wait_magic(self, value):
        while True:
            v = self.terminal.xfer.read32(self.magic_addr)
            time.sleep(0.1)
            if v == value:
                break

    def wait_nmagic(self, value):
        while True:
            v = self.terminal.xfer.read32(self.magic_addr)
            time.sleep(0.1)
            if v != value:
                break
    
    def get_buffer(self):
       self.wait_nmagic(0xa1)
       return self.magic()

    def mboot_cmd(self, cmd):
       data = cmd.encode("ascii")
       data += b"\x00"
       self.terminal.xfer.write(self.cmdaddr, data)
       self.magic(0xdeadbeaf)
       self.wait_nmagic(0xdeadbeaf)

    def dumpuart(self):
        while self.terminal.ser.inWaiting():
            print(self.terminal.ser.readline())
 
    def _write(self, fd, offset, length, callback = None):
        self.commit()
        self.mboot_cmd(f"eupgrade 0x{offset:x} 0x{length:x}")
        es = self.magic()
        self.magic(0xa1)
        total = self.stream_size(fd)
        chunksize = self.erase_size
        while length > 0:
            buffer_addr = self.get_buffer()
            data = fd.read(chunksize)
            self.terminal.xfer.write(buffer_addr, data)
            sent = len(data)
            length -= sent
            self.magic(0xa1)
            if callable(callback):
                callback(total, total - length, sent)
        self.magic(0)
        self.wait_nmagic(0)

    def get_bad_blocks(self):
        self.mboot_cmd("mtd bad; version")
        self.terminal.wait("MTD mnand bad blocks:")
        ret, lines = self.terminal.wait("mboot-{}")
        bads = []
        for l in lines:
            try:
                bads.append(int(l, 16))
            except:
                pass
        return bads

    def _read(self, fd, offset, length, callback = None):
        self.commit()
        bads = self.get_bad_blocks()
        maxchunksize = self.erase_size
        total = length
        while length > 0:
            if length > maxchunksize:
                chunk = maxchunksize
            else:
                chunk = length
            if not offset in bads:
                self.mboot_cmd(f"mtd read 0x40100000 0x{offset:x} 0x{chunk:x}")
                data = self.terminal.xfer.read(0x40100000, chunk)
                fd.write(data)
                length -= len(data)
                offset += len(data)
                if callback(callback):
                    callback(total, total - length, chunk)
            else:
                offset += self.erase_size

    def _erase(self, offset=0, length=-1, callback = None):
        if length == -1:
            length = self.size
        self.terminal.cmd(f"mtd scrub 0x{offset:x} {length:x}")

    def switchbaud(self, newbaud):
        raise Exception("Not implemented for this board")

class Flasher7707NAND(PartitionMboot, FlashDeviceMB7707):
    device = "nand"
    protocol = "legacy_edcl"
    #For MB77.07 device must equal partition, use firmware for full-flash
    def __init__(self, terminal, device):
        self.terminal = terminal #We need that early
        FlashDeviceMB7707.__init__(self, terminal, device)
        PartitionMboot.__init__(self, terminal, device)
