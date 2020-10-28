from rumboot.ops.base import base
import tqdm
import time

class basic_uploader(base):
    formats = {
        "first_upload"      : "boot: host: Hit '{}' for X-Modem upload",
        "first_upload_basis"  : "boot: host: Hit 'X' for xmodem upload",
        "upload_uboot": "Trying to boot from UART",
        "uboot_xmodem": "## Ready for binary (xmodem) download to {} at {} bps..."
        }

    def __init__(self, term):
        super().__init__(term)

    def sync(self, syncword, short = False):
        ser = self.term.ser
        if self.term.replay:
            return
        while True:
            ser.write(syncword.encode())
            if short:
                break
            while True:
                tmp1 = ser.read(1)
                tmp2 = ser.read(1)
                if tmp1 == b"C" and tmp2 == b"C": 
                    return
            break

    def action(self, trigger, result):
        if trigger != "upload_uboot" and self.term.xfer.how == "xmodem":
            self.sync("X")

        if not self.term.xfer.push(self.term.chip.spl_address):
            print("Upload failed")
            return 1
        return True

class smart_uploader(basic_uploader):
    formats = {
        "upload" : "UPLOAD to {:x}. 'X' for X-modem, 'E' for EDCL"
    }

    def action(self, trigger, result):
        if (self.term.xfer.how == "xmodem"):
            self.sync("X", True)

        if not self.term.xfer.push(result[0]):
            print("Upload failed")
            return 1

        if (self.term.xfer.how != "xmodem"):
            self.sync('E', True)
        return True

class smart_downloader(basic_uploader):
    formats = {
        "upload" : "DOWNLOAD: {:d} bytes from {:x} to {}. 'X' for X-modem, 'E' for EDCL"
    }

    def action(self, trigger, result):
        print(result)
        arg = result[2]
        if arg in self.term.plusargs:
            fl = self.term.plusargs[arg]
        else:
            fl = arg
        stream = open(fl, 'wb')

        if (self.term.xfer.how == "xmodem"):
            self.sync("X", True)

        self.term.xfer.recv(stream, result[1], result[0])

        if (self.term.xfer.how != "xmodem"):
            self.sync("E", True)

        pass


class runtime(basic_uploader):
    formats = {
        "runtime"           : "UPLOAD: {} to {:x}. 'X' for X-modem, 'E' for EDCL",
    }

    def action(self, trigger, result):
        arg = result[0]
        fl = self.term.plusargs[arg]
        stream = open(fl, 'rb')
        if (self.term.xfer.how == "xmodem"):
            self.sync("X", True)
        ret = self.term.xfer.send(stream, result[1], "Uploading")
        stream.close()  
        if (self.term.xfer.how != "xmodem"):
            self.sync('E', True)
        return ret



class incremental(basic_uploader):
    formats = {
        "incremental_upload": "boot: host: Back in rom, code {}",
    }

    def action(self, trigger, result):
        ret = int(result[0])

        if ret != 0:
            return ret

        if self.term.next_binary(True) == None:
            print("No more files, exiting")
            return ret

        if (self.term.xfer.how == "xmodem"):
            self.sync("X")

        if not self.term.xfer.push(self.term.chip.spl_address):
            print("Upload failed")
            return 1
        return True

class flasher(basic_uploader):
    formats = {
        "flash_upload"      : "boot: Press '{}' and send me the image"
    }

    def action(self, trigger, result):
        self.term.xfer.selectTransport("xmodem-128")
        desc = "Writing image"
        self.sync("X")
        if not self.term.xfer.push(self.term.chip.spl_address):
            print("Upload failed")
            return 1
        return True