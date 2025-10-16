import pandas as pd
import os
import sys
from pathlib import Path

def find_content_files(product_id, assets_dir):
    """
    Find content PDFs for a product, excluding PROOF files
    Returns list of PDF filenames (not full paths, just names)
    """
    product_folder = assets_dir / f"Product_{product_id}"
    
    if not product_folder.exists():
        return []
    
    # Find all PDF files
    pdf_files = list(product_folder.glob("*.pdf"))
    
    # Filter out PROOF files (case insensitive)
    non_proof_files = [
        f.name for f in pdf_files 
        if 'proof' not in f.name.lower()
    ]
    
    return non_proof_files

def find_thumbnail_files(product_id, thumbnails_dir):
    """
    Find all thumbnail images for a product
    Returns list of image filenames (not full paths, just names)
    """
    thumbnail_folder = thumbnails_dir / f"Product_{product_id}" / "Pages" / "Thumbnails"
    
    if not thumbnail_folder.exists():
        return []
    
    # Find all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(thumbnail_folder.glob(f"*{ext}"))
    
    # Return just filenames
    return [f.name for f in image_files]

def link_assets_to_csv(input_csv, output_csv, assets_dir, thumbnails_dir):
    """
    Link assets to products in CSV and populate ContentFile, Icon, and DetailImage columns
    """
    print(f"Reading CSV: {input_csv}")
    df = pd.read_csv(input_csv, encoding='utf-8')
    
    print(f"Loaded {len(df)} products")
    
    # Convert paths to Path objects
    assets_path = Path(assets_dir)
    thumbnails_path = Path(thumbnails_dir)
    
    # Verify directories exist
    if not assets_path.exists():
        print(f"ERROR: Assets directory not found: {assets_path}")
        sys.exit(1)
    
    if not thumbnails_path.exists():
        print(f"ERROR: Thumbnails directory not found: {thumbnails_path}")
        sys.exit(1)
    
    print(f"\nScanning assets in: {assets_path}")
    print(f"Scanning thumbnails in: {thumbnails_path}")
    
    # Track statistics
    stats = {
        'products_with_pdfs': 0,
        'products_without_pdfs': 0,
        'products_with_thumbnails': 0,
        'products_without_thumbnails': 0,
        'total_pdfs': 0,
        'total_thumbnails': 0
    }
    
    missing_pdfs = []
    missing_thumbnails = []
    
    print("\nProcessing products...")
    
    # Process each product
    for idx, row in df.iterrows():
        product_id = row['uStore_ProductID']
        product_name = row['Name']
        
        # Find content files (PDFs)
        content_files = find_content_files(product_id, assets_path)
        if content_files:
            df.at[idx, 'ContentFile'] = ', '.join(content_files)
            stats['products_with_pdfs'] += 1
            stats['total_pdfs'] += len(content_files)
        else:
            df.at[idx, 'ContentFile'] = ''
            stats['products_without_pdfs'] += 1
            missing_pdfs.append((product_id, product_name))
        
        # Find thumbnail files
        thumbnail_files = find_thumbnail_files(product_id, thumbnails_path)
        if thumbnail_files:
            thumbnails_str = ', '.join(thumbnail_files)
            df.at[idx, 'Icon'] = thumbnails_str
            df.at[idx, 'DetailImage'] = thumbnails_str  # Use same thumbnails for both
            stats['products_with_thumbnails'] += 1
            stats['total_thumbnails'] += len(thumbnail_files)
        else:
            df.at[idx, 'Icon'] = ''
            df.at[idx, 'DetailImage'] = ''
            stats['products_without_thumbnails'] += 1
            missing_thumbnails.append((product_id, product_name))
    
    # Save the updated CSV
    df.to_csv(output_csv, index=False, encoding='utf-8')
    
    # Print report
    print("\n" + "="*80)
    print("ASSET LINKING REPORT")
    print("="*80)
    
    print(f"\n✓ CSV updated and saved to: {output_csv}")
    print(f"\nStatistics:")
    print(f"  Total products processed: {len(df)}")
    print(f"  Products with PDFs: {stats['products_with_pdfs']}")
    print(f"  Products WITHOUT PDFs: {stats['products_without_pdfs']}")
    print(f"  Products with thumbnails: {stats['products_with_thumbnails']}")
    print(f"  Products WITHOUT thumbnails: {stats['products_without_thumbnails']}")
    print(f"  Total PDF files found: {stats['total_pdfs']}")
    print(f"  Total thumbnail files found: {stats['total_thumbnails']}")
    
    # Report missing assets
    if missing_pdfs:
        print(f"\n⚠ Products missing PDFs ({len(missing_pdfs)}):")
        for product_id, name in missing_pdfs[:10]:  # Show first 10
            print(f"  - Product {product_id}: {name}")
        if len(missing_pdfs) > 10:
            print(f"  ... and {len(missing_pdfs) - 10} more")
    
    if missing_thumbnails:
        print(f"\n⚠ Products missing thumbnails ({len(missing_thumbnails)}):")
        for product_id, name in missing_thumbnails[:10]:  # Show first 10
            print(f"  - Product {product_id}: {name}")
        if len(missing_thumbnails) > 10:
            print(f"  ... and {len(missing_thumbnails) - 10} more")
    
    if not missing_pdfs and not missing_thumbnails:
        print("\n✓ All products have complete assets!")
    
    print("\n" + "="*80)
    
    return df, stats, missing_pdfs, missing_thumbnails

if __name__ == "__main__":
    # Configuration
    input_csv = sys.argv[1] if len(sys.argv) > 1 else "Final-Sample-AFC_with_seo.csv"
    output_csv = sys.argv[2] if len(sys.argv) > 2 else input_csv.replace('.csv', '_with_assets.csv')
    
    # Paths relative to script location
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    
    assets_dir = project_dir / "static_assets"
    thumbnails_dir = project_dir / "static_assets_thumbnails"
    
    print("="*80)
    print("ASSET LINKER - uStore to MDSF Migration")
    print("="*80)
    print(f"\nProject directory: {project_dir}")
    print(f"Assets directory: {assets_dir}")
    print(f"Thumbnails directory: {thumbnails_dir}")
    
    # Run the linking process
    df, stats, missing_pdfs, missing_thumbnails = link_assets_to_csv(
        input_csv, 
        output_csv, 
        assets_dir, 
        thumbnails_dir
    )