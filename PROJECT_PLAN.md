# Ralfiz Business Management System (BMS)
## Complete Project Specification & Implementation Plan

---

## 1. Project Overview

### 1.1 Objective
Build a comprehensive web application for managing clients, projects, invoices, quotes, payments, and project-based credentials (servers, domains, expiry tracking) for Ralfiz Technologies.

### 1.2 Core Modules
1. **Client Management** - Store and manage client information
2. **Project Management** - Track projects linked to clients
3. **Credential Vault** - Store project-based credentials (servers, domains, APIs, etc.) with expiry alerts
4. **Quotation System** - Create and send quotes/proposals
5. **Invoice System** - Generate and track invoices
6. **Payment Tracking** - Record payments against invoices (no payment gateway integration)
7. **Dashboard & Reports** - Overview and analytics

### 1.3 Tech Stack
- **Backend:** Django 4.2+
- **Frontend:** Django Templates + Bootstrap 5 + HTMX (for dynamic interactions)
- **Database:** SQLite (dev) / PostgreSQL (production)
- **PDF Generation:** WeasyPrint or xhtml2pdf
- **Authentication:** Django's built-in auth system

---

## 2. Database Schema / Models

### 2.1 Client Model
```
Client
├── id (UUID, primary key)
├── name (string, required)
├── company_name (string, optional)
├── email (email, required)
├── phone (string)
├── whatsapp (string)
├── address (text)
├── gst_number (string) - for Indian GST
├── priority (choice: high/medium/low)
├── notes (text)
├── is_active (boolean, default=True)
├── created_at (datetime)
└── updated_at (datetime)
```

### 2.2 Project Model
```
Project
├── id (UUID, primary key)
├── client (FK → Client)
├── name (string, required)
├── project_type (choice: web_app/mobile_app/full_stack/api/maintenance/consulting/other)
├── description (text)
├── status (choice: lead/proposal/negotiation/confirmed/in_progress/review/completed/on_hold/cancelled)
├── estimated_budget (decimal)
├── final_amount (decimal, nullable)
├── start_date (date, nullable)
├── deadline (date, nullable)
├── completed_date (date, nullable)
├── tech_stack (string) - e.g., "Django, Flutter, PostgreSQL"
├── github_repo (URL, optional)
├── live_url (URL, optional)
├── notes (text)
├── created_at (datetime)
└── updated_at (datetime)
```

### 2.3 Credential Model (For Server/Domain/API Management)
```
Credential
├── id (UUID, primary key)
├── project (FK → Project)
├── credential_type (choice: server/domain/hosting/database/email/api/ssl/cdn/cloud/git/other)
├── name (string) - e.g., "Production Server", "Main Domain"
├── provider (string) - e.g., "DigitalOcean", "GoDaddy", "AWS"
├── url (URL) - Login/dashboard URL
├── ip_address (IP address, nullable)
├── username (string, encrypted)
├── password (string, encrypted)
├── ssh_key (text, encrypted)
├── port (integer, nullable)
├── purchase_date (date, nullable)
├── expiry_date (date, nullable) ⚠️ KEY FIELD FOR ALERTS
├── auto_renew (boolean)
├── renewal_cost (decimal, nullable)
├── notes (text)
├── is_active (boolean)
├── created_at (datetime)
└── updated_at (datetime)

Properties:
- is_expiring_soon → True if expiry within 30 days
- is_expired → True if past expiry date
- days_until_expiry → Integer days remaining
```

### 2.4 Quote Model
```
Quote
├── id (UUID, primary key)
├── quote_number (string, auto-generated: QT20250001)
├── client (FK → Client)
├── project (FK → Project, nullable)
├── title (string)
├── description (text)
├── status (choice: draft/sent/viewed/accepted/rejected/expired)
├── subtotal (decimal)
├── discount (decimal)
├── tax_rate (decimal, default=18 for GST)
├── tax_amount (decimal, calculated)
├── total_amount (decimal, calculated)
├── issue_date (date)
├── valid_until (date)
├── terms (text) - Payment terms
├── notes (text)
├── created_at (datetime)
└── updated_at (datetime)

QuoteItem (Line Items)
├── id (UUID)
├── quote (FK → Quote)
├── description (string)
├── details (text)
├── quantity (decimal)
├── unit_price (decimal)
├── amount (decimal, calculated)
└── order (integer) - For sorting
```

