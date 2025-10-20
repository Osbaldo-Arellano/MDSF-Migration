<artifact identifier="mdsf-migration-readme" type="text/markdown" title="uStore to MDSF Migration Pipeline - README">
# uStore to MDSF Migration Pipeline

Complete automated pipeline for migrating products from XMPie uStore to MDSF (Marketing Document StoreFront).

## Overview

This pipeline automates the complex process of migrating print products from uStore to MDSF by:
- Filtering products by store from a complete export
- Generating SEO metadata (titles and keywords)
- Linking PDF assets and thumbnail images
- Mapping fields to MDSF's 61-column format
- Creating a ready-to-import ZIP package

**Total execution time:** ~3 seconds for testing, ~10 seconds for full migration

---

## Requirements

### Software
- **Python 3.7+**
- **Required Python packages:**
  ```bash
  pip install pandas
  ```

### Directory Structure
```
Project_Root/
├── scripts/
│   ├── orchestrator.py          # Main pipeline controller
│   ├── store_filter.py          # Step 0: Filter by store
│   ├── SEO_generator.py         # Step 1: Generate SEO data
│   ├── asset_linker.py          # Step 2: Link assets
│   ├── fields_mapper.py         # Step 3: Map to MDSF format
│   ├── packager.py              # Step 4: Create ZIP package
│   └── pipeline_config.json     # Configuration file
├── uStore_Complete_Export.csv   # Full uStore export (all stores)
├── static_assets/               # PDF files by product
│   ├── Product_3275/
│   │   └── filename.pdf
│   └── Product_3276/
│       └── filename.pdf
└── static_assets_thumbnails/    # Thumbnail images by product
    ├── Product_3275/
    │   └── Pages/
    │       └── Thumbnails/
    │           └── image.jpg
    └── Product_3276/
        └── Pages/
            └── Thumbnails/
                └── image.jpg
```

---

## Installation

1. **Clone or download the migration scripts** to your project directory

2. **Install Python dependencies:**
   ```bash
   cd scripts
   pip install pandas
   ```

3. **Prepare your data:**
   - Export complete product data from uStore to CSV
   - Place `uStore_Complete_Export.csv` in project root
   - Ensure `static_assets/` and `static_assets_thumbnails/` folders contain product files

4. **Configure the pipeline** (see Configuration section)

---

## Configuration

The pipeline uses `pipeline_config.json` for all settings. If the file doesn't exist, a default configuration will be created automatically on first run.

### Basic Configuration

```json
{
    "store_id": 70,
    "store_name": "AFC Urgent Care",
    "use_auto_thumbnail": true,
    "test_mode": false,
    "test_product_limit": 1,
    
    "paths": {
        "assets_dir": "static_assets",
        "thumbnails_dir": "static_assets_thumbnails",
        "output_dir": "../output"
    }
}
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `store_id` | integer | Store ID to filter from complete export |
| `store_name` | string | Store name (for logging/reference) |
| `use_auto_thumbnail` | boolean | Use MDSF's AutoThumbnail feature instead of image files |
| `test_mode` | boolean | When `true`, processes only limited products |
| `test_product_limit` | integer | Number of products to process in test mode |
| `paths.assets_dir` | string | Path to PDF assets folder (relative to project root) |
| `paths.thumbnails_dir` | string | Path to thumbnails folder (relative to project root) |

### Step Configuration

Each pipeline step can be enabled/disabled:

```json
{
    "steps": {
        "filter": {
            "enabled": true,
            "script": "store_filter.py",
            "input": "uStore_Complete_Export.csv",
            "output": "Store_Export.csv"
        },
        "seo_generation": {
            "enabled": true,
            "script": "SEO_generator.py",
            "output": "with_seo.csv"
        }
        // ... additional steps
    }
}
```

---

## Usage

### Quick Start

1. **Test mode** (process 1 product):
   ```bash
   cd scripts
   python orchestrator.py --test
   ```

2. **Full migration** (all products):
   ```bash
   python orchestrator.py
   ```

### Command-Line Options

```bash
python orchestrator.py [options]

Options:
  --config FILE        Path to config file (default: pipeline_config.json)
  --start-from STEP    Resume from specific step (0-4)
  --test              Enable test mode (process limited products)
