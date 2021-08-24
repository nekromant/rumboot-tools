import io
from rumboot.edclManager import edclmanager
from xmodem import XMODEM
import inspect

class xferBase():
    connected = False
    chip = None
    maxpayload = 1

    def __init__(self, terminal, params = {}):
        self.term = terminal
        self.params = params
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

    def write8(self, address, data):
        raise Exception("write32 not implemented")

    def read8(self, address):
        raise Exception("read32 not implemented")

    def write16(self, address, data):
        raise Exception("write32 not implemented")

    def read16(self, address):
        raise Exception("read32 not implemented")

    def write32(self, address, data):
        raise Exception("write32 not implemented")

    def read32(self, address):
        raise Exception("read32 not implemented")

    def write64(self, address, data):
        raise Exception("write32 not implemented")

    def read64(self, address):
        raise Exception("read32 not implemented")

    def _write(self, buffer, destaddr, callback = None):
        raise Exception("FATAL: NOT IMPLEMENTED")        

    def _read(self, srcaddr, length, callback = None):
        raise Exception("FATAL: NOT IMPLEMENTED")        

    def read_tlb(self):
        raise Exception("read_tlb not implemented")

    def write_tlb(self, data):
        raise Exception("write_tlb not implemented")

    def write(self, data, destaddr, callback = None):
        if self.connected:
            return self._write(data, destaddr, callback)
        else:
            raise Exception("Transport not connected")

    def read(self, srcaddr, length, callback = None):
        if self.connected:
            return self._read(srcaddr, length, callback)
        else:
            raise Exception("Failed to enable transport")

    def from_file(self, address, fl, callback = None, file_offset = -1, length = -1):
        if type(fl) == str:
            fl = open(fl, "rb")

        if file_offset < 0:
            file_offset = 0

        if length == -1:
            fl.seek(0, 2)
            length = fl.tell() - file_offset

        fl.seek(file_offset)

        chunksize = self.maxpayload * 10
        def wrapcb(total, position, lastwrite):
            if callback:
                callback(length, position, lastwrite)

        while True:
            toread = chunksize
            if toread > length:
                toread = length
            chunk = fl.read(length)
            if len(chunk) == 0:
                break
            self.write(address, chunk, wrapcb)
            address = address + chunksize
            length -= toread
            if length == 0:
                break

    def to_file(self, address, length, fl, callback = None):
        if type(fl) == str:
            fl = open(fl, "wb+")
            needclose = True
        else:
            needclose = False
        if self.maxpayload > 0:
            chunksize = self.maxpayload * 10
        else:
            chunksize = length # Just one big chunk-o-data
        def wrapcb(total, position, lastwrite):
            if callback:
                callback(length, position, lastwrite)
        rd = 0
        while rd < length:
            chunk = self.read(address + rd, chunksize, wrapcb)
            fl.write(chunk)
            rd = rd + chunksize
        if needclose:
            fl.close()

    def close(self):
        pass

class xferXmodem(xferBase):
    maxpayload = -1 # Don't care
    increment = 128
    last_ok = 0
    mode = "xmodem"

    def __init__(self, terminal, params = {}):
        super().__init__(terminal, params)

    def connect(self, chip):
        def getc(size, timeout=10):
            ret = self.term.read(size)
            return ret or None
        def putc(data, timeout=10):
            return self.term.write(data)  # note that this ignores the timeout
        self.modem = XMODEM(getc, putc, mode=self.mode)
        return super().connect(chip)

    def _write(self, destaddr, buffer, callback = None):
        def wrap_callback(total_packets, success_count, error_count):
            if self.last_ok != success_count and success_count != 0:
                if callback:
                    callback(total_packets * self.increment, success_count * self.increment, self.increment)
            self.last_ok = success_count
        if not isinstance(buffer, io.IOBase):
            buffer = io.BytesIO(buffer)

        ln = self.stream_size(buffer)
        return self.modem.send(buffer, retry=128, callback=wrap_callback)

    def _read(self, srcaddr, length, callback = None):
        def wrap_callback(total_packets, success_count, error_count, packet_size):
            if self.last_ok != success_count and success_count != 0:
                if callback:
                    callback(length, success_count * packet_size, packet_size)
            self.last_ok = success_count

        stream = io.BytesIO()
        #HACK: Check if this stuff is merged: https://github.com/tehmaze/xmodem/pull/53
        spec = inspect.getargspec(self.modem.recv)
        if "callback" in spec.args:
            self.modem.recv(stream, crc_mode=0, retry=128, callback=wrap_callback)
        else:
            print("WARN: No progressbar will be shown, because xmodem library is too old")
            print("WARN: Please update (pip install --upgrade xmodem) to see progressbar during readdout")
            self.modem.recv(stream, crc_mode=0, retry=128)
        return stream.getvalue()

