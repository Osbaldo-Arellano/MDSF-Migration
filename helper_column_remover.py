import pandas as pd
import sys
from pathlib import Path

def clean_helper_columns(input_csv, output_csv):
    """
    Remove helper columns from CSV before MDSF import
    """
    print("="*80)
    print("COLUMN CLEANER - Remove Helper Columns")
    print("="*80)
    
    print(f"\nReading CSV: {input_csv}")
    df = pd.read_csv(input_csv, encoding='utf-8')
    
    print(f"Loaded {len(df)} products")
    print(f"Current columns ({len(df.columns)}): {list(df.columns)}")
    
    # Define helper columns to remove
    helper_columns = [
        'uStore_ProductID',
        'uStore_StoreID', 
        'uStore_StoreName'
    ]
    
    # Check which helper columns exist
    columns_to_remove = [col for col in helper_columns if col in df.columns]
    columns_not_found = [col for col in helper_columns if col not in df.columns]
    
    if columns_not_found:
        print(f"\nNote: These columns were not found (already removed?): {columns_not_found}")
    
    if not columns_to_remove:
        print("\n✓ No helper columns to remove. CSV is already clean!")
        print(f"Saving to: {output_csv}")
        df.to_csv(output_csv, index=False, encoding='utf-8')
        return df
    
    print(f"\nRemoving helper columns: {columns_to_remove}")
    
    # Remove helper columns
    df_clean = df.drop(columns=columns_to_remove)
    
    print(f"Columns after cleanup ({len(df_clean.columns)}): {list(df_clean.columns)}")
    
    # Save cleaned CSV
    df_clean.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"\n✓ CSV cleaned and saved to: {output_csv}")
    print(f"  Products: {len(df_clean)}")
    print(f"  Columns removed: {len(columns_to_remove)}")
    print(f"  Columns remaining: {len(df_clean.columns)}")
    
    print("\n" + "="*80)
    print("READY FOR MDSF IMPORT")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the cleaned CSV")
    print("2. Place CSV and all asset files in a folder")
    print("3. Create a ZIP file of the folder")
    print("4. Import the ZIP file into MDSF")
    
    return df_clean

if __name__ == "__main__":
    # Get input/output files
    input_csv = sys.argv[1] if len(sys.argv) > 1 else "full_migration_data_AFC_Urgent_Care.csv"
    output_csv = sys.argv[2] if len(sys.argv) > 2 else input_csv.replace('.csv', '_clean.csv')
    
    # Clean the CSV
    df_clean = clean_helper_columns(input_csv, output_csv)