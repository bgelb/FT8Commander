#!/usr/bin/env python
#
# Import existing QSOs from WSJT-X ADIF log into FT8Commander database
# This prevents FT8Commander from calling stations you've already worked
#

import argparse
import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import DXEntity
import geo
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_adif_line(line):
    """Parse a single ADIF line and extract QSO information"""
    qso = {}
    
    # Extract ADIF fields using regex - more flexible pattern
    pattern = r'<(\w+):(\d+)>([^<]*)'
    matches = re.findall(pattern, line)
    
    for field, length, value in matches:
        if length.isdigit():
            actual_length = int(length)
            if len(value) >= actual_length:
                qso[field.upper()] = value[:actual_length]
    
    # Also try to find fields without length specifiers (some ADIF files have this)
    if not qso:
        # Alternative pattern for fields without length
        alt_pattern = r'<(\w+)>([^<]*)'
        alt_matches = re.findall(alt_pattern, line)
        for field, value in alt_matches:
            qso[field.upper()] = value.strip()
    
    return qso

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
            logger.debug(f"Frequency: {freq_str} -> {freq_mhz} MHz")
        
    except (ValueError, TypeError) as e:
        if debug:
            logger.debug(f"Error parsing frequency '{freq_str}': {e}")
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
                logger.debug(f"Matched {freq_mhz} MHz to {band_num}m band")
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
        logger.debug(f"No band match found for {freq_mhz} MHz")
    return 0

