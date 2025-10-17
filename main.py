import pandas as pd
import os
import shutil
import zipfile
from pathlib import Path
import sys

def create_mdsf_package(input_csv, assets_dir, thumbnails_dir, output_dir):
    """
    Create final MDSF import package:
    1. Remove helper columns
    2. Copy all referenced assets
    3. Create ZIP file
    """
    print("="*80)
    print("MDSF PACKAGE CREATOR")
    print("="*80)
    
    # Read the CSV
    print(f"\nReading CSV: {input_csv}")
    df = pd.read_csv(input_csv, encoding='utf-8')
    print(f"Loaded {len(df)} products")
    
    # FOR TESTING: Only process first product
    print("\n⚠ TEST MODE: Processing only the first product")
    df = df.head(1)
    print(f"Test product: {df.iloc[0]['Name']}")
    
    # Create output directory
    output_path = Path(output_dir)
    if output_path.exists():
        print(f"\nRemoving existing output directory: {output_path}")
        shutil.rmtree(output_path)
    
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Created output directory: {output_path}")
    
    # Convert to Path objects
    assets_path = Path(assets_dir)
    thumbnails_path = Path(thumbnails_dir)
    
    # Track statistics
    stats = {
        'products_processed': 0,
        'content_files_copied': 0,
        'icon_files_copied': 0,
        'detail_files_copied': 0,
        'missing_content_files': [],
        'missing_icon_files': [],
        'missing_detail_files': []
    }
    
    # Process each product and copy assets
    print("\nCopying asset files...")
    
    for idx, row in df.iterrows():
        product_id = row.get('uStore_ProductID', row.get('ProductID'))
        product_name = row['Name']
        stats['products_processed'] += 1
        
        # Copy ContentFiles
        content_files = str(row.get('ContentFile', ''))
        if content_files and content_files.strip():
            for filename in content_files.split(','):
                filename = filename.strip()
                if filename:
                    source = assets_path / f"Product_{product_id}" / filename
                    dest = output_path / filename
                    
                    if source.exists():
                        shutil.copy2(source, dest)
                        stats['content_files_copied'] += 1
                    else:
                        stats['missing_content_files'].append((product_name, filename))
        
        # Copy Icon files
        icon_files = str(row.get('Icon', ''))
        if icon_files and icon_files.strip():
            for filename in icon_files.split(','):
                filename = filename.strip()
                if filename:
                    source = thumbnails_path / f"Product_{product_id}" / "Pages" / "Thumbnails" / filename
                    dest = output_path / filename
                    
                    if source.exists():
                        if not dest.exists():  # Avoid duplicates
                            shutil.copy2(source, dest)
                            stats['icon_files_copied'] += 1
                    else:
                        stats['missing_icon_files'].append((product_name, filename))
        
        # Copy DetailImage files (usually same as Icon)
        detail_files = str(row.get('DetailImage', ''))
        if detail_files and detail_files.strip():
            for filename in detail_files.split(','):
                filename = filename.strip()
                if filename and filename not in icon_files:  # Skip if already copied
                    source = thumbnails_path / f"Product_{product_id}" / "Pages" / "Thumbnails" / filename
                    dest = output_path / filename
                    
                    if source.exists():
                        if not dest.exists():
                            shutil.copy2(source, dest)
                            stats['detail_files_copied'] += 1
                    else:
                        stats['missing_detail_files'].append((product_name, filename))
    
    # Remove helper columns
    print("\nRemoving uStore helper columns...")
    helper_columns = ['uStore_ProductID', 'uStore_StoreID', 'uStore_StoreName']
    columns_to_remove = [col for col in helper_columns if col in df.columns]
    
    if columns_to_remove:
        df_clean = df.drop(columns=columns_to_remove)
        print(f"Removed columns: {columns_to_remove}")
    else:
        df_clean = df
        print("No helper columns found (may have been removed already)")
    
    # Save cleaned CSV to output directory
    print("\nSaving CSV to output directory...")
    csv_output_path = output_path / "products.csv"
    df_clean.to_csv(csv_output_path, index=False, encoding='utf-8')
    print(f"Saved CSV: {csv_output_path}")
    print(f"Final columns: {list(df_clean.columns)}")
    
    # Create ZIP file
    print("\nCreating ZIP file...")
    zip_filename = f"{output_dir}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add CSV
        zipf.write(csv_output_path, arcname='products.csv')
        
        # Add all asset files
        for file_path in output_path.iterdir():
            if file_path.is_file() and file_path.name != 'products.csv':
                zipf.write(file_path, arcname=file_path.name)
    
    print(f"Created ZIP file: {zip_filename}")
    
    # Print final report
    print("\n" + "="*80)
    print("PACKAGE CREATION COMPLETE")
    print("="*80)
    
    print(f"\n✓ Output directory: {output_path}")
    print(f"✓ ZIP file: {zip_filename}")
    
    print(f"\nStatistics:")
    print(f"  Products processed: {stats['products_processed']}")
    print(f"  Content files copied: {stats['content_files_copied']}")
    print(f"  Icon files copied: {stats['icon_files_copied']}")
    print(f"  Detail image files copied: {stats['detail_files_copied']}")
    print(f"  Total files in package: {len(list(output_path.iterdir()))}")
    
    # Report missing files
    if stats['missing_content_files']:
        print(f"\n⚠ Missing content files ({len(stats['missing_content_files'])}):")
        for product_name, filename in stats['missing_content_files'][:10]:
            print(f"  - {product_name}: {filename}")
        if len(stats['missing_content_files']) > 10:
            print(f"  ... and {len(stats['missing_content_files']) - 10} more")
    
    if stats['missing_icon_files']:
        print(f"\n⚠ Missing icon files ({len(stats['missing_icon_files'])}):")
        for product_name, filename in stats['missing_icon_files'][:10]:
            print(f"  - {product_name}: {filename}")
        if len(stats['missing_icon_files']) > 10:
            print(f"  ... and {len(stats['missing_icon_files']) - 10} more")
    
    if not stats['missing_content_files'] and not stats['missing_icon_files']:
        print("\n✓ All asset files found and copied successfully!")
    
    print("\n" + "="*80)
    print("READY FOR MDSF IMPORT")
    print("="*80)
    print(f"\nNext steps:")
    print(f"1. Review the contents of: {zip_filename}")
    print(f"2. Go to MDSF: Administration > Export / Import")
    print(f"3. Upload {zip_filename}")
    print(f"4. Verify import results")
    
    return zip_filename

if __name__ == "__main__":
    # Configuration
    input_csv = sys.argv[1] if len(sys.argv) > 1 else "Final-Sample-AFC_with_tickets.csv"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "MDSF_Import_Package"
    
    # Paths relative to script location
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    
    assets_dir = project_dir / "static_assets"
    thumbnails_dir = project_dir / "static_assets_thumbnails"
    
    print(f"Input CSV: {input_csv}")
    print(f"Assets directory: {assets_dir}")
    print(f"Thumbnails directory: {thumbnails_dir}")
    print(f"Output directory: {output_dir}")
    
    # Create the package
    zip_file = create_mdsf_package(input_csv, assets_dir, thumbnails_dir, output_dir)