class xferXmodem1k(xferXmodem):
    mode = "xmodem1k"
    increment = 1024

class xferEdcl(xferBase):
    edcl = None
    def __init__(self, terminal, params):
        super().__init__(terminal, params)

    def connect(self, chip):
        if not self.edcl:
            self.edcl = edclmanager()
            self.edcl.force_static_arp = self.params["force_static_arp"]
            if not self.edcl.connect(chip, self.params):
                print("ERROR: Failed to establish edcl connection")
                return False
            self.maxpayload = self.edcl.maxpayload
        return super().connect(chip)
        
    def _write(self, destaddr, buffer, callback = None):
        return self.edcl.write(destaddr, buffer, callback)

    def _read(self, srcaddr, length, callback = None):
        return self.edcl.read(srcaddr, length, callback)

    def reconnect(self):
        if self.edcl != None:
            self.edcl.reconnect()

    def write32(self, address, data):
        return self.edcl.write32(address, data)

    def read32(self, address):
        return self.edcl.read32(address)

# Params is a dict:
#   default: "xmodem"
#   edcl_ip: "192.168.0.1"
#   edcl_mac: "0:0:5e:0:0:0"
#   edcl_timeout: 7.0
#   force_static_arp: True/False
#
class xferManager():
    xfers = {}
    xfer = None
    how = "xmodem"
    params = None

    def __init__(self, terminal, params = {}):
        self.term = terminal
        self.params = params
        if params == None:
            params = {}
        if not "default" in params:
            params["default"] = "xmodem"
        if not "force_static_arp" in params:
            params["force_static_arp"] = False

        self.xfers["xmodem"] = xferXmodem1k(terminal, params)
        self.xfers["xmodem-128"] = xferXmodem(terminal, params)
        self.xfers["edcl"] = xferEdcl(terminal, params)
        #self.xfers["ubootmx"] = xferUbooMX(terminal, params)
        self.how = params["default"]
        self.xfer = self.xfers[self.how]

    def setChip(self, chip):
        self.chip = chip
   
    def selectTransport(self, how):
        self.how = how
        if not how in self.xfers:
            raise Exception("Unknown xfer method: %s" % how)
        self.xfer = self.xfers[how]

    #Forward API calls to selected transport
    def __getattr__(self, name):
        return getattr(self.xfer, name)

    #TODO: This logic needs heavy refactor
    def push(self, address):
        binary = self.term.next_binary()
        self.send(address, binary)
        return True

    def send(self, destaddr, stream, desc='Sending stream'):
        needclose = False
        if type(stream) == str:
            stream = open(stream, "rb")
            needclose = True
        elif not isinstance(stream, io.IOBase):
            stream = io.BytesIO(stream)
            needclose = True

        def prg(total_bytes, position, increment):
            self.term.progress_update(total_bytes, position, increment)

        if not self.xfer.connect(self.chip):
            raise Exception("Failed to connect transport")

        self.term.progress_start(desc, self.stream_size(stream))
        self.from_file(destaddr, stream, file_offset = 0, callback=prg)
        self.term.progress_end()
        if needclose:
            stream.close()
        return True

    def recv(self, stream, srcaddr, total, desc="Receiving data"):
        if not self.xfer.connect(self.chip):
            raise Exception("Failed to connect transport")

        return self.to_file(srcaddr, total, stream)
