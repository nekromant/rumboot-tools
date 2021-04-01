import struct
import socket
from getmac import get_mac_address
import time
# sudo arp -s 192.168.144.9 0:0:5e:0:0:0

class edcl_packet:
    offset  = 0
    control = 0
    address = 0

    seq = 0
    flag = 0
    plen = 0

    payload = b''
    FORMAT = "=HII"
    def __init__(self, seq=0):
        self.seq = seq

    def read(self, address, len):
        self.plen = len
        self.address = address
        self.flag = 0

    def write(self, address, data):
        self.payload = data
        self.plen = len(data)
        self.address = address
        self.flag = 1

    def update(self):
        self.control = socket.htonl((self.seq & 0x3FFF) << 18 | ((not not self.flag) & 1) << 17 | (self.plen & 0x3FF) << 7)

    def e_seq(self):
            return socket.ntohl(self.control) >> 18

    def e_rwnak(self):
            return (socket.ntohl(self.control) >> 17) & 1

    def e_len(self):
            return (socket.ntohl(self.control) >> 7) & 0x3FF

    def serialize(self):
        self.update()
        #Make sure we're 4-byte aligned
        self.offset  = self.address & 0x3
        self.address = self.address & ~0x3
        ret = struct.pack(self.FORMAT, self.offset, self.control, socket.htonl(self.address)) + self.payload
        return ret

    def deserialize(self,data):
        self.offset, self.control, self.address = struct.unpack_from(self.FORMAT, data)
        start = struct.calcsize(self.FORMAT)
        self.payload = data[start:]
        if (self.e_len() != len(self.payload)):
            raise Exception("edcl_packet: Whoops, got length %d, expected %d" % (len(self.payload), self.e_len()))
        self.len = self.e_len()
        self.seq = self.e_seq()
        
    def add_data(self, data):
        self.payload += data
        self.plen = len(self.payload)

    def dump(self):
        print("addr: ", self.address)
        print("control: ", self.control)
        print("offset: ", self.offset)
        print("len: ", self.plen)
        print("seq: ", self.seq)
        print("RWNAK: ", self.e_rwnak())
        print("------")
    def data(self):
        return self.payload

