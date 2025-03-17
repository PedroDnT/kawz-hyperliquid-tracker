import re
from decimal import Decimal

# Dictionary to store address -> total volume mapping
address_volumes = {}

# Read the input file
with open('whale_addressesnotclean.text', 'r') as file:
    lines = file.readlines()

i = 0
while i < len(lines):
    line = lines[i].strip()
    
    # Check if line contains an Ethereum address (starts with 0x)
    if line.startswith('0x'):
        address = line
        
        # Next line should be volume
        if i+1 < len(lines):
            volume_line = lines[i+1].strip()
            if volume_line.startswith('$'):
                # Extract numeric value, remove commas
                volume_str = volume_line.replace('$', '').replace(',', '').strip()
                try:
                    volume = Decimal(volume_str)
                    
                    # Update the volume for this address
                    if address in address_volumes:
                        address_volumes[address] = max(address_volumes[address], volume)
                    else:
                        address_volumes[address] = volume
                except:
                    pass
    i += 1

# Sort addresses by volume in descending order
sorted_addresses = sorted(address_volumes.keys(), key=lambda addr: address_volumes[addr], reverse=True)

# Write to the output file
with open('cleanWhale_addreses.txt', 'w') as output_file:
    for address in sorted_addresses:
        output_file.write(f'{address}\n')

print(f'Processed {len(sorted_addresses)} unique addresses and saved to cleanWhale_addreses.txt') 