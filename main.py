import pandas as pd
import os
import shutil
import zipfile
from pathlib import Path
import sys

def create_mdsf_package(input_csv, assets_dir, thumbnails_dir, output_dir):
    """
    Create final MDSF import package:
    1. Read the CSV with mapped products (including uStore helper columns)
    2. Copy all referenced assets from uStore folder structure
    3. Remove helper columns from CSV
    4. Create ZIP file with CSV + assets at root level
    
    Args:
        input_csv: Path to the MDSF-formatted CSV (output from migration script)
        assets_dir: Path to static_assets folder (contains Product_* folders with PDFs)
        thumbnails_dir: Path to static_assets_thumbnails folder (contains Product_* folders with images)
        output_dir: Directory name for temporary staging
    """
    print("="*80)
    print("MDSF PACKAGE CREATOR")
    print("="*80)
    
    # Read the CSV
    print(f"\nReading CSV: {input_csv}")
    df = pd.read_csv(input_csv, encoding='utf-8', keep_default_na=False)
    print(f"Loaded {len(df)} products")
    
    # Check for required helper column
    if 'uStore_ProductID' not in df.columns:
        print("\nERROR: uStore_ProductID column not found in CSV")
        print("Make sure you're using the output from the migration script")
        return None
    
    # FOR TESTING: Only process first product
    print("\nTEST MODE: Processing only the first product")
    df = df.head(1)
    print(f"Test product: {df.iloc[0]['Name']}")
    print(f"uStore Product ID: {df.iloc[0]['uStore_ProductID']}")
    
    # Create output directory
    output_path = Path(output_dir)
    if output_path.exists():
        print(f"\nRemoving existing output directory: {output_path}")
        shutil.rmtree(output_path)
    
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Created output directory: {output_path}")
    
    # Convert paths to Path objects
    assets_path = Path(assets_dir)
    thumbnails_path = Path(thumbnails_dir)
    
    # Validate directories exist
    if not assets_path.exists():
        print(f"\nERROR: Assets folder not found: {assets_path}")
        return None
    if not thumbnails_path.exists():
        print(f"\nERROR: Thumbnails folder not found: {thumbnails_path}")
        return None
    
    # Track statistics
    stats = {
        'products_processed': 0,
        'content_files_copied': 0,
        'icon_files_copied': 0,
        'detail_files_copied': 0,
        'missing_files': []
    }
    
    print("\nProcessing assets...")
    files_copied = set()  # Track to avoid duplicates
    
    for idx, row in df.iterrows():
        product_id = str(row['uStore_ProductID'])
        product_name = row['Name']
        stats['products_processed'] += 1
        
        print(f"\nProduct: {product_name} (ID: {product_id})")
        
        # Process ContentFiles (PDFs from static_assets)
        content_files = str(row.get('ContentFile', ''))
        if content_files and content_files.strip():
            for filename in content_files.split(','):
                filename = filename.strip()
                if filename and filename not in files_copied:
                    # Look in static_assets/Product_{id}/filename
                    source_file = assets_path / f"Product_{product_id}" / filename
                    dest_file = output_path / filename
                    
                    if source_file.exists():
                        shutil.copy2(source_file, dest_file)
                        files_copied.add(filename)
                        stats['content_files_copied'] += 1
                        print(f"  Copied content: {filename}")
                    else:
                        stats['missing_files'].append((product_name, filename, 'content', str(source_file)))
                        print(f"  WARNING: Missing content file: {filename}")
                        print(f"           Expected at: {source_file}")
        
        # Process Icon files (images from static_assets_thumbnails)
        icon_files = str(row.get('Icon', ''))
        if icon_files and icon_files.strip() and icon_files != 'AutoThumbnail':
            for filename in icon_files.split(','):
                filename = filename.strip()
                if filename and filename not in files_copied:
                    # Look in static_assets_thumbnails/Product_{id}/Pages/Thumbnails/filename
                    source_file = thumbnails_path / f"Product_{product_id}" / "Pages" / "Thumbnails" / filename
                    dest_file = output_path / filename
                    
                    if source_file.exists():
                        shutil.copy2(source_file, dest_file)
                        files_copied.add(filename)
                        stats['icon_files_copied'] += 1
                        print(f"  Copied icon: {filename}")
                    else:
                        stats['missing_files'].append((product_name, filename, 'icon', str(source_file)))
                        print(f"  WARNING: Missing icon file: {filename}")
                        print(f"           Expected at: {source_file}")
        
        # Process DetailImage files (same location as icons)
        detail_files = str(row.get('DetailImage', ''))
        if detail_files and detail_files.strip() and detail_files != 'AutoThumbnail':
            for filename in detail_files.split(','):
                filename = filename.strip()
                if filename and filename not in files_copied:
                    # Look in static_assets_thumbnails/Product_{id}/Pages/Thumbnails/filename
                    source_file = thumbnails_path / f"Product_{product_id}" / "Pages" / "Thumbnails" / filename
                    dest_file = output_path / filename
                    
                    if source_file.exists():
                        shutil.copy2(source_file, dest_file)
                        files_copied.add(filename)
                        stats['detail_files_copied'] += 1
                        print(f"  Copied detail: {filename}")
                    else:
                        # Only report if not already reported as icon
                        if (product_name, filename, 'icon', str(source_file)) not in stats['missing_files']:
                            stats['missing_files'].append((product_name, filename, 'detail', str(source_file)))
                            print(f"  WARNING: Missing detail file: {filename}")
                            print(f"           Expected at: {source_file}")
    
    # Remove helper columns before saving
    print("\nRemoving uStore helper columns...")
    helper_columns = ['uStore_ProductID', 'uStore_StoreID', 'uStore_StoreName']
    columns_to_remove = [col for col in helper_columns if col in df.columns]
    
    if columns_to_remove:
        df_clean = df.drop(columns=columns_to_remove)
        print(f"Removed columns: {', '.join(columns_to_remove)}")
    else:
        df_clean = df
        print("No helper columns found")
    
    # Save cleaned CSV to output directory
    print("\nSaving cleaned CSV to output directory...")
    csv_filename = "products.csv"
    csv_output_path = output_path / csv_filename
    df_clean.to_csv(csv_output_path, index=False, encoding='utf-8')
    print(f"Saved CSV: {csv_output_path}")
    print(f"Columns in final CSV: {len(df_clean.columns)}")
    
    # Create ZIP file with files at root level
    print("\nCreating ZIP file...")
    zip_filename = f"{output_dir}.zip"
    
    # Remove old ZIP if exists
    if Path(zip_filename).exists():
        os.remove(zip_filename)
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files directly to ZIP root (no folder prefix)
        for file_path in output_path.iterdir():
            if file_path.is_file():
                zipf.write(file_path, arcname=file_path.name)
    
    print(f"Created ZIP file: {zip_filename}")
    
    # Verify ZIP structure
    print("\nZIP file contents:")
    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        file_list = zipf.namelist()
        for name in sorted(file_list)[:10]:
            print(f"  - {name}")
        if len(file_list) > 10:
            print(f"  ... and {len(file_list) - 10} more files")
        
        print(f"\nTotal files in ZIP: {len(file_list)}")
    
    # Print final report
    print("\n" + "="*80)
    print("PACKAGE CREATION COMPLETE")
    print("="*80)
    
    print(f"\nOutput ZIP file: {zip_filename}")
    print(f"Temporary directory: {output_path} (you can delete this after import)")
    
    print(f"\nStatistics:")
    print(f"  Products processed: {stats['products_processed']}")
    print(f"  Content files (PDFs) copied: {stats['content_files_copied']}")
    print(f"  Icon files copied: {stats['icon_files_copied']}")
    print(f"  Detail image files copied: {stats['detail_files_copied']}")
    print(f"  Total unique files copied: {len(files_copied)}")
    print(f"  Total files in ZIP: {len(list(output_path.iterdir()))}")
    
    # Report missing files
    if stats['missing_files']:
        print(f"\nWARNING: Missing files ({len(stats['missing_files'])}):")
        for product_name, filename, file_type, expected_path in stats['missing_files'][:10]:
            print(f"  - {filename} ({file_type})")
            print(f"    Product: {product_name}")
            print(f"    Expected: {expected_path}")
        if len(stats['missing_files']) > 10:
            print(f"  ... and {len(stats['missing_files']) - 10} more")
        
        print("\nPossible issues:")
        print("  1. File doesn't exist in the expected location")
        print("  2. Filename in CSV doesn't match actual filename")
        print("  3. Product folder structure is different than expected")
    else:
        print("\nAll asset files found and copied successfully!")
    
    print("\n" + "="*80)
    print("READY FOR MDSF IMPORT")
    print("="*80)
    print(f"\nNext steps:")
    print(f"1. Review the contents of: {zip_filename}")
    print(f"2. Go to MDSF: Administration > Export / Import")
    print(f"3. Select 'Products-Add or Update' from dropdown")
    print(f"4. Click 'Choose File' and select: {zip_filename}")
    print(f"5. Leave format as 'Unicode (UTF-8)' and delimiter as comma")
    print(f"6. Click 'Import Template'")
    print(f"7. Verify import results")
    
    return zip_filename

