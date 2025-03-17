"""
We're building a bot that looks at all of the open positions here on Hyperliquid.

The tricky part is going to be getting the addresses of the whales.
Because I know how to get positions for anybody. That's easy money.
It's just, who are those whales and how do we identify them?

todo
- Make a list of people with big deposits and then follow those or see what they're up to and see their position.

list of adderess of potentional whales
https://dune.com/x3research/hyperliquid
    - i got stopped at the start of the 4th page here
https://dune.com/kouei/hyperliquid-usdc-deposit
    - i put the first 500 on the list

all hyperliquid protocols
https://data.asxn.xyz/dashboard/hyperliquid-ecosystem
https://hyperdash.info/ -- this is a good one
"""

import os
import json
import time
import pandas as pd
import requests
from datetime import datetime
import nice_funcs as n
import numpy as np

# Configure pandas to display numbers with commas and no scientific notation
pd.set_option('display.float_format', '${:.2f}'.format)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# ===== CONFIGURATION =====
API_URL = "https://api.hyperliquid.xyz/info"
DATA_DIR = "bots/hyperliquid/data/ppls_positions"  # Directory path, not file path
HEADERS = {"Content-Type": "application/json"}
MIN_POSITION_VALUE = 25000  # Only track positions with value >= $25,000

def load_wallet_addresses():
    """Load wallet addresses from text file"""
    addresses_file = os.path.join(DATA_DIR, "whale_addresses.txt")
    try:
        with open(addresses_file, 'r') as f:
            # Read lines and filter out empty lines and comments
            addresses = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"🔧 Kawz's Tools says: Loaded {len(addresses)} addresses from {addresses_file} 🚀")
        return addresses
    except Exception as e:
        print(f"❌ Error loading addresses: {str(e)}")
        return []

def ensure_data_dir():
    """Ensure the data directory exists"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"🔧 Kawz's Tools says: Data directory ready at {DATA_DIR} 🚀")
    except Exception as e:
        print(f"❌ Error creating directory: {str(e)}")
        return False
    return True

def get_positions_for_address(address):
    """
    Fetch positions for a specific wallet address using Hyperliquid API
    """
    try:
        payload = {
            "type": "clearinghouseState",
            "user": address
        }
        
        print(f"🔍 DEBUG: Sending request to {API_URL} for address {address}")
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Successfully fetched data for address: {address[:6]}...{address[-4:]}")
        
        if "assetPositions" in data:
            print(f"🔮 Found {len(data['assetPositions'])} positions")
        else:
            print(f"🔮 No positions found")
            
        return data
    except Exception as e:
        print(f"❌ Error fetching positions for {address}: {str(e)}")
        return None

def process_positions(data, address):
    """
    Process the position data into a more usable format
    """
    if not data or "assetPositions" not in data:
        return []
    
    print(f"🔍 Processing {len(data['assetPositions'])} positions for {address}")
    
    positions = []
    for pos in data["assetPositions"]:
        if "position" in pos:
            p = pos["position"]
            
            try:
                size = float(p.get("szi", "0"))
                position_value = float(p.get("positionValue", "0"))
                
                # Skip positions below minimum value threshold
                if position_value < MIN_POSITION_VALUE:
                    continue
                
                position_info = {
                    "address": address,
                    "coin": p.get("coin", ""),
                    "entry_price": float(p.get("entryPx", "0")),
                    "leverage": p.get("leverage", {}).get("value", 0),
                    "position_value": position_value,
                    "unrealized_pnl": float(p.get("unrealizedPnl", "0")),
                    "liquidation_price": float(p.get("liquidationPx", "0") or 0),
                    "is_long": size > 0,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                positions.append(position_info)
                print(f"✅ Added {p.get('coin', '')} position worth ${position_value:.2f}")
                
            except (TypeError, ValueError) as e:
                print(f"⚠ Error processing position: {str(e)}")
                continue
                
    return positions

def save_positions_to_csv(all_positions):
    """
    Save all positions to a CSV file
    """
    if not all_positions:
        print("🔧 Kawz's Tools says: No positions found to save! 😢")
        return None
    
    df = pd.DataFrame(all_positions)
    
    # Format numeric columns
    numeric_cols = ['entry_price', 'position_value', 'unrealized_pnl', 'liquidation_price']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(float)
    
    # Save all positions
    positions_file = os.path.join(DATA_DIR, "all_positions.csv")
    df.to_csv(positions_file, index=False, float_format='%.2f')
    print(f"🔧 Kawz's Tools says: Saved {len(all_positions)} positions to {positions_file} 🚀")
    
    # Create and save aggregated view
    print("\n🔍 Creating aggregated view...")
    agg_df = df.groupby(['coin', 'is_long']).agg({
        'position_value': 'sum',
        'unrealized_pnl': 'sum',
        'address': 'count'
    }).reset_index()
    
    # Add direction and rename columns
    agg_df['direction'] = agg_df['is_long'].apply(lambda x: 'LONG 📈' if x else 'SHORT 📉')
    agg_df = agg_df.rename(columns={
        'address': 'num_traders',
        'position_value': 'total_value',
        'unrealized_pnl': 'total_pnl'
    })
    
    # Calculate average value per trader
    agg_df['avg_value_per_trader'] = agg_df['total_value'] / agg_df['num_traders']
    
    # Sort by total value
    agg_df = agg_df.sort_values('total_value', ascending=False)
    
    # Save aggregated view
    agg_file = os.path.join(DATA_DIR, "aggregated_positions.csv")
    agg_df.to_csv(agg_file, index=False, float_format='%.2f')
    print(f"📊 Saved aggregated positions to {agg_file}")
    
    # Display summaries
    print("\n===== POSITION SUMMARY =====")
    display_cols = ['coin', 'direction', 'total_value', 'num_traders', 'avg_value_per_trader']
    print(agg_df[display_cols])
    
    print("\n📈 TOP LONG POSITIONS:")
    print(agg_df[agg_df['is_long']][display_cols].head())
    
    print("\n📉 TOP SHORT POSITIONS:")
    print(agg_df[~agg_df['is_long']][display_cols].head())
    
    return df, agg_df

def fetch_all_positions(addresses):
    """
    Fetch positions for all addresses in the list
    """
    all_positions = []
    
    for address in addresses:
        print(f"\n🔍 Fetching positions for address: {address[:6]}...{address[-4:]}")
        data = get_positions_for_address(address)
        
        if data:
            positions = process_positions(data, address)
            all_positions.extend(positions)
            
            if not positions:
                print("No positions found above minimum value threshold")
                
        time.sleep(0.5)  # Small delay to avoid rate limiting
        
    return all_positions

def main():
    """Main function to run the position tracker"""
    print("🔧 Kawz's Tools Whale Position Tracker Starting... 🐳")
    
    # Ensure data directory exists
    ensure_data_dir()
    
    # Load wallet addresses
    addresses = load_wallet_addresses()
    if not addresses:
        print("⚠ No addresses loaded! Exiting...")
        return
        
    print(f"📋 Tracking {len(addresses)} wallet addresses")
    print(f"💰 Minimum position value: ${MIN_POSITION_VALUE:,}")
    
    # Fetch and save positions
    all_positions = fetch_all_positions(addresses)
    positions_df, agg_df = save_positions_to_csv(all_positions)
    
    print("\n🔧 Kawz's Tools says: Position tracking complete! Thanks for using Kawz's Tools! 🚀")
    print(f"📁 CSV files saved in: {DATA_DIR}")
    return positions_df, agg_df

if __name__ == "__main__":
    main()
