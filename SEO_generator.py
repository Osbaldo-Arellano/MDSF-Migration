import pandas as pd
import re
import csv

def clean_text(text):
    """Remove extra quotes and clean up text"""
    if pd.isna(text) or text == '':
        return ''
    text = str(text).strip()
    # Remove surrounding quotes if present
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    # Handle double quotes
    text = text.replace('""', '"')
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
    
    # Extract location from product name if present (only if followed by space or at end)
    location_keywords = ['Beaverton', 'Tigard', 'Oregon City', 'Hillsboro', 'Cedar Mill', 'Camas', 'Orchards']
    location = None
    for loc in location_keywords:
        # Check if location is in name and is a separate word
        if f' {loc}' in name or name.endswith(loc):
            location = loc
            break
    
    # Special case for Portland variations
    if 'NE Portland' in name:
        location = 'NE Portland'
    elif 'NW Portland' in name:
        location = 'NW Portland'
    elif 'Portland' in name and location is None:
        location = 'Portland'
    
    # Extract product type from name and categories
    product_type = None
    type_keywords = {
        'envelope': 'Envelope',
        'business card': 'Business Card',
        'appointment card': 'Appointment Card',
        'qr code': 'QR Code Card',
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
        'lanyard': 'Lanyard',
        'sign': 'Sign',
        'handout': 'Handout'
    }
    
    name_lower = name.lower()
    for keyword, ptype in type_keywords.items():
        if keyword in name_lower:
            product_type = ptype
            break
    
    # If no type found in name, check categories
    if not product_type and categories:
        categories_lower = categories.lower()
        category_mappings = {
            'envelope': 'Envelope',
            'business card': 'Business Card',
            'appointment card': 'Appointment Card',
            'google review': 'Review Card',
            'brochure': 'Brochure',
            'flier': 'Flier',
            'form': 'Form',
            'letter': 'Letter',
            'sales aid': 'Sales Aid',
            'label': 'Label',
            'lanyard': 'Lanyard',
            'booklet': 'Booklet',
            'misc': None  # Skip generic categories
        }
        
        for keyword, ptype in category_mappings.items():
            if keyword in categories_lower and ptype:
                product_type = ptype
                break
    
    # Extract specifications
    specs = []
    specs.extend(extract_specs(brief_desc))
    specs.extend(extract_specs(long_desc))
    
    # Build SEO title
    title_parts = []
    
    # Start with product type (or use first part of name if no type found)
    if product_type:
        title_parts.append(product_type)
    else:
        # Use first meaningful words from name as fallback
        name_parts = name.split()
        if len(name_parts) > 0:
            # Take first 1-3 words that aren't "AFC" or "Urgent Care"
            fallback_words = []
            for word in name_parts[:5]:
                if word.lower() not in ['afc', 'urgent', 'care']:
                    fallback_words.append(word)
                if len(fallback_words) >= 3:
                    break
            if fallback_words:
                title_parts.append(' '.join(fallback_words))
    
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
    title_parts.append("| AFC Urgent Care")
    
    # Fallback to cleaned name if no parts extracted
    if len(title_parts) == 1:  # Only has store name
        return f"{name} | AFC Urgent Care"
    
    seo_title = ' '.join(title_parts)
    
    # Truncate to reasonable length (60-70 chars is optimal for SEO)
    if len(seo_title) > 70:
        seo_title = seo_title[:67] + "..."
    
    return seo_title

