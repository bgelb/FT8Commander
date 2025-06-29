#!/usr/bin/env python
#
# Test frequency parsing and band detection
#

def get_band_from_freq(freq, debug=False):
    """Convert frequency to band number with improved detection"""
    if not freq:
        return 0
    
    # Clean up frequency string
    freq_str = str(freq).strip()
    
    try:
        # Handle different frequency formats
        if '.' in freq_str:
            # Already in MHz (e.g., "14.074")
            freq_mhz = float(freq_str)
        else:
            # Assume Hz and convert to MHz
            freq_hz = float(freq_str)
            freq_mhz = freq_hz / 1000000
        
        if debug:
            print(f"Frequency: {freq_str} -> {freq_mhz} MHz")
        
    except (ValueError, TypeError) as e:
        if debug:
            print(f"Error parsing frequency '{freq_str}': {e}")
        return 0
    
    # Extended band mapping with more tolerance
    bands = {
        # Standard ham bands
        1.8: 160, 3.5: 80, 7.0: 40, 10.1: 30, 14.0: 20,
        18.0: 17, 21.0: 15, 24.8: 12, 28.0: 10, 50.0: 6,
        # Add some common FT8 frequencies with tolerance
        1.840: 160, 3.573: 80, 7.074: 40, 10.136: 30, 14.074: 20,
        18.100: 17, 21.074: 15, 24.915: 12, 28.074: 10, 50.313: 6,
        # Add more FT8 frequencies
        1.841: 160, 3.574: 80, 7.075: 40, 10.137: 30, 14.075: 20,
        18.101: 17, 21.075: 15, 24.916: 12, 28.075: 10, 50.314: 6,
    }
    
    # Find the closest band with more tolerance
    for band_freq, band_num in bands.items():
        if abs(freq_mhz - band_freq) < 0.1:  # Within 0.1 MHz (more tolerant)
            if debug:
                print(f"Matched {freq_mhz} MHz to {band_num}m band")
            return band_num
    
    # If no exact match, try broader ranges
    if 1.8 <= freq_mhz <= 2.0:
        return 160
    elif 3.5 <= freq_mhz <= 4.0:
        return 80
    elif 7.0 <= freq_mhz <= 7.3:
        return 40
    elif 10.1 <= freq_mhz <= 10.15:
        return 30
    elif 14.0 <= freq_mhz <= 14.35:
        return 20
    elif 18.0 <= freq_mhz <= 18.168:
        return 17
    elif 21.0 <= freq_mhz <= 21.45:
        return 15
    elif 24.8 <= freq_mhz <= 24.99:
        return 12
    elif 28.0 <= freq_mhz <= 29.7:
        return 10
    elif 50.0 <= freq_mhz <= 54.0:
        return 6
    
    if debug:
        print(f"No band match found for {freq_mhz} MHz")
    return 0

def test_frequencies():
    """Test various frequency formats"""
    
    test_freqs = [
        # Common FT8 frequencies in Hz
        "14074000",  # 20m FT8
        "7074000",   # 40m FT8
        "3573000",   # 80m FT8
        "28074000",  # 10m FT8
        "21074000",  # 15m FT8
        "18100000",  # 17m FT8
        "10136000",  # 30m FT8
        "24915000",  # 12m FT8
        "50313000",  # 6m FT8
        "1840000",   # 160m FT8
        
        # Common FT8 frequencies in MHz
        "14.074",
        "7.074",
        "3.573",
        "28.074",
        "21.074",
        "18.100",
        "10.136",
        "24.915",
        "50.313",
        "1.840",
        
        # Some variations
        "14074001",
        "14.075",
        "7074001",
        "7.075",
        
        # Invalid frequencies
        "999999999",
        "abc",
        "",
    ]
    
    print("Testing frequency parsing and band detection:")
    print("=" * 50)
    
    for freq in test_freqs:
        band = get_band_from_freq(freq, debug=True)
        if band > 0:
            print(f"✓ {freq} -> {band}m")
        else:
            print(f"✗ {freq} -> Unknown band")
        print()

if __name__ == "__main__":
    test_frequencies() 