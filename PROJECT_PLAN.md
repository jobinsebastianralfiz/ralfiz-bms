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

## 12. Employee Mobile App API Endpoints

**Base URL:** `/api/employees/`
**Auth:** JWT Bearer token (`Authorization: Bearer <access_token>`)
**Content-Type:** `application/json` (unless file upload, then `multipart/form-data`)

---

### 12.1 Auth

#### POST `/api/employees/auth/login/`
Login and get JWT tokens with employee info.
```
Request:
{
  "username": "john",
  "password": "secret123"
}

Response 200:
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": 1,
    "username": "john",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@ralfiz.com"
  },
  "employee": {
    "id": "uuid",
    "employee_id": "EMP001",
    "employment_type": "fulltime",
    "role": "owner",          // employee | intern | owner | partner
    "department": "engineering",
    "designation": "Developer",
    "status": "active",
    "profile_photo": "http://...",
    "has_face_registered": true
  }
}
```

#### POST `/api/employees/auth/token/refresh/`
Refresh expired access token.
```
Request:  { "refresh": "eyJ..." }
Response: { "access": "eyJ..." }
```

#### POST `/api/employees/auth/change-password/`
```
Request:  { "old_password": "old", "new_password": "new123" }
Response: { "message": "Password changed successfully" }
```

#### DELETE `/api/employees/auth/delete-account/`
```
Request:  { "password": "current_password" }
Response: { "message": "Account deleted successfully" }
```

---

### 12.2 Dashboard & Profile

#### GET `/api/employees/dashboard/`
Employee dashboard overview.
```
Response 200:
{
  "employee": { ...EmployeeProfileSerializer... },
  "today_attendance": { ...AttendanceSerializer... } | null,
  "pending_leaves": 2,
  "active_assignments": 3,
  "unread_notifications": 5,
  "recent_assignments": [ ...WorkAssignmentSerializer... ],
  "upcoming_classes": [ ...ScheduledClassSerializer... ]   // only for role=intern
}
```

#### GET `/api/employees/profile/`
```
Response: { ...EmployeeProfileSerializer (id, employee_id, full_name, employment_type, role, department, designation, phone, etc.)... }
```

#### PATCH `/api/employees/profile/`
Update own profile (limited fields).
```
Request (multipart/form-data):
  phone: "9876543210"
  emergency_contact: "John Doe - 1234567890"
  address: "123 Street"
  profile_photo: <file>

Response: { ...updated EmployeeProfileSerializer... }
```

#### POST `/api/employees/profile/face/` (multipart/form-data)
Upload face photo for recognition.
```
Request:  face_photo: <image file>
Response: { "message": "Face photo updated successfully", "face_photo": "http://..." }
Error:    { "error": "No face detected in the uploaded photo..." }
```

#### GET `/api/employees/profile/face/`
```
Response: { "face_photo": "http://...", "face_encoding": "...", "has_face_registered": true }
```

#### POST `/api/employees/device-token/`
Register FCM token for push notifications.
```
Request:  { "token": "fcm_token_string", "device_type": "android" }
Response: { "message": "Device registered", "id": "uuid" }
```

---

### 12.3 Attendance

#### POST `/api/employees/attendance/check-in/` (multipart/form-data)
```
Request:
{
  "verification_method": "face_local",  // face | face_local | face_qr | face_location | qr | location
  "latitude": 11.2588,
  "longitude": 75.7804,
  "qr_code": "office-qr-code-value",   // required for qr, face_qr, face_local
  "face_photo": <image file>,           // required for face, face_qr, face_location, face_local
  "face_confidence": 0.95               // optional, for face_local
}

Response 201:
{
  "message": "Checked in successfully",
  "attendance": { ...AttendanceSerializer... }
}

Errors:
  400: "Location is required for check-in."
  400: "You are 500m away from office. Must be within 200m."
  400: "Invalid QR code. Please scan the office QR sticker."
  400: "No reference face photo registered. Please register your face first."
  400: "Already checked in today"
  403: "Face verification failed. The selfie does not match your registered face."
```

#### POST `/api/employees/attendance/check-out/`
```
Request:  { "latitude": 11.2588, "longitude": 75.7804 }
Response: { "message": "Checked out successfully", "attendance": {...} }
```

#### GET `/api/employees/attendance/today/`
```
Response: { "checked_in": true, "checked_out": false, "attendance": {...} | null }
```

