import pandas as pd
import sys

def merge_ticket_templates(product_csv, pricing_csv, output_csv):
    """
    Merge pricing elements from pricing CSV into product CSV as TicketTemplate values
    """
    print("="*80)
    print("TICKET TEMPLATE MERGER")
    print("="*80)
    
    # Read the product CSV (try to auto-detect delimiter)
    print(f"\nReading product CSV: {product_csv}")
    # First try comma
    try:
        products_df = pd.read_csv(product_csv, encoding='utf-8')
        # Check if it was read correctly (should have multiple columns)
        if len(products_df.columns) == 1:
            # Try tab delimiter instead
            products_df = pd.read_csv(product_csv, sep='\t', encoding='utf-8')
    except:
        products_df = pd.read_csv(product_csv, sep='\t', encoding='utf-8')
    
    print(f"Loaded {len(products_df)} products with {len(products_df.columns)} columns")
    print(f"Product CSV columns (first 5): {list(products_df.columns)[:5]}")
    
    # Read the pricing elements CSV (try to auto-detect delimiter)
    print(f"\nReading pricing elements CSV: {pricing_csv}")
    try:
        pricing_df = pd.read_csv(pricing_csv, sep='\t', encoding='utf-8')
        # Check if it was read correctly
        if len(pricing_df.columns) == 1:
            pricing_df = pd.read_csv(pricing_csv, encoding='utf-8')
    except:
        pricing_df = pd.read_csv(pricing_csv, encoding='utf-8')
    
    print(f"Loaded {len(pricing_df)} pricing element records with {len(pricing_df.columns)} columns")
    print(f"Pricing CSV columns (first 5): {list(pricing_df.columns)[:5]}")
    
    # Check for ProductID column (handle different names)
    product_id_col = None
    if 'uStore_ProductID' in products_df.columns:
        product_id_col = 'uStore_ProductID'
    elif 'ProductID' in products_df.columns:
        product_id_col = 'ProductID'
    else:
        print("\nERROR: No ProductID column found in product CSV!")
        print(f"Available columns: {list(products_df.columns)}")
        sys.exit(1)
    
    print(f"\nUsing '{product_id_col}' column from product CSV")
    
    # Check pricing CSV has ProductID
    if 'ProductID' not in pricing_df.columns:
        print("\nERROR: 'ProductID' column not found in pricing CSV!")
        print(f"Available columns: {list(pricing_df.columns)}")
        sys.exit(1)
    
    # Filter out non-production pricing elements
    # Keep only elements that look like production specs, not "Base" or notes
    print("\nFiltering pricing elements...")
    pricing_df = pricing_df[
        ~pricing_df['PricingElement'].str.contains('Note for|Billing|Assignment', case=False, na=False)
    ].copy()
    
    print(f"After filtering: {len(pricing_df)} pricing element records")
    
    # For products with multiple pricing elements, pick the best one
    # Priority: anything with dimensions > "Base" > first available
    def pick_best_pricing_element(group):
        elements = group['PricingElement'].tolist()
        
        # Filter out "Base" if there are other options
        non_base = [e for e in elements if e.lower() != 'base']
        
        if non_base:
            # Prefer elements with dimensions (contains 'x' or numbers)
            dimension_elements = [e for e in non_base if 'x' in e.lower() or any(char.isdigit() for char in e)]
            if dimension_elements:
                return dimension_elements[0]
            return non_base[0]
        
        # If only "Base" available, return it
        return elements[0] if elements else None
    
    # Group by ProductID and pick best pricing element
    best_pricing = pricing_df.groupby('ProductID').apply(pick_best_pricing_element).reset_index()
    best_pricing.columns = ['ProductID', 'PricingElement']
    
    # Create mapping dictionary
    pricing_map = best_pricing.set_index('ProductID')['PricingElement'].to_dict()
    
    print(f"\nCreated mapping for {len(pricing_map)} unique products")
    
    # Track statistics
    stats = {
        'already_had_template': 0,
        'filled_from_pricing': 0,
        'still_missing': 0,
        'updated_list': []
    }
    
    # Update TicketTemplate column
    print("\nMerging pricing elements into TicketTemplate column...")
    for idx, row in products_df.iterrows():
        product_id = row[product_id_col]  # Use the identified column name
        current_template = row['TicketTemplate']
        
        # If TicketTemplate is already populated, keep it
        if pd.notna(current_template) and str(current_template).strip() != '':
            stats['already_had_template'] += 1
            continue
        
        # Try to fill from pricing elements
        if product_id in pricing_map:
            new_template = pricing_map[product_id]
            products_df.at[idx, 'TicketTemplate'] = new_template
            stats['filled_from_pricing'] += 1
            stats['updated_list'].append((row['Name'], new_template))
        else:
            stats['still_missing'] += 1
    
    # Save updated CSV (comma-delimited)
    products_df.to_csv(output_csv, index=False, encoding='utf-8')
    
    # Report results
    print("\n" + "="*80)
    print("MERGE COMPLETE")
    print("="*80)
    
    print(f"\n✓ CSV updated and saved to: {output_csv}")
    print(f"\nStatistics:")
    print(f"  Total products: {len(products_df)}")
    print(f"  Already had TicketTemplate: {stats['already_had_template']}")
    print(f"  Filled from pricing elements: {stats['filled_from_pricing']}")
    print(f"  Still missing TicketTemplate: {stats['still_missing']}")
    
    # Show some examples of what was updated
    if stats['updated_list']:
        print(f"\nSample of updated products:")
        for name, template in stats['updated_list'][:10]:
            print(f"  - {name[:50]:50} → {template}")
        if len(stats['updated_list']) > 10:
            print(f"  ... and {len(stats['updated_list']) - 10} more")
    
    # Show products still missing TicketTemplate
    if stats['still_missing'] > 0:
        print(f"\n⚠ Products still missing TicketTemplate:")
        missing_df = products_df[
            products_df['TicketTemplate'].isna() | 
            (products_df['TicketTemplate'].astype(str).str.strip() == '')
        ]
        for idx, row in missing_df.head(10).iterrows():
            print(f"  - {row['Name']} (Product ID: {row[product_id_col]})")
        if stats['still_missing'] > 10:
            print(f"  ... and {stats['still_missing'] - 10} more")
    
    print("\n" + "="*80)
    
    return products_df

if __name__ == "__main__":
    # Get file paths from command line or use defaults
    product_csv = sys.argv[1] if len(sys.argv) > 1 else "Final-Sample-AFC.csv"
    pricing_csv = sys.argv[2] if len(sys.argv) > 2 else "Product_Ticket_Templates.csv"
    output_csv = sys.argv[3] if len(sys.argv) > 3 else product_csv.replace('.csv', '_with_tickets.csv')
    
    print(f"Product CSV: {product_csv}")
    print(f"Pricing CSV: {pricing_csv}")
    print(f"Output CSV: {output_csv}")
    
    # Run the merge
    result_df = merge_ticket_templates(product_csv, pricing_csv, output_csv)