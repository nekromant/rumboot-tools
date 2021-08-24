from .base import PartitionBase, FlashDeviceBase
import time
import humanfriendly
import parse
import binascii

class UbootBlockTransportBase():
    required = []

    def __init__(self, terminal, scratch):
        self.terminal = terminal
        self.scratch_addr = scratch

    def block_to_scratch(self, offset, length):
        raise Exception("Implement me!")

    def scratch_to_block(self, offset, length):
        raise Exception("Implement me!")

class UbootHostTransportBase():
    required = []

    def __init__(self, terminal, scratch):
        self.terminal = terminal
        self.scratch_addr = scratch

    def check_required_cmds(self, clist):
        supported = self.query_supported_cmds()
        for l in clist:
            if not l in supported:
                raise Exception("Your uboot doesn't support cmd f{l}. Can't do anything for you")

    def query_supported_cmds(self):
        ret, lines = self.terminal.cmd("help; printenv tmp", "tmp=OK")
        for l in lines:
            print(l)
        return lines

    def host_to_scratch(self, fd, length):
        raise Exception("Implement me!")

    def scratch_to_host(self, fd, length):
        raise Exception("Implement me!")

##################################

class UbootBlockTransportSF(UbootBlockTransportBase):
    def __init__(self, terminal, scratch):
        self.required += ["sf"]
        super().__init__(terminal, scratch)

    def block_to_scratch(self, offset, length):
        self.terminal.cmd(f"sf read {self.scratch_addr:x} {offset:x} {self.chunk_size:x}", "SF: {} bytes @ {} Read: OK")

    def scratch_to_block(self, offset, length):
        self.terminal.cmd(f"sf write {self.scratch_addr:x} {offset:x} {length:x}", "SF: {} bytes @ {} Written: OK")

class UbootHostTransportMDW(UbootHostTransportBase):
    def __init__(self, terminal, scratch):
        super().__init__(terminal, scratch)
        self.required += ["crc32", "mw", "md"]

    #TODO: Handle cases when there is no loadx in firmare
    def host_to_scratch(self, fd, length):
        raise Exception("Implement me!")

    def scratch_to_host(self, fd, length):
        while True:
            ret, lines = self.terminal.cmd(f"crc32 {self.scratch_addr:x} {self.chunk_size:x}", "crc32 for {:x} ... {:x} ==> {:x}")
            crc32_other = ret[2]
            chunk = b""
            ret, lines = self.terminal.cmd(f"md.b {self.scratch_addr:x} {self.chunk_size:x}; printenv tmp", "tmp=OK")
            for l in lines:
                data = parse.parse("{}: {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x} {}", l)
                if data is None:
                    continue
                for p in range(1,17):
                    byte = data[p].to_bytes(1, byteorder="big")
                    chunk += byte
            crc32 = binascii.crc32(chunk) & 0xffffffff
            if crc32 == crc32_other:
                fd.write(chunk)
                break

class UbootHostTransportXMODEM(UbootHostTransportMDW):
    def __init__(self, terminal, scratch):
        super().__init__(terminal, scratch)
        self.required += ["sf", "loadx"]

    def host_to_scratch(self, fd, length, cb):
        self.terminal.cmd(f"loadx {self.scratch_addr:x}", "## Ready for binary ({}) download to {} at {} bps...")
        data = fd.read(length)
        self.terminal.xfer.write(self.scratch_addr, data, cb)

class FlashDeviceUbootBase(FlashDeviceBase):
    prompt = [
        ['Net:{}', b"\x03\n\r\n\r"]
    ]

    def check_env(self):
        print("Checking uboot capabilities...")
        self.terminal.write("setenv tmp OK\n\r".encode())
        ret, lines = self.terminal.cmd("help; printenv tmp", "tmp=OK")
        supported = []
        for l in lines:
            data = parse.parse("{} - {}", l)
            if data is not None:
                supported += [ data[0].rstrip() ]
        for cmd in self.required:
            if not cmd in self.required:
                raise Exception(f"FATAL: u-boot doesn't support required command {cmd}")

    def __init__(self, terminal):
        self.required += ["setenv"]
        FlashDeviceBase.__init__(self)
        fmt = None
        while fmt is None:
            line = terminal.readline().decode("ascii", errors="replace")
            for p in self.prompt:
                fmt = parse.parse(p[0], line)
                if fmt is not None:
                    terminal.write(p[1])
                    break
        self.check_env()

    def _read(self, fd, offset, length, cb = None):
        total = length
        for pos in range(offset, offset + length, self.chunk_size):
            self.block_to_scratch(pos, self.chunk_size)
            self.scratch_to_host(fd, self.chunk_size)
            if cb is not None:
                cb(total, pos, self.chunk_size)

    def _erase(self, offset=0, length=-1, callback = None):
        self._erase_lastpos = offset
        def linecb(line):
            ret = parse.parse("Erasing at {off:x} -- {} complete.", line)
            if not ret is None and callable(callback):
                pos = ret["off"]
                callback(length, pos, pos - self._erase_lastpos) 
                self._erase_lastpos = pos
        self.terminal.cmd(f"sf erase {offset:x} {length:x}", "SF: {} bytes @ {} Erased: OK", callback=linecb)
        if callable(callback): #One last callback
            callback(length, length, length - self._erase_lastpos) 

    def _write(self, fd, offset, length, cb = None):
        self.host_to_scratch(fd, length, cb)
        self.scratch_to_block(offset, length)   

class FlashDeviceUbootSF(PartitionBase, FlashDeviceUbootBase, UbootBlockTransportSF, UbootHostTransportXMODEM):
    device = "hisisf{}"
    protocol = "uboot"

    info_formats = [
        'hifmc_spi_nor_probe({}): Block:{erase_size} hifmc_spi_nor_probe({}): Chip:{size} hifmc_spi_nor_probe({}): Name:"{part}"'
    ]

    def parse_info(self, line):
        for f in self.info_formats:
            ret = parse.parse(f, line)
            if ret is not None:
                return ret
        return None

    def __init__(self, terminal, config):
        scratch = config["scratch"]
        print(f"Using scratch area at 0x{scratch:x}")
        UbootBlockTransportSF.__init__(self, terminal, scratch)
        UbootHostTransportXMODEM.__init__(self, terminal, scratch)
        while True:
            line = terminal.readline().decode("ascii", errors="replace")
            fmt = self.parse_info(line)
            if fmt is not None:
                break
        self.part = fmt["part"]
        self.erase_size = humanfriendly.parse_size(fmt["erase_size"].replace("KB", "KiB"))
        self.size = humanfriendly.parse_size(fmt["size"].replace("MB", "MiB"))
        self.chunk_size = 1024
        self.write_size = 1
        self.read_size = 16
        FlashDeviceUbootBase.__init__(self, terminal)
        self.terminal.write("sf probe\n\r".encode("ascii"))