#### GET `/api/employees/attendance/history/?month=3&year=2026`
```
Response: [ { ...AttendanceSerializer (id, date, check_in, check_out, working_hours, status, verification_method)... }, ... ]
```

---

### 12.4 Leave

#### GET `/api/employees/leave/types/`
```
Response: [ { "id": "uuid", "name": "Casual Leave", "days_allowed": 12, "is_active": true }, ... ]
```

#### GET `/api/employees/leave/requests/?status=pending`
```
Response: [ { ...LeaveRequestSerializer (id, leave_type, start_date, end_date, total_days, reason, status)... }, ... ]
```

#### POST `/api/employees/leave/requests/`
```
Request:
{
  "leave_type": "uuid",
  "start_date": "2026-03-20",
  "end_date": "2026-03-21",
  "reason": "Personal work"
}

Response 201: { ...LeaveRequestSerializer... }
```

#### POST `/api/employees/leave/requests/<uuid>/cancel/`
```
Response: { "message": "Leave request cancelled" }
Error:    { "error": "Only pending requests can be cancelled" }
```

#### GET `/api/employees/leave/balance/`
```
Response: [
  { "leave_type": "Casual Leave", "total_allowed": 12, "used": 3, "remaining": 9 },
  { "leave_type": "Sick Leave", "total_allowed": 6, "used": 1, "remaining": 5 }
]
```

---

### 12.5 Work Assignments

#### GET `/api/employees/work/?status=in_progress`
```
Response: [ { ...WorkAssignmentSerializer (id, title, description, priority, status, due_date, assigned_by, updates)... }, ... ]
```

#### GET `/api/employees/work/<uuid>/`
```
Response: { ...WorkAssignmentSerializer... }
```

#### POST `/api/employees/work/<uuid>/status/`
Update assignment status.
```
Request:
{
  "status": "completed",   // assigned | in_progress | completed | on_hold
  "message": "Done, deployed to staging"  // optional update message
}

Response: { "message": "Status updated", "assignment": {...} }
```

#### POST `/api/employees/work/<uuid>/update/` (multipart/form-data)
Add update/note to assignment.
```
Request:  { "message": "Progress update text", "attachment": <file> }
Response: { ...WorkUpdateSerializer (id, message, attachment, created_at)... }
```

---

### 12.6 Scheduled Classes (Interns Only)

Returns empty for non-intern roles.

#### GET `/api/employees/classes/?status=scheduled&upcoming=true`
```
Response: [ { ...ScheduledClassSerializer (id, title, date, start_time, end_time, instructor, location, status, participants)... }, ... ]
```

#### GET `/api/employees/classes/<uuid>/`
```
Response: { ...ScheduledClassSerializer... }
Error 403: "Scheduled classes are only available for interns."
```

---

### 12.7 Payslips

#### GET `/api/employees/payslips/?year=2026`
```
Response: [ { ...PayrollSerializer (id, month, year, basic_salary, deductions, net_salary, status, paid_date)... }, ... ]
```

#### GET `/api/employees/payslips/<uuid>/`
```
Response: { ...PayrollSerializer... }
```

---

### 12.8 Notifications

#### GET `/api/employees/notifications/`
```
Response: [ { "id": "uuid", "title": "New Leave Request", "body": "...", "notification_type": "leave", "is_read": false, "created_at": "..." }, ... ]
```

#### POST `/api/employees/notifications/read/`
Mark all as read.
```
Response: { "message": "Marked as read" }
```

#### POST `/api/employees/notifications/<uuid>/read/`
Mark single as read.
```
Response: { "message": "Marked as read" }
```

---

### 12.9 Owner/Partner APIs — Read

All require `role` = `owner` or `partner`. Returns `403` otherwise.

#### GET `/api/employees/owner/dashboard/`
```
Response 200:
{
  "clients": { "total": 15, "active": 12 },
  "projects": { "active": 8, "total": 25 },
  "revenue": { "total": "5000000.00", "this_month": "350000.00", "outstanding": "120000.00" },
  "expenses": { "total": "1200000.00", "this_month": "85000.00" },
  "recent_payments": [
    { "amount": "50000.00", "payment_date": "2026-03-10", "payment_method": "bank_transfer", "client_name": "TechStart", "invoice_number": "INV20260015" }
  ],
  "employees": { "total": 10, "fulltime": 5, "parttime": 2, "intern": 3 }
}
```

