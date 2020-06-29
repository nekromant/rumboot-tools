from rumboot.ops.base import base
from rumboot.ops.xmodem import xmodem
import tqdm

class edcl_generic_uploader(xmodem):
    formats = {
        "mm7705": "boot: Waiting for a valid image @ {}"
    }

    def action(self, trigger, result):
        print(result)
        if tp.name == "RumBootV1":
            print("")
        return True


class mb7707_boot_uploader(xmodem):
    formats = {
        "edcl" : "FIXME..."
    }

    def action(self, trigger, result):
        return True

    def on_start(self):
        #HACK: Do we need to push the first binary via edcl?
        def prg(total_bytes, position, increment):
                self.term.progress.update(increment)     
        tp = self.term.formats.guess(self.term.runlist[0])
        if tp.name == "Legacy K1879XB1YA":
            print("Triggering initial edcl upload")
            self.term.enable_edcl()
            binary = self.term.next_binary()
            desc = "Initial Upload"
            self.term.tqdm(desc=desc, total=self.stream_size(binary), unit_scale=True, unit_divisor=1024, unit='B', disable=False)
            self.term.edcl.smartupload(0x00100000, binary, callback=prg)
            self.term.tqdm(disable=True)
            self.term.edcl.write32(0x00100010, 0x00100014)