from rumboot.ops.base import base
from rumboot.ops.xmodem import xmodem
import tqdm

class edcl_generic_uploader(xmodem):
    formats = {
        "mm7705": "\x00boot: Waiting for a valid image @ {:x}"
    }


    def action(self, trigger, result):
        def prg(total_bytes, position, increment):
                self.term.progress.update(increment)     
        self.term.enable_edcl()
        binary = self.term.next_binary()
        desc = "Initial Upload"   
        self.term.tqdm(desc=desc, total=self.stream_size(binary), unit_scale=True, unit_divisor=1024, unit='B', disable=False)
        self.term.edcl.smartupload(result[0], binary, callback=prg)
        self.term.tqdm(disable=True)
        return True


class dumb_chips_uploader(xmodem):
    formats = {
        
    }

    chipformats = {
        "Legacy K1879XB1YA" : 0x00100000,
        "NM6408 (Legacy)" : 0x0
    }
    def action(self, trigger, result):
        return True

    def on_start(self):
        #HACK: Old chips don't print anything via uart
        #HACK: edcl is the only way to bring 'em up
        #HACK: We do the lucky guess by looking at the image header
        def prg(total_bytes, position, increment):
                self.term.progress.update(increment)     

        tp = self.term.formats.guess(self.term.runlist[0])
        if tp.name in self.chipformats:
            print("Triggering initial edcl upload")
            self.term.enable_edcl()
            binary = self.term.next_binary()
            desc = "Initial Upload"
            self.term.tqdm(desc=desc, total=self.stream_size(binary), unit_scale=True, unit_divisor=1024, unit='B', disable=False)
            self.term.edcl.smartupload(self.chipformats[tp.name], binary, callback=prg)
            self.term.tqdm(disable=True)

        #Some chip-specific hacks
        if tp.name == "Legacy K1879XB1YA":
            self.term.edcl.write32(0x00100010, 0x00100014)
            return
        if tp.name == "NM6408 (Legacy)":
            self.term.edcl.write32(0x30000, 0x1)
            return