from rumboot.ops.base import base
import tqdm

class xmodem(base):
    formats = {
        "first_upload"      : "boot: host: Hit '{}' for X-Modem upload",
        "incremental_upload": "boot: host: Back in rom, code {}",
        "runtime"           : "UPLOAD: {} to {}",
        "flash_upload"      : "boot: Press '{}' and send me the image"
        }

    def __init__(self, term):
        super().__init__(term)
        self.ser = term.ser
        self.modem = term.modem

    def sync(self, syncword):
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
        if type(stream) is str:
            stream = open(stream, 'rb')

        pbar = tqdm.tqdm(desc=desc, total=self.stream_size(stream), unit_scale=True, unit_divisor=1024, unit='B')
        def callback(total_packets, success_count, error_count):
            if success_count*128 < pbar.total:
                pbar.update(128)
            else:
                pbar.update(128 - (success_count*128 - pbar.total))
        
        return self.modem.send(stream, retry=128, callback=callback)

    def xmodem_from_plusarg(self, arg):
        fl = self.term.plusargs[arg]
        stream = open(fl, 'rb')
        print("Sending %s via xmodem" % fl)
        ret = self.send(stream, "Uploading")
        stream.close()  
        return ret

    def action(self, trigger, result):
        if trigger == "runtime":
            if not self.xmodem_from_plusarg(result[0]):
                print("Upload failed")
                return 1
            return True
            
        desc = "Sending stream"
        if trigger == "flash_upload":
            desc = "Writing image"

        binary = self.term.next_binary();
        if binary == None: 
            if trigger == "incremental_upload":
                print("No more files, exiting")
                return int(result[0])
            else:
                return 1

        self.sync("X")
        if not self.send(binary, desc):
            print("Upload failed")
            return 1
        return True