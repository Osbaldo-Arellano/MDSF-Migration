"""
SEO Generator
Generates SEO-friendly titles and keywords for any storefront
"""

import pandas as pd
import re
import sys
from pathlib import Path

def clean_text(text):
    """Remove extra quotes and clean up text"""
    if pd.isna(text) or text == '':
        return ''
    text = str(text).strip()
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    text = text.replace('""', '"')
    return text

def extract_specs(text):
    """Extract size/spec information from text"""
    if not text:
        return []
    specs = []
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

def extract_locations_from_text(text):
    """
    Auto-detect location keywords from text (city names, states)
    Returns list of detected locations
    """
    if not text:
        return []
    
    # Common US location patterns
    # State abbreviations
    state_pattern = r'\b[A-Z]{2}\b'
    # City names (capitalized words, potentially multi-word)
    city_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    
    locations = []
    
    # Find state abbreviations
    states = re.findall(state_pattern, text)
    locations.extend(states)
    
    # Find potential city names (but filter out common false positives)
    false_positives = {'The', 'A', 'An', 'In', 'On', 'At', 'To', 'For', 'With', 'And', 'Or'}
    cities = re.findall(city_pattern, text)
    locations.extend([c for c in cities if c not in false_positives])
    
    return list(set(locations))

def get_product_type(name, categories):
    """
    Extract product type from name and categories
    Generic - works for any product
    """
    type_keywords = {
        'envelope': 'Envelope',
        'business card': 'Business Card',
        'appointment card': 'Appointment Card',
        'qr code': 'QR Code Card',
        'review card': 'Review Card',
        'card': 'Card',
        'flier': 'Flier',
        'flyer': 'Flyer',
        'brochure': 'Brochure',
        'letterhead': 'Letterhead',
        'registration': 'Registration Form',
        'form': 'Form',
        'letter': 'Letter',
        'sales aid': 'Sales Aid',
        'postcard': 'Postcard',
        'booklet': 'Booklet',
        'poster': 'Poster',
        'label': 'Label',
        'sticker': 'Sticker',
        'lanyard': 'Lanyard',
        'badge': 'Badge',
        'sign': 'Sign',
        'banner': 'Banner',
        'handout': 'Handout',
        'presentation': 'Presentation',
        'folder': 'Folder',
        'notepad': 'Notepad',
        'pen': 'Pen',
        'gift': 'Gift',
        'merchandise': 'Merchandise'
    }
    
    name_lower = name.lower()
    categories_lower = categories.lower() if categories else ''
    
    # Check name first (more specific)
    for keyword, ptype in type_keywords.items():
        if keyword in name_lower:
            return ptype
    
    # Then check categories
    for keyword, ptype in type_keywords.items():
        if keyword in categories_lower:
            return ptype
    
    return None

def generate_seo_title(row):
    """Generate SEO-friendly title for any product"""
    name = clean_text(row['Name'])
    brief_desc = clean_text(row.get('BriefDescription', ''))
    long_desc = clean_text(row.get('LongDescription', ''))
    categories = clean_text(row.get('StoreFront/Categories', ''))
    store_name = clean_text(row.get('uStore_StoreName', ''))
    
    # Extract product type
    product_type = get_product_type(name, categories)
    
    # Auto-detect locations from name
    locations = extract_locations_from_text(name)
    location = locations[0] if locations else None
    
    # Extract specifications
    specs = []
    specs.extend(extract_specs(brief_desc))
    specs.extend(extract_specs(long_desc))
    
    # Build SEO title
    title_parts = []
    
    # Start with product type or cleaned name
    if product_type:
        title_parts.append(product_type)
    else:
        # Use first meaningful words from name
        name_parts = name.split()
        if name_parts:
            # Take first 2-3 words, excluding common store prefixes
            common_prefixes = ['the', 'a', 'an']
            meaningful_words = [
                word for word in name_parts[:5] 
                if word.lower() not in common_prefixes
            ][:3]
            if meaningful_words:
                title_parts.append(' '.join(meaningful_words))
    
    # Add location if detected
    if location:
        title_parts.append(f"- {location}")
    
    # Add first meaningful spec
    if specs:
        spec = specs[0].strip()
        if spec and 'Updated' not in spec and len(spec) < 30:
            title_parts.append(f"({spec})")
    
    # Add store name
    if store_name:
        title_parts.append(f"| {store_name}")
    
    # Fallback to cleaned name if no parts extracted
    if len(title_parts) <= 1:
        return f"{name} | {store_name}" if store_name else name
    
    seo_title = ' '.join(title_parts)
    
    # Truncate to SEO-optimal length (60-70 chars)
    if len(seo_title) > 70:
        seo_title = seo_title[:67] + "..."
    
    return seo_title

