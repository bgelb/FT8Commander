#!/usr/bin/env python
#
# Test script to examine ADIF file format
#

import argparse
import re
from pathlib import Path

def examine_adif_file(adif_file, num_samples=5):
    """Examine the structure of an ADIF file"""
    
    print(f"Examining ADIF file: {adif_file}")
    print("=" * 60)
    
    try:
        with open(adif_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"File size: {len(content)} characters")
        
        # Split into QSO blocks
        qso_blocks = content.split('<eor>')
        print(f"Found {len(qso_blocks)} QSO blocks")
        
        # Show first few QSOs
        for i, block in enumerate(qso_blocks[:num_samples]):
            if not block.strip():
                continue
                
            print(f"\nQSO Block {i+1}:")
            print("-" * 40)
            print(block[:500] + "..." if len(block) > 500 else block)
            
            # Parse fields
            qso = parse_adif_fields(block)
            print(f"\nParsed fields: {qso}")
            
            # Check for required fields
            required_fields = ['CALL', 'FREQ', 'MODE']
            missing = [field for field in required_fields if not qso.get(field)]
            if missing:
                print(f"Missing required fields: {missing}")
            else:
                print("All required fields present")
    
    except Exception as e:
        print(f"Error reading file: {e}")

def parse_adif_fields(block):
    """Parse ADIF fields from a block"""
    qso = {}
    
    # Standard ADIF pattern with length
    pattern = r'<(\w+):(\d+)>([^<]*)'
    matches = re.findall(pattern, block)
    
    for field, length, value in matches:
        if length.isdigit():
            actual_length = int(length)
            if len(value) >= actual_length:
                qso[field.upper()] = value[:actual_length]
    
    # Alternative pattern without length
    if not qso:
        alt_pattern = r'<(\w+)>([^<]*)'
        alt_matches = re.findall(alt_pattern, block)
        for field, value in alt_matches:
            qso[field.upper()] = value.strip()
    
    return qso

def main():
    parser = argparse.ArgumentParser(description="Examine ADIF file format")
    parser.add_argument("adif_file", help="Path to ADIF file")
    parser.add_argument("-n", "--num-samples", type=int, default=5, 
                       help="Number of QSO samples to show (default: 5)")
    
    args = parser.parse_args()
    
    adif_path = Path(args.adif_file)
    if not adif_path.exists():
        print(f"ADIF file not found: {adif_path}")
        return 1
    
    examine_adif_file(adif_path, args.num_samples)
    return 0

if __name__ == "__main__":
    exit(main()) 