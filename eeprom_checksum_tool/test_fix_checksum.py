import struct
from typing import Union

def calc_sum(data: bytes) -> int:
    """Calculate 16 bit bytes sum"""
    return sum(data) & 0xFFFF

def process_ms2107_eeprom(data: bytearray, fix_checksums: bool = False) -> Union[None, str]:
    """
    Process EEPROM data for MS2107 with signature 08 16.
    
    Params:
        data: EEPROM data (must be  bytearray for modifications).
        fix_checksums: If true, fix checksums
    
    Return:
        None on success or error string
    """
    # Minmal size: signature (2) + code length (2) + header (0x30) + checksums for code and header (4)
    if len(data) < 0x30 + 4:
        return "File is too short (minimal size 0x34 bytes)"

    # Check signature
    signature = struct.unpack_from('>H', data, 0)[0]  # Big-endian 2 bytes
    if signature != 0x0816:
        return f"Wrong signature: wait for 0x0816, received {signature:04X}"

    # Read code segment length (bytes 2-3)
    code_length = struct.unpack_from('>H', data, 2)[0]
    print(f"-- code length: {code_length}")
    code_end_pos = 0x30 + code_length

    # Check file length
    if len(data) < code_end_pos + 4:
        return "File too short for specified code size"

    # Calculate checksums
    # 1. Header checksum (bytes 2-0x2F), but skip firmware version (0x0C-0x0F bytes)
    header_sum = calc_sum(data[2:11]) + calc_sum(data[16:0x30])
    
    # 2. Code checksum (bytes from 0x30 and till end of the code)
    code_sum = calc_sum(data[0x30:code_end_pos])

    # Calculate checksums positions
    checksum_pos = code_end_pos
    print(f"-- checksum pos: {checksum_pos}")

    # Verify checksums mode 
    if not fix_checksums:
        # Read existing checksums from EEPROM
        stored_header_sum = struct.unpack_from('>H', data, checksum_pos)[0]
        stored_code_sum = struct.unpack_from('>H', data, checksum_pos + 2)[0]
        print(f"-- checksums from EEPROM: hdr={stored_header_sum:04X} code={stored_code_sum:04X}, calculated hdr={header_sum:04X} code={code_sum:04X}")
        # Verification
        errors = []
        if header_sum != stored_header_sum:
            errors.append(f"header: {header_sum:04X} != {stored_header_sum:04X}")
        if code_sum != stored_code_sum:
            errors.append(f"code: {code_sum:04X} != {stored_code_sum:04X}")
        
        if errors:
            return "Checksum verification FAILED " + ", ".join(errors)
    else:
        # Write recalculated checksums mode
        struct.pack_into('>H', data, checksum_pos, header_sum)
        struct.pack_into('>H', data, checksum_pos + 2, code_sum)
    
    return None

# Open eeprom.bin and process
with open('eeprom.bin', 'rb') as f:
    eeprom_data = bytearray(f.read())

# Verify without changings
if error := process_ms2107_eeprom(eeprom_data):
    print(f"Ошибка: {error}")
else:
    print("Checksums verification SUCCESS!")

# Recalculate checksums
process_ms2107_eeprom(eeprom_data, fix_checksums=True)

# Save to eeprom_modified.bin
with open('eeprom_modified.bin', 'wb') as f:
    f.write(eeprom_data)
