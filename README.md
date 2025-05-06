
# Macrosilicon MS2107 CVBS to USB converter research

Cheap CVBS-USB converter device contains **MS2107** chip and **AT24C16** EEPROM.

I want to fix some issues in behavior. I read EEPROM with **CH341A** EEPROM programmer and tried to understand internal structure.

Here's my research results:

## Useful resources

8051 command line disassembler, helpful for code analysis
https://github.com/anarcheuz/8051-disassembler.git

ms-tools: research and modifications for MS2106 MS2109 MS2130 chips
https://github.com/BertoldVdb/ms-tools.git


## EEPROM data structure

### Format structure

MS2107 EEPROM contains section:
1. [2 bytes] Signature 08 16
2. [2 bytes] Code size N
3. [from 0x04 to 0x30 bytes]  Header data. Configuration parameters and USB devices names
4. [N bytes] Code size 
5. [2 bytes] Header checksum
6. [2 bytes] Code checksum
7. ?? Extended configuration section or code

### Checksums
EEPROM contains 2 checksums, first for code, second for header, but firmware version field is excluded from checksum calculation.
Type of checksums is simple **uint16**, just sum of bytes:

```
header_checksum = sum(2:11) + sum(16:0x30)  # excluded last 4 bytes from first 16-byte line
code_checksum = sum(0x30:0x30+code_size)
```

### Details

bytes 0x00 0x01 - signature 08 16
bytes 0x02 0x03 - program code length, started on 0x30

bytes 0x04 0x05 - USB VID (big endian, first byte is hi-byte, second lo-byte). 0xFFFF - default
bytes 0x05 0x06 - USB PID (big endian, first byte is hi-byte, second lo-byte). 0xFFFF - default

byte  0x08 - Common flags

common flags:
bit 0 - Patch_Common
bit 1 - USB_cmd
bit 2 - USB_int
bit 3 - Timer_Int
bit 4 - VSync_int
bit 5 - TVD_int
bit 6 - Reserved
bit 7 - Reserved

byte 0x09 - Function flag 1 (in my case 0xFF by default)
bit 0 - AV port enabled
bit 1 - SV port enabled
other bits: 1

byte 0x0A:
  H 4bit           L 4bit
[mute partern] [functions 2 enabled]

mute patterns:
0 - pure black
1 - pure blue
2 - pure green
3 - pure red
4 - pure white
5 - cross hatch
6 - H ramp
7 - V ramp
8 - color bar
9 - H gray scale
A - V gray scale
B - 2nd H gray scale
C - primary color 
D - interlace black 
E - B&W random
F - color random

functions enabled
bit 0 (1) - audio enable
bit 1 (2) - stereo enabled
bit 3 (4) - save Brightness/Contrast/Saturation/Hue (4-byte signed int8 config block after checksums)

byte 0x0B:
  H 1bit           L 7bit
[default port] [default TV mode]

default port:
0 - AV
1 - SV  

default TV mode:
0 - NTSC 358
1 - NTSC 443 
2 - PAL
3 - PAL M
4 - PAL NC
5 - SECAM
6 - PAL 60
0x7F - NO SIGNAL

bytes 0x0C-0x0F - firmware version (not used in CRC calculation)

byte 0x10 - USB Video name length. 0xFF - no name
byte 0x11-0x1F - 'USB Video' device name. End bytes 0xFF, default should be 0xFF all

byte 0x20 - USB Audio name length. 0xFF - no name
byte 0x21-0x2F - 'USB Audio' device name. End bytes 0xFF, default should be 0xFF all


## Fix checksums after EEPROM modifications

I wrote simple python script for verify and recalculate checksums for MS2107 EEPROM images, it placed in *eeprom_checksum_tool* directory.
How to use script `test_fix_checksum.py`

1. Create file `eeprom.bin` with binary data from EEPROM and place it into directory with `test_fix_checksum.py`
2. Open terminal or cmd, change directory to `{PROJECT_DIR}/eeprom_checksum_tool`
3. Run `python test_fix_checksum.py` without parameters
4. Script verifies checksums, recalculate them and create file `eeprom_modified.bin` file with correct recalculated checksums

## Code section analysis

### TBD

First subroutine (0x30? -> 0x66) probably process USB
I changed `jb xxx` to `nop` instructions - and device was not correctly detected as USB dev

