from rumboot.chips.base import chipBase

class mm7705(chipBase):
    part="1888ТХ018"
    chip_id=1
    chip_rev=1
    skipsync=True
    spl_address=0x48000
    warning='''
    This chip has a RumBoot V1 bootloader. 
    RumBootV2 may be flashed onto SPI flash and executed from internal memory
    to provide additional functionality, e.g. xmodem loading
    Please be careful not wipe it! Recovery will be only possible via JTAG/EDCL
    '''
    welcome='host'
    baudrate=1000000
    memories = {
        "spi" : "rumboot-mm7705-PostProduction-updater-spiflash.bin"
    }
    edcl = [
    {   
        "name"   : "Greth 100Mbit #0", 
        "ip"     : "192.168.1.2", 
        "mac"    : "ec:17:66:00:00:02"
    },
    {   
        "name"   : "Greth 100Mbit #1", 
        "ip"     : "192.168.1.3", 
        "mac"    : "ec:17:66:00:00:03"
    },
    {   
        "name"   : "Greth 100Mbit #2", 
        "ip"     : "192.168.1.0", 
        "mac"    : "ec:17:66:00:00:00"
    },
    {   
        "name"   : "Greth 1Gbit #0", 
        "ip"     : "192.168.1.49", 
        "mac"    : "ec:17:66:77:05:01"
    },
    {   
        "name"   : "Greth 1Gbit #1", 
        "ip"     : "192.168.1.48", 
        "mac"    : "ec:17:66:77:05:00"
    }
    ]

    hacks = {
        "skipsync"   : True, # Doesn't Send U\r\n\r\n at the start.
    }

    romdump = "mm7705-v1.dmp"    
    
class basis(chipBase):
    part="1888ВС048"
    chip_id=3
    chip_rev=1
    welcome='host'
    baudrate=115200
    spl_address = 0x40000
    memories = {
        "i2c0-0x50": "rumboot-basis-PostProduction-updater-i2c0-0x50.bin",
        "i2c0-0x51": "rumboot-basis-PostProduction-updater-i2c0-0x51.bin", 
        "i2c0-0x52": "rumboot-basis-PostProduction-updater-i2c0-0x52.bin", 
        "i2c0-0x53": "rumboot-basis-PostProduction-updater-i2c0-0x53.bin",
        "spi0-gpio0_5-cs": "rumboot-basis-PostProduction-updater-spi0-gpio0_5-cs.bin",
        "spi0-internal-cs": "rumboot-basis-PostProduction-updater-spi0-internal-cs.bin",
        "spi1-internal-cs": "rumboot-basis-PostProduction-updater-spi1-internal-cs.bin",
    }
    flashrom = {
        "spi0-gpio0_5-cs": "rumboot-basis-PostProduction-serprog-spi0-gpio0_5-cs.bin",
        "spi0-internal-cs": "rumboot-basis-PostProduction-serprog-spi0-internal-cs.bin",
        "spi1-internal-cs": "rumboot-basis-PostProduction-serprog-spi1-internal-cs.bin",
    }
    romdump = "basis-v1.dmp"    

class oi10(chipBase):
    part="1888ВМ018(A)/1888ВМ01H4"
    chip_id=4
    chip_rev=1
    welcome='host'
    baudrate=115200
    memories = {
        "spi0-internal-cs": "rumboot-oi10-PostProduction-updater-spi-flash-0.bin",
        "nor":  "rumboot-oi10-PostProduction-updater-nor-mt150.04.bin",
        "nor-bootrom":  "rumboot-oi10-PostProduction-updater-nor-mt150.04-brom.bin"
    }
    stub = "rumboot-oi10-PostProduction-gdb-stub.bin"
    romdump = "oi10-v1.dmp"
    gdb = "powerpc-rcm-elf-gdb"
    spl_address = 0xC0000000
    edcl = [
    {   
        "name"   : "Greth #1", 
        "ip"     : "192.168.1.48", 
        "mac"    : "ec:17:66:0e:10:00"
    },
    {   
        "name"   : "Greth #2", 
        "ip"     : "192.168.1.49", 
        "mac"    : "ec:17:66:0e:10:01"
    },
    ]

class bbp3(chipBase):
    part="1888ВС058"
    chip_id=5
    baudrate=115200
    chip_rev=1
    welcome='host'
    baudrate=115200
    spl_address=0x8000
    memories = {
        "spi0-cs0": "rumboot-bbp3-PostProduction-updater-spi0-cs0.bin",
    }
    romdump = "bbp3-v1.dmp"    
    edcl = [
        {   
            "name"   : "GRETH", 
            "ip"     : "192.168.1.48", 
            "mac"    : "ec:17:66:ae:de:30"
        }
    ]

class nm6408(chipBase):
    part="1888ВС058"
    chip_id=6
    chip_rev=1
    welcome='host'
    baudrate=115200
    spl_address = 0x0
    warning='''
    This chip has a legacy ROM bootloader. 
    RumBoot is flashed onto SPI flash and executed from internal memory
    to provide additional functionality
    Please be careful not wipe it! Recovery will be only possible via JTAG
    '''


    #This chip's mac/ip are configurable via 4 boot pins
    #Let's handle it here
    def __populate_6408_edcl_params():
        edcl = []
        for i in range(0,16):
            greth = {   
                "name"   : "GRETH #" + str(i), 
                "ip"     : "192.168.1."+str(i), 
                "mac"    : "ec:17:66:64:08:"+str(i)
            }
            edcl.append(greth)
        return edcl

    edcl = __populate_6408_edcl_params()

    memories = {
        "spi0-cs0": "rumboot-nm6408-PostProduction-updater-spi0-cs0.bin",
    }

    hacks = {
        "skipsync"   : True, # Doesn't Send U\r\n\r\n at the start. All legacy stuff
        "silentRom"  : True, # Bootrom is totally silent
        "noxmodem"   : True,  # Chip lacks xmodem implementation
    }

class mb7707(chipBase):
    part="K1879XB1YA"
    chip_id=2
    chip_rev=1
    welcome='host'
    baudrate=38400
    spl_address = 0x00100000
    warning='''
    This chip has a legacy ROM bootloader. 
    RumBoot is flashed onto NAND flash and executed from internal memory
    to provide additional functionality
    Please be careful not wipe it! Recovery will be only possible via JTAG/EDCL
    '''
    memories = {

    }

    hacks = {
        "skipsync"   : True, # Doesn't Send U\r\n\r\n at the start. All legacy stuff
        "silentRom"  : True, # Bootrom is totally silent
        "noxmodem"   : True,  # Chip lacks xmodem implementation
    }

    edcl = [
        {   
            "name"   : "GRETH", 
            "ip"     : "192.168.1.0", 
            "mac"    : "0:0:5e:0:0:0"
        }
    ]
