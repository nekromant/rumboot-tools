class chipBase:
    name = "whatever" # Will be replaced by class name during load!
    part="part"
    chip_id=0
    chip_rev=0
    gdb = "gdb"
    baudrate=115200
    warning=None
    memories = {}
    dumps = {}
    hacks = {
        "skipsync"   : False, # Doesn't Send U\r\n\r\n at the start. All legacy stuff
        "edclArpBug" : False, # EDCL doesn't have a valid IP, needs a static ARP entry (mb7707)
        "silentRom"  : False, # Bootrom is totally silent
        "noxmodem"   : False,  # Chip lacks xmodem implementation
        "noedcl"     : False  # Chip lacks edcl implementation
    }

    edcl = None
    