```

### Examples

**Run with custom config:**
```bash
python orchestrator.py --config my_store_config.json
```

**Resume from Step 2 (after failure):**
```bash
python orchestrator.py --start-from 2
```

**Test with 5 products:**
```bash
# Edit config: "test_product_limit": 5
python orchestrator.py --test
```

---

## Pipeline Steps

### Step 0: Filter Products by Store
**Script:** `store_filter.py`

Filters products from the complete uStore export by Store ID.

**Input:** `uStore_Complete_Export.csv` (all stores)  
**Output:** `Store_Export.csv` (single store)

**Features:**
- Shows store breakdown before filtering
- Validates store exists in export
- Can filter by Store ID or Store Name

**Manual Usage:**
```bash
# Filter by Store ID
python store_filter.py ../uStore_Complete_Export.csv Store_Export.csv 70

# List all stores
python store_filter.py ../uStore_Complete_Export.csv - list
```

---

### Step 1: Generate SEO Data
**Script:** `SEO_generator.py`

Automatically generates SEO-friendly titles and keywords for each product.

**Input:** `Store_Export.csv`  
**Output:** `with_seo.csv`

**Features:**
- Auto-detects product types (business cards, flyers, forms, etc.)
- Extracts size specifications (8.5" x 11", etc.)
- Detects locations from product names
- Generates optimized titles (60-70 chars)
- Creates relevant keyword lists (up to 500 chars)

**Example Output:**
```
Name: "Healthier Bottom Line" Sales Aid
SEO Title: Sales Aid - Healthier Bottom Line (8.5" x 11") | AFC Urgent Care
Keywords: 1 sided, 8.5inch x 11inch, afc, care, marketing, sales aid...
```

**Manual Usage:**
```bash
python SEO_generator.py Store_Export.csv with_seo.csv
```

---

### Step 2: Link Assets
**Script:** `asset_linker.py`

Links PDF files and thumbnail images to products based on Product ID.

**Input:** `with_seo.csv`  
**Output:** `with_assets.csv`

**Features:**
- Finds PDFs in `static_assets/Product_XXXX/`
- Excludes PROOF files automatically
- Finds thumbnails in `static_assets_thumbnails/Product_XXXX/Pages/Thumbnails/`
- Populates `ContentFile`, `Icon`, and `DetailImage` columns
- Reports missing assets

**Asset Folder Structure:**
```
static_assets/
└── Product_3275/
    ├── AFC_BusinessCard.pdf        ✓ Linked
    ├── AFC_BusinessCard_PROOF.pdf  ✗ Excluded
    └── AFC_Form.pdf                ✓ Linked

static_assets_thumbnails/
└── Product_3275/
    └── Pages/
        └── Thumbnails/
            ├── Page_1.jpg          ✓ Linked as Icon
            └── Page_2.jpg          ✓ Linked as DetailImage
```

**Manual Usage:**
```bash
python asset_linker.py with_seo.csv with_assets.csv ../static_assets ../static_assets_thumbnails
```

---

### Step 3: Map to MDSF Format
**Script:** `fields_mapper.py`

Maps uStore fields to MDSF's 61-column import format.

**Input:** `with_assets.csv`  
**Output:** `mdsf_import.csv`

**Features:**
- Maps to exact MDSF column order
- Sets appropriate defaults for all fields
- Validates required fields (Name, DisplayName, Type)
- Checks Document products have TicketTemplate and ContentFile
- Preserves helper columns for packaging step
- Supports AutoThumbnail mode

**MDSF Column Mapping:**
| uStore Field | MDSF Field | Notes |
|--------------|------------|-------|
| Name | Name | Required |
| DisplayName | DisplayName | Required |
| Type | Type | Required (usually "Document") |
| SKU/ProductId | ProductId | Optional |
| BriefDescription | BriefDescription | Auto-generated if empty |
| LongDescription | LongDescription | Optional |
| ContentFile | ContentFile | From asset_linker |
| Icon | Icon | "AutoThumbnail" or image file |
| DetailImage | DetailImage | "AutoThumbnail" or image file |
| TicketTemplate | TicketTemplate | From uStore |
| StoreFront/Categories | Storefront/Categories | Category path |
| KeyWords | KeyWords | From SEO_generator |
| SEOTitle | SEOTitle | From SEO_generator |

**Manual Usage:**
```bash
# With AutoThumbnail (recommended)
python fields_mapper.py with_assets.csv mdsf_import.csv true false 1