### 2.5 Invoice Model
```
Invoice
├── id (UUID, primary key)
├── invoice_number (string, auto-generated: INV20250001)
├── client (FK → Client)
├── project (FK → Project, nullable)
├── quote (FK → Quote, nullable) - If converted from quote
├── title (string)
├── description (text)
├── status (choice: draft/sent/viewed/partial/paid/overdue/cancelled)
├── subtotal (decimal)
├── discount (decimal)
├── tax_rate (decimal, default=18)
├── tax_amount (decimal, calculated)
├── total_amount (decimal, calculated)
├── amount_paid (decimal, updated from payments)
├── issue_date (date)
├── due_date (date)
├── terms (text)
├── notes (text)
├── created_at (datetime)
└── updated_at (datetime)

Properties:
- balance_due → total_amount - amount_paid
- is_overdue → True if past due_date and not paid

InvoiceItem (Line Items)
├── id (UUID)
├── invoice (FK → Invoice)
├── description (string)
├── details (text)
├── quantity (decimal)
├── unit_price (decimal)
├── amount (decimal, calculated)
└── order (integer)
```

### 2.6 Payment Model
```
Payment
├── id (UUID, primary key)
├── invoice (FK → Invoice)
├── amount (decimal)
├── payment_date (date)
├── payment_method (choice: bank_transfer/upi/cash/cheque/card/paypal/other)
├── transaction_id (string, optional)
├── notes (text)
└── created_at (datetime)

On Save: Update invoice.amount_paid and invoice.status automatically
```

### 2.7 Company Settings Model (Your Business Info)
```
CompanySettings (Singleton)
├── company_name (string) - "Ralfiz Technologies"
├── tagline (string)
├── email (email)
├── phone (string)
├── address (text)
├── gst_number (string)
├── pan_number (string)
├── logo (image)
├── bank_name (string)
├── bank_account_number (string)
├── bank_ifsc (string)
├── bank_branch (string)
├── upi_id (string)
├── invoice_prefix (string, default="INV")
├── quote_prefix (string, default="QT")
├── default_tax_rate (decimal, default=18)
├── invoice_terms (text) - Default terms
└── quote_terms (text)
```

---

## 3. Features Breakdown

### 3.1 Dashboard
- **Summary Cards:**
  - Total Clients (active)
  - Active Projects
  - Pending Invoices (count & amount)
  - Revenue This Month/Year
  
- **Alerts Section:**
  - Credentials expiring in next 30 days ⚠️
  - Overdue invoices
  - Projects past deadline
  - Quotes expiring soon
  
- **Recent Activity:**
  - Latest payments received
  - Recent invoices
  - New clients

- **Quick Charts:**
  - Revenue trend (last 6 months)
  - Project status breakdown (pie chart)
  - Payment method distribution

### 3.2 Client Management
- List view with search, filter (priority, status)
- Detail view showing:
  - Client info
  - All projects
  - All quotes & invoices
  - Payment history
  - Total revenue from client
- Add/Edit/Delete clients
- Quick actions: Create project, Create quote, Create invoice

### 3.3 Project Management
- List view with filters (status, client, type)
- Kanban board view (optional, by status)
- Detail view showing:
  - Project info & timeline
  - All credentials (with expiry alerts)
  - Linked quotes & invoices
  - Payment summary
- Project timeline/progress tracking
- Add/Edit credentials directly from project

### 3.4 Credential Vault
- **List View:**
  - Filter by project, type, expiry status
  - Color coding: Red (expired), Orange (expiring soon), Green (OK)
  - Quick search
  
- **Expiry Dashboard:**
  - Calendar view of upcoming expiries
  - Grouped by month
  - One-click renewal reminder
  
- **Security:**
  - Password fields masked by default, reveal on click
  - Copy to clipboard buttons
  - Optional: Encrypt sensitive fields in DB

- **Bulk Actions:**
  - Export credentials for a project
  - Mark as renewed

### 3.5 Quotation System
- Create quote with line items
- Clone existing quote
- Convert quote to invoice (one-click)
- PDF generation with company branding
- Email quote to client (optional)
- Track quote status
- Quote validity tracking

### 3.6 Invoice System
- Create invoice with line items
- Create from quote (pre-fill items)
- PDF generation with:
  - Company logo & details
  - Client details
  - Line items table
  - Tax breakdown (GST)
  - Bank details for payment
  - Terms & conditions
- Track invoice status
- Send invoice via email (optional)
- Mark as paid (full/partial)

### 3.7 Payment Tracking
- Record payment against invoice
- Auto-update invoice status
- Payment history per invoice
- Payment methods tracking
- Receipt generation (optional)

### 3.8 Reports (Phase 2)
- Revenue report (by period, client, project)
- Outstanding payments report
- Client-wise summary
- Credential expiry report
- Tax report (for GST filing)
- Export to Excel/PDF

