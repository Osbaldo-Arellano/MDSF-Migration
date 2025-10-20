"""
MDSF Packager
Creates final ZIP package with CSV and all assets
Works for any storefront
"""

import pandas as pd
import os
import shutil
import zipfile
from pathlib import Path
import sys

def create_package(input_csv, assets_dir, thumbnails_dir, test_mode=False):
    """
    Create final MDSF import package:
    1. Read CSV with mapped products (including helper columns)
    2. Copy all referenced assets from uStore folder structure
    3. Remove helper columns from CSV
    4. Create ZIP file with CSV + assets at root level
    
    Args:
        input_csv: Path to MDSF-formatted CSV (from fields_mapper)
        assets_dir: Path to static_assets folder
        thumbnails_dir: Path to static_assets_thumbnails folder
        test_mode: If True, process only first product
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("="*80)
    print("MDSF PACKAGER")
    print("="*80)
    
    # Validate inputs
    if not Path(input_csv).exists():
        print(f"ERROR: CSV file not found: {input_csv}")
        return False
    
    assets_path = Path(assets_dir)
    thumbnails_path = Path(thumbnails_dir)
    
    if not assets_path.exists():
        print(f"ERROR: Assets folder not found: {assets_path}")
        return False
    
    if not thumbnails_path.exists():
        print(f"ERROR: Thumbnails folder not found: {thumbnails_path}")
        return False
    
    # Read CSV
    print(f"\nReading CSV: {input_csv}")
    try:
        df = pd.read_csv(input_csv, encoding='utf-8', keep_default_na=False)
    except Exception as e:
        print(f"ERROR: Failed to read CSV: {e}")
        return False
    
    print(f"Loaded {len(df)} products")
    
    # Check for required helper column
    if 'uStore_ProductID' not in df.columns:
        print("ERROR: uStore_ProductID column not found in CSV")
        print("Make sure you're using output from fields_mapper script")
        return False
    
    # Test mode
    if test_mode:
        print("\nTEST MODE: Processing only first product")
        df = df.head(1)
        print(f"Test product: {df.iloc[0].get('Name', 'Unknown')}")
    
    # Create output directory
    output_dir = "MDSF_Import_Package"
    output_path = Path(output_dir)
    
    if output_path.exists():
        shutil.rmtree(output_path)
    
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Created staging directory: {output_path}")
    
    # Track statistics
    stats = {
        'products_processed': 0,
        'content_files_copied': 0,
        'icon_files_copied': 0,
        'detail_files_copied': 0,
        'missing_files': []
    }
    
    files_copied = set()  # Avoid duplicates
    
    print(f"\nProcessing {len(df)} product(s)...")
    
    # Process each product
    for idx, row in df.iterrows():
        product_id = str(row['uStore_ProductID'])
        product_name = row.get('Name', f'Product {product_id}')
        stats['products_processed'] += 1
        
        # Process ContentFiles (PDFs)
        content_files = str(row.get('ContentFile', '')).strip()
        if content_files and content_files != 'AutoThumbnail':
            for filename in content_files.split(','):
                filename = filename.strip()
                if filename and filename not in files_copied:
                    source_file = assets_path / f"Product_{product_id}" / filename
                    dest_file = output_path / filename
                    
                    if source_file.exists():
                        shutil.copy2(source_file, dest_file)
                        files_copied.add(filename)
                        stats['content_files_copied'] += 1
                    else:
                        stats['missing_files'].append((product_name, filename, 'PDF'))
        
        # Process Icon files (images)
        icon_files = str(row.get('Icon', '')).strip()
        if icon_files and icon_files != 'AutoThumbnail':
            for filename in icon_files.split(','):
                filename = filename.strip()
                if filename and filename not in files_copied:
                    source_file = thumbnails_path / f"Product_{product_id}" / "Pages" / "Thumbnails" / filename
                    dest_file = output_path / filename
                    
                    if source_file.exists():
                        shutil.copy2(source_file, dest_file)
                        files_copied.add(filename)
                        stats['icon_files_copied'] += 1
                    else:
                        stats['missing_files'].append((product_name, filename, 'Icon'))
        
        # Process DetailImage files
        detail_files = str(row.get('DetailImage', '')).strip()
        if detail_files and detail_files != 'AutoThumbnail':
            for filename in detail_files.split(','):
                filename = filename.strip()
                if filename and filename not in files_copied:
                    source_file = thumbnails_path / f"Product_{product_id}" / "Pages" / "Thumbnails" / filename
                    dest_file = output_path / filename
                    
                    if source_file.exists():
                        shutil.copy2(source_file, dest_file)
                        files_copied.add(filename)
                        stats['detail_files_copied'] += 1
                    else:
                        # Only report if not already reported as icon
                        if (product_name, filename, 'Icon') not in stats['missing_files']:
                            stats['missing_files'].append((product_name, filename, 'DetailImage'))
    
    print(f"  Copied {len(files_copied)} unique asset files")
    
    # Remove helper columns
    print("\nCleaning CSV...")
    helper_columns = ['uStore_ProductID', 'uStore_StoreID', 'uStore_StoreName']
    columns_to_remove = [col for col in helper_columns if col in df.columns]
    
    if columns_to_remove:
        df_clean = df.drop(columns=columns_to_remove)
        print(f"  Removed helper columns: {', '.join(columns_to_remove)}")
    else:
        df_clean = df
    
    # Save cleaned CSV
    csv_filename = "products.csv"
    csv_output_path = output_path / csv_filename
    
    try:
        df_clean.to_csv(csv_output_path, index=False, encoding='utf-8')
        print(f"  Saved cleaned CSV: {csv_filename}")
        print(f"  Final columns: {len(df_clean.columns)}")
    except Exception as e:
        print(f"ERROR: Failed to save CSV: {e}")
        return False
    
    # Create ZIP file
    print("\nCreating ZIP package...")
    zip_filename = f"{output_dir}.zip"
    
    if Path(zip_filename).exists():
        os.remove(zip_filename)
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_path.iterdir():
                if file_path.is_file():
                    zipf.write(file_path, arcname=file_path.name)
        
        print(f"  Created: {zip_filename}")
    except Exception as e:
        print(f"ERROR: Failed to create ZIP: {e}")
        return False
    
    # Verify ZIP
    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        file_list = zipf.namelist()
        print(f"  ZIP contains {len(file_list)} files")
    
    # Final report
    print("\n" + "="*80)
    print("PACKAGING COMPLETE")
    print("="*80)
    print(f"\nPackage: {zip_filename}")
    print(f"Staging directory: {output_path} (can be deleted)")
    
    print(f"\nStatistics:")
    print(f"  Products: {stats['products_processed']}")
    print(f"  PDFs copied: {stats['content_files_copied']}")
    print(f"  Icons copied: {stats['icon_files_copied']}")
    print(f"  Detail images copied: {stats['detail_files_copied']}")
    print(f"  Total files: {len(files_copied) + 1}")  # +1 for CSV
    
    # Report missing files
    if stats['missing_files']:
        print(f"\nWARNING: {len(stats['missing_files'])} missing files")
        if len(stats['missing_files']) <= 5:
            for product_name, filename, file_type in stats['missing_files']:
                print(f"  - {filename} ({file_type}): {product_name}")
        else:
            for product_name, filename, file_type in stats['missing_files'][:3]:
                print(f"  - {filename} ({file_type}): {product_name}")
            print(f"  ... and {len(stats['missing_files']) - 3} more")
    else:
        print("\nAll asset files found and copied!")
    
    print("\n" + "="*80)
    print("READY FOR MDSF IMPORT")
    print("="*80)
    print("\nNext steps:")
    print("1. Go to MDSF: Administration > Export / Import")
    print("2. Select 'Products-Add or Update'")
    print(f"3. Upload: {zip_filename}")
    print("4. Format: Unicode (UTF-8), Delimiter: comma")
    print("5. Click 'Import Template'")
    print("="*80 + "\n")
    
    return True

def main():
    """Main entry point"""
    if len(sys.argv) < 4:
        print("Usage: python packager.py <input_csv> <assets_dir> <thumbnails_dir> [test_mode]")
        print("\nExample:")
        print("  python packager.py mdsf_import.csv ../static_assets ../static_assets_thumbnails false")
        print("\nArguments:")
        print("  test_mode: true/false (default: false)")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    assets_dir = sys.argv[2]
    thumbnails_dir = sys.argv[3]
    
    test_mode = False
    if len(sys.argv) > 4:
        test_mode = sys.argv[4].lower() in ['true', '1', 'yes']
    
    # Run packaging
    success = create_package(input_csv, assets_dir, thumbnails_dir, test_mode)
    
    if success:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()