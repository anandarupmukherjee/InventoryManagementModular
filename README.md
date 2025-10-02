## 📦 Inventory Management Data Model

The system is built around products, their lot-level items, and stock movements (withdrawals, registrations, purchase orders, and QA checks).  
Below is the entity–relation diagram of the core data structures:

```mermaid
erDiagram
  PRODUCT ||--o{ PRODUCTITEM : has
  SUPPLIER ||--o{ PRODUCT : supplies
  LOCATION ||--o{ PRODUCTITEM : stores

  PRODUCTITEM ||--o{ WITHDRAWAL : has_withdrawals
  LOCATION ||--o{ WITHDRAWAL : occurs_at
  USER ||--o{ WITHDRAWAL : performed_by

  PRODUCTITEM ||--o{ STOCKREGISTRATIONLOG : has_registrations
  LOCATION ||--o{ STOCKREGISTRATIONLOG : occurs_at
  USER ||--o{ STOCKREGISTRATIONLOG : performed_by

  PRODUCTITEM ||--o{ PURCHASEORDER : requested_as
  USER ||--o{ PURCHASEORDER : ordered_by

  PURCHASEORDER ||--o{ PURCHASEORDERCOMPLETIONLOG : completed_into
  USER ||--o{ PURCHASEORDERCOMPLETIONLOG : created_by
  USER ||--o{ PURCHASEORDERCOMPLETIONLOG : completed_by

  PRODUCTITEM ||--o{ LOTACCEPTANCETEST : tested_by
```

```mermaid
erDiagram
  PRODUCT {
    int id
    string product_code
    string name
    string supplier_enum
    int threshold
    duration lead_time
  }

  SUPPLIER {
    int id
    string name
    string contact_email
    string contact_phone
  }

  LOCATION {
    int id
    string name
    bool is_default
  }

  PRODUCTITEM {
    int id
    int product_id
    string lot_number
    date expiry_date
    decimal current_stock
    int units_per_quantity
    int accumulated_partial
    string product_feature
    int location_id
  }

  WITHDRAWAL {
    int id
    int product_item_id
    decimal quantity
    string withdrawal_type
    datetime timestamp
    int user_id
    string barcode
    int location_id
    int parts_withdrawn
    string product_code
    string product_name
    string lot_number
    date expiry_date
  }

  STOCKREGISTRATIONLOG {
    int id
    int product_item_id
    decimal quantity
    datetime timestamp
    int user_id
    string barcode
    datetime delivery_datetime
    int location_id
    string product_code
    string product_name
    string lot_number
    date expiry_date
  }

  PURCHASEORDER {
    int id
    int product_item_id
    int quantity_ordered
    int ordered_by_id
    datetime order_date
    datetime expected_delivery
    string status
    datetime delivered_at
    string po_reference
    string product_code
    string product_name
    string lot_number
    date expiry_date
  }

  PURCHASEORDERCOMPLETIONLOG {
    int id
    int purchase_order_id
    string product_code
    string product_name
    string lot_number
    date expiry_date
    int quantity_ordered
    int ordered_by_id
    int completed_by_id
    datetime order_date
    datetime completed_at
    text remarks
  }

  LOTACCEPTANCETEST {
    int id
    int product_item_id
    bool tested
    bool passed
    string signed_off_by
    datetime signed_off_at
    string test_reference
    datetime created_at
    datetime updated_at
  }

  PRODUCT ||--o{ PRODUCTITEM : has
  SUPPLIER ||--o{ PRODUCT : supplies
  LOCATION ||--o{ PRODUCTITEM : stores
  PRODUCTITEM ||--o{ WITHDRAWAL : has_withdrawals
  PRODUCTITEM ||--o{ STOCKREGISTRATIONLOG : has_registrations
  PRODUCTITEM ||--o{ PURCHASEORDER : requested_as
  PURCHASEORDER ||--o{ PURCHASEORDERCOMPLETIONLOG : completed_into
  PRODUCTITEM ||--o{ LOTACCEPTANCETEST : tested_by
```