#### GET `/api/employees/owner/clients/?search=tech`
```
Response: [
  {
    "id": "uuid", "name": "TechStart Solutions", "company_name": "TechStart Pvt Ltd",
    "email": "info@techstart.com", "phone": "9876543210", "is_active": true,
    "total_revenue": "350000.00", "pending_amount": "50000.00", "project_count": 3
  }
]
```

#### GET `/api/employees/owner/clients/<uuid>/`
```
Response:
{
  "id": "uuid", "name": "TechStart Solutions", "company_name": "...", "email": "...",
  "phone": "...", "whatsapp": "...", "address": "...", "gst_number": "...",
  "priority": "high", "is_active": true,
  "total_invoiced": "500000.00", "total_paid": "350000.00", "balance_due": "150000.00",
  "projects": [ { "id": "uuid", "name": "E-commerce", "status": "in_progress", ... } ],
  "invoices": [ { "id": "uuid", "invoice_number": "INV20260001", "title": "...", "status": "paid", ... } ],
  "quotes": [ { "id": "uuid", "quote_number": "QT20260001", "title": "...", "status": "sent", ... } ]
}
```

#### GET `/api/employees/owner/projects/?status=in_progress&search=ecommerce`
```
Response: [
  {
    "id": "uuid", "name": "E-commerce Platform", "client_name": "TechStart",
    "status": "in_progress", "project_type": "web_app",
    "estimated_budget": "350000.00", "final_amount": "0",
    "invoiced_amount": "200000.00", "paid_amount": "150000.00",
    "start_date": "2026-01-15", "deadline": "2026-06-30"
  }
]
```

#### GET `/api/employees/owner/projects/<uuid>/`
```
Response:
{
  "id": "uuid", "name": "E-commerce Platform", "client_name": "TechStart",
  "client_id": "uuid", "project_type": "web_app", "status": "in_progress",
  "description": "...", "estimated_budget": "350000.00", "final_amount": "0",
  "start_date": "2026-01-15", "deadline": "2026-06-30", "completed_date": null,
  "tech_stack": "Django, Flutter", "github_repo": "...", "live_url": "...", "is_overdue": false,
  "financial_summary": {
    "total_invoiced": "200000.00", "total_paid": "150000.00",
    "balance_due": "50000.00", "total_expenses": "25000.00"
  },
  "credentials": [
    {
      "id": "uuid", "credential_type": "server", "name": "Production Server",
      "provider": "DigitalOcean", "url": "...", "ip_address": "...",
      "username": "root", "password": "***", "ssh_key": "...", "port": 22,
      "purchase_date": "2026-01-01", "expiry_date": "2027-01-01",
      "auto_renew": true, "renewal_cost": "5000.00",
      "is_active": true, "is_expired": false, "is_expiring_soon": false, "days_until_expiry": 292
    }
  ],
  "invoices": [ { "id": "uuid", "invoice_number": "INV20260001", ... } ],
  "expenses": [ { "id": "uuid", "category": "hosting", "amount": "5000.00", ... } ]
}
```

#### GET `/api/employees/owner/invoices/?status=paid&client_id=uuid&search=INV`
```
Response: [
  {
    "id": "uuid", "invoice_number": "INV20260001", "title": "Phase 1 Payment",
    "client_name": "TechStart", "project_name": "E-commerce",
    "status": "paid", "total_amount": "100000.00",
    "amount_paid": "100000.00", "balance_due": "0.00",
    "issue_date": "2026-02-01", "due_date": "2026-02-15", "is_overdue": false
  }
]
```

#### GET `/api/employees/owner/invoices/<uuid>/`
```
Response:
{
  "id": "uuid", "invoice_number": "INV20260001", "title": "Phase 1 Payment",
  "description": "...", "client_name": "TechStart", "client_id": "uuid",
  "project_name": "E-commerce", "project_id": "uuid", "quote_number": null,
  "status": "paid", "subtotal": "100000.00", "discount": "0.00",
  "tax_rate": "18.00", "tax_amount": "18000.00",
  "total_amount": "118000.00", "amount_paid": "118000.00", "balance_due": "0.00",
  "issue_date": "2026-02-01", "due_date": "2026-02-15", "is_overdue": false,
  "items": [
    { "description": "Frontend Development", "details": "...", "quantity": "1", "unit_price": "50000.00", "amount": "50000.00" },
    { "description": "Backend Development", "details": "...", "quantity": "1", "unit_price": "50000.00", "amount": "50000.00" }
  ],
  "payments": [
    { "id": "uuid", "amount": "118000.00", "payment_date": "2026-02-10", "payment_method": "bank_transfer", "transaction_id": "TXN123", "notes": "" }
  ]
}
```

