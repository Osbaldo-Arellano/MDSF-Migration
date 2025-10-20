 # =============================================================================
# uStore to MDSF - Complete Product Export
# =============================================================================
# This script exports all necessary product data from uStore in one query
# Output: Single CSV with all fields needed for MDSF migration
# =============================================================================

# --- CONFIGURE THESE ---
$Server   = "SIS-SQL\XMPIE"
$Database = "uStore"
$User     = "XMPieUStore"
$Password = "uStore1"
$OutputPath = "C:\temp\uStore_Complete_Export.csv"

# Optional: Filter by specific store (uncomment and set StoreID)
$FilterStoreID = $null  # Set to 70 for AFC Urgent Care only, or leave null for all stores

# --- MAIN QUERY ---
$Query = @"
-- Complete uStore to MDSF export query with Ticket Templates
SELECT 
    -- REQUIRED FIELDS
    LEFT(pc.Name, 50) as Name,
    LEFT(pc.Name, 2000) as DisplayName,
    'Document' as Type,
    
    -- TICKET TEMPLATE (from pricing dials)
    ISNULL(
        STUFF((
            SELECT DISTINCT ',' + dc.FriendlyName
            FROM Dial d
            INNER JOIN Dial_Culture dc ON d.DialID = dc.DialID
            WHERE d.ProductId = p.ProductID
              AND d.UsedInPricingCalculation = 1
              AND dc.FriendlyName IS NOT NULL
            FOR XML PATH(''), TYPE
        ).value('.', 'NVARCHAR(MAX)'), 1, 1, ''),
        ''
    ) as TicketTemplate,
    
    '' as ContentFile,
    
    -- STRONGLY SUGGESTED FIELDS
    COALESCE(p.ExternalId, p.CatalogNo, CAST(p.ProductID AS VARCHAR)) as [SKU/ProductId],
    LEFT(ISNULL(pc.ShortDescription, ''), 2000) as BriefDescription,
    LEFT(ISNULL(pc.Description, ''), 4000) as LongDescription,
    CASE WHEN p.StatusID = 1 THEN 'TRUE' ELSE 'FALSE' END as Active,
    
    '' as Icon,
    '' as DetailImage,
    
    LEFT(ISNULL(pc.KeyWords, ''), 500) as KeyWords,
    '' as SEOTitle,
    LEFT(ISNULL(pc.ShortDescription, ''), 160) as MetaDescription,
    
    'Any' as QuantityType,
    '' as MaxOrderQuantityPermitted,
    'TRUE' as MobileSupported,
    
    -- StoreFront/Categories - combine store name and category names (comma-separated)
    ISNULL(sc.Name, '') + 
    CASE 
        WHEN EXISTS (SELECT 1 FROM ProductGroupMembership pgm3 WHERE pgm3.ProductID = p.ProductID)
        THEN '/' + STUFF((
            SELECT ',' + pgc2.Name
            FROM ProductGroupMembership pgm2
            JOIN ProductGroup pg2 ON pgm2.ProductGroupID = pg2.ProductGroupID
            JOIN ProductGroup_Culture pgc2 ON pg2.ProductGroupID = pgc2.ProductGroupID
            WHERE pgm2.ProductID = p.ProductID
            ORDER BY pgm2.DisplayOrder
            FOR XML PATH(''), TYPE
        ).value('.', 'NVARCHAR(MAX)'), 1, 1, '')
        ELSE ''
    END as [StoreFront/Categories],
    
    -- HELPER FIELDS (for asset location during migration)
    p.ProductID as uStore_ProductID,
    p.StoreID as uStore_StoreID,
    sc.Name as uStore_StoreName

FROM Product p
    LEFT JOIN Product_Culture pc ON p.ProductID = pc.ProductID
    LEFT JOIN Store s ON p.StoreID = s.StoreID
    LEFT JOIN Store_Culture sc ON s.StoreID = sc.StoreID

WHERE 
    p.StatusID = 1  -- Active products only
    AND p.IsProfile = 0  -- Exclude profile products
    AND p.StoreID IS NOT NULL  -- Must be assigned to a store
    $(if ($FilterStoreID) { "AND p.StoreID = $FilterStoreID" })

GROUP BY 
    p.ProductID, p.StoreID, p.ExternalId, p.CatalogNo, p.StatusID,
    pc.Name, pc.ShortDescription, pc.Description, pc.KeyWords,
    sc.Name

ORDER BY p.StoreID, p.ProductID;
"@

# --- EXECUTE QUERY ---
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "uStore Product Export" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Server: $Server"
Write-Host "  Database: $Database"
Write-Host "  Output: $OutputPath"
if ($FilterStoreID) {
    Write-Host "  Filter: Store ID = $FilterStoreID" -ForegroundColor Green
} else {
    Write-Host "  Filter: All Stores" -ForegroundColor Green
}
Write-Host ""
Write-Host "Connecting to database..." -ForegroundColor Yellow

try {
    $ConnStr = "Server=$Server;Database=$Database;User ID=$User;Password=$Password;Trusted_Connection=False;"
    $Conn = New-Object System.Data.SqlClient.SqlConnection
    $Conn.ConnectionString = $ConnStr
    $Conn.Open()
    
    Write-Host "Executing query..." -ForegroundColor Yellow
    $Cmd = $Conn.CreateCommand()
    $Cmd.CommandText = $Query
    $Reader = $Cmd.ExecuteReader()
    
    $table = New-Object System.Data.DataTable
    $table.Load($Reader)
    $Conn.Close()
    
    Write-Host "Query completed successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Display summary
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "Export Summary" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "Total Products: $($table.Rows.Count)" -ForegroundColor Green
    Write-Host "Columns: $($table.Columns.Count)" -ForegroundColor Green
    Write-Host ""
    
    # Show breakdown by store
    Write-Host "Products by Store:" -ForegroundColor Yellow
    $table | Group-Object uStore_StoreName | ForEach-Object {
        Write-Host "  $($_.Name): $($_.Count) products"
    }
    Write-Host ""
    
    # Check for missing ticket templates
    $missingTemplates = $table | Where-Object { [string]::IsNullOrWhiteSpace($_.TicketTemplate) }
    if ($missingTemplates.Count -gt 0) {
        Write-Host "WARNING: $($missingTemplates.Count) products without Ticket Templates:" -ForegroundColor Red
        $missingTemplates | Select-Object -First 5 Name, uStore_ProductID | Format-Table -AutoSize
        if ($missingTemplates.Count -gt 5) {
            Write-Host "  ... and $($missingTemplates.Count - 5) more" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    # Show sample of data
    Write-Host "Sample Data (first 3 rows):" -ForegroundColor Yellow
    $table | Select-Object -First 3 Name, TicketTemplate, [StoreFront/Categories], uStore_ProductID | Format-Table -AutoSize
    Write-Host ""
    
    # Export to CSV
    Write-Host "Exporting to CSV..." -ForegroundColor Yellow
    $table | Export-Csv $OutputPath -NoTypeInformation -Encoding UTF8
    
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "CSV saved to: $OutputPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Review the exported CSV"
    Write-Host "2. Verify Ticket Templates are populated"
    Write-Host "3. Run the migration script: migration_script.py"
    Write-Host "4. Run the packaging script: package_script.py"
    Write-Host "5. Import to MDSF"
    Write-Host ""
    
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "- Check server name and connection"
    Write-Host "- Verify credentials"
    Write-Host "- Ensure database name is correct"
    exit 1
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 
