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
            line = terminal.readline()
            for p in self.prompt:
                fmt = parse.parse(p[0], line)
                if fmt is not None:
                    terminal.write(p[1])
                    break
        self.check_env()

    def _read(self, fd, offset, length, callback = None):
        total = length
        for pos in range(offset, offset + length, self.chunk_size):
            self.block_to_scratch(pos, self.chunk_size)
            self.scratch_to_host(fd, self.chunk_size)
            if callable(callback):
                callback(total, pos, self.chunk_size)

    def _erase(self, offset=0, length=-1, callback = None):
        self._erase_lastpos = 0
        def linecb(line):
            ret = parse.parse("Erasing at 0x{off:x} --  {} complete.", line)
            if ret is None:
                return
            if callable(callback):
                pos = ret["off"] - offset
                callback(length, pos, pos - self._erase_lastpos) 
                self._erase_lastpos = pos
        self.terminal.cmd(f"sf erase {offset:x} {length:x}", "SF: {} bytes @ {} Erased: OK", callback=linecb)
        if self._erase_lastpos != (offset + length) and callable(callback):
            callback(length, length, length - self._erase_lastpos)

    def _write(self, fd, offset, length, callback = None):
        self.host_to_scratch(fd, length, callback)
        self.scratch_to_block(offset, length)   


class PartitionUbootBase(PartitionBase):
    def saveenv(self):
        self.terminal.cmd("saveenv; printenv tmp", "tmp=OK")

    def env(self, key, value=None):
        if not value is None:
            self.terminal.cmd(f"setenv '{key}' '{value}'; printenv tmp", "tmp=OK")
            newv = self.env(key)
            if newv.strip() == value.strip():
                return value
            else:
                raise Exception(f"Failed to set u-boot env {key}")
        else:
            ret, lines = self.terminal.cmd(f"printenv {key}; printenv tmp", "tmp=OK")
            for l in lines:
                ret = parse.parse("%s={}" % key, l)
                if not ret is None:
                    return ret[0]
            return None

class PartitionUbootMTDPARTS(PartitionUbootBase):
    def save_partitions(self):
        ba = self.env("bootargs") + "  "
        rt = parse.parse("{} mtdparts={dev}:{parts} {}", ba)
        if rt is None: 
            raise Exception("Failed to read current mtdparts")
        fmt=''

        for name,p in self.partitions.items():
            sz = int(p.size / 1024)
            sz = f"{sz}k"

            #If the last partition covers all flash, make it flexible
            if p.offset + p.size == self.size:
                sz = "-"

            fmt = f"{fmt}{sz}({p.name}),"

        fmt = fmt.rstrip(",")
        ba = ba.replace(rt["parts"], fmt)
        self.env("bootargs", ba)
        self.saveenv()

    def load_partitions(self):
        raise Exception(f"FATAL: Loading partition table is not implemented for this device")


class FlashDeviceUbootSF(PartitionUbootMTDPARTS, FlashDeviceUbootBase, UbootBlockTransportSF, UbootHostTransportXMODEM):
    device = "hisisf{}"
    protocol = "uboot"
    name = "SPI Flash"

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
        PartitionUbootMTDPARTS.__init__(self, terminal)
        UbootBlockTransportSF.__init__(self, terminal, scratch)
        UbootHostTransportXMODEM.__init__(self, terminal, scratch)
        while True:
            line = terminal.readline()
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