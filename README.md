# RumBoot Loader Tools

## Summary
This repository is home to a set of tools to create, update and run rumboot v1, v2 and other images
This repository contains several tools


* _rumboot-packimage_ - Adds/prints/updates checksums in image files
* _rumboot-xrun_ - Directly executes images via serial line or network
* _rumboot-gdb_ - Debug your binaries, even without JTAG
* _rumboot-xflash_ - Write on-board memories via serial line or network (Simple interface)
* _rumboot-flashrom_ - Wrapper around flashrom tool for advanced SPI flash programming
* _rumboot-daemon_ - Provides network shared access to different boards



Sounds like too much? How you are you expected to use them in your app? 

* Use _rumboot-packimage_ to add valid checksums to your binaries, so that bootrom would accept them

* Run them via UART using _rumboot-xrun_ (or your favourite jtag tool), flash them via _rumboot-xflash_

* If rumboot-xflash doesn't work with your SPI Flash chip, check out _rumboot-flashrom_ instead

* Have only one board for a few developers? Want easy remote access during COVID-19 or some other epidemic? Check out _rumboot-daemon_. 

* Want to combine a set of tests into one image? Check out the _rumboot-combine_ tool.

## Chip IDs 

rumboot-tools use IDs to identify chips. Every supported chip has it's own id. 


Platform Name  | Part Number             | Endianess | #Cores | ChipID | ChipRev | Image Format 
-------------- | ----------------------- | --------- | ------ | ------ | ------- | ------------
mm7705         | 1888ТХ018               | big       | 2      | 1      | 1       | RumBoot V1
mb7707         | К1879ХБ1YA              | little    | -      | 2      | 1       | Legacy K1879XB1YA
basis          | 1888ВС048               | little    | 1      | 3      | 1       | RumBoot V2
oi10           | 1888ВМ018(A)/1888ВМ01H4 | big       | 1      | 4      | 1       | RumBoot V2
bbp3           | 1888ВС058               | little    | 1      | 5      | 1       | RumBoot V2
nm6408         | 1888ВС058               | little    | 1      | 6      | 1       | Legacy NM6408
-------------- | ----------------------- | --------- | ------ | ------ | ------- | -------------
zed            | Zed Board / Tang Hex    | little    | 2      | 255    | 1       | Other
rpi4           | BCM2711 (Raspberry Pi 4)| little    | 4      | 255    | 2       | Other

Since different chips have different ROM loaders, default baudrates, flash memories and etc., some tools require you either set ChipId explicitly (via -c option) or try their best to guess it from image file header. Only newer (rumboot V2 and later) image formats have a dedicated field called chip_id. 

You can either specify chip id via it's number or via platform name, whichever suits you. (`-c 2` and `-c mb7707` do the same).

For rumboot v2 and later, if the chip id doesn't match the one in silicon, the image is considered invalid

Thirdparty chips that are used for testing and prototyping always have chip id set as 255. 

The chip revision may be used to distinguish different versions of the same chip, if any. It is only
supported by Rumboot V2 headers and later. If Chip revision of the file you are uploading and the one stored 
in silicon don't match - you'll get a warning.

## EDCL Notes

### Basic stuff
Uart is the simplest possible interface for all debugging stuff, but it's also quite slow if you are going
to send huge files (e.g. linux kernel, initrd, etc.) Starting with version 0.9.4 rumboot-tools support a side-channel to do data transfers. Right now the only possible sidechannel is EDCL.

EDCL stands for 'Ethernet communications debug link'. It provides a way to access physical memory via a special protocol over UDP. It exists in all RC Module's chips (except 'basis' platform). The protocol has *NO* security at all, so please disable edcl in a production enviroment. If you didn't get it, I'll write it in *bold*:

*NEVER ENABLE EDCL IN A PRODUCTION ENVIRONMENT* 

### Seting up

EDCL IP and MAC adresses are hardcoded in silicon. Therefore putting several same chips in one LAN is not likely to work. The recommended setup is a dedicated network interface directly connected to the target board.
the interface should have an IP _192.168.0.1_ netmask _255.255.0.0_

After the interface setup is done, just add _-e_ option for xrun/xflash and enjoy

### ARP Bugs and workarounds

Some old chips have an invalid IP set as 192.168.0.0. The OS will discard ARP replies as invalid. However since EDCL only checks mac, we can set a static ARP record. The xrun does that automatically when needed using sudo/runas on linux/windows respectively. If a static record exists, no static record is added.

### IP clash bug and workarounds 

Okay, so despite the warning above, you want to use several different chips in the same LAN and noticed that different chips (e.g. mm7705 and oi10) have the same IP, though MACs are unique. There's a special flag called 
--force-static-arp that make xrun/xflash always drop arp existing records (if any) and add proper ones.
Just note that this usage case is 'officially' unsupported. 

## Requirements

* Python 3.7 or above

* pyserial

* pyft232 

* parse

* xmodem

* tqdm

* pyyaml

* pyusb

* gdbgui

* arpreq

* netifaces

* netaddr

* getmac

## Installation

```
    pip3 install .
```

or 

```
    pip3 install .
```

P.S. Make sure you have a proper internet connection, or pip will fail to fetch dependencies.

## Tool descriptions

### rumboot-packimage
#### Description

This tool adds/checks/updates checksums in existing images. The image must already have a proper header placed by the linker. 

#### Options 

