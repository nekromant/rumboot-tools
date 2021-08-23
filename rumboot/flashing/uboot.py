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

    def erase_region(self, offset, length):
        raise Exception("Implement me!")

    def block_to_scratch(self, offset, length):
        raise Exception("Implement me!")

    def scratch_to_block(self, offset, length):
        raise Exception("Implement me!")

class UBootHostTransportBase():
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
    info_formats = [
        'hifmc_spi_nor_probe({}): Block:{erase_size} hifmc_spi_nor_probe({}): Chip:{size} hifmc_spi_nor_probe({}): Name:"{part}"'
    ]

    def __init__(self, terminal, scratch):
        super().__init__(terminal, scratch)
        self.required += ["sf"]

#    def parse_info(self, line):
#        for f in self.info_formats:

    def erase_region(self, offset, length):
        self.terminal.cmd(f"sf erase {offset:x} {length:x}", "SF: {} bytes @ {} Erased: OK")

    def block_to_scratch(self, offset, length):
        self.terminal.cmd(f"sf read {self.scratch_addr:x} {pos:x} {self.read_size:x}", "SF: {} bytes @ {} Read: OK")

    def scratch_to_block(self, offset, length):
        self.terminal.cmd(f"sf write {self.scratch_addr:x} {offset:x} {length:x}", "SF: {} bytes @ {} Written: OK")

class UBootHostTransportMDW(UBootHostTransportBase):
    def __init__(self, terminal, scratch):
        super().__init__(terminal, scratch)
        self.required += ["crc32", "mw", "md"]

    #TODO: Handle cases when there is no loadx in firmare
    def host_to_scratch(self, fd, length):
        raise Exception("Implement me!")

    def scratch_to_host(self, fd, length):
        while True:
            ret, lines = self.terminal.cmd(f"crc32 {self.scratch_addr:x} {self.read_size:x}", "crc32 for {:x} ... {:x} ==> {:x}")
            crc32_other = ret[2]
            chunk = b""
            ret, lines = self.terminal.cmd(f"md.b {self.scratch_addr:x} {self.read_size:x}; printenv tmp", "tmp=OK")
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

class UbootHostTransportXMODEM(UbootTransportMDW):
    def __init__(self):
        super().__init__()
        self.required += ["sf", "loadx"]

    def host_to_scratch(self, fd, length, cb):
        self.terminal.cmd(f"loadx {self.scratch_addr:x}", "## Ready for binary ({}) download to {} at {} bps...")
        data = fd.read(length)
        self.terminal.xfer.write(self.scratch_addr, data, cb)

#######################################################
class FlashDeviceUbootBase(FlashDeviceBase):
    pass

class FlashDeviceUbootSF(FlashDeviceBase, UbootBlockTransportSF, UbootHostTransportXMODEM):
    pass

class FlashDeviceUbootBase(FlashDeviceBase):
    flash_info_formats = [
        'hifmc_spi_nor_probe(1723): Block:{erase_size} hifmc_spi_nor_probe(1724): Chip:{size} hifmc_spi_nor_probe(1725): Name:"{part}"',
    ]

    prompt_formats = [
        ['Net:{}', "\n\r"]
    ]

    flash_info_format = 'hifmc_spi_nor_probe({}): Block:{erase_size} hifmc_spi_nor_probe({}): Chip:{size} hifmc_spi_nor_probe({}): Name:"{part}"'

    prompt_format = 'Net:{}' 
    stop_sequence = b"\x03" 
    scratch_addr = 0x42000000

class FlashDeviceUbootMDW(FlashDeviceUbootBase):
    def parse_flash_info(self, fmt, lines):
        self.part = fmt["part"]
        self.erase_size = humanfriendly.parse_size(fmt["erase_size"].replace("KB", "KiB"))
        self.size = humanfriendly.parse_size(fmt["size"].replace("MB", "MiB"))
        self.write_size = 512
        self.read_size  = 512

    def __init__(self):
        if not self.flash_info_format is None:
            fmt, lines = self.terminal.wait(self.flash_info_format)
            self.parse_flash_info(fmt, lines)

        self.terminal.wait(self.prompt_format)
        for i in range(0,10):
            self.terminal.write(self.stop_sequence)
            time.sleep(0.1)
        self.terminal.write("sf probe\r\n".encode("ascii"))
        self.terminal.write("setenv tmp OK\r\n".encode("ascii"))

        super().__init__()

    def _read(self, fd, offset, length, cb = None):
        #TODO: Move chunked read to base.py
        total = length
        for pos in range(offset, offset + length, self.read_size):
            while True:
                self.terminal.cmd(f"sf read {self.scratch_addr:x} {pos:x} {self.read_size:x}", "SF: {} bytes @ {} Read: OK")
                ret, lines = self.terminal.cmd(f"crc32 {self.scratch_addr:x} {self.read_size:x}", "crc32 for {:x} ... {:x} ==> {:x}")
                crc32_other = ret[2]
                chunk = b""
                ret, lines = self.terminal.cmd(f"md.b {self.scratch_addr:x} {self.read_size:x}; printenv tmp", "tmp=OK")
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

            if cb:
                handled = pos - offset
                cb(total, handled, self.read_size)

    def _write(self, fd, offset, length, cb = None):
        erase_length = length
        if length % self.erase_size > 0:
            erase_length += self.erase_size - (length % self.erase_size)
        print("+++", length, erase_length)
        self.terminal.cmd(f"sf erase {offset:x} {erase_length:x}", "SF: {} bytes @ {} Erased: OK")
        self.terminal.cmd(f"loadx {self.scratch_addr:x}", "## Ready for binary ({}) download to {} at {} bps...")
        data = fd.read(length)
        self.terminal.xfer.write(self.scratch_addr, data, cb)
        self.terminal.cmd(f"sf write {self.scratch_addr:x} {offset:x} {length:x}", "SF: {} bytes @ {} Written: OK")

    def _erase(self, offset=0, length=-1, cb = None):
        self.terminal.cmd(f"sf erase {offset:x} {length:x}", "SF: {} bytes @ {} Erased: OK")

    def switchbaud(self, newbaud):
        raise Exception("Not implemented")

class FlasherUbootSFHiSi(PartitionBase, FlashDeviceUbootMDW):
    device = "hisisf{}"
    protocol = "uboot"

    def __init__(self, terminal, device):
        scratch=terminal.chip.memories[device]["scratch"]
        print(f"using scratch address 0x{scratch:x}")
        self.terminal = terminal #We need that early
        FlashDeviceUbootMDW.__init__(self)
        PartitionBase.__init__(self, terminal)