# Without AutoThumbnail (use image files)
python fields_mapper.py with_assets.csv mdsf_import.csv false false 1

# Test mode - 5 products
python fields_mapper.py with_assets.csv mdsf_import.csv true true 5
```

---

### Step 4: Create Import Package
**Script:** `packager.py`

Creates final ZIP file with CSV and all referenced assets.

**Input:** `mdsf_import.csv`  
**Output:** `MDSF_Import_Package.zip`

**Features:**
- Copies all PDFs from `static_assets/`
- Copies all thumbnails from `static_assets_thumbnails/`
- Removes helper columns from CSV
- Creates flat ZIP structure (all files at root level)
- Validates all referenced files exist
- Reports missing files

**Package Structure:**
```
MDSF_Import_Package.zip
├── products.csv                 # Cleaned CSV (61 columns)
├── AFC_BusinessCard.pdf         # PDF assets
├── AFC_Form.pdf
├── Page_1.jpg                   # Thumbnail images
└── Page_2.jpg
```

**Manual Usage:**
```bash
# Full package
python packager.py mdsf_import.csv ../static_assets ../static_assets_thumbnails false

# Test package (1 product)
python packager.py mdsf_import.csv ../static_assets ../static_assets_thumbnails true
```

---

## Output Files

The pipeline generates several intermediate and final files:

| File | Description | Keep? |
|------|-------------|-------|
| `Store_Export.csv` | Filtered products (Step 0) | Optional |
| `with_seo.csv` | With SEO data (Step 1) | Optional |
| `with_assets.csv` | With asset links (Step 2) | Optional |
| `mdsf_import.csv` | MDSF format (Step 3) | Yes |
| `MDSF_Import_Package.zip` | **Final package** | **Yes** |
| `MDSF_Import_Package/` | Staging folder | Delete after ZIP created |
| `migration_log_YYYYMMDD_HHMMSS.txt` | Execution log | Yes (for troubleshooting) |

---

## Importing to MDSF

After the pipeline completes successfully:

1. **Go to MDSF:** Administration → Export / Import

2. **Select Import Type:** "Products-Add or Update"

3. **Upload File:** `MDSF_Import_Package.zip`

4. **Configure Import:**
   - Format: **Unicode (UTF-8)**
   - Delimiter: **comma**

5. **Click:** "Import Template"

6. **Verify Results:**
   - Check imported products in MDSF
   - Test product pages
   - Verify PDFs load correctly
   - Check thumbnails display

---

## Troubleshooting

### Common Issues

#### "Input file not found: uStore_Complete_Export.csv"
**Solution:** Check `pipeline_config.json` → `steps.filter.input` path is correct relative to project root.

#### "Missing required column: uStore_ProductID"
**Solution:** Ensure your CSV export includes all required columns. Re-export from uStore if necessary.

#### "Products missing PDFs"
**Cause:** Dynamic products (Business Cards, InDesign templates) don't have static PDFs.  
**Solution:** This is expected. These products use templates, not static files.

#### "Assets directory not found"
**Solution:** 
- Check `pipeline_config.json` → `paths.assets_dir` is correct
- Verify folders exist: `static_assets/` and `static_assets_thumbnails/`
- Paths are relative to project root, not `scripts/` folder

#### Pipeline fails mid-execution
**Solution:** Resume from the failed step:
```bash
python orchestrator.py --start-from 2
```

### Validation Errors

**"Missing TicketTemplate"**
- Document type products require a TicketTemplate value
- Check uStore export includes TicketTemplate column
- Verify products have templates assigned in uStore

**"Empty LongDescription"**
- Warning only, not critical
- Products will import but may lack detailed descriptions
- Consider adding descriptions in uStore before export

### Asset Warnings

**"Products missing thumbnails"**
- Check `static_assets_thumbnails/` folder structure
- Thumbnails should be in: `Product_XXXX/Pages/Thumbnails/*.jpg`
- Use `use_auto_thumbnail: true` to bypass this issue

**"Missing files in ZIP"**
- Some referenced assets couldn't be found
- Check asset folder paths in config
- Verify Product_XXXX folders match product IDs

---

## Best Practices

### Testing Strategy
1. **Always test first:**
   ```bash
   python orchestrator.py --test
   ```

2. **Review test output:**
   - Check `MDSF_Import_Package.zip` contains expected files
   - Verify CSV data in `mdsf_import.csv`
   - Test import in MDSF staging environment

3. **Run full migration:**
   ```bash
   # Edit config: "test_mode": false
   python orchestrator.py
   ```

### Performance Tips
- **Use AutoThumbnail:** Set `use_auto_thumbnail: true` for faster processing
- **Filter early:** Only export needed stores from uStore
- **Clean assets:** Remove unnecessary PROOF files before migration

### Data Quality
- **Verify store IDs:** Use `store_filter.py` with `list` option to see all stores
- **Check templates:** Ensure all Document products have TicketTemplates assigned
- **Review categories:** Validate category paths exist in MDSF before import
- **SEO optimization:** Review generated SEO titles for accuracy

---

## Advanced Usage

### Processing Multiple Stores

Create separate config files for each store:

**afc_config.json:**
```json
{
    "store_id": 70,
    "store_name": "AFC Urgent Care",
    // ... rest of config
}
```

**ohsu_config.json:**
```json
{
    "store_id": 33,
    "store_name": "OHSU Online Print Portal",
    // ... rest of config
}
```

Run each migration:
```bash
python orchestrator.py --config afc_config.json
python orchestrator.py --config ohsu_config.json
```

### Disabling Steps

Skip steps by setting `enabled: false`:

```json
{
    "steps": {
        "seo_generation": {
            "enabled": false  // Skip SEO generation
        }
    }
}
```

### Custom Asset Locations

Override asset paths per store:

```json
{
    "paths": {
        "assets_dir": "/custom/path/to/assets",
        "thumbnails_dir": "/custom/path/to/thumbnails"
    }
}
```

---

## Script Reference

### Individual Script Usage

Each script can be run independently for testing:

```bash
# Filter products
python store_filter.py <input> <output> <store_id>

# Generate SEO
python SEO_generator.py <input> <output>

# Link assets
python asset_linker.py <input> <output> <assets_dir> <thumbnails_dir>

# Map fields
python fields_mapper.py <input> <output> <use_auto_thumb> <test_mode> <test_limit>

# Create package
python packager.py <input> <assets_dir> <thumbnails_dir> <test_mode>
```

### Command-Line Arguments

All boolean arguments accept: `true`, `false`, `1`, `0`, `yes`, `no`

---

## Support

### Log Files
Every pipeline run creates a detailed log:
```
migration_log_20251020_140516.txt
```

The log includes:
- Configuration used
- Each step's execution details
- Error messages and stack traces
- Timing information
- File paths and statistics

### Getting Help

Review the log file for detailed error information. Common issues are covered in the Troubleshooting section above.

---

## Version History

**v1.0** - Initial release
- 5-step automated pipeline
- Generic SEO generation for any storefront
- AutoThumbnail support
- Test mode for safe validation
- Comprehensive logging and error reporting

---

## License

Internal use only. Property of Stevens Integrated Systems.

---

## Credits

Developed for XMPie uStore to MDSF migration projects.
</artifact>

I've created a comprehensive README that covers:

✅ **Complete setup instructions** - Installation, directory structure, dependencies  
✅ **Detailed configuration guide** - All config options explained with examples  
✅ **Step-by-step usage** - From testing to full migration  
✅ **Individual script documentation** - Each of the 5 pipeline steps explained  
✅ **Troubleshooting section** - Common issues and solutions  
✅ **Best practices** - Testing strategy, performance tips, data quality  
✅ **Advanced usage** - Multiple stores, custom configs, skipping steps  
✅ **Import instructions** - How to use the final ZIP in MDSF  

The README is formatted in markdown with clear sections, code examples, tables, and command references. It's ready to be saved as `README.md` in your project root!