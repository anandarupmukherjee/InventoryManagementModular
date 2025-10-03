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

```mermaid
sequenceDiagram
  autonumber
  participant Admin as Admin/User
  participant Scanner as Scanner
  participant UI as Web UI
  participant API as Django API
  participant DB as Database

  Note over Admin,DB: PRODUCT & LOT CREATION
  Admin->>UI: Create/Update Product
  UI->>API: POST /product
  API->>DB: Upsert Product
  Admin->>UI: Create ProductItem (lot)
  UI->>API: POST /product-item
  API->>DB: Insert ProductItem
  API->>DB: Set default Location if missing

  Note over Admin,DB: LOT ACCEPTANCE TEST
  Admin->>UI: Record LotAcceptanceTest
  UI->>API: POST /acceptance-test
  API->>DB: Insert LotAcceptanceTest

  Note over Admin,DB: STOCK REGISTRATION (INBOUND)
  Admin->>Scanner: Scan barcode (optional)
  Scanner-->>UI: Send barcode
  UI->>API: POST /stock/register
  API->>DB: Resolve ProductItem and Product
  API->>DB: Insert StockRegistrationLog
  API->>DB: Increment ProductItem.current_stock
  API-->>UI: OK with new stock

  Note over Admin,DB: WITHDRAWAL (OUTBOUND)
  Admin->>Scanner: Scan barcode or select lot
  Scanner-->>UI: Send barcode
  UI->>API: POST /withdraw
  API->>DB: Resolve ProductItem and Product
  API->>DB: Insert Withdrawal
  alt unit or volume
    API->>DB: Decrement current_stock
  else partial
    API->>DB: Keep current_stock
    API->>DB: Store parts_withdrawn
  end
  API-->>UI: OK with new stock or confirmation

  Note over Admin,DB: PURCHASE ORDER CREATE
  Admin->>UI: Create PO
  UI->>API: POST /po
  API->>DB: Insert PurchaseOrder
  API-->>UI: PO created

  Note over Admin,DB: PURCHASE ORDER COMPLETE
  Admin->>UI: Complete PO
  UI->>API: POST /po/{id}/complete
  API->>DB: Insert PurchaseOrderCompletionLog
  API->>DB: Increment ProductItem.current_stock
  API-->>UI: OK with new stock

```
```mermaid
sequenceDiagram
  autonumber
  participant Dev as Developer
  participant GH as GitHub
  participant FS as Local Repo
  participant SH as start.sh
  participant DC as docker compose
  participant DD as Docker Daemon
  participant DB as Postgres/SQLite
  participant DJ as Django App
  participant NG as Nginx Proxy
  participant UI as React UI
  participant MIG as Django Migrate
  participant ST as Collectstatic
  participant BR as Browser

  Dev->>GH: git clone or pull
  GH-->>FS: repo updated
  Dev->>FS: copy .env.example to .env

  Dev->>SH: run start.sh
  SH->>DC: compose build
  DC->>DD: build images
  DD-->>DC: images built
  SH->>DC: compose up -d
  DC->>DD: start containers

  DD-->>DB: start database
  DD-->>DJ: start backend
  DD-->>UI: start frontend
  DD-->>NG: start proxy

  DJ->>DB: health check
  DJ->>MIG: run migrations
  MIG->>DB: apply schema
  DJ->>ST: collect static
  ST-->>DJ: static ready

  DJ-->>DC: healthy
  UI-->>DC: healthy
  NG-->>DC: healthy

  Dev->>BR: open http://localhost
  BR->>NG: request app
  NG->>UI: serve frontend
  UI->>DJ: API requests
  DJ->>DB: queries
  DB-->>DJ: data
  DJ-->>UI: JSON
  UI-->>BR: dashboard loaded

```