def generate_keywords(row):
    """Generate SEO keywords for any product"""
    name = clean_text(row['Name'])
    brief_desc = clean_text(row.get('BriefDescription', ''))
    categories = clean_text(row.get('StoreFront/Categories', ''))
    store_name = clean_text(row.get('uStore_StoreName', ''))
    
    keywords = set()
    
    # Extract locations (auto-detect)
    locations = extract_locations_from_text(name)
    keywords.update([loc.lower() for loc in locations])
    
    # Product type keywords
    name_lower = name.lower()
    type_keyword_groups = {
        'envelope': ['envelope', 'mailing', 'stationery'],
        'business card': ['business card', 'card', 'networking', 'contact'],
        'appointment card': ['appointment card', 'reminder'],
        'qr code': ['qr code', 'review', 'feedback'],
        'card': ['card'],
        'flier': ['flier', 'flyer', 'marketing', 'promotional'],
        'brochure': ['brochure', 'marketing', 'informational'],
        'letterhead': ['letterhead', 'stationery', 'correspondence'],
        'registration': ['registration', 'form'],
        'form': ['form', 'document'],
        'letter': ['letter', 'correspondence'],
        'sales aid': ['sales aid', 'marketing', 'sales tool'],
        'postcard': ['postcard', 'mailing', 'marketing'],
        'booklet': ['booklet', 'guide'],
        'poster': ['poster', 'signage', 'display'],
        'label': ['label', 'sticker'],
        'lanyard': ['lanyard', 'badge holder'],
        'sign': ['sign', 'signage'],
        'banner': ['banner', 'display'],
        'handout': ['handout', 'informational']
    }
    
    # Add keywords based on product type
    for keyword, related_terms in type_keyword_groups.items():
        if keyword in name_lower:
            keywords.update(related_terms)
            break
    
    # Add category-based keywords
    if categories:
        categories_lower = categories.lower()
        # Extract category names as keywords
        category_parts = [c.strip() for c in categories.split('/')]
        for part in category_parts:
            if part and len(part) > 2:  # Skip very short parts
                keywords.add(part.lower())
    
    # Add language-specific keywords
    if 'spanish' in name_lower or 'español' in name_lower:
        keywords.add('spanish')
    
    # Add size specifications as keywords
    specs = extract_specs(brief_desc)
    for spec in specs[:2]:
        if 'Updated' not in spec:
            spec_clean = spec.strip().replace('"', 'inch').replace("'", 'inch')
            if spec_clean and len(spec_clean) < 20:
                keywords.add(spec_clean.lower())
    
    # Add brand keywords from store name
    if store_name:
        # Split store name into words and add as keywords
        store_words = store_name.lower().split()
        # Filter out common words
        common_words = {'online', 'print', 'portal', 'store', 'ordering', 'the', 'a', 'an'}
        meaningful_store_words = [w for w in store_words if w not in common_words]
        keywords.update(meaningful_store_words)
    
    # Convert to comma-separated string
    keywords_list = sorted(list(keywords))
    keywords_str = ', '.join(keywords_list)
    
    # Truncate to 500 character limit
    if len(keywords_str) > 500:
        keywords_str = keywords_str[:500]
        last_comma = keywords_str.rfind(',')
        if last_comma > 0:
            keywords_str = keywords_str[:last_comma]
    
    return keywords_str

def generate_seo_data(input_csv, output_csv):
    """
    Main function to generate SEO data for products
    """
    print("="*80)
    print("SEO GENERATOR")
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
    required_columns = ['Name']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    # Add SEOTitle and KeyWords columns if they don't exist
    if 'SEOTitle' not in df.columns:
        df['SEOTitle'] = ''
    if 'KeyWords' not in df.columns:
        df['KeyWords'] = ''
    
    print(f"\nGenerating SEO data for {len(df)} products...")
    
    # Generate SEO data
    df['SEOTitle'] = df.apply(generate_seo_title, axis=1)
    df['KeyWords'] = df.apply(generate_keywords, axis=1)
    
    # Show sample results
    print("\nSample SEO Data Generated:")
    print("-" * 80)
    sample_size = min(5, len(df))
    for idx, row in df.head(sample_size).iterrows():
        print(f"{clean_text(row['Name'])[:40]:40}")
        print(f"  SEO Title: {row['SEOTitle']}")
        print(f"  Keywords:  {row['KeyWords'][:60]}...")
        print()
    
    # Save output
    try:
        df.to_csv(output_csv, index=False, encoding='utf-8')
    except Exception as e:
        print(f"ERROR: Failed to save CSV: {e}")
        return False
    
    print("="*80)
    print("SEO GENERATION COMPLETE")
    print("="*80)
    print(f"Output saved to: {output_csv}")
    print(f"Total products processed: {len(df)}")
    print(f"SEO titles generated: {df['SEOTitle'].notna().sum()}")
    print(f"Keywords generated: {df['KeyWords'].notna().sum()}")
    print()
    
    return True

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python SEO_generator.py <input_csv> [output_csv]")
        print("\nExample:")
        print("  python SEO_generator.py raw_export.csv with_seo.csv")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    
    # Default output filename
    if len(sys.argv) >= 3:
        output_csv = sys.argv[2]
    else:
        # Auto-generate output filename
        input_path = Path(input_csv)
        output_csv = str(input_path.parent / f"{input_path.stem}_with_seo{input_path.suffix}")
    
    # Run SEO generation
    success = generate_seo_data(input_csv, output_csv)
    
    if success:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()