```
~# rumboot-packimage --help
usage: rumboot-packimage [-h] -f FILE [-i] [-c] [-C] [-r] [-R relocation] [-Z]
                         [-U] [-z value] [-a value] [-F value value]
                         [--set-data offset value] [-g key] [-s key value]
                         [-e] [-w WRAP]

rumboot-packimage 0.9.7 - Universal RumBoot Image Manipulation Tool

(C) 2018-2021 Andrew Andrianov <andrew@ncrmnt.org>, RC Module
https://module.ru
https://github.com/RC-MODULE

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  image file
  -i, --info            Show information about the image
  -c, --checksum        This option will modify the file! Calculates valid
                        checksums to the header. The length is set to cover
                        the full length of file only if it's non-zero.
  -C, --checksum_fix_length
                        This option will modify the file! The same as
                        --checksum, but always overrides length with the
                        actual length of file
  -r, --raw             Display raw header field names
  -R relocation, --relocate relocation
                        Tell bootrom to relocate the image at the specified
                        address before executing it. Only RumBootV3 and above
  -Z, --compress        Compress image data with heatshrink algorithm (V3 or
                        above only)
  -U, --decompress      Decompress image data with heatshrink algorithm (V3 or
                        above only)
  -z value, --add_zeroes value
                        This option will add N bytes of zeroes to the end of
                        the file (after checksummed area). This is required to
                        avoid propagating 'X' during the next image check
                        during simulation. Normally, you do not need this
                        option
  -a value, --align value
                        Pad resulting image size to specified alignment
  -F value value, --flag value value
                        Set image flag to a desired value. Only RumBootV3 or
                        above
  --set-data offset value
                        Sets data at byte 'offset' to value 'offset'
  -g key, --get key     Get a single field from header. Nothing else will be
                        printed. NOTE: The value will be formatted as hex
  -s key value, --set key value
                        This option will modify the file! Set a header key to
                        specified value. Use -r flag on an existing image to
                        find out what keys exist. Use -c to update the
                        checksums
  -e, --reverse-endianness
                        Use this option to reverse endianness of all headers.
                        This will not touch data. For testing only
  -w WRAP, --wrap WRAP  Use this option to wrap arbitrary data to V1/V2/V3
                        images.

```

#### Typical uses

##### Check if an image file is valid

```
~# rumboot-packimage -f myimage.bin
```

This command will silently validate an image and exit code 0 if everything's okay. 1 if something isn't right. Useful for scripts.

##### Dump header information

```
~# rumboot-packimage -f image.bin -i

Detected RumBootV1 image, endian: big
=== RumBootV1 Header Information ===
Endianess:              big
Magic:                  0xbeefc0de
Data Length:            69108
Header CRC32:           0x1e955d90 [Valid]
Data CRC32:             0x1929eb8e [Valid]

```

This command will dump all header contents of a file

##### Write correct data length and checksums to the image

```
~# rumboot-packimage -f image.bin -с

Detected RumBootV1 image, endian: big
Wrote valid checksums to image header
=== RumBootV1 Header Information ===
Endianess:              big
Magic:                  0xbeefc0de
Data Length:            69108
Header CRC32:           0x1e955d90 [Valid]
Data CRC32:             0x1929eb8e [Valid]
```


### rumboot-xrun
#### Description

This tool directly uploads a binary to the target board, executes it and provides you with human-readable output. It also resets the board if necessary.

#### Options 

```
~# rumboot-xrun --help
[!] Using configuration file: /home/necromant/.rumboot.yaml
usage: rumboot-xrun [-h] [-f FILE] [-c chip_id] [-l LOG] [-p port] [-b speed]
                    [-e] [--force-static-arp] [-r method]
                    [--apc-host APC_HOST] [--apc-user APC_USER]
                    [--apc-pass APC_PASS] [--apc-outlet APC_OUTLET] [-S value]
                    [-P value] [--pl2303-invert] [--redd-port REDD_PORT]
                    [--redd-relay-id REDD_RELAY_ID]
                    [-A [PLUSARGS [PLUSARGS ...]]] [-R] [-I]
                    [--replay-no-exit]

rumboot-xrun 0.9.7 - RumBoot X-Modem execution tool

(C) 2018-2021 Andrew Andrianov <andrew@ncrmnt.org>, RC Module
https://module.ru
https://github.com/RC-MODULE

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Image file (may be specified multiple times)
  -R, --rebuild         Attempt to rebuild/update target before uploading
  -I, --stdin           Use stdin redirection to tty
  --replay-no-exit      Do not exit on panics/rom returns when replaying logs
                        (for batch analysis)

File Handling:
  -c chip_id, --chip_id chip_id
                        Override chip id (by name or chip_id)

Connection Settings:
  -l LOG, --log LOG     Log terminal output to file
  -p port, --port port  Serial port to use
  -b speed, --baud speed
                        Serial line speed
  -e, --edcl            Use edcl for data uploads (when possible)
  --force-static-arp    Always add static ARP entries

Reset Sequence options:
  These options control how the target board will be reset

  -r method, --reset method
                        Reset sequence to use (apc base mt12505 pl2303
                        powerhub redd)

apc reset sequence options:
  --apc-host APC_HOST   APC IP Address/hostname
  --apc-user APC_USER   APC IP username
  --apc-pass APC_PASS   APC IP username
  --apc-outlet APC_OUTLET
                        APC power outlet to use

mt12505 reset sequence options:
  -S value, --ft232-serial value
                        FT232 serial number for MT125.05

pl2303 reset sequence options:
  -P value, --pl2303-port value
                        PL2303 physical port
  --pl2303-invert       Invert all pl2303 gpio signals

redd reset sequence options:
  --redd-port REDD_PORT
                        Redd serial port (e.g. /dev/ttyACM1)
  --redd-relay-id REDD_RELAY_ID
                        Redd Relay Id (e.g. A)

Plusargs parser options:
  
          rumboot-xrun can parse plusargs (similar to verilog simulator)
          and use them for runtime file uploads. This option is intended
          to be used for
          

  -A [PLUSARGS [PLUSARGS ...]], --plusargs [PLUSARGS [PLUSARGS ...]]

```