#### GET `/api/employees/owner/quotes/?status=sent&client_id=uuid`
```
Response: [
  {
    "id": "uuid", "quote_number": "QT20260001", "title": "Website Redesign Proposal",
    "client_name": "TechStart", "project_name": "",
    "status": "sent", "total_amount": "250000.00",
    "issue_date": "2026-03-01", "valid_until": "2026-03-31", "is_expired": false
  }
]
```

#### GET `/api/employees/owner/expenses/?category=hosting&project_id=uuid&start_date=2026-01-01&end_date=2026-03-31`
```
Response:
{
  "total": "85000.00",
  "count": 12,
  "expenses": [
    {
      "id": "uuid", "category": "hosting", "amount": "5000.00", "date": "2026-03-01",
      "vendor": "DigitalOcean", "description": "Monthly server cost",
      "project_name": "E-commerce", "is_billable": true, "payment_method": "card"
    }
  ]
}
```

#### GET `/api/employees/owner/financial-report/`
```
Response:
{
  "summary": {
    "total_income": "2500000.00", "total_expenses": "800000.00",
    "net_profit": "1700000.00", "collection_rate": 78.5
  },
  "monthly_trends": [
    { "month": "Apr", "year": 2025, "income": "180000.00", "expenses": "60000.00", "profit": "120000.00" },
    ...
  ],
  "revenue_by_client": [
    { "client": "TechStart Solutions", "revenue": "500000.00" },
    { "client": "MediCare Hospital", "revenue": "350000.00" }
  ]
}
```

#### GET `/api/employees/owner/employees/?status=active&department=engineering&role=employee&search=john`
```
Response: [
  {
    "id": "uuid", "employee_id": "EMP001", "name": "John Doe",
    "email": "john@ralfiz.com", "phone": "9876543210",
    "department": "engineering", "department_display": "Engineering",
    "designation": "Senior Developer",
    "employment_type": "fulltime", "employment_type_display": "Full-Time",
    "role": "employee", "role_display": "Employee",
    "status": "active", "status_display": "Active",
    "joining_date": "2025-06-15",
    "profile_photo": "http://..."
  }
]
```

#### GET `/api/employees/owner/employees/<uuid>/`
```
Response:
{
  "id": "uuid", "employee_id": "EMP001", "name": "John Doe",
  "first_name": "John", "last_name": "Doe",
  "email": "john@ralfiz.com", "phone": "9876543210",
  "emergency_contact": "Jane Doe - 1234567890", "address": "123 Street",
  "date_of_birth": "1995-05-20", "joining_date": "2025-06-15",
  "department": "engineering", "department_display": "Engineering",
  "designation": "Senior Developer",
  "employment_type": "fulltime", "employment_type_display": "Full-Time",
  "role": "employee", "role_display": "Employee",
  "status": "active", "status_display": "Active",
  "monthly_salary": "50000.00", "hourly_rate": null,
  "profile_photo": "http://...", "has_face_registered": true,
  "supervisor": null,
  "attendance_summary": {
    "month": "March 2026", "present": 10, "absent": 1, "late": 2, "total_hours": 82.5
  },
  "recent_attendance": [
    { "date": "2026-03-14", "check_in": "09:15", "check_out": "18:00", "working_hours": "8.75", "status": "present", "status_display": "Present", "verification_method": "face_local" }
  ],
  "leave_balance": [
    { "leave_type": "Casual Leave", "total_allowed": 12, "used": 3, "remaining": 9 }
  ],
  "pending_leaves": [
    { "id": "uuid", "leave_type": "Casual Leave", "start_date": "2026-03-20", "end_date": "2026-03-21", "total_days": 2, "reason": "Personal" }
  ],
  "active_assignments": [
    { "id": "uuid", "title": "Fix login bug", "priority": "high", "status": "in_progress", "due_date": "2026-03-16" }
  ]
}
```

#### GET `/api/employees/owner/attendance/?start_date=2026-03-01&end_date=2026-03-14&employee_id=uuid`
```
Response: [
  {
    "employee_id": "EMP001", "name": "John Doe", "department": "engineering",
    "records": [ { ...AttendanceSerializer (id, date, check_in, check_out, working_hours, status)... } ]
  }
]
```

