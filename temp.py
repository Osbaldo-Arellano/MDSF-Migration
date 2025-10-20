import csv

source_file = "AFC_SalesAids.csv"
template_file = "Template.csv"
output_file = "products_mdsf_ready.csv"

# Load template header
with open(template_file, newline='', encoding='utf-8') as tfile:
    template_header = next(csv.reader(tfile))

# Load source CSV
with open(source_file, newline='', encoding='utf-8') as sfile:
    source_reader = csv.DictReader(sfile)
    source_data = list(source_reader)

field_map = {
    "Name": "Name",
    "DisplayName": "DisplayName",
    "Type": "Type",
    "ProductId": "SKU/ProductId",
    "BriefDescription": "BriefDescription",
    "Icon": "Icon",
    "LongDescription": "LongDescription",
    "DetailImage": "DetailImage",
    "Active": "Active",
    "TicketTemplate": "TicketTemplate",
    "ContentFile": "ContentFile",
    "KeyWords": "KeyWords",
    "SEOTitle": "SEOTitle",
    "MetaDescription": "MetaDescription",
    "QuantityType": "QuantityType",
    "MaxOrderQuantityPermitted": "",
    "MobileSupported": "MobileSupported",
    "Storefront/Categories": "StoreFront/Categories",
}

efi_defaults = {
    "TurnAroundTime": "2",
    "TurnAroundTimeUnit": "Day",
    "QuantityType": "Any",
    "MaxOrderQuantityPermitted": "1000",
    "Active": "TRUE",
    "MobileSupported": "TRUE",
    "BuyerDeliverableType": "PrintAndDownload",
    "WeightValue": "0",
    "WeightUnit": "lb",
    "WidthValue": "0",
    "LengthValue": "0",
    "HeightValue": "0",
    "DimensionUnit": "Inches",
    "AllowBuyerConfiguration": "FALSE",
    "AllowBackOrder": "FALSE",
    "BackOrderRule": "None",
    "EnableProductReturn": "FALSE",
    "UseNewSmartCanvas": "",
    "DynamicPreview": "FALSE",
}

# Boolean fields in EFI template
boolean_fields = {
    "Active",
    "AllowBuyerToEditMultipleQuantity",
    "EnforceMaxQuantityPermittedInCart",
    "OrderQuantitiesAllowSplitAcrossMultipleRecipients",
    "MobileSupported",
    "ShipItemSeparately",
    "AllowBuyerConfiguration",
    "IsHighValueProduct",
    "HasUniqueSkid",
    "NotifyOnInventoryReceive",
    "AllowBackOrder",
    "ShowInventoryWhenBackOrderAllowed",
    "EnableProductReturn",
    "DynamicPreview",
}

output_rows = []
for record in source_data:
    new_row = {}
    for field in template_header:
        if field in field_map and field_map[field] in record:
            value = record[field_map[field]].strip()
        elif field in efi_defaults:
            value = efi_defaults[field]
        else:
            value = ""

        # Normalize Boolean fields to TRUE/FALSE
        if field in boolean_fields:
            if str(value).strip().upper() == "TRUE":
                value = "TRUE"
            else:
                value = "FALSE"

        new_row[field] = value
    output_rows.append(new_row)

# Write UTF-8 CSV (no BOM)
with open(output_file, "w", newline='', encoding="utf-8") as ofile:
    writer = csv.DictWriter(ofile, fieldnames=template_header)
    writer.writeheader()
    writer.writerows(output_rows)

print(f"✅ Exported {len(output_rows)} product(s) → {output_file}")