def import_adif_log(adif_file, db_name, my_grid, debug=False):
    """Import QSOs from ADIF file into FT8Commander database"""
    
    if debug:
        logger.setLevel(logging.DEBUG)
    
    # Get your location for distance calculations
    try:
        origin = geo.grid2latlon(my_grid)
        logger.info(f"Your location: {my_grid} -> {origin}")
    except Exception as e:
        logger.error(f"Invalid grid square: {my_grid}")
        return False
    
    # DXEntity lookup
    dxe_lookup = DXEntity.DXCC().lookup
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    mode_skipped = 0
    freq_skipped = 0
    call_skipped = 0
    band_skipped = 0
    freq_examples = []  # Store examples of unknown frequencies
    
    try:
        with open(adif_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Read {len(content)} characters from ADIF file")
        
        # Split into individual QSOs
        qso_blocks = content.split('<eor>')
        logger.info(f"Found {len(qso_blocks)} QSO blocks")
        
        for i, block in enumerate(qso_blocks):
            if not block.strip():
                continue
                
            if debug and i < 5:  # Show first 5 QSOs for debugging
                logger.debug(f"Processing QSO block {i}: {block[:200]}...")
            
            try:
                qso = parse_adif_line(block)
                
                if debug and i < 5:
                    logger.debug(f"Parsed QSO {i}: {qso}")
                
                # Check for required fields
                if not qso.get('CALL'):
                    call_skipped += 1
                    if debug:
                        logger.debug(f"QSO {i}: Skipping - no CALL field")
                    continue
                
                if not qso.get('MODE'):
                    if debug:
                        logger.debug(f"QSO {i}: No MODE field, assuming FT8")
                    mode = 'FT8'  # Default to FT8 if no mode specified
                else:
                    mode = qso.get('MODE', '').upper()
                
                # Only import FT8/FT4 QSOs
                if mode not in ['FT8', 'FT4']:
                    mode_skipped += 1
                    if debug:
                        logger.debug(f"QSO {i}: Skipping - mode '{mode}' not FT8/FT4")
                    continue
                
                call = qso.get('CALL', '').strip()
                freq = qso.get('FREQ', '')
                grid = qso.get('GRIDSQUARE', '')
                qso_date = qso.get('QSO_DATE', '')
                qso_time = qso.get('TIME_ON', '')
                
                # Skip if missing frequency
                if not freq:
                    freq_skipped += 1
                    if debug:
                        logger.debug(f"QSO {i}: Skipping - no FREQ field")
                    continue
                
                # Get band from frequency
                band = get_band_from_freq(freq, debug)
                if band == 0:
                    band_skipped += 1
                    freq_examples.append(freq)
                    if debug:
                        logger.debug(f"QSO {i}: Skipping {call} - unknown band for freq {freq}")
                    continue
                
                # Get DXEntity info
                try:
                    dxentity = dxe_lookup(call)
                    country = dxentity.country
                    continent = dxentity.continent
                    cqzone = dxentity.cqzone
                    ituzone = dxentity.ituzone
                except KeyError:
                    logger.warning(f"DXEntity not found for {call}")
                    country = "Unknown"
                    continent = "Unknown"
                    cqzone = 0
                    ituzone = 0
                
                # Calculate location and distance
                if grid:
                    try:
                        lat, lon = geo.grid2latlon(grid)
                        distance = geo.distance(origin, (lat, lon))
                        azimuth = geo.azimuth(origin, (lat, lon))
                    except Exception:
                        lat, lon = 0, 0
                        distance = 0
                        azimuth = 0
                else:
                    lat, lon = 0, 0
                    distance = 0
                    azimuth = 0
                
                # Create timestamp
                if qso_date and qso_time:
                    try:
                        # ADIF format: YYYYMMDD HHMM
                        dt_str = f"{qso_date} {qso_time}"
                        timestamp = datetime.strptime(dt_str, "%Y%m%d %H%M")
                    except ValueError:
                        timestamp = datetime.now()
                else:
                    timestamp = datetime.now()
                
                # Insert into database with status=2 (worked)
                cursor.execute("""
                    INSERT OR REPLACE INTO cqcalls 
                    (call, extra, time, status, snr, grid, lat, lon, distance, azimuth, 
                     country, continent, cqzone, ituzone, frequency, band, packet)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    call, '', timestamp, 2, 0, grid, lat, lon, distance, azimuth,
                    country, continent, cqzone, ituzone, int(float(freq)), band, '{}'
                ))
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    logger.info(f"Imported {imported_count} QSOs...")
                
            except Exception as e:
                logger.error(f"Error processing QSO {i}: {e}")
                error_count += 1
                continue
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error reading ADIF file: {e}")
        return False
    finally:
        conn.close()
    
    logger.info(f"Import completed:")
    logger.info(f"  - Imported: {imported_count} QSOs")
    logger.info(f"  - Skipped (no CALL): {call_skipped}")
    logger.info(f"  - Skipped (no FREQ): {freq_skipped}")
    logger.info(f"  - Skipped (wrong MODE): {mode_skipped}")
    logger.info(f"  - Skipped (unknown BAND): {band_skipped}")
    logger.info(f"  - Other skipped: {skipped_count}")
    logger.info(f"  - Errors: {error_count}")
    
    if freq_examples:
        logger.info(f"Examples of unknown frequencies: {freq_examples[:10]}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Import WSJT-X ADIF log into FT8Commander database")
    parser.add_argument("adif_file", help="Path to ADIF log file")
    parser.add_argument("-c", "--config", help="FT8Commander config file (default: ft8ctrl.yaml)")
    parser.add_argument("-d", "--database", help="Database file path (overrides config)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = Config(args.config)
        config = config['ft8ctrl']
        my_grid = config.my_grid
        db_name = args.database or config.db_name
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    # Check if ADIF file exists
    adif_path = Path(args.adif_file)
    if not adif_path.exists():
        logger.error(f"ADIF file not found: {adif_path}")
        return 1
    
    # Expand database path
    db_path = Path(db_name).expanduser()
    
    logger.info(f"Importing from: {adif_path}")
    logger.info(f"Database: {db_path}")
    logger.info(f"Your grid: {my_grid}")
    
    # Import the log
    if import_adif_log(adif_path, db_path, my_grid, args.debug):
        logger.info("Import successful! FT8Commander will now skip these stations.")
        return 0
    else:
        logger.error("Import failed!")
        return 1

if __name__ == "__main__":
    exit(main()) 