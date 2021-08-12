class MacGenerator():
    macs = {}

    def __init__(self, chip_id = 0, board_id = 0, oui = "EC:17:66"):
        self.oui = oui
        self.chip_id = chip_id
        self.board_id = board_id

    def get(self, id: int, iface :int):
        if not id in self.macs:
            self.macs[id] = [ chip_id % 256, board_id % 256, random.randrange(0,255) & 0xF8 ]
        b = self.macs[id]
        return f"{self.oui}:{b[0]:X}:{b[1]:X}:{b[2] | iface :X}"
