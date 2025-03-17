#!/usr/bin/env python3

def extract_and_sort_addresses():
    # Dictionary to store address -> deposit amount mapping
    addresses = {}
    
    # Read the input file
    with open('whale_addressesnotclean.text', 'r') as file:
        lines = file.readlines()
    
    # Extract addresses and their deposit amounts
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if line contains an Ethereum address (starts with 0x)
        if line.startswith('0x'):
            address = line
            
            # Next line should contain the deposit amount
            if i + 1 < len(lines):
                deposit_line = lines[i + 1].strip()
                if deposit_line.startswith('$'):
                    # Remove $ and commas, then convert to float
                    deposit_amount = float(deposit_line.replace('$', '').replace(',', ''))
                    addresses[address] = deposit_amount
        i += 1
    
    # Sort addresses by deposit amount (highest to lowest)
    sorted_addresses = sorted(addresses.items(), key=lambda x: x[1], reverse=True)
    
    # Write addresses to output file
    with open('cleanWhale_addreses.txt', 'w') as out_file:
        for address, _ in sorted_addresses:
            out_file.write(f"{address}\n")
    
    print(f"Successfully processed {len(sorted_addresses)} addresses and saved to cleanWhale_addreses.txt")

if __name__ == "__main__":
    extract_and_sort_addresses() 