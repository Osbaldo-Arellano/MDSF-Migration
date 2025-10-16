import pandas as pd
import re

def clean_text(text):
    """Remove extra quotes and clean up text"""
    if pd.isna(text) or text == '':
        return ''
    text = str(text).strip()
    # Remove surrounding quotes if present
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return text

def extract_specs(text):
    """Extract size/spec information from text"""
    if not text:
        return []
    specs = []
    # Look for dimensions like 8.5" x 11" or 8.5x11
    size_patterns = [
        r'\d+\.?\d*\s*["\']?\s*x\s*\d+\.?\d*\s*["\']?',
        r'\d+\s*sided?',
        r'Updated \d{1,2}/\d{4}',
        r'Updated \d{1,2}-\d{1,2}-\d{4}'
    ]
    for pattern in size_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        specs.extend(matches)
    return specs

def generate_seo_title(row):
    """Generate SEO-friendly title for each product"""
    name = clean_text(row['Name'])
    brief_desc = clean_text(row['BriefDescription'])
    long_desc = clean_text(row['LongDescription'])
    categories = clean_text(row['StoreFront/Categories'])
    store_name = clean_text(row['uStore_StoreName'])
    
    # Extract location from product name if present
    location_keywords = ['Beaverton', 'Tigard', 'Portland', 'Oregon City', 
                        'Hillsboro', 'Cedar Mill', 'Camas', 'Orchards', 'NE', 'NW']
    location = None
    for loc in location_keywords:
        if loc.lower() in name.lower():
            location = loc
            break
    
    # Extract product type from name
    product_type = None
    type_keywords = {
        'envelope': 'Envelope',
        'card': 'Card',
        'flier': 'Flier',
        'flyer': 'Flyer',
        'brochure': 'Brochure',
        'letterhead': 'Letterhead',
        'form': 'Form',
        'sales aid': 'Sales Aid',
        'postcard': 'Postcard',
        'booklet': 'Booklet',
        'poster': 'Poster',
        'label': 'Label',
        'lanyard': 'Lanyard',
        'sign': 'Sign'
    }
    for keyword, ptype in type_keywords.items():
        if keyword.lower() in name.lower():
            product_type = ptype
            break
    
    # Extract specifications
    specs = []
    specs.extend(extract_specs(brief_desc))
    specs.extend(extract_specs(long_desc))
    
    # Build SEO title
    title_parts = []
    
    # Start with product type if found
    if product_type:
        title_parts.append(product_type)
    
    # Add location if found
    if location:
        title_parts.append(f"- {location}")
    
    # Add key specs (first one only to keep it concise)
    if specs and len(specs) > 0:
        # Get first meaningful spec
        spec = specs[0].strip()
        if spec and 'Updated' not in spec:
            title_parts.append(f"({spec})")
    
    # Add store name
    if store_name and store_name != 'AFC Urgent Care':
        title_parts.append(f"| {store_name}")
    else:
        title_parts.append("| AFC Urgent Care")
    
    # Fallback to cleaned name if no parts extracted
    if not title_parts:
        return name
    
    seo_title = ' '.join(title_parts)
    
    # Truncate to reasonable length (60-70 chars is optimal for SEO)
    if len(seo_title) > 70:
        seo_title = seo_title[:67] + "..."
    
    return seo_title

def generate_seo_data(csv_file):
    """
    Generate SEO titles for all products in CSV
    Returns a dictionary mapping ProductID to SEO title
    """
    # Read the CSV
    df = pd.read_csv(csv_file, sep='\t')
    
    # Generate SEO titles
    seo_mapping = {}
    
    for idx, row in df.iterrows():
        product_id = row['uStore_ProductID']
        seo_title = generate_seo_title(row)
        seo_mapping[product_id] = seo_title
    
    return seo_mapping

# Example usage
if __name__ == "__main__":
    import sys
    
    # Get input CSV file from command line or use default
    input_csv = sys.argv[1] if len(sys.argv) > 1 else 'Final-Sample-AFC.csv'
    output_csv = sys.argv[2] if len(sys.argv) > 2 else input_csv.replace('.csv', '_with_seo.csv')
    
    print(f"Reading CSV: {input_csv}")
    
    # Read the CSV with tab delimiter (TSV file)
    df = pd.read_csv(input_csv, sep='\t', encoding='utf-8')
    print(f"Loaded {len(df)} products")
    print(f"Columns found: {list(df.columns)[:5]}...")
    
    print(f"Processing {len(df)} products...")
    
    # Generate SEO titles for each row
    df['SEOTitle'] = df.apply(generate_seo_title, axis=1)
    
    # Show sample of what was generated
    print("\nSample SEO Titles Generated:")
    print("-" * 80)
    for idx, row in df.head(10).iterrows():
        print(f"{row['Name'][:40]:40} -> {row['SEOTitle']}")
    
    # Save the modified CSV (as TSV with tabs)
    df.to_csv(output_csv, sep='\t', index=False)
    
    print(f"\n✓ CSV saved with SEO titles: {output_csv}")
    print(f"  Total products processed: {len(df)}")
    print(f"  SEO titles generated: {df['SEOTitle'].notna().sum()}")