---

### 12.10 Owner/Partner APIs — Create / Update / Delete

All require `role` = `owner` or `partner`.

#### POST `/api/employees/owner/clients/create/`
```
Request:
{
  "name": "New Client",           // required
  "company_name": "Client Corp",
  "email": "client@example.com",
  "phone": "9876543210",
  "whatsapp": "9876543210",
  "address": "123 Main St",
  "gst_number": "29ABCDE1234F1Z5",
  "priority": "high",             // high | medium | low
  "notes": "Referred by John"
}

Response 201: { "id": "uuid", "message": "Client created" }
Error 400:    { "error": "Client name is required" }
```

#### PATCH `/api/employees/owner/clients/<uuid>/edit/`
Partial update — send only fields you want to change.
```
Request:
{
  "name": "Updated Name",
  "priority": "low",
  "is_active": false
}

Response 200: { "message": "Client updated" }
Error 404:    { "error": "Client not found" }
```

#### DELETE `/api/employees/owner/clients/<uuid>/edit/`
```
Response 204: { "message": "Client deleted" }
Error 404:    { "error": "Client not found" }
```

---

#### POST `/api/employees/owner/projects/create/`
```
Request:
{
  "name": "New Project",           // required
  "client_id": "uuid",             // required
  "project_type": "web_app",       // web_app | mobile_app | full_stack | api | maintenance | consulting | other
  "description": "Project description",
  "status": "lead",                // lead | proposal | negotiation | confirmed | in_progress | review | completed | on_hold | cancelled
  "estimated_budget": 350000,
  "final_amount": null,
  "start_date": "2026-04-01",
  "deadline": "2026-09-30",
  "tech_stack": "Django, Flutter",
  "github_repo": "https://github.com/...",
  "live_url": "https://...",
  "notes": ""
}

Response 201: { "id": "uuid", "message": "Project created" }
Error 400:    { "error": "Project name and client_id are required" }
Error 404:    { "error": "Client not found" }
```

#### PATCH `/api/employees/owner/projects/<uuid>/edit/`
```
Request:
{
  "status": "in_progress",
  "final_amount": 400000,
  "client_id": "new-client-uuid"    // reassign to different client
}

Response 200: { "message": "Project updated" }
```

#### DELETE `/api/employees/owner/projects/<uuid>/edit/`
```
Response 204: { "message": "Project deleted" }
```

---

#### POST `/api/employees/owner/credentials/create/`
```
Request:
{
  "project_id": "uuid",            // required
  "name": "Production Server",     // required
  "credential_type": "server",     // server | domain | hosting | database | email | api | ssl | cdn | cloud | git | other
  "provider": "DigitalOcean",
  "url": "https://cloud.digitalocean.com",
  "ip_address": "164.90.xxx.xxx",
  "username": "root",
  "password": "secure_password",
  "ssh_key": "-----BEGIN RSA KEY-----...",
  "port": 22,
  "purchase_date": "2026-01-01",
  "expiry_date": "2027-01-01",
  "auto_renew": true,
  "renewal_cost": 5000,
  "notes": ""
}

Response 201: { "id": "uuid", "message": "Credential created" }
Error 400:    { "error": "project_id and name are required" }
Error 404:    { "error": "Project not found" }
```

#### PATCH `/api/employees/owner/credentials/<uuid>/edit/`
```
Request:
{
  "password": "new_password",
  "expiry_date": "2028-01-01",
  "is_active": false
}

Response 200: { "message": "Credential updated" }
```

#### DELETE `/api/employees/owner/credentials/<uuid>/edit/`
```
Response 204: { "message": "Credential deleted" }
```

---

#### POST `/api/employees/owner/invoices/create/`
```
Request:
{
  "client_id": "uuid",             // required
  "title": "Phase 1 Payment",      // required
  "project_id": "uuid",            // optional
  "description": "",
  "status": "draft",               // draft | sent | viewed | partial | paid | overdue | cancelled
  "discount": 0,
  "tax_rate": 18,
  "issue_date": "2026-03-15",
  "due_date": "2026-03-30",
  "terms": "Payment due within 15 days",
  "client_notes": "Thank you for your business",
  "notes": "Internal note",
  "items": [                        // line items
    { "description": "Frontend Development", "details": "React UI", "quantity": 1, "unit_price": 50000 },
    { "description": "Backend API", "details": "Django REST", "quantity": 1, "unit_price": 50000 }
  ]
}

Response 201: { "id": "uuid", "invoice_number": "INV20260005", "message": "Invoice created" }
Error 400:    { "error": "client_id and title are required" }
```

