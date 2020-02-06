from rumboot.ops.base import base
from parse import parse

class stackframe(base):
    hidden = True
    dumps = {}
    formats = {
        "frame" : "frame[{}] address {}",
        }

#80023590:	4b ff f9 15 	bl      80022ea4 <rumboot_vprintf>
#80023518 <rumboot_printf>:
#['80023844:', 'ff', 'ff', 'e4', '08', '.long', '0xffffe408']

    def getdump(self):
        dmp = self.term.current_dump()
        if dmp.name in self.dumps:
            return self.dumps[dmp.name]
        dmp.seek(0)
        dumpdb = {}
        func = "none"
        funcaddr = 0
        while True:
            line = dmp.readline()
            if not line:
                break
            ret = parse("{} <{}>:", line)
            if ret:
                func = ret[1]
                funcaddr = int(ret[0],16)
            line = line.strip().split()
            try:
                add = int(parse("{}:", line[0])[0], 16)
                opcodes = []
#                for i in range(2,5):
#                    opcodes = opcodes.append(int(line[i], 16))
                del line[0:5]
                instructions = " ".join(line)
                dumpdb[add] = {}
                dumpdb[add]["assembly"]       =  instructions
                dumpdb[add]["opcodes"]        = opcodes
                dumpdb[add]["function"]       = func
                dumpdb[add]["function_addr"]  = funcaddr
            except:
                pass
            # Cache it!
        self.dumps[dmp.name] = dumpdb
        return dumpdb

    def action(self, trigger, result):
        id = int(result[0])
        dump = self.getdump()
        address = int(result[1], 16)
        if not address in dump:
            return False
        data = dump[address]
        print("frame[%d] address: 0x%x %30s: %s" % (id, address, data["function"], data["assembly"]))
        return True
