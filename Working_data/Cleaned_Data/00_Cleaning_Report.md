# Data Cleaning Report
*Generated: 2026-02-11 12:56:59*

## Summary

| File | Input Rows | Output Rows | Rows Removed | % Removed |
|------|------------|-------------|--------------|-----------|
| Cleaned_01_Assessor_-_Parcel_Sales_2023_2025.csv | 216,550 | 214,571 | 1,979 | 0.9% |
| Cleaned_02_Assessor_-_Parcel_Addresses_20260205.csv | 5,592,069 | 5,592,069 | 0 | 0.0% |
| Cleaned_03_Assessor_-_Assessed_Values_2023_2025.csv | 5,592,069 | 5,592,069 | 0 | 0.0% |
| Cleaned_04_Assessor_-_Single_and_Multi-Family_Improvement_Characteristics_20260205_websiteDL.csv | 3,306,906 | 3,289,856 | 17,050 | 0.5% |
| **TOTAL** | **14,707,594** | **14,688,565** | **19,029** | **0.1%** |

## Overall Statistics

- **Files Processed:** 4
- **Total Input Rows:** 14,707,594
- **Total Output Rows:** 14,688,565
- **Total Rows Removed:** 19,029
- **Data Reduction:** 0.1%

---

## Detailed Actions by File

### Cleaned_01_Assessor_-_Parcel_Sales_2023_2025.csv

**Input:** 216,550 rows  
**Output:** 214,571 rows  
**Removed:** 1,979 rows (0.9%)

#### 🗑️ Deleted Columns (5)

- `is_mydec_date`
- `sale_filter_deed_type`
- `sale_filter_less_than_10k`
- `sale_filter_same_sale_within_365`
- `sale_type`

#### 🧹 Cleaned Columns (10)

**`class`** (int)
  - Parsing errors: `median`
  - Outliers (±4.0σ): `median`

**`neighborhood_code`** (int)

**`num_parcels_sale`** (int)
  - Outliers (±3.0σ): `cap`

**`pin`** (int)

**`row_id`** (int)

**`sale_date`** (date)
  - Date range: `2023-01-01` to `2025-12-19`

**`sale_document_num`** (int)

**`sale_price`** (int)
  - Outliers (±2.0σ): `remove`

**`township_code`** (int)

**`year`** (int)

#### 📋 Copied As-Is (5)

`is_multisale`, `mydec_deed_type`, `sale_buyer_name`, `sale_deed_type`, `sale_seller_name`


---

### Cleaned_02_Assessor_-_Parcel_Addresses_20260205.csv

**Input:** 5,592,069 rows  
**Output:** 5,592,069 rows  
**Removed:** 0 rows (0.0%)

#### 🗑️ Deleted Columns (2)

- `mailing_state`
- `property_state`

#### 🧹 Cleaned Columns (6)

**`mailing_zip`** (int)
  - Missing: `median`

**`pin`** (int)

**`pin10`** (int)

**`property_zip`** (int)
  - Missing: `median`

**`row_id`** (int)

**`tax_year`** (int)

#### 📋 Copied As-Is (5)

`mailing_address`, `mailing_city`, `mailing_name`, `property_address`, `property_city`


---

### Cleaned_03_Assessor_-_Assessed_Values_2023_2025.csv

**Input:** 5,592,069 rows  
**Output:** 5,592,069 rows  
**Removed:** 0 rows (0.0%)

#### 🗑️ Deleted Columns (3)

- `board_hie`
- `certified_hie`
- `mailed_hie`

#### 🧹 Cleaned Columns (15)

**`board_bldg`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `mean`

**`board_land`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `mean`

**`board_tot`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `mean`

**`certified_bldg`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `mean`

**`certified_land`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `mean`

**`certified_tot`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `mean`

**`class`** (int)
  - Missing: `median`

**`mailed_bldg`** (int)
  - Outliers (±3.0σ): `cap`

**`mailed_land`** (int)
  - Outliers (±3.0σ): `cap`

**`mailed_tot`** (int)
  - Outliers (±3.0σ): `cap`

**`neighborhood_code`** (int)

**`pin`** (int)

**`row_id`** (int)

**`tax_year`** (int)

**`township_code`** (int)

#### 📋 Copied As-Is (1)

`township_name`


---

### Cleaned_04_Assessor_-_Single_and_Multi-Family_Improvement_Characteristics_20260205_websiteDL.csv

**Input:** 3,306,906 rows  
**Output:** 3,289,856 rows  
**Removed:** 17,050 rows (0.5%)

#### 🗑️ Deleted Columns (16)

- `card_num`
- `card_proration_rate`
- `cdu`
- `construction_quality`
- `design_plan`
- `num_commercial_units`
- `pin_is_multicard`
- `pin_is_multiland`
- `pin_num_cards`
- `pin_num_landlines`
- `pin_proration_rate`
- `porch`
- `proration_key_pin`
- `renovation`
- `repair_condition`
- `site_desirability`

#### 🧹 Cleaned Columns (13)

**`building_sqft`** (int)
  - Outliers (±3.0σ): `cap`

**`class`** (int)
  - Parsing errors: `median`

**`land_sqft`** (int)
  - Outliers (±1.0σ): `cap`

**`num_bedrooms`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `median`

**`num_fireplaces`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `median`

**`num_full_baths`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `median`

**`num_half_baths`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `median`

**`num_rooms`** (int)
  - Outliers (±3.0σ): `cap`
  - Missing: `median`

**`pin`** (int)

**`row_id`** (int)
  - Outliers (±3.0σ): `remove`

**`tax_year`** (int)

**`township_code`** (int)

**`year_built`** (int)

#### 📋 Copied As-Is (15)

`attic_finish`, `attic_type`, `basement_finish`, `basement_type`, `central_air`, `central_heating`, `ext_wall_material`, `garage_area_included`, `garage_attached`, `garage_ext_wall_material`, `garage_size`, `num_apartments`, `roof_material`, `single_v_multi_family`, `type_of_residence`


---
