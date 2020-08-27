from rumboot.edclManager import edclmanager
from xmodem import XMODEM

class xferBase():
    connected = False
    chip = None
    def __init__(self, terminal):
        self.term = terminal
        pass

    def reconnect(self):
        pass
    
    def connect(self, chip):
        self.connected = True
        self.chip = chip
        return True

    def stream_size(self, stream):
        stream.seek(0,2)
        len = stream.tell()
        stream.seek(0)
        return len

    def write32(self, address, data):
        raise Exception("write32 not implemented")

    def read32(self, address):
        raise Exception("read32 not implemented")

    def _send(self, stream, destaddr, desc="Sending stream"):
        pass

    def send(self, stream, destaddr, desc="Sending stream"):
        if type(stream) is str:
            stream = open(stream, 'rb')
        if self.connected:
            return self._send(stream, destaddr, desc)
        else:
            raise Exception("Transport not connected")

    def _recv(self, stream, srcaddr, total, desc="Sending stream"):
        print("FATAL: NOT IMPLEMENTED")        
        pass

    def recv(self, stream, srcaddr, total, desc="Receiving stream"):
        if type(stream) is str:
            stream = open(stream, 'wb')
        if self.connected:
            return self._recv(stream, srcaddr, total, desc=desc)
        else:
            raise Exception("Failed to enable transport")

class xferXmodem(xferBase):
    increment = 128
    mode = "xmodem"

    def __init__(self, terminal):
        super().__init__(terminal)

    def connect(self, chip):
        ser = self.term.ser
        def getc(size, timeout=10):
            ret = ser.read(size)
            return ret or None
        def putc(data, timeout=10):
            return ser.write(data)  # note that this ignores the timeout
        self.modem = XMODEM(getc, putc, mode=self.mode)
        return super().connect(chip)

    def _send(self, stream, destaddr, desc="Sending stream"):
        total = self.stream_size(stream)
        terminal = self.term
        increment = self.increment
        terminal.progress_start(desc, total)
        self.last_ok = 0
        def callback(total_packets, success_count, error_count):
            if self.last_ok != success_count and success_count != 0:
                terminal.progress_update(total_packets * increment, success_count * increment, increment)
            self.last_ok = success_count
        ret = self.modem.send(stream, retry=128, callback=callback)
        terminal.progress_end()
        return ret
 
    def _recv(self, stream, srcaddr, total, desc='Receiving stream'):
        terminal = self.term
        increment = self.increment
        #terminal.progress_start(desc, total)
        self.last_ok = 0
        def callback(total_packets, success_count, error_count):
            if self.last_ok != success_count and success_count != 0:
                terminal.progress_update(total_packets * increment, success_count * increment, increment)
            self.last_ok = success_count
        #FixMe: modem.recv doesn't support callback mechanism
        ret = self.modem.recv(stream, crc_mode=0, retry=128)
        #terminal.progress_end()
        return ret

class xferXmodem1k(xferXmodem):
    mode = "xmodem1k"
    increment = 1024

class xferEdcl(xferBase):
    edcl = None
    force_static_arp = False
    def __init__(self, terminal):
        super().__init__(terminal)

    def connect(self, chip):
        if not self.edcl:
            self.edcl = edclmanager()
            self.edcl.force_static_arp = self.force_static_arp
            if not self.edcl.connect(chip):
                print("ERROR: Failed to establish edcl connection")
                return False
        return super().connect(chip)
        
    def _recv(self, stream, srcaddr, total, desc="Sending stream"):
        def prg(total_bytes, position, increment):
            self.term.progress_update(total_bytes, position, increment) 
        return self.edcl.recv_to_file(srcaddr, total, stream, callback=prg)

    def reconnect(self):
        if self.edcl != None:
            self.edcl.reconnect()

    def write32(self, address, data):
        return self.edcl.write32(address, data)

    def read32(self, address):
        return self.edcl.read32(address)

    def _send(self, stream, destaddr, desc='Sending stream'):
        terminal = self.term
        total = self.stream_size(stream)
        terminal.progress_start(desc, total)
        def prg(total_bytes, position, increment):
            terminal.progress_update(total_bytes, position, increment) 
        self.edcl.smartupload(destaddr, stream, callback=prg)
        terminal.progress_end()
        return True


class xferManager(xferBase):
    xfers = {}
    xfer = None
    how = "xmodem"

    def __init__(self, terminal, how="xmodem"):
        super().__init__(terminal)
        self.xfers["xmodem"] = xferXmodem1k(terminal)
        self.xfers["xmodem-128"] = xferXmodem(terminal)
        self.xfers["edcl"] = xferEdcl(terminal)
        self.how = how
        self.xfer = self.xfers[how]

    def setChip(self, chip):
        self.chip = chip

    def write32(self, address, data):
        return self.xfer.write32(address, data)

    def read32(self, address):
        return self.xfer.read32(address)
    
    def selectTransport(self, how):
        self.how = how
        if not how in self.xfers:
            raise Exception("Unknown xfer method: %s" % how)
        self.xfer = self.xfers[how]

    def push(self, address):
        binary = self.term.next_binary()
        return self.term.xfer.send(binary, address, "Sending binary")

    def send(self, stream, destaddr, desc='Sending stream'):
        if self.xfer.connect(self.chip):
            return self.xfer.send(stream, destaddr, desc=desc)
        else:
            raise Exception("Failed to connect transport")

    def recv(self, stream, srcaddr, total, desc="Receiving data"):
        if self.xfer.connect(self.chip):
            return self.xfer.recv(stream, srcaddr, total, desc=desc)
        else:
            raise Exception("Failed to connect transport")

    def reconnect(self):
        self.xfer.reconnect()
        
#    def _recv(self, stream, desc='Receiving stream'):
#        return super()._recv(stream, desc=desc)