import tqdm
import sys
from rumboot.ops.base import base
from rumboot.ops.xfer import basic_uploader
import rumboot.xfer

class settings():
    # crctab calculated by Mark G. Mendel, Network Systems Corporation
    crctable = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
        0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
        0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
        0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
        0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0,
    ]
    MAX_DATA_LEN = 0x400
    AA = b'\xaa'
    ACK = 170


    def twos_complement_to_int(n, bits=32):
        mask = (1 << bits) - 1
        if n < 0:
            n = ((abs(n) ^ mask) + 1)
        return (n & mask)

    ack_b = bytearray(1)
    ack_b[0] = twos_complement_to_int(ACK)


class bootdownload(object):
    '''
    Hisilicon boot downloader

    >>> downloader = bootdownload()
    >>> downloader.burn(filename)

    '''
    DEBUG=0
    def init_bootmode(self):
        i = 0
        counter = 0
        while i < 30:
            in_bin = self.s.read(1)
            if in_bin == b'\x00':
                continue
            if in_bin == b'\x20':
                counter = counter + 1
            if counter == 5:
                self.s.flushOutput()
                self.s.write(settings.AA)
                self.s.flushInput()
                return None
            i = i + 1
        sys.exit(1)

    def __init__(self, terminal, options):
        self.s = terminal.ser
        self.terminal = terminal
        self.init_bootmode()
        self.chip = options

    def calc_crc(self, data, crc=0):
        for char in data:
            crc = ((crc << 8) | char) ^ settings.crctable[(crc >> 8) & 0xff]
        for i in range(0, 2):
            crc = ((crc << 8) | 0) ^ settings.crctable[(crc >> 8) & 0xff]
        return crc & 0xffff

    def sendframe(self, data, loop):
        for i in range(1, loop):
            self.s.flushOutput()
            if self.DEBUG == 1:
                if len(data) > 20:
                    print(
                        "len: ",
                        len(data),
                        "write : [",
                        ''.join('%02x ' % i for i in data[:20]), "... ]"
                    )
                else:
                    print(
                        "len: ",
                        len(data),
                        "write : [",
                        ''.join('%02x ' % i for i in data), "]"
                    )
            self.s.write(data)
            self.s.flushInput()
            try:
                ack = self.s.read()
                if len(ack) == 1:
                    if self.DEBUG == 1:
                        print(
                            "ret ack   : ",
                            ''.join('0x%02x ' % i for i in ack)
                        )
                    if ack == settings.ack_b:
                        return None
            except:
                return None

        raise Exception("Failed to send frame")

    def send_head_frame(self, length, address):
        self.s.timeout = 0.03

        frame = bytearray(14)
        frame[0] = settings.twos_complement_to_int(-2, 8)
        frame[1] = settings.twos_complement_to_int(0, 8)
        frame[2] = settings.twos_complement_to_int(-1, 8)
        frame[3] = settings.twos_complement_to_int(1, 8)

        frame[4] = (length >> 24) & 0xff
        frame[5] = (length >> 16) & 0xff
        frame[6] = (length >> 8) & 0xff
        frame[7] = (length) & 0xff
        frame[8] = (address >> 24) & 0xff
        frame[9] = (address >> 16) & 0xff
        frame[10] = (address >> 8) & 0xff
        frame[11] = (address) & 0xff
        crc = self.calc_crc(frame[:12])
        frame[12] = (crc >> 8) & 0xff
        frame[13] = crc & 0xff

        self.sendframe(frame, 16)

    def send_ddrstep(self):
        seq = 1
        self.s.timeout = 0.15

        address0 = int(self.chip["ADDRESS"][0], 16)
        self.send_head_frame(64, address0)
        head = bytearray(3)
        head[0] = 0xDA  # b'\xDA'  # 0xDA
        head[1] = seq & 0xFF
        head[2] = (~seq) & 0xFF
        data = head + bytes(self.chip["DDRSTEP0"])
        crc = self.calc_crc(data)
        h = bytearray(2)
        h[0] = (crc >> 8) & 0xff
        h[1] = crc & 0xff
        data += h

        self.sendframe(data, 16)
        self.send_tail_frame(seq + 1)

    def send_tail_frame(self, seq):
        data = bytearray(3)
        data[0] = 0xED
        data[1] = seq & 0xFF
        data[2] = (~seq) & 0xFF

        crc = self.calc_crc(data)
        h = bytearray(2)
        h[0] = (crc >> 8) & 0xff
        h[1] = crc & 0xff
        data += h

        self.sendframe(data, 16)

    def send_data_frame(self, seq, data):
        self.s.timeout = 0.15
        head = bytearray(3)
        head[0] = 0xDA
        head[1] = seq & 0xFF
        head[2] = (~seq) & 0xFF
        data = head + data

        crc = self.calc_crc(data)
        h = bytearray(2)
        h[0] = (crc >> 8) & 0xff
        h[1] = crc & 0xff
        data += h

        self.sendframe(data, 32)

    def store_SPL(self, data):
        first_length = int(self.chip["FILELEN"][1], 16)
        address1 = int(self.chip["ADDRESS"][1], 16)
        self.send_head_frame(first_length, address1)

        self.terminal.progress_start("Sending SPL   ", first_length)
        seq = 1
        data = data[:first_length]
        for chunk in (
            data[_:_+settings.MAX_DATA_LEN] for _ in range(
                0, first_length, settings.MAX_DATA_LEN
            )
        ):
            self.send_data_frame(
                seq,
                chunk
            )
            self.terminal.progress_update(first_length, seq*len(chunk), len(chunk))
            seq += 1
        self.terminal.progress_end()
        self.send_tail_frame(seq)

    def store_Uboot(self, data):
        length = len(data)
        address2 = int(self.chip["ADDRESS"][2], 16)
        self.send_head_frame(length, address2)

        self.terminal.progress_start("Sending u-boot", length)

        seq = 1
        for chunk in (
            data[_:_+settings.MAX_DATA_LEN] for _ in range(
                0, length, settings.MAX_DATA_LEN
            )
        ):
            self.send_data_frame(
                seq,
                chunk
            )
            self.terminal.progress_update(length, seq*len(chunk), len(chunk))
            seq += 1
        self.terminal.progress_end()
        self.send_tail_frame(seq)

    def send_data(self, data):
        self.send_ddrstep()
        self.store_SPL(data)
        self.store_Uboot(data)

    def burn(self, filename):
        f = open(filename, "rb")
        data = f.read()
        f.close()

        print('Sending', filename, '...')
        self.send_data(data)
        print('Done\n')


class hisi_chips_uploader(basic_uploader):
    def on_start(self):
        if not hasattr(self.term.chip,"vendor"):
            return

        if not "bootprotocol" in self.term.chip.vendor:
            return

        if self.term.chip.vendor["bootprotocol"] != "hi3xxx":
            return

        options = self.term.chip.vendor    
        fd = self.term.next_binary()
        if fd is None:
            return
        downloader = bootdownload(self.term, self.term.chip.vendor)
        downloader.burn(fd.name)
        return True