if __name__ == "__main__":
    # Configuration
    if len(sys.argv) >= 4:
        input_csv = sys.argv[1]
        assets_dir = sys.argv[2]
        thumbnails_dir = sys.argv[3]
        output_dir = sys.argv[4] if len(sys.argv) > 4 else "MDSF_Import_Package"
    else:
        # Default values - modify these based on your folder structure
        input_csv = "mdsf_import.csv"
        assets_dir = "../static_assets"
        thumbnails_dir = "../static_assets_thumbnails"
        output_dir = "MDSF_Import_Package"
    
    print(f"Configuration:")
    print(f"  Input CSV: {input_csv}")
    print(f"  Assets directory: {assets_dir}")
    print(f"  Thumbnails directory: {thumbnails_dir}")
    print(f"  Output directory: {output_dir}")
    print()
    
    # Validate inputs
    if not Path(input_csv).exists():
        print(f"ERROR: CSV file not found: {input_csv}")
        print("Please provide a valid CSV file path")
        sys.exit(1)
    
    if not Path(assets_dir).exists():
        print(f"ERROR: Assets folder not found: {assets_dir}")
        print("Please provide a valid assets folder path")
        sys.exit(1)
    
    if not Path(thumbnails_dir).exists():
        print(f"ERROR: Thumbnails folder not found: {thumbnails_dir}")
        print("Please provide a valid thumbnails folder path")
        sys.exit(1)
    
    # Create the package
    zip_file = create_mdsf_package(input_csv, assets_dir, thumbnails_dir, output_dir)
    
    if zip_file:
        print(f"\nSUCCESS! Package ready: {zip_file}")
    else:
        print(f"\nERROR: Package creation failed")
        sys.exit(1)