def generate_keywords(row):
    """Generate SEO keywords for each product"""
    name = clean_text(row['Name'])
    brief_desc = clean_text(row['BriefDescription'])
    categories = clean_text(row['StoreFront/Categories'])
    ticket_template = clean_text(row['TicketTemplate'])
    
    keywords = set()  # Use set to avoid duplicates
    
    # Extract location keywords
    location_keywords = ['Beaverton', 'Tigard', 'Oregon City', 'Hillsboro', 
                        'Cedar Mill', 'Camas', 'Orchards', 'Portland', 'NE Portland', 'NW Portland']
    for loc in location_keywords:
        if loc in name:
            keywords.add(loc.lower())
            # Add city name without prefix
            if 'Portland' in loc:
                keywords.add('portland')
    
    # Extract product type keywords
    name_lower = name.lower()
    type_keywords = {
        'envelope': ['envelope', 'mailing', 'stationery'],
        'business card': ['business card', 'card', 'networking', 'contact'],
        'appointment card': ['appointment card', 'card', 'reminder'],
        'qr code': ['qr code', 'card', 'review', 'feedback'],
        'card': ['card'],
        'flier': ['flier', 'flyer', 'marketing', 'promotional'],
        'brochure': ['brochure', 'marketing', 'informational'],
        'letterhead': ['letterhead', 'stationery', 'correspondence'],
        'registration': ['registration', 'form', 'patient'],
        'form': ['form', 'document'],
        'letter': ['letter', 'correspondence'],
        'sales aid': ['sales aid', 'marketing', 'sales tool'],
        'postcard': ['postcard', 'mailing', 'marketing'],
        'booklet': ['booklet', 'guide', 'informational'],
        'poster': ['poster', 'signage', 'display'],
        'label': ['label', 'sticker'],
        'lanyard': ['lanyard', 'badge holder', 'credential'],
        'sign': ['sign', 'signage', 'display'],
        'handout': ['handout', 'informational', 'patient education']
    }
    
    for keyword, related_terms in type_keywords.items():
        if keyword in name_lower:
            keywords.update(related_terms)
            break
    
    # Add category-based keywords
    if categories:
        categories_lower = categories.lower()
        if 'sales aid' in categories_lower:
            keywords.update(['sales aid', 'marketing', 'sales tool'])
        if 'envelope' in categories_lower:
            keywords.update(['envelope', 'mailing'])
        if 'form' in categories_lower or 'letter' in categories_lower:
            keywords.update(['form', 'document', 'patient'])
        if 'brochure' in categories_lower or 'flier' in categories_lower:
            keywords.update(['brochure', 'marketing', 'informational'])
        if 'business card' in categories_lower:
            keywords.update(['business card', 'networking'])
        if 'label' in categories_lower:
            keywords.update(['label', 'sticker'])
        if 'booklet' in categories_lower:
            keywords.update(['booklet', 'guide'])
        if 'google review' in categories_lower:
            keywords.update(['review', 'feedback', 'qr code'])
    
    # Add specific keywords based on content
    if 'spanish' in name_lower:
        keywords.add('spanish')
    if 'uscis' in name_lower:
        keywords.update(['uscis', 'immigration'])
    if 'occupational' in name_lower or 'occmed' in name_lower:
        keywords.update(['occupational medicine', 'workers comp', 'workplace health'])
    if 'orientation' in name_lower:
        keywords.add('orientation')
    if 'translation' in name_lower:
        keywords.add('translation')
    if 'physical' in name_lower:
        keywords.add('physical exam')
    
    # Add size specifications as keywords
    specs = extract_specs(brief_desc)
    for spec in specs[:2]:  # Only first 2 specs to avoid clutter
        if 'Updated' not in spec:
            spec_clean = spec.strip().replace('"', 'inch').replace("'", 'inch')
            if spec_clean and len(spec_clean) < 20:
                keywords.add(spec_clean.lower())
    
    # Always include core brand keywords
    keywords.update(['afc', 'urgent care', 'medical', 'healthcare'])
    
    # Convert to comma-separated string
    keywords_list = sorted(list(keywords))  # Sort for consistency
    keywords_str = ', '.join(keywords_list)
    
    # Truncate to 500 character limit
    if len(keywords_str) > 500:
        # Trim to last complete keyword before 500 chars
        keywords_str = keywords_str[:500]
        last_comma = keywords_str.rfind(',')
        if last_comma > 0:
            keywords_str = keywords_str[:last_comma]
    
    return keywords_str

# Example usage
if __name__ == "__main__":
    import sys
    
    # Get input CSV file from command line or use default
    input_csv = sys.argv[1] if len(sys.argv) > 1 else 'Final-Sample-AFC.csv'
    output_csv = sys.argv[2] if len(sys.argv) > 2 else input_csv.replace('.csv', '_with_seo.csv')
    
    print(f"Reading CSV: {input_csv}")
    
    # Read as standard CSV (comma-delimited with quoted fields)
    # This handles embedded newlines and commas within quoted fields
    df = pd.read_csv(input_csv, encoding='utf-8')
    
    print(f"Loaded {len(df)} products")
    print(f"Columns: {list(df.columns)}")
    
    # Check if SEOTitle column exists
    if 'SEOTitle' not in df.columns:
        print("ERROR: SEOTitle column not found in CSV!")
        print("Available columns:", list(df.columns))
        sys.exit(1)
    
    print(f"\nProcessing {len(df)} products...")
    
    # Generate SEO titles and keywords for each row
    df['SEOTitle'] = df.apply(generate_seo_title, axis=1)
    df['KeyWords'] = df.apply(generate_keywords, axis=1)
    
    # Show sample of what was generated
    print("\nSample SEO Data Generated:")
    print("-" * 80)
    for idx, row in df.head(10).iterrows():
        print(f"{clean_text(row['Name'])[:35]:35}")
        print(f"  SEO Title: {row['SEOTitle']}")
        print(f"  Keywords:  {row['KeyWords'][:70]}...")
        print()
    
    # Save as standard CSV (comma-delimited with quoted fields)
    df.to_csv(output_csv, index=False)
    
    print(f"\n✓ CSV saved with SEO data: {output_csv}")
    print(f"  Total products processed: {len(df)}")
    print(f"  SEO titles generated: {df['SEOTitle'].notna().sum()}")
    print(f"  Keywords generated: {df['KeyWords'].notna().sum()}")