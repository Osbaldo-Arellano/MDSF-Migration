"""
Fields Mapper - Generic Version
Maps uStore CSV to MDSF 61-column format
Works for any storefront
"""

import pandas as pd
import sys
from pathlib import Path

def map_to_mdsf(input_file, output_file, use_auto_thumbnail=True, test_mode=False, test_limit=1):
    """
    Maps uStore product data to MDSF CSV template format
    
    Args:
        input_file: Path to uStore CSV export (with SEO and assets)
        output_file: Path for MDSF import CSV
        use_auto_thumbnail: If True, replaces Icon and DetailImage with "AutoThumbnail"
        test_mode: If True, process limited number of products
        test_limit: Number of products to process in test mode
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("="*80)
    print("MDSF FIELDS MAPPER")
    print("="*80)
    
    # Validate input file
    if not Path(input_file).exists():
        print(f"ERROR: Input file not found: {input_file}")
        return False
    
    print(f"\nReading CSV: {input_file}")
    
    # Read the uStore CSV
    try:
        df_ustore = pd.read_csv(input_file, encoding='utf-8', keep_default_na=False)
    except Exception as e:
        print(f"ERROR: Failed to read CSV: {e}")
        return False
    
    print(f"Loaded {len(df_ustore)} products")
    
    # Test mode
    if test_mode:
        print(f"\nTEST MODE: Processing only {test_limit} product(s)")
        df_ustore = df_ustore.head(test_limit)
    
    # Create DataFrame with exact MDSF template columns (in correct order)
    mdsf_columns = [
        'Name', 'DisplayName', 'Type', 'ProductId', 'BriefDescription', 'Icon', 
        'LongDescription', 'DetailImage', 'Active', 'TurnAroundTime', 'TurnAroundTimeUnit',
        'QuantityType', 'MaxOrderQuantityPermitted', 'Quantities', 
        'AllowBuyerToEditMultipleQuantity', 'EnforceMaxQuantityPermittedInCart',
        'OrderQuantitiesAllowSplitAcrossMultipleRecipients', 'DescriptionFooter',
        'ProductNotes', 'KeyWords', 'SEOTitle', 'UrlSlug', 'MetaDescription',
        'MobileSupported', 'BuyerDeliverableType', 'WeightValue', 'WeightUnit',
        'WidthValue', 'LengthValue', 'HeightValue', 'DimensionUnit',
        'MaxQuantityPerSubcontainer', 'ShipItemSeparately', 'ContentFile',
        'TicketTemplate', 'ProductNameToCopySecuritySettings', 'MISItemTemplate',
        'SmartCanvasTemplateName', 'DynamicPreview', 'AllowBuyerConfiguration',
        'StartDate', 'EndDate', 'PickLocation', 'WareHouseName', 'IsHighValueProduct',
        'HasUniqueSkid', 'PickStrategy', 'NotifyOnInventoryReceive', 'CustomerRep',
        'SalesRep', 'PhysicalCountInterval', 'StorageType', 'AllowBackOrder',
        'BackOrderRule', 'BackOrderMaxQty', 'ShowInventoryWhenBackOrderAllowed',
        'Threshold', 'Emails', 'Storefront/Categories', 'Barcode', 
        'EnableProductReturn', 'BuyNowButtonDescription', 'UseNewSmartCanvas'
    ]
    
    df_mdsf = pd.DataFrame(columns=mdsf_columns)
    
    # Direct field mappings from uStore to MDSF
    field_mapping = {
        'Name': 'Name',
        'DisplayName': 'DisplayName',
        'Type': 'Type',
        'SKU/ProductId': 'ProductId',
        'BriefDescription': 'BriefDescription',
        'Icon': 'Icon',
        'LongDescription': 'LongDescription',
        'DetailImage': 'DetailImage',
        'Active': 'Active',
        'QuantityType': 'QuantityType',
        'MaxOrderQuantityPermitted': 'MaxOrderQuantityPermitted',
        'KeyWords': 'KeyWords',
        'SEOTitle': 'SEOTitle',
        'MetaDescription': 'MetaDescription',
        'MobileSupported': 'MobileSupported',
        'ContentFile': 'ContentFile',
        'TicketTemplate': 'TicketTemplate',
        'StoreFront/Categories': 'Storefront/Categories'  # Note: different capitalization
    }
    
    print("\nMapping fields...")
    
    # Apply direct mappings
    for ustore_field, mdsf_field in field_mapping.items():
        if ustore_field in df_ustore.columns:
            df_mdsf[mdsf_field] = df_ustore[ustore_field]
        else:
            print(f"  WARNING: Column '{ustore_field}' not found in source CSV")
    
    # Preserve uStore helper columns for asset location during packaging
    helper_columns = ['uStore_ProductID', 'uStore_StoreID', 'uStore_StoreName']
    for col in helper_columns:
        if col in df_ustore.columns:
            df_mdsf[col] = df_ustore[col]
    
    print(f"  Preserved {len([c for c in helper_columns if c in df_ustore.columns])} helper columns")
    
    # Handle AutoThumbnail
    if use_auto_thumbnail:
        df_mdsf['Icon'] = 'AutoThumbnail'
        df_mdsf['DetailImage'] = 'AutoThumbnail'
        print("  Using AutoThumbnail for Icon and DetailImage")
    
    # Set default values for fields not in uStore
    print("  Setting default values for empty fields...")
    
    df_mdsf['TurnAroundTime'] = ''
    df_mdsf['TurnAroundTimeUnit'] = ''
    df_mdsf['Quantities'] = ''
    df_mdsf['AllowBuyerToEditMultipleQuantity'] = 'FALSE'
    df_mdsf['EnforceMaxQuantityPermittedInCart'] = 'FALSE'
    df_mdsf['OrderQuantitiesAllowSplitAcrossMultipleRecipients'] = 'FALSE'
    df_mdsf['DescriptionFooter'] = ''
    df_mdsf['ProductNotes'] = ''
    df_mdsf['UrlSlug'] = ''
    df_mdsf['BuyerDeliverableType'] = 'Print'
    df_mdsf['WeightValue'] = ''
    df_mdsf['WeightUnit'] = ''
    df_mdsf['WidthValue'] = ''
    df_mdsf['LengthValue'] = ''
    df_mdsf['HeightValue'] = ''
    df_mdsf['DimensionUnit'] = ''
    df_mdsf['MaxQuantityPerSubcontainer'] = ''
    df_mdsf['ShipItemSeparately'] = ''
    df_mdsf['ProductNameToCopySecuritySettings'] = ''
    df_mdsf['MISItemTemplate'] = ''
    df_mdsf['SmartCanvasTemplateName'] = ''
    df_mdsf['DynamicPreview'] = ''
    df_mdsf['AllowBuyerConfiguration'] = ''
    df_mdsf['StartDate'] = ''
    df_mdsf['EndDate'] = ''
    
    # FF-Inventory specific fields (empty for static documents)
    df_mdsf['PickLocation'] = ''
    df_mdsf['WareHouseName'] = ''
    df_mdsf['IsHighValueProduct'] = ''
    df_mdsf['HasUniqueSkid'] = ''
    df_mdsf['PickStrategy'] = ''
    df_mdsf['NotifyOnInventoryReceive'] = ''
    df_mdsf['CustomerRep'] = ''
    df_mdsf['SalesRep'] = ''
    df_mdsf['PhysicalCountInterval'] = ''
    df_mdsf['StorageType'] = ''
    df_mdsf['AllowBackOrder'] = ''
    df_mdsf['BackOrderRule'] = ''
    df_mdsf['BackOrderMaxQty'] = ''
    df_mdsf['ShowInventoryWhenBackOrderAllowed'] = ''
    df_mdsf['Threshold'] = ''
    df_mdsf['Emails'] = ''
    df_mdsf['Barcode'] = ''
    df_mdsf['EnableProductReturn'] = ''
    df_mdsf['BuyNowButtonDescription'] = ''
    df_mdsf['UseNewSmartCanvas'] = ''
    
    # Save to CSV
    try:
        df_mdsf.to_csv(output_file, index=False, encoding='utf-8')
    except Exception as e:
        print(f"ERROR: Failed to save CSV: {e}")
        return False
    
    # Validation
    print("\n" + "="*80)
    print("VALIDATION REPORT")
    print("="*80)
    
    errors = []
    warnings = []
    
    # Check required fields
    missing_name = df_mdsf['Name'].eq('').sum()
    missing_display = df_mdsf['DisplayName'].eq('').sum()
    missing_type = df_mdsf['Type'].eq('').sum()
    
    if missing_name > 0:
        errors.append(f"{missing_name} products missing Name (REQUIRED)")
    if missing_display > 0:
        errors.append(f"{missing_display} products missing DisplayName (REQUIRED)")
    if missing_type > 0:
        errors.append(f"{missing_type} products missing Type (REQUIRED)")
    
    # Check type-specific requirements
    doc_count = 0
    missing_templates = []
    missing_content = []
    
    for idx, row in df_mdsf.iterrows():
        product_type = str(row['Type'])
        product_name = str(row['Name'])
        
        if product_type == 'Document':
            doc_count += 1
            if not row['TicketTemplate']:
                missing_templates.append(product_name)
            if not row['ContentFile']:
                missing_content.append(product_name)
    
    if missing_templates:
        errors.append(f"{len(missing_templates)} Document products missing TicketTemplate")
    if missing_content:
        errors.append(f"{len(missing_content)} Document products missing ContentFile")
    
    # Check for empty descriptions
    empty_brief = df_mdsf['BriefDescription'].eq('').sum()
    empty_long = df_mdsf['LongDescription'].eq('').sum()
    
    if empty_brief > 0:
        warnings.append(f"{empty_brief} products have empty BriefDescription")
    if empty_long > 0:
        warnings.append(f"{empty_long} products have empty LongDescription")
    
    # Print results
    if errors:
        print("\nERRORS (Must fix before import):")
        for error in errors:
            print(f"  - {error}")
        
        # Show examples
        if missing_templates and len(missing_templates) <= 3:
            print("  Missing TicketTemplate:")
            for name in missing_templates:
                print(f"    - {name}")
        if missing_content and len(missing_content) <= 3:
            print("  Missing ContentFile:")
            for name in missing_content:
                print(f"    - {name}")
    else:
        print("\nNo critical errors found!")
    
    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    
    print(f"\nProduct Summary:")
    print(f"  Total products: {len(df_mdsf)}")
    print(f"  Static Documents: {doc_count}")
    print(f"  Columns: {len(df_mdsf.columns)}")
    
    print("\n" + "="*80)
    print("MAPPING COMPLETE")
    print("="*80)
    print(f"Output saved to: {output_file}")
    print("\nNext: Run packaging script to create final ZIP")
    print("="*80 + "\n")
    
    return True

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python fields_mapper.py <input_csv> <output_csv> [use_auto_thumbnail] [test_mode] [test_limit]")
        print("\nExample:")
        print("  python fields_mapper.py with_assets.csv mdsf_import.csv true false 1")
        print("\nArguments:")
        print("  use_auto_thumbnail: true/false (default: true)")
        print("  test_mode: true/false (default: false)")
        print("  test_limit: number (default: 1)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "mdsf_import.csv"
    
    # Parse boolean arguments
    use_auto_thumbnail = True
    if len(sys.argv) > 3:
        use_auto_thumbnail = sys.argv[3].lower() in ['true', '1', 'yes']
    
    test_mode = False
    if len(sys.argv) > 4:
        test_mode = sys.argv[4].lower() in ['true', '1', 'yes']
    
    test_limit = 1
    if len(sys.argv) > 5:
        try:
            test_limit = int(sys.argv[5])
        except ValueError:
            print(f"WARNING: Invalid test_limit '{sys.argv[5]}', using default: 1")
            test_limit = 1
    
    # Run the mapping
    success = map_to_mdsf(input_file, output_file, use_auto_thumbnail, test_mode, test_limit)
    
    if success:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()