#### PATCH `/api/employees/owner/invoices/<uuid>/edit/`
If `items` is provided, existing items are deleted and replaced.
```
Request:
{
  "status": "sent",
  "due_date": "2026-04-15",
  "items": [
    { "description": "Updated item", "quantity": 2, "unit_price": 60000 }
  ]
}

Response 200: { "message": "Invoice updated" }
```

#### DELETE `/api/employees/owner/invoices/<uuid>/edit/`
Cannot delete invoices with recorded payments.
```
Response 204: { "message": "Invoice deleted" }
Error 400:    { "error": "Cannot delete invoice with payments recorded" }
```

---

#### POST `/api/employees/owner/invoices/<uuid>/payments/`
Record a payment against an invoice.
```
Request:
{
  "invoice_id": "uuid",            // required
  "amount": 50000,                 // required
  "payment_date": "2026-03-15",
  "payment_method": "bank_transfer",  // bank_transfer | upi | cash | cheque | card | paypal | other
  "transaction_id": "TXN456",
  "notes": "Partial payment"
}

Response 201:
{
  "id": "uuid",
  "message": "Payment recorded",
  "invoice_status": "partial",
  "amount_paid": "50000.00",
  "balance_due": "68000.00"
}
```

---

#### POST `/api/employees/owner/quotes/create/`
```
Request:
{
  "client_id": "uuid",             // required
  "title": "Website Redesign",     // required
  "valid_until": "2026-04-30",     // required
  "project_id": "uuid",            // optional
  "description": "Complete redesign proposal",
  "status": "draft",               // draft | sent | viewed | accepted | rejected | expired
  "discount": 5000,
  "tax_rate": 18,
  "issue_date": "2026-03-15",
  "duration": "3 months",
  "start_date": "2026-04-01",
  "deliverables": "Homepage, 5 inner pages, Mobile responsive",
  "payment_terms": "50-50",
  "terms": "Standard terms apply",
  "client_notes": "",
  "notes": "",
  "items": [
    { "description": "UI/UX Design", "details": "Figma mockups", "quantity": 1, "unit_price": 30000 },
    { "description": "Development", "details": "Frontend + Backend", "quantity": 1, "unit_price": 120000 }
  ]
}

Response 201: { "id": "uuid", "quote_number": "QT20260003", "message": "Quote created" }
Error 400:    { "error": "client_id, title, and valid_until are required" }
```

#### PATCH `/api/employees/owner/quotes/<uuid>/edit/`
If `items` is provided, existing items are deleted and replaced.
```
Request:
{
  "status": "sent",
  "valid_until": "2026-05-15",
  "items": [
    { "description": "Updated scope", "quantity": 1, "unit_price": 200000 }
  ]
}

Response 200: { "message": "Quote updated" }
```

#### DELETE `/api/employees/owner/quotes/<uuid>/edit/`
```
Response 204: { "message": "Quote deleted" }
```

---

#### POST `/api/employees/owner/expenses/create/` (multipart/form-data for receipt upload)
```
Request:
{
  "category": "hosting",           // required
  "amount": 5000,                  // required
  "vendor": "DigitalOcean",        // required
  "date": "2026-03-01",
  "description": "Monthly server cost",
  "receipt": <file>,               // optional image/pdf
  "project_id": "uuid",            // optional
  "is_billable": true,
  "payment_method": "card",        // bank_transfer | upi | cash | cheque | card | paypal | other
  "notes": ""
}

Response 201: { "id": "uuid", "message": "Expense created" }
Error 400:    { "error": "amount, vendor, and category are required" }
```

#### PATCH `/api/employees/owner/expenses/<uuid>/edit/` (multipart/form-data for receipt)
```
Request:
{
  "amount": 6000,
  "receipt": <file>,
  "project_id": "new-project-uuid"
}

Response 200: { "message": "Expense updated" }
```

#### DELETE `/api/employees/owner/expenses/<uuid>/edit/`
```
Response 204: { "message": "Expense deleted" }
```

---

*Document Version: 2.0*
*Last Updated: March 2026*
*For: Ralfiz Technologies*