class edcl():
    sock = None
    local_port = 0x8088
    remote_port = 0x9099
    remote_ip = "192.168.0.1"
    maxpayload = 456
    swap_endian = False
    seq = 0

    stats = {
        "noreply" : 0,
        "lostack" : 0,
        "rwnak": 0,
        "badseq" : 0
    }

    def __init__(self):        
        rc = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP
        rc.bind(("0.0.0.0", 0x8088))
        self.sock = rc

    def set_max_payload(self, p):
        self.maxpayload = p

    def xfer(self, packet, checkrwnak=True, retries=32):
        rcv = edcl_packet()
        noreply = False
        while packet.plen % 4:
            packet.add_data(b'\x00')

        for i in range(0,retries):
            packet.seq = self.seq
            sentlen = 0
            try:
                self.sock.sendto(packet.serialize(), (self.remote_ip, self.remote_port))
                data, addr = self.sock.recvfrom(struct.calcsize(edcl_packet.FORMAT) + self.maxpayload)
                if addr[0] != self.remote_ip:
                    continue
                rcv.deserialize(data)
            except Exception as e:
                self.stats["noreply"] +=1
                noreply = True
                continue

            if not checkrwnak:
                return rcv

            if rcv.e_rwnak():
                self.stats["rwnak"] +=1
                if noreply and rcv.e_seq() == packet.e_seq() + 1:
                    noreply = False
                    self.seq = rcv.e_seq()
                    self.stats["lostack"] +=1
                    continue

                if rcv.e_seq() != packet.e_seq():
                    self.stats["badseq"] +=1
                    print("edcl: Sync lost. got %d expected %d" % (rcv.e_seq(), packet.e_seq()))
                    self.seq = rcv.e_seq()
                    continue

            if rcv.e_seq() == packet.e_seq():
                self.seq = self.seq + 1                
                return rcv
        raise Exception("EDCL Transfer failed")

    def _read_raw_(self, address, len):
        tx = edcl_packet()
        tx.read(address, len)
        rx = self.xfer(tx)
        return rx.payload

    def _write_raw_(self, address, data):
        tx = edcl_packet()
        tx.write(address, data)
        rx = self.xfer(tx)
        return (rx.e_rwnak() == 0)

    def _read_raw(self, address, len):
        if self.swap_endian and (address % 4 or len % 4):
            raise Exception("edcl: Requested misaligned operation for slave that needs endian swap")
        #TODO: Swap endian here
        return self._read_raw_(address, len)

    def _write_raw(self, address, data):
        if self.swap_endian and (address % 4 or len % 4):
            raise Exception("edcl: Requested misaligned operation for slave that needs endian swap")
        #TODO: Swap endian here
        return self._write_raw_(address, data)

    def read32(self, address):
        data = _read_raw(self, address, 4)
        return struct.unpack_from("=I",data)

    def write32(self, address, data):
        data = struct.pack("=I",  data)
        self._write_raw(address, data)

    def read(self, address, len, callback = None):
        ret = b''
        for l in range (0, len, self.maxpayload):
            if (len - l > self.maxpayload):
                toread = self.maxpayload
            else:
                toread = len - l
            ret = ret + self._read_raw(address + l, toread)
            if callback:
                callback(len, l + toread, toread)
        return ret

    def write(self, address, data, callback = None):
        length = len(data)
        for l in range (0, length, self.maxpayload):
            if (length - l > self.maxpayload):
                towrite = self.maxpayload
            else:
                towrite = length - l

            self._write_raw(address + l, data[l:l+towrite])
            if callback:
                callback(len, l + towrite, towrite)


    def send_from_file(self, address, fl, callback = None, offset = 0, length = -1):
        if type(fl) == str:
            fl = open(fl, "rb")

        if length == -1:
            fl.seek(0, 2)
            length = fl.tell() - offset

        fl.seek(offset)
        chunksize = self.maxpayload * 10
        def wrapcb(total, position, lastwrite):
            if callback:
                callback(length, position, lastwrite)

        while True:
            toread = chunksize
            if toread > length:
                toread = length
            chunk = fl.read(length)
            if len(chunk) == 0:
                break
            self.write(address, chunk, wrapcb)
            address = address + chunksize
            length -= toread
            if length == 0:
                break
#        print(self.stats)
        
    def recv_to_file(self, address, length, fl, callback = None):
        if type(fl) == str:
            fl = open(fl, "wb+")
            needclose = True
        else:
            needclose = False
        chunksize = self.maxpayload * 10
        def wrapcb(total, position, lastwrite):
            if callback:
                callback(length, position, lastwrite)
        rd = 0
        while rd < length:
            chunk = self.read(address + rd, chunksize, wrapcb)
            fl.write(chunk)
            rd = rd + chunksize
        if needclose:
            fl.close()
#        print(self.stats)

    def reconnect(self):
        return self.connect(remote_ip=self.remote_ip, remote_port=self.remote_port)

    def connect(self, remote_ip="192.168.144.9", remote_port=0x9099):
        self.sock.settimeout(0.6) # the timeout should include ARP request timeout overwise the requests will be accumulated and next requests will be delayed
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        tx = edcl_packet()

        # Get rid of any residual data we may get
        # Works around some rare corner-cases
        try: 
            self.sock.recvfrom(4096)
        except:
            pass

        try:
            rx = self.xfer(tx, False, 1)
            if rx.e_rwnak():
                self.seq = rx.e_seq()
            else:
                self.seq = rx.e_seq() + 1
            self.seq = rx.e_seq() + 1
            self.sock.settimeout(0.1)
            for shit in self.stats:
                self.stats[shit]=0
            return (tx.address == rx.address) and (tx.e_len() == rx.e_len())
        except Exception as e:
            return False

