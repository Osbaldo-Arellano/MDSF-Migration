"""
Asset Linker - Generic Version
Links PDFs and images to products based on uStore_ProductID
Works for any storefront
"""

import pandas as pd
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

def link_assets(input_csv, output_csv, assets_dir, thumbnails_dir):
    """
    Link assets to products in CSV and populate ContentFile, Icon, and DetailImage columns
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("="*80)
    print("ASSET LINKER")
    print("="*80)
    print(f"\nReading CSV: {input_csv}")
    
    # Validate input file
    if not Path(input_csv).exists():
        print(f"ERROR: Input file not found: {input_csv}")
        return False
    
    # Read CSV
    try:
        df = pd.read_csv(input_csv, encoding='utf-8', keep_default_na=False)
    except Exception as e:
        print(f"ERROR: Failed to read CSV: {e}")
        return False
    
    print(f"Loaded {len(df)} products")
    
    # Validate required columns
    if 'uStore_ProductID' not in df.columns:
        print("ERROR: Missing required column: uStore_ProductID")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    # Convert paths to Path objects
    assets_path = Path(assets_dir)
    thumbnails_path = Path(thumbnails_dir)
    
    # Verify directories exist
    if not assets_path.exists():
        print(f"ERROR: Assets directory not found: {assets_path}")
        return False
    
    if not thumbnails_path.exists():
        print(f"ERROR: Thumbnails directory not found: {thumbnails_path}")
        return False
    
    print(f"Assets directory: {assets_path}")
    print(f"Thumbnails directory: {thumbnails_path}")
    
    # Add columns if they don't exist
    if 'ContentFile' not in df.columns:
        df['ContentFile'] = ''
    if 'Icon' not in df.columns:
        df['Icon'] = ''
    if 'DetailImage' not in df.columns:
        df['DetailImage'] = ''
    
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
    
    print(f"\nProcessing {len(df)} products...")
    
    # Process each product
    for idx, row in df.iterrows():
        product_id = row['uStore_ProductID']
        product_name = row.get('Name', f'Product {product_id}')
        
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
    try:
        df.to_csv(output_csv, index=False, encoding='utf-8')
    except Exception as e:
        print(f"ERROR: Failed to save CSV: {e}")
        return False
    
    # Print report
    print("\n" + "="*80)
    print("ASSET LINKING COMPLETE")
    print("="*80)
    print(f"\nOutput saved to: {output_csv}")
    print(f"\nStatistics:")
    print(f"  Total products processed: {len(df)}")
    print(f"  Products with PDFs: {stats['products_with_pdfs']}")
    print(f"  Products WITHOUT PDFs: {stats['products_without_pdfs']}")
    print(f"  Products with thumbnails: {stats['products_with_thumbnails']}")
    print(f"  Products WITHOUT thumbnails: {stats['products_without_thumbnails']}")
    print(f"  Total PDF files found: {stats['total_pdfs']}")
    print(f"  Total thumbnail files found: {stats['total_thumbnails']}")
    
    # Report missing assets (limited output)
    if missing_pdfs:
        print(f"\nWARNING: {len(missing_pdfs)} products missing PDFs")
        if len(missing_pdfs) <= 5:
            for product_id, name in missing_pdfs:
                print(f"  - Product {product_id}: {name}")
        else:
            for product_id, name in missing_pdfs[:3]:
                print(f"  - Product {product_id}: {name}")
            print(f"  ... and {len(missing_pdfs) - 3} more")
    
    if missing_thumbnails:
        print(f"\nWARNING: {len(missing_thumbnails)} products missing thumbnails")
        if len(missing_thumbnails) <= 5:
            for product_id, name in missing_thumbnails:
                print(f"  - Product {product_id}: {name}")
        else:
            for product_id, name in missing_thumbnails[:3]:
                print(f"  - Product {product_id}: {name}")
            print(f"  ... and {len(missing_thumbnails) - 3} more")
    
    if not missing_pdfs and not missing_thumbnails:
        print("\nAll products have complete assets!")
    
    print("\n" + "="*80)
    
    # Return success if at least some assets were found
    # This is not a critical failure if some products are missing assets
    return True

def main():
    """Main entry point"""
    if len(sys.argv) < 4:
        print("Usage: python asset_linker.py <input_csv> <output_csv> <assets_dir> <thumbnails_dir>")
        print("\nExample:")
        print("  python asset_linker.py with_seo.csv with_assets.csv ../static_assets ../static_assets_thumbnails")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_csv = sys.argv[2]
    assets_dir = sys.argv[3]
    thumbnails_dir = sys.argv[4]
    
    # Run asset linking
    success = link_assets(input_csv, output_csv, assets_dir, thumbnails_dir)
    
    if success:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()