#### Configuration file

The rumboot-xrun tries to find a configuration file on your system in the following locations:

* ~/.rumboot.yaml

* /etc/rumboot.yaml

Example configuration file is provided below:

```yaml
xrun:
    defaults:
        port: /dev/ttyUSB0
    chips:
        oi10:   
            port: /dev/ttyUSB1
            baudrate: 19200
        basis:  
            port: /dev/ttyUSB2
        mm7705: 
            port: socket://10.7.11.59:10002
```

The configuration file contains default ports and speeds for all known chip ids. If you supply a file to rumboot-xrun without any other options, rumboot-xrun will find out the chip id from the header file and set default port and baudrate accordingly. 

If no configuration file can be found in any location, the default serial port will be /dev/ttyUSB0. Default baudrate will be taken from the internal chip database and should match most typical settings


#### Typical usage
##### Execute a file on bare metal enviroment

```
~# rumboot-xrun -f myimage.bin -p /dev/ttyUSB0
Detected chip:    oi10 (1888ВМ018(A)/1888ВМ01H4)
Reset method:     None
Baudrate:         115200 bps
Port:             /dev/ttyUSB0
Please, power-cycle board






    RC Module's          __                __
   _______  ______ ___  / /_  ____  ____  / /_
  / ___/ / / / __ `__ \/ __ \/ __ \/ __ \/ __/
 / /  / /_/ / / / / / / /_/ / /_/ / /_/ / /_
/_/   \__,_/_/ /_/ /_/_.___/\____/\____/\__/
oi10 | Production | HEAD-0a2dc3a8
--- RumBoot Configuration ---
Force Host Mode: enabled
Selftest:        disabled
EDCL/RMAP:       enabled
UART speed:      115200 bps
Max SPL size:    131072 bytes
SD Card:         Not inserted
CPU ECC:         disabled
NOR/SRAM ECC:    disabled
Direct NOR boot: disabled
Reset cause:     SCTL: 0x800 SPR_DBCR0: 0x0
---          ---          ---
boot: host: Entering Host Mode
boot: host: GRETH0 EDCL MAC: ec:17:66:e:10:0 IP: 192.168.1.48
boot: host: GRETH1 EDCL MAC: ec:17:66:e:10:1 IP: 192.168.1.49
boot: host: Hit 'X' for X-Modem upload



boot: host: Received 40960 bytes, executing in 100ms
boot: host: --- Boot Image Header ---
boot: host: Magic:            0xb01dface
boot: host: Header version:   2
boot: host: Chip Id:          4
boot: host: Chip Revision:    1
boot: host: Data length:      40800
boot: host: Header CRC32:     0xb47a8252
boot: host: Data CRC32:       0x87065aa6
boot: host: ---        ---        ---
Hello, World!
boot: host: Back in rom, code 0

```

This command waits for bootrom prompt, uploads a file via xmodem and prints everything received to stdout acting pretty much the same, as your favorite terminal program. The exit code from the program will be the exit code of rumboot-run (0 in the example above), therefore you can rumboot-xrun in your scripts during unit-testing.

NOTE: Make sure the jumpers on the board are set to 'host mode'. After running the command press the reset button or supply power to the board.

##### Start u-boot and enter interactive prompt

```
~# rumboot-xrun -f spl/u-boot-spl-dtb.rbi -f u-boot-dtb.img -e -I -r pl2303

Detected chip:    oi10 (1888ВМ018(A)/1888ВМ01H4)
pl2303: /dev/ttyUSB8 detected at USB path 2-1.2
Reset method:               pl2303
Baudrate:                   115200 bps
Port:                       /dev/ttyUSB8
Preferred data transport:   xmodem



    RC Module's                           
   _______  ______ ___  / /_  ____  ____  / /_
  / ___/ / / /  ` \/  \/  \/  \/ /
 / /  / /_/ / / / / / / /_/ / /_/ / /_/ / /_  
/_/   \__,_/_/ /_/ /_/_.___/\____/\____/\__/  
oi10 | Production | HEAD-0a2dc3a8
--- RumBoot Configuration ---
Force Host Mode: enabled
Selftest:        disabled
EDCL/RMAP:       enabled
UART speed:      115200 bps
Max SPL size:    131072 bytes
SD Card:         Inserted
CPU ECC:         enabled
NOR/SRAM ECC:    disabled
Direct NOR boot: disabled
Reset cause:     SCTL: 0x800 SPR_DBCR0: 0x0
---          ---          ---
boot: host: Entering Host Mode
boot: host: GRETH0 EDCL MAC: ec:17:66:e:10:0 IP: 192.168.1.48
boot: host: GRETH1 EDCL MAC: ec:17:66:e:10:1 IP: 192.168.1.49
boot: host: Hit 'X' for X-Modem upload
Sending binary: 43.0kB [00:06, 6.73kB/s]                                        



boot: host: Received 44032 bytes, executing in 100ms
boot: host: --- Boot Image Header ---
boot: host: Magic:            0xb01dface
boot: host: Header version:   2
boot: host: Chip Id:          4
boot: host: Chip Revision:    1
boot: host: Data length:      43907
boot: host: Header CRC32:     0xb6bc96ec
boot: host: Data CRC32:       0x6fd63f77
boot: host: ---        ---        ---

U-Boot SPL 2020.04-rc1-g67f6b3d9a6-dirty (Jul 21 2020 - 11:50:55 +0300)
Testing SDRAM...
Trying to boot from RUMBOOT
Skip rumboot chain - host mode
Trying to boot from X-MODEM/EDCL
UPLOAD to 0x21e00000. 'X' for X-modem, 'E' for EDCL
Sending binary: 296kB [00:29, 10.4kB/s]                                         
 xyzModem - CRC mode, 0(SOH)/296(STX)/0(CAN) packets, 0 retries
Loaded 302430 bytes
The image has been loaded


U-Boot 2020.04-rc1-g67f6b3d9a6-dirty (Jul 21 2020 - 11:50:55 +0300)

CPU:   RC Module PowerPC 476FP core
Model: RCM MB150-02
DRAM:  32 MiB
MMC:   mmc0@D002C000: 0
Loading Environment from MMC... OK
In:    uart0@D0029000
Out:   uart0@D0029000
Err:   uart0@D0029000
Net:   eth0: greth0@D002A000
Hit any key to stop autoboot:  0 
=>

```

