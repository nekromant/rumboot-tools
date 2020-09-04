from rumboot.ops.base import base
from rumboot.ops.xfer import basic_uploader
import tqdm
import rumboot.xfer


class edcl_generic_uploader(basic_uploader):
    formats = {
        "mm7705": "\x00boot: Waiting for a valid image @ {:x}"
    }

    def action(self, trigger, result):
        tp = self.term.formats.guess(self.term.runlist[0])
        if not tp or tp.name != "RumBootV1":
            return False

        print("WARNING: Bootloader doesn't support xmodem, forcing edcl upload")
        old = self.term.xfer.how
        self.term.xfer.selectTransport("edcl")
        if not self.term.xfer.push(result[0]):
            return 1
        self.term.xfer.selectTransport(old)
        return True


class dumb_chips_uploader(basic_uploader):
    def on_start(self):
        #HACK: Old chips don't print anything via uart
        #HACK: edcl is the only way to bring 'em up
        #HACK: We do the lucky guess by looking at the image header
        def prg(total_bytes, position, increment):
                self.term.progress.update(increment)     

        tp = self.term.formats.guess(self.term.runlist[0])
        if self.term.hack("silentRom"):
            print("WARNING: Bootloader doesn't support xmodem, forcing initial edcl upload")
            old = self.term.xfer.how
            self.term.xfer.selectTransport("edcl")
            if not self.term.xfer.push(self.term.chip.spl_address):
                return 1
            self.term.xfer.selectTransport(old)

        if not tp:
            return True

        if tp.name == "Legacy K1879XB1YA":
            self.term.xfer.write32(0x00100010, 0x00100014)
            return True
        if tp.name == "NM6408 (Legacy)":
            self.term.xfer.write32(0x30000, 0x1)
            return True