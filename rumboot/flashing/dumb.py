from .base import PartitionBase, FlashDeviceBase
class FlashDeviceDumb(FlashDeviceBase):
    def __init__(self):
        self.erase_size = 1
        self.write_size = 1
        self.read_size = 1
        self.size = 128 * 1024 * 1024
        self.part = "dumb flash device"
        super().__init__()

    def _read(self, fd, offset, length, callback = None):
        raise Exception("DUMB SPLs DO NOT SUPPORT READBACK")

    def _write(self, fd, offset, length, callback = None):
        if offset != 0:
            raise Exception(f"DUMB SPLs DO NOT SUPPORT OFFSET != 0 (current is {offset}")
        self.terminal.wait("boot: Press 'X' and send me the image")
        self.terminal.write("X".encode("ascii"))
        if self.terminal.xfer.how != "xmodem" and self.terminal.xfer.how != "xmodem1k":
            raise Exception("Dumb spls only support xmodem")
        return self.terminal.xfer.from_file(0, fd, callback, offset, length)

    def _erase(self, offset=0, length=-1, callback = None):
        pass

    def switchbaud(self, newbaud):
        raise Exception("Not implemented")

class FlasherDumb(PartitionBase, FlashDeviceDumb):
    device = "dumb"
    protocol = "dumb"
    def __init__(self, terminal, device):
        FlashDeviceDumb.__init__(self)
        PartitionBase.__init__(self, terminal)
