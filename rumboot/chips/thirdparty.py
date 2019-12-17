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

class chipRPI4(chipBase):
    name="rpi4"
    part="BCM2711 (Raspberry Pi 4)"
    chip_id=255
    baudrate=115200
    chip_rev=2
    welcome='U-Boot> '
    baudrate=115200
    memories = {}