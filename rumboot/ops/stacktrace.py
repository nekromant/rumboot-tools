from rumboot.ops.base import base
from parse import parse

class stackframe(base):
    hidden = True
    dumps = {}
    formats = {
        "mcsrr0": "MCSRR0: {}",
        "csrr0":  "CSRR0: {}",
        "srr1":   "SRR0: {}",
        "frame" : "frame[{}] address {}",
        }

    def getdump(self, dmp):
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


    def lookup(self, address):
        dump = self.getdump(self.term.current_dump())
        if not address in dump:
            dump = self.getdump(self.term.dumps["rom"])
        if not address in dump:
            return None
        return dump[address]
        
    def dump_register(self, name, address):
        if address == 0:
            return False
        data = self.lookup(address)
        if data:
            print("%s:  0x%x [%s(): %s]" % (name, address, data["function"], data["assembly"]))
            return True

    def action(self, trigger, result):
        if trigger == "frame":
            id = int(result[0])
            address = int(result[1], 16)
            data = self.lookup(address)
            if data:
                print("%d. 0x%x %30s(): %s" % (id, address, data["function"], data["assembly"]))
                return True
        if trigger == "mcsrr0":
            address = int(result[0].strip(), 16)
            return self.dump_register("MCSRR0", address)
        if trigger == "csrr0":
            address = int(result[0].strip(), 16)
            return self.dump_register("CSRR0", address)
        if trigger == "csrr1":
            address = int(result[0].strip(), 16)
            return self.dump_register("CSRR1", address)


