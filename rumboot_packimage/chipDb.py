class chipBase:
    name="name"
    part="part"
    chip_id=0
    chip_rev=0
    baudrate=115200

class chipMM7705:
    name="mm7705"
    part="1888ТХ018"
    chip_id=1
    chip_rev=1
    welcome='host'
    baudrate=1000000

class chipBasis:
    name="basis"
    part="1888ВС048"
    chip_id=3
    chip_rev=1
    welcome='host'
    baudrate=115200
    memories = {
        "i2c0-0x50": "rumboot-basis-PostProduction-updater-i2c0-0x50.bin",
        "i2c0-0x51": "rumboot-basis-PostProduction-updater-i2c0-0x51.bin", 
        "i2c0-0x52": "rumboot-basis-PostProduction-updater-i2c0-0x52.bin", 
        "i2c0-0x53": "rumboot-basis-PostProduction-updater-i2c0-0x53.bin",
        "spi0-gpio0_5-cs": "rumboot-basis-PostProduction-updater-spi0-gpio0_5-cs.bin",
        "spi0-internal-cs": "rumboot-basis-PostProduction-updater-spi0-internal-cs.bin",
        "spi1-internal-cs": "rumboot-basis-PostProduction-updater-spi1-internal-cs.bin",
    }

class chipOI10:
    name="bbp3"
    part="???"
    chip_id=4
    chip_rev=1
    welcome='host'
    baudrate=115200

class chipBBP3:
    name="bbp3"
    part="???"
    chip_id=5
    chip_rev=1
    welcome='host'
    baudrate=115200


class chipDb:
    chips = {chipMM7705, chipBasis,chipOI10, chipBBP3}
    
    def query(self, id, rev):
        for c in self.chips:
            if c.chip_id == id and c.chip_rev == rev:
                return c
        return None
    