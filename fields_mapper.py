import pandas as pd
import os

def map_ustore_to_mdsf(input_file, output_file, use_auto_thumbnail=False):
    """
    Maps uStore product data to MDSF CSV template format
    
    Args:
        input_file: Path to uStore CSV export
        output_file: Path for MDSF import CSV
        use_auto_thumbnail: If True, replaces Icon and DetailImage with "AutoThumbnail"
    """
    
    # Read the uStore CSV with proper handling for quotes and special characters
    df_ustore = pd.read_csv(input_file, encoding='utf-8', keep_default_na=False)
    
    # TESTING MODE: Process only first product
    print("TEST MODE: Processing only the first product")
    df_ustore = df_ustore.head(1)
    
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
    
    # Apply direct mappings
    for ustore_field, mdsf_field in field_mapping.items():
        if ustore_field in df_ustore.columns:
            df_mdsf[mdsf_field] = df_ustore[ustore_field]
    
    # IMPORTANT: Preserve uStore helper columns for asset location during packaging
    # These will be removed in the final packaging step
    helper_columns = ['uStore_ProductID', 'uStore_StoreID', 'uStore_StoreName']
    for col in helper_columns:
        if col in df_ustore.columns:
            df_mdsf[col] = df_ustore[col]
            print(f"Preserved helper column: {col}")
    
    # Optional: Use AutoThumbnail for static documents instead of image files
    if use_auto_thumbnail:
        df_mdsf['Icon'] = 'AutoThumbnail'
        df_mdsf['DetailImage'] = 'AutoThumbnail'
        print("Using AutoThumbnail for Icon and DetailImage")
    
    # Set default/empty values for fields not in uStore
    # These are optimized for Static Document products
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
    
    # FF-Inventory specific fields (not needed for static documents)
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
    
    # Save to CSV with proper encoding
    df_mdsf.to_csv(output_file, index=False, encoding='utf-8')
    
    print("=" * 60)
    print("MIGRATION COMPLETE!")
    print("=" * 60)
    print(f"Total products processed: {len(df_mdsf)}")
    print(f"Output saved to: {output_file}")
    print()
    
    # Validation report
    print("VALIDATION REPORT")
    print("-" * 60)
    
    # Check for required fields
    errors = []
    warnings = []
    
    missing_name = df_mdsf['Name'].eq('').sum()
    missing_display = df_mdsf['DisplayName'].eq('').sum()
    missing_type = df_mdsf['Type'].eq('').sum()
    
    if missing_name > 0:
        errors.append(f"ERROR: {missing_name} products missing Name (REQUIRED)")
    if missing_display > 0:
        errors.append(f"ERROR: {missing_display} products missing DisplayName (REQUIRED)")
    if missing_type > 0:
        errors.append(f"ERROR: {missing_type} products missing Type (REQUIRED)")
    
    # Check type-specific requirements for Static Documents
    doc_count = 0
    for idx, row in df_mdsf.iterrows():
        product_type = str(row['Type'])
        product_name = str(row['Name'])
        
        if product_type == 'Document':
            doc_count += 1
            if not row['TicketTemplate']:
                errors.append(f"ERROR: '{product_name}' Missing TicketTemplate (REQUIRED for Document type)")
            if not row['ContentFile']:
                errors.append(f"ERROR: '{product_name}' Missing ContentFile (REQUIRED for Document type)")
    
    # Check for empty descriptions
    empty_brief = df_mdsf['BriefDescription'].eq('').sum()
    empty_long = df_mdsf['LongDescription'].eq('').sum()
    
    if empty_brief > 0:
        warnings.append(f"WARNING: {empty_brief} products have empty BriefDescription")
    if empty_long > 0:
        warnings.append(f"WARNING: {empty_long} products have empty LongDescription")
    
    # Print results
    if errors:
        print("\nERRORS (Must fix before import):")
        for error in errors:
            print(f"   {error}")
    else:
        print("\nNo critical errors found!")
    
    if warnings:
        print("\nWARNINGS (Recommended to review):")
        for warning in warnings:
            print(f"   {warning}")
    
    print(f"\nProduct Summary:")
    print(f"   - {doc_count} Static Document products")
    print(f"   - {len(df_mdsf)} total products")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Review the output CSV file")
    print("2. IMPORTANT: The CSV contains helper columns (uStore_ProductID, etc.)")
    print("   These are needed for the packaging script to locate assets")
    print("   They will be automatically removed when creating the final ZIP")
    print("3. Run the packaging script to:")
    print("   - Gather all asset files using uStore IDs")
    print("   - Remove helper columns")
    print("   - Create final ZIP for MDSF import")
    print("=" * 60)
    
    # Create asset checklist
    print("\nASSET CHECKLIST:")
    print("-" * 60)
    
    if not use_auto_thumbnail:
        # Collect unique image files
        icon_files = set()
        detail_files = set()
        for val in df_mdsf['Icon']:
            if val and val != 'AutoThumbnail':
                # Handle comma-separated values
                icon_files.update([f.strip() for f in str(val).split(',')])
        for val in df_mdsf['DetailImage']:
            if val and val != 'AutoThumbnail':
                detail_files.update([f.strip() for f in str(val).split(',')])
        
        print(f"\nIcon Images ({len(icon_files)} unique files):")
        for f in sorted(icon_files):
            if f:
                print(f"   - {f}")
        
        print(f"\nDetail Images ({len(detail_files)} unique files):")
        for f in sorted(detail_files):
            if f:
                print(f"   - {f}")
    
    # Collect unique content files
    content_files = set()
    for val in df_mdsf['ContentFile']:
        if val:
            content_files.update([f.strip() for f in str(val).split(',')])
    
    print(f"\nContent Files ({len(content_files)} unique files):")
    for f in sorted(content_files):
        if f:
            print(f"   - {f}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Configuration
    input_file = "raw_data.csv"   # Your uStore export file
    output_file = "mdsf_import.csv"    # Output file for MDSF
    
    # Set to True to use AutoThumbnail instead of image files
    # This lets MDSF generate thumbnails from your PDFs automatically
    use_auto_thumbnail = True
    
    # Run the migration
    map_ustore_to_mdsf(input_file, output_file, use_auto_thumbnail)