---

## 4. URL Structure

```
/                           → Dashboard
/clients/                   → Client list
/clients/add/               → Add client
/clients/<uuid>/            → Client detail
/clients/<uuid>/edit/       → Edit client

/projects/                  → Project list
/projects/add/              → Add project
/projects/<uuid>/           → Project detail
/projects/<uuid>/edit/      → Edit project

/credentials/               → All credentials (with filters)
/credentials/expiring/      → Expiring credentials dashboard
/credentials/<uuid>/        → Credential detail
/projects/<uuid>/credentials/add/  → Add credential to project

/quotes/                    → Quote list
/quotes/add/                → Create quote
/quotes/<uuid>/             → Quote detail
/quotes/<uuid>/edit/        → Edit quote
/quotes/<uuid>/pdf/         → Download PDF
/quotes/<uuid>/convert/     → Convert to invoice

/invoices/                  → Invoice list
/invoices/add/              → Create invoice
/invoices/<uuid>/           → Invoice detail
/invoices/<uuid>/edit/      → Edit invoice
/invoices/<uuid>/pdf/       → Download PDF
/invoices/<uuid>/payments/add/  → Record payment

/payments/                  → All payments list

/settings/                  → Company settings
/reports/                   → Reports dashboard
```

---

## 5. UI/UX Requirements

### 5.1 Design System
- **Framework:** Bootstrap 5
- **Theme:** Clean, professional, minimal
- **Colors:**
  - Primary: #2563eb (Blue)
  - Success: #16a34a (Green)
  - Warning: #f59e0b (Orange)
  - Danger: #dc2626 (Red)
  - Background: #f8fafc
  
### 5.2 Common Components
- Sidebar navigation (collapsible on mobile)
- Top navbar with search & user menu
- Card-based layouts
- DataTables for lists (search, sort, paginate)
- Modal forms for quick actions
- Toast notifications for feedback
- Loading spinners

### 5.3 Key UI Elements
- **Status Badges:** Color-coded pills for status fields
- **Currency Display:** Always show ₹ symbol, formatted with commas
- **Date Display:** DD MMM YYYY format (e.g., 03 Jan 2026)
- **Empty States:** Friendly messages with action buttons
- **Confirmation Modals:** For delete/destructive actions

### 5.4 Responsive Design
- Mobile-friendly tables (horizontal scroll or card view)
- Collapsible sidebar on mobile
- Touch-friendly buttons

---

## 6. File/Folder Structure

```
ralfiz_bms/
├── config/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── core/                   # Main application
│   ├── models/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── project.py
│   │   ├── credential.py
│   │   ├── quote.py
│   │   ├── invoice.py
│   │   ├── payment.py
│   │   └── settings.py
│   │
│   ├── views/
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── clients.py
│   │   ├── projects.py
│   │   ├── credentials.py
│   │   ├── quotes.py
│   │   ├── invoices.py
│   │   └── payments.py
│   │
│   ├── forms/
│   │   ├── __init__.py
│   │   ├── client_forms.py
│   │   ├── project_forms.py
│   │   ├── credential_forms.py
│   │   ├── quote_forms.py
│   │   └── invoice_forms.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── components/
│   │   │   ├── sidebar.html
│   │   │   ├── navbar.html
│   │   │   ├── cards.html
│   │   │   └── modals.html
│   │   ├── dashboard/
│   │   ├── clients/
│   │   ├── projects/
│   │   ├── credentials/
│   │   ├── quotes/
│   │   ├── invoices/
│   │   └── pdf/
│   │       ├── quote_pdf.html
│   │       └── invoice_pdf.html
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── custom.css
│   │   ├── js/
│   │   │   └── app.js
│   │   └── images/
│   │
│   ├── admin.py
│   ├── urls.py
│   └── utils.py            # Helper functions
│
├── media/                  # Uploaded files
├── static/                 # Collected static files
├── requirements.txt
├── manage.py
└── README.md
```

---

## 7. Implementation Phases

### Phase 1: Foundation (Week 1)
1. Setup Django project structure
2. Create all models with migrations
3. Setup Django admin for all models
4. Create base template with Bootstrap 5
5. Implement authentication (login/logout)
6. Build sidebar navigation

### Phase 2: Client & Project Management (Week 2)
1. Client CRUD operations
2. Client list with search/filter
3. Client detail page
4. Project CRUD operations
5. Project list with filters
6. Project detail page
7. Link projects to clients