This command resets the board, uploads u-boot spl, u-boot and enters interactive mode for you to play with.
The uploads are performed using xmodem.

##### Start u-boot and enter interactive prompt, prefer edcl for uploads

```
~# rumboot-xrun -f spl/u-boot-spl-dtb.rbi -f u-boot-dtb.img -e -I -r pl2303

Detected chip:    oi10 (1888ВМ018(A)/1888ВМ01H4)
pl2303: /dev/ttyUSB8 detected at USB path 2-1.2
Reset method:               pl2303
Baudrate:                   115200 bps
Port:                       /dev/ttyUSB8
Preferred data transport:   edcl



    RC Module's                           
   _______  ______ ___  / /_  ____  ____  / /_
  / ___/ / / /  ` \/  \/  \/  \/ /
 / /  / /_/ / / / / / / /_/ / /_/ / /_/ / /_  
/_/   \__,_/_/ /_/ /_/_.___/\____/\____/\__/  
oi10 | Production | HEAD-0a2dc3a8
--- RumBoot Configuration ---
Force Host Mode: enabled
Selftest:        disabled
EDCL/RMAP:       enabled
UART speed:      115200 bps
Max SPL size:    131072 bytes
SD Card:         Inserted
CPU ECC:         enabled
NOR/SRAM ECC:    disabled
Direct NOR boot: disabled
Reset cause:     SCTL: 0x800 SPR_DBCR0: 0x0
---          ---          ---
boot: host: Entering Host Mode
boot: host: GRETH0 EDCL MAC: ec:17:66:e:10:0 IP: 192.168.1.48
boot: host: GRETH1 EDCL MAC: ec:17:66:e:10:1 IP: 192.168.1.49
boot: host: Hit 'X' for X-Modem upload
Connected: oi10 (Greth #1)
Sending binary: 100%|█████████████████████▉| 42.9k/42.9k [00:00<00:00, 1.15MB/s]
boot: host: --- Boot Image Header ---
boot: host: Magic:            0xb01dface
boot: host: Header version:   2
boot: host: Chip Id:          4
boot: host: Chip Revision:    1
boot: host: Data length:      43907
boot: host: Header CRC32:     0xb6bc96ec
boot: host: Data CRC32:       0x6fd63f77
boot: host: ---        ---        ---

U-Boot SPL 2020.04-rc1-g67f6b3d9a6-dirty (Jul 21 2020 - 11:50:55 +0300)
Testing SDRAM...
Trying to boot from RUMBOOT
Skip rumboot chain - host mode
Trying to boot from X-MODEM/EDCL
UPLOAD to 0x21e00000. 'X' for X-modem, 'E' for EDCL
Sending binary: 100%|███████████████████████▉| 295k/295k [00:00<00:00, 1.18MB/s]
The image has been loaded


U-Boot 2020.04-rc1-g67f6b3d9a6-dirty (Jul 21 2020 - 11:50:55 +0300)

CPU:   RC Module PowerPC 476FP core
Model: RCM MB150-02
DRAM:  32 MiB
MMC:   mmc0@D002C000: 0
Loading Environment from MMC... OK
In:    uart0@D0029000
Out:   uart0@D0029000
Err:   uart0@D0029000
Net:   eth0: greth0@D002A000
Hit any key to stop autoboot:  0 
=>
```

This command resets the board, uploads u-boot spl, u-boot and enters interactive mode for you to play with.
The uploads are performed using edcl side-channel.

##### Execute a file, custom port/speed, automatically reset board via pl2303

```
~# rumboot-xrun -f myimage.bin -p /dev/ttyUSB0 -b 19200 -r pl2303
```
The -r option specifies one of the ways to reset board. For more info on
board reset mechanism, please see Appendix A

##### Execute a chain of files without reset

```
~# rumboot-xrun -f init_ddr.bin -f test_ddr.bin -r pl2303
```

The -f option can be specified multiple times. Every image should exit with code 0 for the chain to move on. (See rumboot docs for more about this logic)

##### Log serial output to a file

```
~# rumboot-xrun -f init_ddr.bin -f test_ddr.bin -l uart.log
```

The -l option can be used to log output to a file

##### Using stdin

```
~# rumboot-xrun -f init_ddr.bin -I 
```

The -I options makes the terminal _bi-directional_. E.g. You can not only see what the board sends you, but you can also type in some commands. 

##### Auto-rebuilding project

```
~# rumboot-xrun -R -f example.bin 
```

The -R options convenience option invokes automatically _cmake --build example.all_ in the directory with the binary file. The target name is calculating by changing .bin to .all. This is hardcoded for 'rumboot' SDK for now.

##### Automatic stack trace decoding

rumboot-xrun provides a mechanism to decode runtime stack traces. To use this functionality, you have to place a .dmp file with disassembly in the same directory and with the same name as the .bin file


### rumboot-gdb
#### Description

This tool uploads gdb stub to the target board and starts _gdb_ or _gdbgui_ for debugging. The board is reset if necessary. The stub provides easy access to debugging even without using JTAG. Unlike most tools, this tool accepts ELF binaries, not .bin files. For debugging you app should be compiled with _-gdwarf-2_ option.

Limitations:

- GDB stub occupies some of the internal memory and MUST own some of the exception vectors. If your apps uses IRQs, see notes below
- At the moment only _powerpc_ is supported (mm7705, oi10)
- No SMP debugging possible
- Printf's in your app should either be disabled, or redirected via a gdbmon syscall
- Since getting Chip Id from supplied elf is difficult, user should always specify target chip id manually
- GDB 'run' command doesn't work correctly and may crash gdb. Use 'load' and 'continue' to start the application

#### Options 

```
~# rumboot-gdb --help

```
```
  rumboot-gdb -c oi10 -f rumboot-oi10-PostProduction-simple-iram-hello
```

##### Rebuild the application file, then launch commandline gdb 
```
  rumboot-gdb -c oi10 -Rf rumboot-oi10-PostProduction-simple-iram-hello
```

##### Rebuild the application file, launch commandline gdb, load the file into memory
```
  rumboot-gdb -c oi10 -Rf rumboot-oi10-PostProduction-simple-iram-hello -L
```

##### Same as the above, but start with a graphical user interface (gdbgui)
```
  rumboot-gdb -c oi10 -Rf rumboot-oi10-PostProduction-simple-iram-hello -LG
```

##### Rebuild the application file, launch commandline gdb, load the file into memory and start it
```
  rumboot-gdb -c oi10 -Rf rumboot-oi10-PostProduction-simple-iram-hello -E
```

### rumboot-xflash
#### Description

This tool allows you to quickly program different flashes attached to the target chip. It is done by uploading a precompiled stub that implements the programming protocol of the target flash media and accepts an xmodem payload. Pre-compiled stubs are shipped with rumboot-tools.

#### Options 

```
~# rumboot-xflash --help
[!] Using configuration file: /home/necromant/.rumboot.yaml
usage: rumboot-xflash [-h] [-f FILE] [-c chip_id] [-l LOG] [-p port]
                      [-b speed] [-e] [--force-static-arp] [-v] -m memory
                      [-z SPL_PATH] [-r method] [--apc-host APC_HOST]
                      [--apc-user APC_USER] [--apc-pass APC_PASS]
                      [--apc-outlet APC_OUTLET] [-S value] [-P value]
                      [--pl2303-invert] [--redd-port REDD_PORT]
                      [--redd-relay-id REDD_RELAY_ID]

rumboot-xflash 0.9.7 - RumBoot X-Modem firmware update tool

(C) 2018-2021 Andrew Andrianov <andrew@ncrmnt.org>, RC Module
https://module.ru
https://github.com/RC-MODULE

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Image file (may be specified multiple times)
  -v, --verbose         Print serial debug messages during update
  -m memory, --memory memory
                        Memory program. Help for a list of memories
  -z SPL_PATH, --spl-path SPL_PATH
                        Path for SPL writers (Debug only)

File Handling:
  -c chip_id, --chip_id chip_id
                        Override chip id (by name or chip_id)

Connection Settings:
  -l LOG, --log LOG     Log terminal output to file
  -p port, --port port  Serial port to use
  -b speed, --baud speed
                        Serial line speed
  -e, --edcl            Use edcl for data uploads (when possible)
  --force-static-arp    Always add static ARP entries

Reset Sequence options:
  These options control how the target board will be reset

  -r method, --reset method
                        Reset sequence to use (apc base mt12505 pl2303
                        powerhub redd)

apc reset sequence options:
  --apc-host APC_HOST   APC IP Address/hostname
  --apc-user APC_USER   APC IP username
  --apc-pass APC_PASS   APC IP username
  --apc-outlet APC_OUTLET
                        APC power outlet to use

mt12505 reset sequence options:
  -S value, --ft232-serial value
                        FT232 serial number for MT125.05

pl2303 reset sequence options:
  -P value, --pl2303-port value
                        PL2303 physical port
  --pl2303-invert       Invert all pl2303 gpio signals

redd reset sequence options:
  --redd-port REDD_PORT
                        Redd serial port (e.g. /dev/ttyACM1)
  --redd-relay-id REDD_RELAY_ID
                        Redd Relay Id (e.g. A)

```
```
~# rumboot-xflash -m help -c basis
Memory        i2c0-0x50: rumboot-basis-PostProduction-updater-i2c0-0x50.bin
Memory        i2c0-0x51: rumboot-basis-PostProduction-updater-i2c0-0x51.bin
Memory        i2c0-0x52: rumboot-basis-PostProduction-updater-i2c0-0x52.bin
Memory        i2c0-0x53: rumboot-basis-PostProduction-updater-i2c0-0x53.bin
Memory  spi0-gpio0_5-cs: rumboot-basis-PostProduction-updater-spi0-gpio0_5-cs.bin
Memory spi0-internal-cs: rumboot-basis-PostProduction-updater-spi0-internal-cs.bin
Memory spi1-internal-cs: rumboot-basis-PostProduction-updater-spi1-internal-cs.bin
```

Or you can just specify the file you are going to flash instead.

```
~# rumboot-xflash -m help -f ../build-test/oi10-PostProduction/rumboot-oi10-PostProduction-simple-iram-hello.bin 
Memory spi0-internal-cs: rumboot-oi10-PostProduction-updater-spi-flash-0.bin
Memory              nor: rumboot-oi10-PostProduction-updater-nor-mt150.04.bin
Memory      nor-bootrom: rumboot-oi10-PostProduction-updater-nor-mt150.04-brom.bin
```

##### Write image to flash

```
~# rumboot-xflash -m spi0-gpio0_5-cs -f rumboot-basis-PostProduction-simple-iram-hello-iram.bin

Detected chip:    basis (1888ВС048)
Reset method:     None
Baudrate:         115200 bps
Port:             /dev/ttyUSB0
Sending stream: 100%|███████████████████████████████| 13.6k/13.6k [00:21<00:00, 650B/s]
Writing image: 100%|████████████████████████████████| 62.9k/62.9k [01:29<00:00, 717B/s]

```

##### Write image to flash, reset automatically via pl2303

```
~# rumboot-xflash -m spi0-gpio0_5-cs -f rumboot-basis-PostProduction-simple-iram-hello-iram.bin -r pl2303

Detected chip:    basis (1888ВС048)
Reset method:     None
Baudrate:         115200 bps
Port:             /dev/ttyUSB0
Sending stream: 100%|███████████████████████████████| 13.6k/13.6k [00:21<00:00, 650B/s]
Writing image: 100%|████████████████████████████████| 62.9k/62.9k [01:29<00:00, 717B/s]

```

##### Write raw data to flash, overriding chip id

```
~# rumboot-xflash -c basis -m spi0-gpio0_5-cs -f raw.bin

Detected chip:    basis (1888ВС048)
Reset method:     None
Baudrate:         115200 bps
Port:             /dev/ttyUSB0
Sending stream: 100%|███████████████████████████████| 13.6k/13.6k [00:21<00:00, 650B/s]
Writing image: 100%|████████████████████████████████| 62.9k/62.9k [01:29<00:00, 717B/s]

```


##### Write raw data to flash over network

```
~# rumboot-xflash -c basis -m spi0-gpio0_5-cs -f raw.bin -p socket://10.7.11.59:10001

Detected chip:    basis (1888ВС048)
Reset method:     None
Baudrate:         115200 bps
Port:             socket://10.7.11.59:10001
Sending stream: 100%|███████████████████████████████| 13.6k/13.6k [00:21<00:00, 650B/s]
Writing image: 100%|████████████████████████████████| 62.9k/62.9k [01:29<00:00, 717B/s]

```

### rumboot-flashrom
#### Description

This tool works as a flashrom (http://flashrom.org) frontend/wrapper and allows you to read/write SPI flash chips that are (for some reasons) unsupported by rumboot-xflash. It works by uploading a stub that implements serprog protocol and attaching the flashrom to it. This tool can be used along with boards accesible via _rumboot-daemon_ over the network.


#### Options 

This tool works differently, compared to other tools. It accepts two sets of arguments:
* rumboot-flashrom arguments. They are needed to configure port, reset, find & upload stub etc.
* flashrom options. These are passed directly to flashrom utility. They do all the work.

In the example below

```
rumboot-flashrom -p /dev/ttyUSB1 -c basis -- --read img.bin
```

* _-p /dev/ttyUSB1 -c basis_ are rumboot-flashrom's options. 
* -- is the separator
* _--read img.bin_ are the flashrom options

```
~# rumboot-flashrom --help
[!] Using configuration file: /home/necromant/.rumboot.yaml
usage: rumboot-flashrom [-h] [-l LOG] [-p port] [-b speed] [-e]
                        [--force-static-arp] [-v] -m memory [-z SPL_PATH]
                        [-f FLASHROM_PATH] -c CHIP_ID [-r method]
                        [--apc-host APC_HOST] [--apc-user APC_USER]
                        [--apc-pass APC_PASS] [--apc-outlet APC_OUTLET]
                        [-S value] [-P value] [--pl2303-invert]
                        [--redd-port REDD_PORT]
                        [--redd-relay-id REDD_RELAY_ID]
                        ...

rumboot-flashrom 0.9.7 - flashrom wrapper tool

(C) 2018-2021 Andrew Andrianov <andrew@ncrmnt.org>, RC Module
https://module.ru
https://github.com/RC-MODULE

positional arguments:
  remaining             Flashrom arguments

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Print serial debug messages during preload phase
  -m memory, --memory memory
                        SPI bus to use. Names match '-m help' of rumboot-
                        xflash
  -z SPL_PATH, --spl-path SPL_PATH
                        Path for SPL writers (Debug only)
  -f FLASHROM_PATH, --flashrom-path FLASHROM_PATH
                        Path to flashrom binary
  -c CHIP_ID, --chip_id CHIP_ID
                        Chip Id (numeric or name)

Connection Settings:
  -l LOG, --log LOG     Log terminal output to file
  -p port, --port port  Serial port to use
  -b speed, --baud speed
                        Serial line speed
  -e, --edcl            Use edcl for data uploads (when possible)
  --force-static-arp    Always add static ARP entries

Reset Sequence options:
  These options control how the target board will be reset

  -r method, --reset method
                        Reset sequence to use (apc base mt12505 pl2303
                        powerhub redd)

apc reset sequence options:
  --apc-host APC_HOST   APC IP Address/hostname
  --apc-user APC_USER   APC IP username
  --apc-pass APC_PASS   APC IP username
  --apc-outlet APC_OUTLET
                        APC power outlet to use

mt12505 reset sequence options:
  -S value, --ft232-serial value
                        FT232 serial number for MT125.05

pl2303 reset sequence options:
  -P value, --pl2303-port value
                        PL2303 physical port
  --pl2303-invert       Invert all pl2303 gpio signals

redd reset sequence options:
  --redd-port REDD_PORT
                        Redd serial port (e.g. /dev/ttyACM1)
  --redd-relay-id REDD_RELAY_ID
                        Redd Relay Id (e.g. A)

```
```
~# rumboot-flashrom -c basis -m spi0-gpio0_5-cs 
Detected chip:    basis (1888ВС048)
SPL               rumboot-basis-PostProduction-serprog-spi0-gpio0_5-cs.bin
Reset method:     None
Baudrate:         115200 bps
Port:             socket://10.7.11.59:10001
FlashRom:         /usr/sbin/flashrom
FlashRom args:    
Sending stream: 100%|████████████████████████| 10.6k/10.6k [00:16<00:00, 659B/s]
Serprog stub ready!
Trying port 20000
Invoking flashrom: /usr/sbin/flashrom -p serprog:ip=127.0.0.1:20000 
flashrom  on Linux 4.19.0-5-amd64 (x86_64)
flashrom is free software, get the source code at https://flashrom.org

Using clock_gettime for delay loops (clk_id: 1, resolution: 1ns).
serprog: Programmer name is "rumboot:basis"
serprog: requested mapping AT45CS1282 is incompatible: 0x1080000 bytes at 0x00000000fef80000.
Found Winbond flash chip "W25Q32.V" (4096 kB, SPI) on serprog.
No operations were specified.
```

##### Write data to SPI flash
WARNING: The size of the image file must always match the size of SPI flash. This a flashrom limitation.

```
~# rumboot-flashrom -m spi0-gpio0_5-cs  -c basis -- --write img.bin
```

##### Read data from SPI flash

```
~# rumboot-flashrom -m spi0-gpio0_5-cs  -c basis -- --read img.bin
```

##### For more advanced usage please refer to flashrom docs

https://flashrom.org/Flashrom


### rumboot-demon
#### Description

The idea behind _rumboot-daemon_ is to allow access allow several apps/users to work with the same board over network. Basically it's a serial-to-tcp bridge that also handles board resetting and queues users for access to the board. 

WARNING: rumboot-daemon lacks ANY kind of authorization or encryption and is supposed to be used in secure networks. Please, DO NOT EXPOSE IT TO THE INTERNET!!! You have been warned.

_rumboot-daemon_ can theoretically work without the _-r_ option, prompting the user to reset the board, but
in real life this is pretty much useless. 

See Typical Usage section for examples

When a user connects to rumboot-daemon, the tool powers on and resets the board, preloads it with any files specified on the commandline (if any) and redirects all serial traffic there. When the user disconnects, the board is powered off. If a second user connects when the board is in use, he/she would be placed in a virtual queue and wait until the board is available.


#### Options 
```
usage: rumboot-daemon [-h] [-l LOG] [-p port] [-b speed] [-f FILE]
                      [-c chip_id] [-r method] [--apc-ip APC_IP]
                      [--apc-user APC_USER] [--apc-pass APC_PASS]
                      [--apc-port APC_PORT] [-S value] [-P value]
                      [--pl2303-invert] [-L listen]

rumboot-daemon 0.9.1 - Collaborative board access daemon

(C) 2018-2020 Andrew Andrianov <andrew@ncrmnt.org>, RC Module
https://module.ru
https://github.com/RC-MODULE

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Image file (may be specified multiple times)
  -L listen, --listen listen
                        Specify address:port to listen (default 0.0.0.0:10000)

Serial Terminal Settings:
  -l LOG, --log LOG     Log terminal output to file
  -p port, --port port  Serial port to use
  -b speed, --baud speed
                        Serial line speed

File Handling:
  -c chip_id, --chip_id chip_id
                        Override chip id (by name or chip_id)

Reset Sequence options:
  These options control how the target board will be reset

  -r method, --reset method
                        Reset sequence to use (apc base mt12505 pl2303
                        powerhub)

apc reset sequence options:
  --apc-ip APC_IP       APC IP Address/hostname
  --apc-user APC_USER   APC IP username
  --apc-pass APC_PASS   APC IP username
  --apc-port APC_PORT   APC Power port

mt12505 reset sequence options:
  -S value, --ft232-serial value
                        FT232 serial number for MT125.05

pl2303 reset sequence options:
  -P value, --pl2303-port value
                        PL2303 physical port
  --pl2303-invert       Invert all pl2303 gpio signals
```


#### Typical Usage
##### Manually start the daemon with typical settings for 'basis' platform

```
~# rumboot-daemon -c basis -p /dev/ttyUSB0 -r pl2303
Detected chip:    basis (1888ВС048)
Reset method:     pl2303
Baudrate:         115200 bps
Serial Port:      /dev/ttyUSB0
Listen address:   ['0.0.0.0:10000']
Please, power-cycle board
waiting for a connection
```

Once the daemon is working, you can connect to it on port 10000 with rumboot-xrun:

```
rumboot-xrun -f rumboot-basis-PostProduction-spl-ok.bin -p socket://192.168.10.1:10000
```

N.B. Remember to specify the correct IP address.

##### Start the daemon on boot using systemd, listen on a different port

This will require
Create /etc/systemd/system/rumboot-daemon.service with the following contents

```ini
[Unit]
Description=Rumboot Daemon 
After=network.target

[Service]
User=developer
Group=codemonkeys
Type=simple
ExecStart=/home/developer/.local/bin/rumboot-daemon -r pl2303 -p /dev/ttyUSB0 -b 115200 -L 0.0.0.0:10001
Restart=always

[Install]
WantedBy=multi-user.target
```

Adjust the script for your desired User and Group

Next enable and start the daemon

```
  ~# systemctl enable rumboot-daemon
  ~# systemctl start rumboot-daemon
```

##### Preloading an application before giving the user access to the daemon


Sometimes it's useful to initialize some external memories (e.g. ddr) or execute an application before 
allowing user access to the board. You can specify one or several applications using the -f flag

```
~# rumboot-daemon -c basis -p /dev/ttyUSB0 -r pl2303 -f ddr_init.bin
Detected chip:    basis (1888ВС048)
Reset method:     pl2303
Baudrate:         115200 bps
Serial Port:      /dev/ttyUSB0
Listen address:   ['0.0.0.0:10000']
Please, power-cycle board
waiting for a connection
```

The ddr_init.bin in the example above should initialize the ddr memory and return to bootrom with code 0. _rumboot-daemon_ will send it to the board and only then redirect serial stream to the connected user. 
 

# Appendix A. Board reset methods

rumboot-xrun, rumboot-xflash and rumboot-daemon all accept the _-r_ option that configures the way boards are reset. The following reset methods are available: 

* pl2303 (linux-only) - Uses PL2303 chip GPIO for power and reset control. The two GPIO lines of PL2303HXA should be connected to reset and power lines. Most RC Module's reference boards have this circuit. rumboot-tools will try to guess the correct device if more than one pl2303 device are connected.

* mt12505 - Uses MT12505 board for power control. Internal RC Module's hardware. Don't use.

* apc - Uses telnet-accessible APC Switched Rack PDU. Requires a set of options to be supplied: 

```  
  --apc-ip APC_IP       APC IP Address/hostname
  --apc-user APC_USER   APC IP username
  --apc-pass APC_PASS   APC IP username
  --apc-port APC_PORT   APC Power port
```

If you wish to implement your own reset method - look into rumboot/resetSeq


### rumboot-combine
#### Description

_rumboot-combine_ is a simple to tool to compose a chain of several image file. Since Rumboot V2 the rom loader can load a chain of applications, one after another from flash media. Different boot sources require different size alignment, so this app can handle all that. For basis this tool is also used to append the .ini configuration file to the image.

#### Options

```
~# rumboot-combine --help
usage: rumboot-combine [-h] -i INPUT -o OUTPUT [-a ALIGN]

rumboot-combine 0.9.7 - RumBoot Image Merger Tool

(C) 2018-2021 Andrew Andrianov <andrew@ncrmnt.org>, RC Module
https://module.ru
https://github.com/RC-MODULE

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input image file (may be specified several times)
  -o OUTPUT, --output OUTPUT
                        Output image
  -a ALIGN, --align ALIGN
                        Set alignment pattern of images in bytes or via
                        keyword (SD, physmap, ini)

```


#### Typical usage
##### Combine several apps into SPI flash image


```
  rumboot-combine -a spi -i ddr_init.bin -i memorytest.bin -i uboot.bin -o spiflash.bin
```

or 

```
  rumboot-combine -a 1 -i ddr_init.bin -i memorytest.bin -i uboot.bin -o spiflash.bin
```

##### Combine several apps into SD flash image

```
  rumboot-combine -a SD -i ddr_init.bin -i memorytest.bin -i uboot.bin -o spiflash.bin
```

##### Combine several apps into NOR flash image

```
  rumboot-combine -a physmap -i ddr_init.bin -i memorytest.bin -i uboot.bin -o spiflash.bin
```

##### Append ini to a chip config tool

```
  rumboot-combine -a ini -i tool.bin -i config.ini -o runme.bin
```

##### Combine images with custom alignment

```
  rumboot-combine -a 32 -i 1.bin -i 2.bin -o all.bin
```


## Appendix B. Adding Rumboot V1 header to your app

The tool expects that your compiled binary will already have a valid header that has all required fields except for the checksums and data length.
To to this, you have to add a single .c file to your project that will define the header structure.

The V1 is the initial header as implemented in 1888TX018. It's very basic, but may contain two entry points.

Your project should have the following C code that will put the header in your code.

```c
    extern void entry0();
    extern void entry1();

    #define BOOTHEADER_MAGIC__BOOT_IMAGE_VALID       0xbeefc0de
    #define BOOTHEADER_MAGIC__HOST_IMAGE_VALID       0xdeadc0de
    #define BOOTHEADER_MAGIC__RESUME_IMAGE_VALID     0xdeadbabe
    #define BOOTHEADER_MAGIC__CORERESET_IMAGE_VALID  0xdefec8ed


    struct legacy_bootheader
    {
        uint32_t magic;
        uint32_t length;
        uint32_t entry0;
        uint32_t entry1;
        uint32_t sum;
        uint32_t hdrsum; /* Checksum of all previous fields. */

        uint8_t imagedata[1]; /* Image data. */
    } __attribute__((packed));

    static const __attribute__((used)) __attribute__((section(".header")))
    struct legacy_bootheader hdr = {
    	.magic		= BOOTHEADER_MAGIC__BOOT_IMAGE_VALID,
    	.entry0	= (uint32_t) &entry0,
    	.entry1	= (uint32_t) &entry1,        
    };
```

A typical lds script tht will place that header at the very top of IM0 SRAM would look like this:

```ld
MEMORY
{
    IM0 (rwx): ORIGIN = 0x40000, LENGTH = 0x40000
}

SECTIONS
{


.text :
{
  KEEP(*(.header))
  *(.rumboot_platform_runtime_info);
  *(.text)
  *(.text.*)
  *(.rodata)
  *(.data)
} > IM0

.bss :
{
  rumboot_platform_bss_start = .;
  *(.bss)
  *(.bss.*)
  rumboot_platform_bss_end = .;
  rumboot_platform_heap_start = .;
  . = . + 0xf000; /* 60k heap */
  rumboot_platform_heap_end = .;
  rumboot_platform_spl_start = .;
  . = . + 0xf00;
  rumboot_platform_spl_end = .;
} > IM0

.data :
{
    *(.data)
} > IM0

.rodata :
{
  *(.rodata)
  *(.rodata).*
} > IM0

}
```

Once you compile and link your app, run 
```
rumboot-packimage -c -f file.bin
```
And it should do all magic, required to boot this image

## Appendix C. Adding Rumboot V2 header to your app

TODO: ...

## Appendix D. Adding NM6408 header to your app
TODO: ...
