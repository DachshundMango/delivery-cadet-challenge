# Data Pipeline Setup Guide

**For First-Time Users**: This guide provides step-by-step instructions for the interactive data pipeline setup process. It is specifically tailored to the sample dataset provided in this challenge (Cookie Franchise Data) and shows the exact inputs needed at each interactive step.

> **Note**: This guide assumes you are using the provided challenge dataset. If you are using your own data, the specific inputs will differ, but the overall process remains the same.

## Overview

The data pipeline consists of 6 automated steps, with 2 requiring user interaction:
- **Step 2**: Relationship Discovery (Primary & Foreign Keys)
- **Step 5**: Transform Data (SQL transformations)

**PII Detection Note**: Step 6 automatically detects PII (Personally Identifiable Information) columns using LLM analysis. For the provided dataset, this should work correctly and detect `first_name` and `last_name` as PII. However, if the detection seems incorrect or you're using your own dataset, you can manually edit the `src/config/schema_info.json` file after generation to add or remove PII columns from the `pii_columns` field.

Example format in `schema_info.json`:
```json
"pii_columns": {
  "sales_customers": [
    "first_name",
    "last_name"
  ]
}
```

---

## Step 2: Relationship Discovery

### Primary Key Selection

When prompted to select PRIMARY KEY for each table, enter the following:

| Table | Input | Selected Column |
|-------|-------|----------------|
| `sales_suppliers` | `0` | `supplierID` |
| `media_gold_reviews_chunked` | `3` | `chunk_id` |
| `sales_customers` | `0` | `customerID` |
| `sales_franchises` | `1` | `franchiseID` |
| `media_customer_reviews` | `0` | `new_id` |
| `sales_transactions` | `0` | `transactionID` |
| `sales_suppliers_missing_suppliers` | `0` | `supplierID` |

### Foreign Key Configuration

When prompted to select FK (foreign keys), enter the following:

#### Table: sales_suppliers
```
Select FK (or 'q'): q
```
*(No foreign keys)*

#### Table: media_gold_reviews_chunked
```
Select FK (or 'q'): 0
Target: 2
Select FK (or 'q'): q
```
- FK: `franchiseID` → `sales_franchises.franchiseID`

#### Table: sales_customers
```
Select FK (or 'q'): q
```
*(No foreign keys)*

#### Table: sales_franchises
```
Select FK (or 'q'): 8
Target: 0
Select FK (or 'q'): q
```
- FK: `supplierID` → `sales_suppliers.supplierID`

#### Table: media_customer_reviews
```
Select FK (or 'q'): 1
Target: 3
Select FK (or 'q'): q
```
- FK: `franchiseID` → `sales_franchises.franchiseID`

#### Table: sales_transactions
```
Select FK (or 'q'): 0
Target: 2
Select FK (or 'q'): 1
Target: 3
Select FK (or 'q'): q
```
- FK: `customerID` → `sales_customers.customerID`
- FK: `franchiseID` → `sales_franchises.franchiseID`

#### Table: sales_suppliers_missing_suppliers
```
Select FK (or 'q'): q
```
*(No foreign keys)*

---

## Step 5: Transform Data

### SQL Transformations

After the integrity checker identifies data issues, execute the following SQL queries in order:

#### 1. Fix Customer ID Offset
```sql
UPDATE sales_customers SET "customerID" = "customerID" - 1000000;
```
**Purpose**: Corrects systematic offset in customer IDs (they were 1000000-1000299 instead of 0-299)

#### 2. Import Missing Suppliers
```sql
INSERT INTO sales_suppliers ("supplierID", "name", "ingredient", "continent", "city", "district", "size", "longitude", "latitude", "approved") SELECT m."supplierID", m."Name", m."Ingredient", m."Continent", m."City", 'Unknown', 'Unknown', 0, 0, 'N' FROM sales_suppliers_missing_suppliers m ON CONFLICT ("supplierID") DO NOTHING;
```
**Purpose**: Adds 21 missing supplier records that are referenced by franchises