### Phase 3: Credential Vault (Week 3)
1. Credential CRUD operations
2. Credential list with expiry filtering
3. Expiry dashboard/alerts
4. Password reveal/copy functionality
5. Dashboard integration (expiry alerts)

### Phase 4: Quotation System (Week 4)
1. Quote CRUD with line items
2. Dynamic line item management (JS)
3. Quote list and detail views
4. PDF generation for quotes
5. Quote status management
6. Clone quote functionality

### Phase 5: Invoice & Payment System (Week 5)
1. Invoice CRUD with line items
2. Convert quote to invoice
3. PDF generation for invoices
4. Payment recording
5. Auto-update invoice status
6. Payment history

### Phase 6: Dashboard & Polish (Week 6)
1. Dashboard with summary cards
2. Charts (revenue, project status)
3. Alert widgets
4. Recent activity feed
5. Company settings page
6. Final UI polish

### Phase 7: Reports & Export (Optional)
1. Revenue reports
2. Outstanding payments report
3. Export to Excel
4. Tax/GST report

---

## 8. Key Implementation Notes

### 8.1 Auto-Generated Numbers
```python
# Quote: QT20260001, QT20260002...
# Invoice: INV20260001, INV20260002...
# Format: PREFIX + YEAR + 4-digit sequence
```

### 8.2 Tax Calculation
```python
subtotal = sum of line items
tax_amount = (subtotal - discount) * (tax_rate / 100)
total_amount = subtotal - discount + tax_amount
```

### 8.3 Invoice Status Logic
```python
if amount_paid >= total_amount:
    status = 'paid'
elif amount_paid > 0:
    status = 'partial'
elif due_date < today and status not in ['paid', 'cancelled']:
    status = 'overdue'
```

### 8.4 Credential Expiry Logic
```python
is_expired = expiry_date < today
is_expiring_soon = expiry_date <= today + 30 days
days_until_expiry = expiry_date - today
```

### 8.5 Security Considerations
- Use Django's CSRF protection
- Encrypt sensitive credential fields (passwords, SSH keys)
- Implement proper user permissions
- Validate all inputs
- Use HTTPS in production

---

## 9. Sample Data for Testing

### Clients
1. TechStart Solutions - Kozhikode - High Priority
2. MediCare Hospital - Kannur - Medium Priority
3. EduHub Academy - Malappuram - Low Priority

### Projects
1. TechStart - E-commerce Platform - In Progress - ₹3,50,000
2. MediCare - Patient Portal - Completed - ₹5,00,000
3. EduHub - LMS Development - Lead - ₹2,00,000

### Credentials
1. TechStart Server - DigitalOcean - Expires: 15 Feb 2026
2. techstart.com Domain - GoDaddy - Expires: 10 Jan 2026 (EXPIRING SOON!)
3. MediCare SSL - Let's Encrypt - Expires: 01 Mar 2026

---

## 10. Commands for Claude Code

Use these prompts with Claude Code to implement each phase:

### Initial Setup
```
Create a Django project called 'ralfiz_bms' with a 'core' app. Setup the project structure as specified in the PROJECT_PLAN.md file. Include Bootstrap 5, configure static files, and create the base template with sidebar navigation.
```

### Models
```
Create Django models for Client, Project, Credential, Quote, QuoteItem, Invoice, InvoiceItem, Payment, and CompanySettings as specified in the PROJECT_PLAN.md database schema section. Include all fields, relationships, properties, and auto-generation logic.
```

### Views & Templates
```
Create CRUD views and templates for [MODULE_NAME] following the PROJECT_PLAN.md specifications. Use class-based views, include search/filter functionality, and implement the specified URL patterns.
```

### Dashboard
```
Create the dashboard view with summary cards, expiry alerts, recent activity, and charts as specified in PROJECT_PLAN.md section 3.1.
```

### PDF Generation
```
Implement PDF generation for quotes and invoices using WeasyPrint. Include company branding, line items table, tax breakdown, and bank details.
```

---

## 11. Future Enhancements (Phase 2+)

1. **Email Integration** - Send quotes/invoices via email
2. **Recurring Invoices** - Auto-generate monthly invoices
3. **Multi-currency Support** - USD, EUR, etc.
4. **Client Portal** - Clients can view their invoices/quotes
5. **Mobile App** - Flutter app for on-the-go access
6. **WhatsApp Integration** - Send reminders via WhatsApp
7. **Document Attachments** - Attach files to projects/invoices
8. **Task Management** - Break projects into tasks
9. **Time Tracking** - Track hours per project
10. **API** - REST API for integrations

---

*Document Version: 1.0*
*Last Updated: January 2026*
*For: Ralfiz Technologies*
