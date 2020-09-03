from rumboot.chips.base import chipBase

class chipZynq(chipBase):
    name="zed"
    part="Xilinx Zynq series (Zed Board, Tang Hex, ...)"
    chip_id=255
    baudrate=115200
    chip_rev=1
    welcome='Zynq> '
    baudrate=115200
    memories = {}
    spl_address = 0x100
    hacks = {
        "skipsync"   : True, # Doesn't Send U\r\n\r\n at the start. All legacy stuff
        "silentRom"  : False, # Bootrom is totally silent
        "noxmodem"   : False,  # Chip lacks xmodem implementation
    }

class chipRPI4(chipBase):
    name="rpi4"
    part="BCM2711 (Raspberry Pi 4)"
    chip_id=255
    baudrate=115200
    chip_rev=2
    welcome='U-Boot> '
    baudrate=115200
    memories = {}