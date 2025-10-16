# --- CONFIGURE THESE ---
$Server   = "xxxxxx"
$Database = "xxxxxx"
$User     = "xxxxxx"
$Password = "xxxxxx"

# Query only from Product table
$Query = @"
-- FINAL FIXED: Complete uStore to MDSF export query (no duplicates)
SELECT 
    -- REQUIRED FIELDS
    LEFT(pc.Name, 50) as Name,
    LEFT(pc.Name, 2000) as DisplayName,
    'Document' as Type,
    ISNULL(prof_pc.Name, '') as TicketTemplate,
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
    
    -- HELPER FIELDS
    p.ProductID as uStore_ProductID,
    p.StoreID as uStore_StoreID,
    sc.Name as uStore_StoreName

FROM Product p
    LEFT JOIN Product_Culture pc ON p.ProductID = pc.ProductID
    LEFT JOIN (
        -- Get only the first profile for each product to avoid duplicates
        SELECT ProductID, MIN(ProfileID) as ProfileID
        FROM ProductProfileDependency
        GROUP BY ProductID
    ) ppd ON p.ProductID = ppd.ProductID
    LEFT JOIN Product prof ON ppd.ProfileID = prof.ProductID AND prof.IsProfile = 1
    LEFT JOIN Product_Culture prof_pc ON prof.ProductID = prof_pc.ProductID
    LEFT JOIN Store s ON p.StoreID = s.StoreID
    LEFT JOIN Store_Culture sc ON s.StoreID = sc.StoreID

WHERE 
    p.StatusID = 1
    AND p.IsProfile = 0
    AND p.StoreID IS NOT NULL
    -- Uncomment to filter by store:
    --AND p.StoreID = 70  -- AFC Urgent Care

GROUP BY 
    p.ProductID, p.StoreID, p.ExternalId, p.CatalogNo, p.StatusID,
    pc.Name, pc.ShortDescription, pc.Description, pc.KeyWords,
    prof_pc.Name, sc.Name

ORDER BY p.StoreID, p.ProductID;
"@

# --- DO NOT EDIT BELOW ---
$ConnStr = "Server=$Server;Database=$Database;User ID=$User;Password=$Password;Trusted_Connection=False;"
$Conn = New-Object System.Data.SqlClient.SqlConnection
$Conn.ConnectionString = $ConnStr
$Conn.Open()

$Cmd = $Conn.CreateCommand()
$Cmd.CommandText = $Query
$Reader = $Cmd.ExecuteReader()

$table = New-Object System.Data.DataTable
$table.Load($Reader)
$Conn.Close()

# Show results in console
$table | Format-Table -AutoSize

# Export to CSV
$table | Export-Csv "C:\temp\Final-Sample-AFC.csv" -NoTypeInformation
