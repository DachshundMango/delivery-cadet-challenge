# Database Schema
Generated from keys.json and PostgreSQL information_schema
---

## 1. Table `media_customer_reviews`
**Primary Key:** `new_id`

**Foreign Keys:**
- `franchiseID` → `sales_franchises.franchiseID`

**Columns:**
| Column | Type |
|--------|------|
| `review` | text |
| `franchiseID` | bigint |
| `review_date` | text |
| `new_id` | bigint |

## 2. Table `media_gold_reviews_chunked`
**Primary Key:** None

**Foreign Keys:**
- `franchiseID` → `sales_franchises.franchiseID`

**Columns:**
| Column | Type |
|--------|------|
| `franchiseID` | bigint |
| `review_date` | text |
| `chunked_text` | text |
| `chunk_id` | text |
| `review_uri` | text |

## 3. Table `sales_customers`
**Primary Key:** `customerID`

**Columns:**
| Column | Type |
|--------|------|
| `customerID` | bigint |
| `first_name` | text |
| `last_name` | text |
| `email_address` | text |
| `phone_number` | text |
| `address` | text |
| `city` | text |
| `state` | text |
| `country` | text |
| `continent` | text |
| `postal_zip_code` | bigint |
| `gender` | text |

## 4. Table `sales_franchises`
**Primary Key:** `franchiseID`

**Foreign Keys:**
- `supplierID` → `sales_suppliers.supplierID`

**Columns:**
| Column | Type |
|--------|------|
| `franchiseID` | bigint |
| `name` | text |
| `city` | text |
| `district` | text |
| `zipcode` | text |
| `country` | text |
| `size` | text |
| `longitude` | double precision |
| `latitude` | double precision |
| `supplierID` | bigint |

## 5. Table `sales_suppliers`
**Primary Key:** `supplierID`

**Columns:**
| Column | Type |
|--------|------|
| `supplierID` | bigint |
| `name` | text |
| `ingredient` | text |
| `continent` | text |
| `city` | text |
| `district` | text |
| `size` | text |
| `longitude` | double precision |
| `latitude` | double precision |
| `approved` | text |

## 6. Table `sales_transactions`
**Primary Key:** `transactionID`

**Foreign Keys:**
- `customerID` → `sales_customers.customerID`
- `franchiseID` → `sales_franchises.franchiseID`

**Columns:**
| Column | Type |
|--------|------|
| `transactionID` | bigint |
| `customerID` | bigint |
| `franchiseID` | bigint |
| `dateTime` | text |
| `product` | text |
| `quantity` | bigint |
| `unitPrice` | bigint |
| `totalPrice` | bigint |
| `paymentMethod` | text |
| `cardNumber` | bigint |