#### 3. Drop Temporary Table
```sql
DROP TABLE sales_suppliers_missing_suppliers;
```
**Purpose**: Removes the temporary table after merging data

#### 4-8. Add Foreign Key Constraints
```sql
ALTER TABLE "sales_franchises" ADD CONSTRAINT "fk_sales_franchises_supplierID" FOREIGN KEY ("supplierID") REFERENCES "sales_suppliers"("supplierID");

ALTER TABLE "sales_transactions" ADD CONSTRAINT "fk_sales_transactions_customerID" FOREIGN KEY ("customerID") REFERENCES "sales_customers"("customerID");

ALTER TABLE "sales_transactions" ADD CONSTRAINT "fk_sales_transactions_franchiseID" FOREIGN KEY ("franchiseID") REFERENCES "sales_franchises"("franchiseID");

ALTER TABLE "media_customer_reviews" ADD CONSTRAINT "fk_media_customer_reviews_franchiseID" FOREIGN KEY ("franchiseID") REFERENCES "sales_franchises"("franchiseID");

ALTER TABLE "media_gold_reviews_chunked" ADD CONSTRAINT "fk_media_gold_reviews_chunked_franchiseID" FOREIGN KEY ("franchiseID") REFERENCES "sales_franchises"("franchiseID");
```
**Purpose**: Manually adds the foreign key constraints that initially failed

#### 9. Complete Transformation
```
done
```
Type `done` to verify all transformations and update `keys.json`

---

## Expected Results

After completing all steps, you should see:

```
[Verifying Transformation]
All integrity issues resolved!

----------------------------------------------------------------
SUCCESS: Transformation completed - all verified
----------------------------------------------------------------
```

The pipeline will then proceed to:
- **Step 6**: Generate Schema with PII detection
- PII columns detected: `sales_customers.first_name`, `sales_customers.last_name`

---

## Final Database Schema

### Tables (6 total):
1. **sales_suppliers** (27 rows)
   - PK: `supplierID`

2. **media_gold_reviews_chunked** (196 rows)
   - PK: `chunk_id`
   - FK: `franchiseID` → `sales_franchises`

3. **sales_customers** (300 rows)
   - PK: `customerID`
   - PII: `first_name`, `last_name`

4. **sales_franchises** (48 rows)
   - PK: `franchiseID`
   - FK: `supplierID` → `sales_suppliers`

5. **media_customer_reviews** (204 rows)
   - PK: `new_id`
   - FK: `franchiseID` → `sales_franchises`

6. **sales_transactions** (3,333 rows)
   - PK: `transactionID`
   - FK: `customerID` → `sales_customers`
   - FK: `franchiseID` → `sales_franchises`

---

## Troubleshooting

### If you make a mistake:

1. **During PK/FK selection**: You can restart the pipeline by running `./start.sh` again
2. **During SQL transformation**: Type `quit` to exit without saving, then restart Step 5
3. **To reset everything and start from scratch**:
   ```bash
   ./start.sh --reset
   ```
   This will delete all generated configuration files and restart the entire pipeline.

---

## Quick Reference Commands

```bash
# Start the data pipeline setup (UI mode will launch after completion)
./start.sh

# Reset everything and start from scratch
./start.sh --reset

# After setup is complete, run in UI mode (default)
./start.sh

# After setup is complete, run in CLI mode
python src/cli.py
```

---

## Notes for Evaluators

- **Dataset**: This guide is specifically for the challenge's provided dataset
- **Interactive Design**: The interactive steps ensure data integrity through human verification
- **Smart Recommendations**: The system provides recommendations (marked as `[Recommended]`) based on column analysis
- **Real Data Issues**: All transformations fix actual data quality issues in the provided dataset
- **Time Estimate**: The entire process takes approximately 5 minutes for the provided challenge dataset
- **Two Modes Available**:
  - **UI Mode** (recommended): ChatGPT-style web interface with streaming responses and visualisations
  - **CLI Mode**: Terminal-based interface for quick queries without UI dependencies
