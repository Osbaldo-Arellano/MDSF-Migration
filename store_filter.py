"""
Store Filter
Filters products by store from complete export CSV
"""

import pandas as pd
import sys
from pathlib import Path

def filter_by_store(input_csv, output_csv, store_id=None, store_name=None):
    """
    Filter products by store ID or store name
    
    Args:
        input_csv: Path to complete export CSV
        output_csv: Path for filtered output CSV
        store_id: Store ID to filter (optional)
        store_name: Store name to filter (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("="*80)
    print("STORE FILTER")
    print("="*80)
    
    # Validate input
    if not Path(input_csv).exists():
        print(f"ERROR: Input file not found: {input_csv}")
        return False
    
    if not store_id and not store_name:
        print("ERROR: Must provide either store_id or store_name")
        return False
    
    # Read CSV
    print(f"\nReading CSV: {input_csv}")
    try:
        df = pd.read_csv(input_csv, encoding='utf-8', keep_default_na=False)
    except Exception as e:
        print(f"ERROR: Failed to read CSV: {e}")
        return False
    
    print(f"Total products loaded: {len(df)}")
    
    # Validate required columns
    if 'uStore_StoreID' not in df.columns and 'uStore_StoreName' not in df.columns:
        print("ERROR: CSV missing store columns (uStore_StoreID or uStore_StoreName)")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    # Show store breakdown
    print("\nStores in export:")
    if 'uStore_StoreName' in df.columns:
        store_counts = df.groupby('uStore_StoreName').size().sort_values(ascending=False)
        for store, count in store_counts.head(10).items():
            store_id_display = df[df['uStore_StoreName'] == store]['uStore_StoreID'].iloc[0] if 'uStore_StoreID' in df.columns else 'N/A'
            print(f"  {store} (ID: {store_id_display}): {count} products")
        if len(store_counts) > 10:
            print(f"  ... and {len(store_counts) - 10} more stores")
    
    # Filter
    print(f"\nFiltering...")
    if store_id is not None:
        if 'uStore_StoreID' not in df.columns:
            print("ERROR: uStore_StoreID column not found")
            return False
        filtered_df = df[df['uStore_StoreID'] == store_id]
        filter_desc = f"Store ID {store_id}"
    else:
        if 'uStore_StoreName' not in df.columns:
            print("ERROR: uStore_StoreName column not found")
            return False
        filtered_df = df[df['uStore_StoreName'] == store_name]
        filter_desc = f"Store Name '{store_name}'"
    
    if len(filtered_df) == 0:
        print(f"WARNING: No products found for {filter_desc}")
        print("\nAvailable stores:")
        if 'uStore_StoreName' in df.columns:
            for store in df['uStore_StoreName'].unique()[:20]:
                print(f"  - {store}")
        return False
    
    print(f"  Filter: {filter_desc}")
    print(f"  Products found: {len(filtered_df)}")
    
    # Save filtered data
    try:
        filtered_df.to_csv(output_csv, index=False, encoding='utf-8')
    except Exception as e:
        print(f"ERROR: Failed to save CSV: {e}")
        return False
    
    # Summary
    print("\n" + "="*80)
    print("FILTERING COMPLETE")
    print("="*80)
    print(f"\nOutput saved to: {output_csv}")
    print(f"Products: {len(filtered_df)}")
    print(f"Store: {filtered_df['uStore_StoreName'].iloc[0] if 'uStore_StoreName' in filtered_df.columns else 'N/A'}")
    print(f"Store ID: {filtered_df['uStore_StoreID'].iloc[0] if 'uStore_StoreID' in filtered_df.columns else 'N/A'}")
    
    # Show sample
    print(f"\nSample products:")
    for idx, row in filtered_df.head(5).iterrows():
        print(f"  - {row['Name']}")
    if len(filtered_df) > 5:
        print(f"  ... and {len(filtered_df) - 5} more")
    
    print("\n" + "="*80)
    
    return True

def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage: python store_filter.py <input_csv> <output_csv> [store_id OR store_name]")
        print("\nExamples:")
        print("  # Filter by Store ID")
        print("  python store_filter.py uStore_Complete_Export.csv AFC_Export.csv 70")
        print("\n  # Filter by Store Name")
        print("  python store_filter.py uStore_Complete_Export.csv AFC_Export.csv 'AFC Urgent Care'")
        print("\n  # Show all stores")
        print("  python store_filter.py uStore_Complete_Export.csv - list")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_csv = sys.argv[2]
    
    # Special case: list stores
    if len(sys.argv) == 4 and sys.argv[3].lower() == 'list':
        df = pd.read_csv(input_csv, encoding='utf-8', keep_default_na=False)
        print("\nAll stores in export:")
        print("="*80)
        if 'uStore_StoreName' in df.columns:
            store_counts = df.groupby(['uStore_StoreID', 'uStore_StoreName']).size().reset_index(name='count')
            store_counts = store_counts.sort_values('count', ascending=False)
            for _, row in store_counts.iterrows():
                print(f"  Store ID {row['uStore_StoreID']:3d}: {row['uStore_StoreName']:50s} ({row['count']:4d} products)")
        print("="*80)
        sys.exit(0)
    
    if len(sys.argv) < 4:
        print("ERROR: Must provide store_id or store_name")
        sys.exit(1)
    
    filter_value = sys.argv[3]
    
    # Try to parse as store ID (integer)
    store_id = None
    store_name = None
    
    try:
        store_id = int(filter_value)
    except ValueError:
        store_name = filter_value
    
    # Run filter
    success = filter_by_store(input_csv, output_csv, store_id, store_name)
    
    if success:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()