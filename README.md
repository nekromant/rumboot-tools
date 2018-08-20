# RumBoot image packing tools

This is a simple tool to add checksums to rumboot-compatible images and
validate them. The tool also supports error injection for rumboot testing.
Provided binaries must have a correct header for the tool to autodetect their
format. You'll find instructions on how to prepare images and detailed header description further in this README.

# Requirements

python3

# Installation

```
    pip3 install .
    pip3 install rumboot-packimage
```

# Usage

## Validate image

```
    rumboot-packimage -f myimage.bin
```
    This command will silently validate an image and exit code 0 if everything's okay. 1 if something isn't right  

## Dump header information

```
rumboot-packimage -f image.bin -i
Detected RumBootV1 image, endian: big
=== RumBootV1 Header Information ===
Endianess:              big
Magic:                  0xbeefc0de
Data Length:            69108
Header CRC32:           0x1e955d90 [Valid]
Data CRC32:             0x1929eb8e [Valid]

```

This command will dump header contents

## Write correct data length and checksums to the image

```
rumboot-packimage -f image.bin -с
Detected RumBootV1 image, endian: big
Wrote valid checksums to image header
=== RumBootV1 Header Information ===
Endianess:              big
Magic:                  0xbeefc0de
Data Length:            69108
Header CRC32:           0x1e955d90 [Valid]
Data CRC32:             0x1929eb8e [Valid]
```

# Supported formats

## General stuff

The tool expects that your compiled binary will already have a valid header that has all required fields except for the checksums and data length.
To to this, you have to add a single .c file to your project that will define the header structure.

## RumBootV1

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

## RumBootV2
    TBD
