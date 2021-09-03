import io
import re
import copy

class PartitionBase():
    name = "invalid"
    erase_size = 0
    read_size = 0
    write_size = 0
    size = 0
    offset = 0
    partitions = {}
    last_added_partition_end = 0

    def __init__(self, terminal):
        self.terminal = terminal

    def __getitem__(self, key):
        return self.partitions[key]

    def save_partitions(self):
        raise Exception(f"FATAL: Saving partition table is not implemented for this device")

    def load_partitions(self):
        raise Exception(f"FATAL: Loading partition table is not implemented for this device")

    def erase(self, offset=0, length=-1, callback=None):
        off = 0
        if length < 0:
            length = self.size

        ln = length

        if length % self.erase_size > 0:
            raise Exception(f"FATAL: Erase length is not aligned by erase_size boundary")
        if offset % self.erase_size > 0:
            raise Exception(f"FATAL: Erase offset is not aligned by erase_size boundary")

        self._erase(self.offset + offset, length, callback=callback)

    def write(self, fd, offset, length = -1, callback = None):
        if length < 0:
            ln = self.stream_size(fd)
        else:
            ln = length

        pad = 0
        if ln % self.write_size:
            pad += self.write_size - (ln % self.write_size)

        #TODO: Do we really have to handle padding here?
        if pad > 0:
            #print("WARNING: padding data, it eats up ram")
            fd = fd.read()
            while pad > 0:
                fd +=b"\x00"
                pad -= 1
            fd = io.BytesIO(fd)
            ln = self.stream_size(fd)

        if (offset + self.offset) % self.write_size:
            raise Exception("Misaligned write offset")
        
        initial_pos = fd.tell()

        if not ln > 0:
            raise Exception(f"FATAL: Length can't be {ln}")
        
        return self._write(fd, self.offset + offset, ln, callback)

    def read(self, fd, offset, length = -1, callback = None):
        if offset + self.offset % self.read_size:
            raise Exception("Misaligned read")

        if length % self.read_size:
            raise Exception("Misaligned read size")

        if length < 0:
            ln = self.size - self.offset - offset
        else:
            ln = length

        return self._read(fd, self.offset + offset, ln, callback)

    # offset: positive - byte offset from start of device
    #         negative - byte offset from the end of device
    #         None     - make it follow last added partition

    def add_partition(self, name, offset = 0, length=-1):

        partitions = self.partitions
        partitions[name]        = copy.copy(self)
        partitions[name].name   = name

        if offset is None:
            offset = self.last_added_partition_end
        elif offset < 0:
            offset = self.size - offset

        if offset % self.erase_size:
            raise Exception(f"FATAL: Partition {name} offset is not aligned by erase_size boundary")

        partitions[name].offset = offset

        maxsize = self.size - offset

        if length == -1 or length > maxsize:
            partitions[name].size = maxsize
        else:
            partitions[name].size = length

        if partitions[name].size % self.erase_size:
            raise Exception(f"FATAL: Partition {name} size is not aligned by erase_size boundary")
        
        self.last_added_partition_end = offset + partitions[name].size

        return partitions[name]

    def stream_size(self, stream):
        pos = stream.tell()
        stream.seek(0,2)
        ln = stream.tell()
        stream.seek(pos)
        return ln - pos

    def fromfile(self, path):
        if type(path) == str:
            path = open(path, "rb")
        return self.write(0, path)

    def tofile(self, path):
        if type(path) == str:
            path = open(path, "wb+")
        self.read(0, self.size, path)
        path.close()

    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def dump(self):
        print(f"Device: {self.name} part: {self.part} size: {self.sizeof_fmt(self.size)} erase_size: {self.sizeof_fmt(self.erase_size)} write_size: {self.sizeof_fmt(self.write_size)}")

    def dump_parts(self):
        for k,v in self.partitions.items():
            v.dump()
            
#Basic flash device with access functions
class FlashDeviceBase():
    skip_erase_before_write = False

    def _read(self, fd, offset, length, callback = None):
        raise Exception("NOT IMPLEMENTED")

    def _write(self, fd, offset, length, callback = None):
        raise Exception("NOT IMPLEMENTED")

    def _erase(self, offset=0, length=-1, callback = None):
        raise Exception("NOT IMPLEMENTED")

    def switchbaud(self, newbaud):
        raise Exception("Not implemented")

    def saveenv(self):
        raise Exception("Not implemented")

    def env(self, key, value=None):
        raise Exception("Not implemented")
