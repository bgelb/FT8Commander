#!/usr/bin/env python
#
# FT8Commander Database Utilities
# Manual database management tools
#

import argparse
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import DXEntity
import geo
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_callsign(db_name, callsign, band, grid="", status=2):
    """Add a single callsign to the database"""
    
    # Load config to get your grid
    try:
        config = Config()
        config = config['ft8ctrl']
        my_grid = config.my_grid
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return False
    
    # Get your location
    try:
        origin = geo.grid2latlon(my_grid)
    except Exception as e:
        logger.error(f"Invalid grid square: {my_grid}")
        return False
    
    # Get DXEntity info
    try:
        dxe_lookup = DXEntity.DXCC().lookup
        dxentity = dxe_lookup(callsign)
        country = dxentity.country
        continent = dxentity.continent
        cqzone = dxentity.cqzone
        ituzone = dxentity.ituzone
    except KeyError:
        logger.warning(f"DXEntity not found for {callsign}")
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
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False
    
    try:
        # Insert the callsign
        cursor.execute("""
            INSERT OR REPLACE INTO cqcalls 
            (call, extra, time, status, snr, grid, lat, lon, distance, azimuth, 
             country, continent, cqzone, ituzone, frequency, band, packet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            callsign, '', datetime.now(), status, 0, grid, lat, lon, distance, azimuth,
            country, continent, cqzone, ituzone, 0, band, '{}'
        ))
        
        conn.commit()
        logger.info(f"Added {callsign} on {band}m band with status {status}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding callsign: {e}")
        return False
    finally:
        conn.close()

def list_callsigns(db_name, status=None, band=None):
    """List callsigns in the database"""
    
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False
    
    try:
        query = "SELECT call, band, status, country, continent, grid, time FROM cqcalls"
        params = []
        
        conditions = []
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        if band is not None:
            conditions.append("band = ?")
            params.append(band)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY call, band"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("No callsigns found matching criteria")
            return True
        
        logger.info(f"Found {len(rows)} callsigns:")
        logger.info("Callsign    Band  Status  Country          Continent  Grid     Time")
        logger.info("-" * 70)
        
        for row in rows:
            status_text = {0: "New", 1: "Contacting", 2: "Worked"}.get(row['status'], "Unknown")
            logger.info(f"{row['call']:<10} {row['band']:>4}m {status_text:<8} {row['country']:<15} {row['continent']:<9} {row['grid']:<8} {row['time']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error listing callsigns: {e}")
        return False
    finally:
        conn.close()

def remove_callsign(db_name, callsign, band=None):
    """Remove a callsign from the database"""
    
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False
    
    try:
        if band:
            cursor.execute("DELETE FROM cqcalls WHERE call = ? AND band = ?", (callsign, band))
            logger.info(f"Removed {callsign} from {band}m band")
        else:
            cursor.execute("DELETE FROM cqcalls WHERE call = ?", (callsign,))
            logger.info(f"Removed {callsign} from all bands")
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error removing callsign: {e}")
        return False
    finally:
        conn.close()

def database_stats(db_name):
    """Show database statistics"""
    
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False
    
    try:
        # Total records
        cursor.execute("SELECT COUNT(*) FROM cqcalls")
        total = cursor.fetchone()[0]
        
        # By status
        cursor.execute("SELECT status, COUNT(*) FROM cqcalls GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        # By band
        cursor.execute("SELECT band, COUNT(*) FROM cqcalls GROUP BY band ORDER BY band")
        band_counts = dict(cursor.fetchall())
        
        # By continent
        cursor.execute("SELECT continent, COUNT(*) FROM cqcalls GROUP BY continent ORDER BY COUNT(*) DESC")
        continent_counts = dict(cursor.fetchall())
        
        logger.info("Database Statistics:")
        logger.info(f"Total records: {total}")
        logger.info("")
        logger.info("By Status:")
        for status, count in status_counts.items():
            status_text = {0: "New", 1: "Contacting", 2: "Worked"}.get(status, f"Status {status}")
            logger.info(f"  {status_text}: {count}")
        logger.info("")
        logger.info("By Band:")
        for band, count in band_counts.items():
            logger.info(f"  {band}m: {count}")
        logger.info("")
        logger.info("By Continent:")
        for continent, count in continent_counts.items():
            logger.info(f"  {continent}: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return False
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="FT8Commander Database Utilities")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add callsign command
    add_parser = subparsers.add_parser('add', help='Add a callsign to the database')
    add_parser.add_argument('callsign', help='Callsign to add')
    add_parser.add_argument('band', type=int, help='Band in meters')
    add_parser.add_argument('--grid', default='', help='Grid square')
    add_parser.add_argument('--status', type=int, default=2, choices=[0, 1, 2], 
                           help='Status: 0=New, 1=Contacting, 2=Worked (default: 2)')
    add_parser.add_argument('-c', '--config', help='Config file')
    add_parser.add_argument('-d', '--database', help='Database file path')
    
    # List callsigns command
    list_parser = subparsers.add_parser('list', help='List callsigns in database')
    list_parser.add_argument('--status', type=int, choices=[0, 1, 2], help='Filter by status')
    list_parser.add_argument('--band', type=int, help='Filter by band')
    list_parser.add_argument('-c', '--config', help='Config file')
    list_parser.add_argument('-d', '--database', help='Database file path')
    
    # Remove callsign command
    remove_parser = subparsers.add_parser('remove', help='Remove a callsign from database')
    remove_parser.add_argument('callsign', help='Callsign to remove')
    remove_parser.add_argument('--band', type=int, help='Remove from specific band only')
    remove_parser.add_argument('-c', '--config', help='Config file')
    remove_parser.add_argument('-d', '--database', help='Database file path')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    stats_parser.add_argument('-c', '--config', help='Config file')
    stats_parser.add_argument('-d', '--database', help='Database file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Load configuration
    try:
        config = Config(args.config)
        config = config['ft8ctrl']
        db_name = args.database or config.db_name
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    # Expand database path
    db_path = Path(db_name).expanduser()
    
    if args.command == 'add':
        return 0 if add_callsign(db_path, args.callsign, args.band, args.grid, args.status) else 1
    elif args.command == 'list':
        return 0 if list_callsigns(db_path, args.status, args.band) else 1
    elif args.command == 'remove':
        return 0 if remove_callsign(db_path, args.callsign, args.band) else 1
    elif args.command == 'stats':
        return 0 if database_stats(db_path) else 1

if __name__ == "__main__":
    exit(main()) 