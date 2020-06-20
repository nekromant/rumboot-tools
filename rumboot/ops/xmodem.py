from rumboot.ops.base import base
import tqdm

class xmodem(base):
    formats = {
        "first_upload"      : "boot: host: Hit '{}' for X-Modem upload",
        "first_upload_basis"  : "boot: host: Hit 'X' for xmodem upload",
        "upload_uboot": "Trying to boot from UART"
        }

    def __init__(self, term):
        super().__init__(term)
        self.ser = term.ser
        self.modem = term.modem

    def sync(self, syncword):
            if self.term.replay:
                return
            while True:
                self.ser.write(syncword.encode())
                while True:
                    tmp1 = self.ser.read(1)
                    tmp2 = self.ser.read(1)
                    if tmp1 == b"C" and tmp2 == b"C": 
                        return
                break

    def stream_size(self, stream):
        stream.seek(0,2)
        len = stream.tell()
        stream.seek(0)
        return len
        
    def send(self, stream, desc="Sending stream"):
        if self.term.replay:
            print("xmodem: We're in replay mode, not actually sending anything")
            return 123

        if type(stream) is str:
            stream = open(stream, 'rb')

        increment = 128 
        if self.modem.mode =='xmodem1k':
            increment = 1024

        self.term.tqdm(desc=desc, total=self.stream_size(stream), unit_scale=True, unit_divisor=1024, unit='B', disable=False)
        pbar = self.term.progress
        def callback(total_packets, success_count, error_count):
            if success_count*increment < pbar.total:
                pbar.update(increment)
            else:
                pbar.update(increment - (success_count*increment - pbar.total))        
        ret = self.modem.send(stream, retry=128, callback=callback)
        self.term.tqdm(disable=True)
        return ret


    def xmodem_from_plusarg(self, arg):
        fl = self.term.plusargs[arg]
        stream = open(fl, 'rb')
        print("Sending %s via xmodem" % fl)
        ret = self.send(stream, "Uploading")
        stream.close()  
        return ret

    def action(self, trigger, result):
        binary = self.term.next_binary()
        if trigger != "upload_uboot":
            self.sync("X")
        if not self.send(binary):
            print("Upload failed")
            return 1
        return True


class flasher(xmodem):
    formats = {
        "flash_upload"      : "boot: Press '{}' and send me the image"
    }

    def action(self, trigger, result):
        desc = "Writing image"
        binary = self.term.next_binary()
        self.sync("X")
        if not self.send(binary, desc):
            print("Upload failed")
            return 1
        return True


class incremental(xmodem):
    formats = {
        "incremental_upload": "boot: host: Back in rom, code {}",
    }

    def action(self, trigger, result):
        binary = self.term.next_binary()
        ret = int(result[0])
        if binary == None: 
            if trigger == "incremental_upload":
                print("No more files, exiting")
                return ret
            else:
                return 1

        if ret != 0:
            return ret

        self.sync("X")
        if not self.send(binary):
            print("Upload failed")
            return 1
        return True


class runtime(xmodem):
    formats = {
        "runtime"           : "UPLOAD: {} to {}",
    }

    def action(self, trigger, result):
        if not self.xmodem_from_plusarg(result[0]):
            print("Upload failed")
            return 1
        return True

class mb7707_uploader(xmodem):
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