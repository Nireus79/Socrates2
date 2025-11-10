# Phase 4: Critical Features for Production Launch

**Status:** Planning Phase
**Priority Level:** CRITICAL (blocks monetization and production readiness)
**Target Completion:** 2-3 weeks
**Effort Estimate:** 80-100 developer-days

---

## Overview

Phase 4 implements 5 critical features that are blockers for production launch:

1. **Payment & Billing System** - Enable customer payments and usage tracking
2. **Analytics Dashboard** - Show metrics and ROI to users and admins
3. **Search & Filter System** - Critical UX feature across all sections
4. **Admin Panel** - User and system management for operations team
5. **Error Tracking Integration** - Production monitoring and debugging

Each feature is detailed with:
- Architecture design
- Database schema changes
- API endpoints
- Frontend components
- Implementation steps
- Effort estimate
- Dependencies

---

## 1. Payment & Billing System (Highest Priority)

**Status:** Not implemented (0%)
**Priority:** CRITICAL - Blocks monetization
**Effort:** 25-30 days
**Dependencies:** None (standalone)

### Overview

Enable Socrates to accept payments and track customer usage for billing.

**Business Model:**
- Pricing tiers: Free, Professional ($99/mo), Enterprise ($499/mo)
- Usage tracking: Projects, AI analyses, storage
- Overage charges: $0.10 per analysis above plan limit
- Payment processor: Stripe (PCI compliance, refunds, webhooks)

### Database Schema

```python
# New models needed:

class SubscriptionTier(BaseModel):
    """Pricing tier definition"""
    __tablename__ = "subscription_tier"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True)  # free, professional, enterprise
    monthly_price = Column(Float, default=0.0)
    max_projects = Column(Integer, default=None)  # None = unlimited
    max_analyses_per_month = Column(Integer, default=None)
    max_storage_gb = Column(Float, default=None)
    includes_priority_support = Column(Boolean, default=False)
    includes_advanced_analytics = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="tier")


class Subscription(BaseModel):
    """Active subscription for user"""
    __tablename__ = "subscription"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    tier_id = Column(String(36), ForeignKey("subscription_tier.id"), nullable=False)
    stripe_subscription_id = Column(String(255), unique=True)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)  # active, cancelled, past_due
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscription")
    tier = relationship("SubscriptionTier", back_populates="subscriptions")
    usage = relationship("UsageRecord", back_populates="subscription", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="subscription", cascade="all, delete-orphan")


class UsageRecord(BaseModel):
    """Track customer usage for billing"""
    __tablename__ = "usage_record"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("subscription.id"), nullable=False, index=True)
    metric_type = Column(String(50))  # projects_created, analyses_run, storage_used_gb
    metric_value = Column(Float)  # numeric value
    billed = Column(Boolean, default=False)  # included in invoice?
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    subscription = relationship("Subscription", back_populates="usage")


class Invoice(BaseModel):
    """Generated invoice for billing period"""
    __tablename__ = "invoice"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("subscription.id"), nullable=False, index=True)
    stripe_invoice_id = Column(String(255), unique=True)
    billing_period_start = Column(DateTime)
    billing_period_end = Column(DateTime)
    subtotal_cents = Column(Integer)  # in cents to avoid float precision issues
    tax_cents = Column(Integer)
    total_cents = Column(Integer)
    overage_charges_cents = Column(Integer, default=0)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)  # draft, sent, paid, failed
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    subscription = relationship("Subscription", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(BaseModel):
    """Line item on invoice (base fee, overages, credits)"""
    __tablename__ = "invoice_item"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String(36), ForeignKey("invoice.id"), nullable=False)
    description = Column(String(255))  # "Professional Monthly Subscription"
    quantity = Column(Float, default=1.0)
    unit_price_cents = Column(Integer)  # in cents
    total_cents = Column(Integer)  # quantity * unit_price
    item_type = Column(String(50))  # subscription, overage, credit

    invoice = relationship("Invoice", back_populates="items")
```

**Enums:**
```python
class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIAL = "trial"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
```

### API Endpoints

**Subscription Management:**
```
GET    /api/subscriptions/current              - Get user's active subscription
POST   /api/subscriptions/upgrade              - Upgrade to higher tier
POST   /api/subscriptions/downgrade            - Downgrade to lower tier
POST   /api/subscriptions/cancel               - Cancel subscription
GET    /api/subscriptions/tiers                - List all pricing tiers
GET    /api/subscriptions/usage                - Get current month usage
```

**Billing Management:**
```
GET    /api/billing/invoices                   - List all invoices
GET    /api/billing/invoices/{id}              - Get invoice details
POST   /api/billing/invoices/{id}/retry        - Retry failed payment
GET    /api/billing/payment-methods            - List saved payment methods
POST   /api/billing/payment-methods            - Add new payment method
DELETE /api/billing/payment-methods/{id}       - Remove payment method
POST   /api/billing/stripe-webhook             - Stripe webhook handler
```

### Services

**BillingService (480+ lines):**
- `create_subscription(user_id, tier)` - Create new subscription
- `track_usage(subscription_id, metric_type, value)` - Record usage event
- `get_usage_this_month(subscription_id)` - Get current month metrics
- `check_usage_exceeded(subscription_id)` - Detect overage situations
- `calculate_overages(subscription_id, usage_data)` - Compute overage fees
- `generate_invoice(subscription_id)` - Create monthly invoice
- `process_stripe_webhook(event)` - Handle Stripe events (subscription updated, invoice paid, etc.)

**StripeIntegrationService (320+ lines):**
- `create_stripe_customer(user)` - Register with Stripe
- `create_subscription_on_stripe(customer, tier)` - Create Stripe subscription
- `update_subscription_on_stripe(stripe_sub_id, new_tier)` - Change subscription
- `cancel_subscription_on_stripe(stripe_sub_id)` - Cancel Stripe subscription
- `create_setup_intent()` - Setup payment method
- `list_invoices_from_stripe(customer_id)` - Sync invoices from Stripe

### Frontend Components

**Pages:**
1. **BillingPage.tsx** (350+ lines)
   - Current subscription display (tier name, renewal date, price)
   - Usage meter (projects, analyses, storage)
   - Upgrade/Downgrade buttons
   - Payment methods management
   - Invoice history with download links

2. **UpgradeModal.tsx** (250+ lines)
   - Show all tiers with features comparison
   - Select new tier
   - Stripe payment form (Card element)
   - Confirm charges and process payment
   - Success/error handling

3. **InvoiceDetailPage.tsx** (200+ lines)
   - Display invoice details (items, taxes, total)
   - Show breakdown of charges
   - Download as PDF button
   - Retry payment button if failed

4. **UsageProgressCard.tsx** (150+ lines)
   - Display usage meters for each metric
   - Show percentage used
   - Warning when approaching limit
   - Breakdown by project/analysis type

**Redux Slices:**
```typescript
// billingSlice.ts
- currentSubscription: Subscription | null
- usageMetrics: UsageMetrics
- invoices: Invoice[]
- loadingSubscription, loadingUsage, loadingInvoices
- actions: fetchSubscription, upgradeSubscription, fetchUsage, fetchInvoices
```

### Implementation Steps

1. **Week 1: Backend Setup**
   - Create 5 new models (SubscriptionTier, Subscription, UsageRecord, Invoice, InvoiceItem)
   - Create Alembic migration
   - Create repositories for each model
   - Set up Stripe account and API keys

2. **Week 2: Services & Integration**
   - Implement BillingService
   - Implement StripeIntegrationService
   - Add webhook endpoint for Stripe events
   - Create usage tracking middleware

3. **Week 3: Frontend & Testing**
   - Build 4 frontend components
   - Integrate with Redux
   - Set up Stripe SDK (https://js.stripe.com/v3/)
   - Test upgrade/downgrade flows
   - Test payment processing

4. **Week 4: Monitoring**
   - Add usage alerts
   - Create billing admin reports
   - Set up email notifications for invoices
   - Document billing workflows

### Effort Estimate

- Backend: 15 days (models, services, Stripe integration)
- API: 5 days (endpoints, validation, error handling)
- Frontend: 8 days (components, forms, Redux)
- Testing: 2 days (payment flows, edge cases)
- **Total: 30 days**

### Key Dependencies

- Stripe Python library (`pip install stripe`)
- Stripe JavaScript SDK (frontend)
- Email service (for invoice notifications)

---

## 2. Analytics Dashboard (High Priority)

**Status:** Not implemented (0%)
**Priority:** HIGH - Shows ROI to users
**Effort:** 18-22 days
**Dependencies:** Usage tracking from Payment system

### Overview

Provide users and admins with insights into their project data and usage patterns.

**Metrics to Track:**
- Project count, completion rates, duration
- Code quality scores, bug detection
- AI analysis usage and confidence scores
- Customer acquisition and retention
- User engagement (login frequency, feature usage)

### Database Schema

```python
class AnalyticsEvent(BaseModel):
    """Track user actions for analytics"""
    __tablename__ = "analytics_event"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(50))  # page_view, project_created, analysis_run, export_download
    event_data = Column(JSON, default={})  # flexible metadata: {project_id, analysis_type, etc}
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User")


class ProjectMetrics(BaseModel):
    """Aggregate metrics per project"""
    __tablename__ = "project_metrics"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), unique=True, nullable=False)
    total_analyses = Column(Integer, default=0)
    total_bugs_found = Column(Integer, default=0)
    avg_quality_score = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)
    completion_percentage = Column(Float, default=0.0)
    last_analysis_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="metrics")


class UserDashboardMetrics(BaseModel):
    """Aggregate metrics per user"""
    __tablename__ = "user_dashboard_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    total_projects = Column(Integer, default=0)
    total_analyses = Column(Integer, default=0)
    projects_completed = Column(Integer, default=0)
    active_projects = Column(Integer, default=0)
    ai_interactions = Column(Integer, default=0)
    last_activity = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="dashboard_metrics")
```

### API Endpoints

**User Analytics:**
```
GET /api/analytics/dashboard              - User's personal dashboard metrics
GET /api/analytics/projects               - Project-level breakdown
GET /api/analytics/timeline               - Activity timeline (last 30 days)
GET /api/analytics/export                 - Export analytics as CSV
```

**Admin Analytics:**
```
GET /api/admin/analytics/users            - User growth, engagement, churn
GET /api/admin/analytics/platform         - Platform-wide metrics
GET /api/admin/analytics/revenue          - Revenue and subscription metrics
GET /api/admin/analytics/quality          - Code quality trends
```

### Frontend Components

**Pages:**
1. **UserAnalyticsPage.tsx** (400+ lines)
   - Overview cards: Total projects, analyses, completion rate
   - Charts: Project timeline, analysis distribution, quality trends
   - Activity feed: Recent events
   - Export button for data

2. **AdminAnalyticsDashboard.tsx** (500+ lines)
   - Top section: Platform KPIs (users, revenue, engagement)
   - Charts: User growth, subscription mix, feature adoption
   - Tables: Top projects, top customers
   - Filters by date range, subscription tier

3. **ProjectAnalyticsDetail.tsx** (350+ lines)
   - Project name, owner, status
   - Metrics: Analysis count, bug detection, quality score
   - Quality trend chart
   - Agent performance breakdown
   - Identified issues and resolutions

**Chart Library:**
- Use `recharts` for React charts (already popular)
- Install: `npm install recharts`

### Implementation Steps

1. **Week 1: Analytics Infrastructure**
   - Create event tracking middleware
   - Implement event logging in all major user actions
   - Create 3 analytics models
   - Build Alembic migration

2. **Week 2: Aggregation Service**
   - Create AnalyticsService for computing metrics
   - Implement daily aggregation job (celery task)
   - Create repositories for analytics tables
   - Build admin analytics endpoints

3. **Week 3: Frontend**
   - Build UserAnalyticsPage
   - Build AdminAnalyticsDashboard
   - Build ProjectAnalyticsDetail
   - Integrate with Redux
   - Add filters and date ranges

4. **Week 4: Visualization**
   - Add recharts components
   - Create reusable chart components
   - Add export to CSV functionality
   - Test all dashboard views

### Effort Estimate

- Backend: 10 days (models, event tracking, aggregation)
- Services: 5 days (AnalyticsService, aggregation jobs)
- Frontend: 6 days (components, charts, filters)
- Testing: 1 day
- **Total: 22 days**

---

## 3. Search & Filter System (Critical UX)

**Status:** Not implemented (0%)
**Priority:** CRITICAL - Affects all features
**Effort:** 12-15 days
**Dependencies:** None (applicable to all modules)

### Overview

Enable users to quickly find projects, analyses, customers, and reviews.

**Search Scope:**
- Projects (by name, description, owner)
- Code snippets (by language, content)
- Analyses (by type, timestamp, confidence)
- Customer intakes (by customer name, status, date)
- Users (admin panel, by email, name)

### Database Schema Changes

Add full-text search indexes to major tables:

```python
# Modify existing models to add search indexes:

class Project(BaseModel):
    __tablename__ = "projects"
    # ... existing columns ...

    # Add index for search
    __table_args__ = (
        Index('idx_project_search', 'name', 'description', postgresql_using='gin'),  # PostgreSQL
    )


# Create FTS (Full-Text Search) table for better search
class ProjectSearchIndex(BaseModel):
    """Fast full-text search index for projects"""
    __tablename__ = "project_search_index"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), unique=True)
    search_text = Column(String, nullable=False)  # name + description + owner concatenated
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
```

### API Endpoints

```
GET /api/search                              - Global search across all resources
GET /api/search/projects                     - Search projects
GET /api/search/analyses                     - Search analyses
GET /api/search/customers                    - Search customers (PM)
GET /api/search/intakes                      - Search customer intakes
GET /api/search/code                         - Full-code search
GET /api/search/suggestions                  - Auto-complete suggestions
```

**Query Parameters:**
```
?q=search_term              - Search term
&type=project|analysis|...  - Filter by type
&status=active|completed    - Filter by status
&owner_id=xxx               - Filter by owner
&date_from=YYYY-MM-DD       - Date range start
&date_to=YYYY-MM-DD         - Date range end
&limit=20                   - Results per page
&offset=0                   - Pagination offset
```

### Frontend Components

**Components:**
1. **SearchBar.tsx** (200+ lines)
   - Global search input (appears in navigation)
   - Real-time suggestions/autocomplete
   - Search scope selector (Projects, Code, Analyses, etc.)
   - Keyboard shortcuts (Cmd+K)

2. **SearchResults.tsx** (300+ lines)
   - Display results grouped by type
   - Highlight matching terms
   - Show metadata (date, owner, status)
   - Links to full details

3. **AdvancedFilter.tsx** (250+ lines)
   - Collapsible advanced filters
   - Date range picker
   - Status/type multi-select
   - Owner/creator filter
   - Save search filters

4. **SearchPage.tsx** (400+ lines)
   - Full-page search interface
   - Search history
   - Popular searches
   - Filter sidebar
   - Results list/grid toggle

**Redux:**
```typescript
// searchSlice.ts
- searchQuery: string
- results: SearchResult[]
- filters: FilterConfig
- searchHistory: string[]
- loadingSearch: boolean
- actions: performSearch, setQuery, setFilters, saveSearch
```

### Implementation Steps

1. **Week 1: Backend Search**
   - Create search indexes on major tables
   - Implement SearchService with basic text search
   - Build search endpoints with pagination
   - Add filtering logic

2. **Week 2: Advanced Search**
   - Add autocomplete/suggestions endpoint
   - Implement search highlighting
   - Add search history tracking
   - Create admin search tools

3. **Week 3: Frontend**
   - Build SearchBar component
   - Build SearchResults component
   - Build AdvancedFilter component
   - Build SearchPage component
   - Integrate with navigation

4. **Week 4: Polish**
   - Add keyboard shortcuts
   - Implement search history
   - Add saved searches
   - Test across all sections

### Effort Estimate

- Backend: 7 days (indexes, search logic, endpoints)
- Frontend: 6 days (components, UX, integration)
- Testing: 2 days
- **Total: 15 days**

---

## 4. Admin Panel (Operations Critical)

**Status:** Not implemented (0%)
**Priority:** HIGH - Required for operations
**Effort:** 15-18 days
**Dependencies:** Auth system (already exists)

### Overview

Provide operations team with tools to manage users, monitor system, and handle support.

**Admin Capabilities:**
- User management (create, suspend, delete, reset password)
- View detailed usage metrics
- Manage subscription tiers and pricing
- View and respond to support tickets
- System monitoring (uptime, API health, error logs)
- Bulk operations (data export, user import)

### Database Schema

```python
class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"        # Full access
    BILLING_ADMIN = "billing_admin"    # Subscriptions and invoices
    SUPPORT_ADMIN = "support_admin"    # User support, tickets
    ANALYTICS_ADMIN = "analytics_admin" # Reports and metrics

class AdminUser(BaseModel):
    """Admin user with elevated permissions"""
    __tablename__ = "admin_user"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    role = Column(SQLEnum(AdminRole), default=AdminRole.SUPPORT_ADMIN)
    permissions = Column(JSON, default={})  # Additional granular permissions
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(String(36), ForeignKey("admin_user.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    user = relationship("User")
    granted_by_admin = relationship("AdminUser", remote_side=[id])


class SupportTicket(BaseModel):
    """Support/issue tickets from users"""
    __tablename__ = "support_ticket"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20))  # low, medium, high, critical
    status = Column(String(50), default='open')  # open, in_progress, resolved, closed
    assigned_to = Column(String(36), ForeignKey("admin_user.id"))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    user = relationship("User")
    assigned_admin = relationship("AdminUser")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")


class TicketMessage(BaseModel):
    """Messages/responses on support tickets"""
    __tablename__ = "ticket_message"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("support_ticket.id"), nullable=False)
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("SupportTicket", back_populates="messages")
    sender = relationship("User")


class SystemLog(BaseModel):
    """System events and errors for monitoring"""
    __tablename__ = "system_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    level = Column(String(20))  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text)
    component = Column(String(100))  # api, database, auth, scheduler, etc.
    context = Column(JSON, default={})  # Additional context data
    stack_trace = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
```

### API Endpoints

**User Management:**
```
GET    /api/admin/users                      - List all users with filters
GET    /api/admin/users/{id}                 - User details and history
POST   /api/admin/users/{id}/suspend         - Suspend user account
POST   /api/admin/users/{id}/reactivate      - Reactivate user
POST   /api/admin/users/{id}/reset-password  - Send password reset
DELETE /api/admin/users/{id}                 - Delete user account
```

**Subscription Management:**
```
GET    /api/admin/subscriptions              - All subscriptions with status
POST   /api/admin/subscriptions/tiers        - Manage pricing tiers
POST   /api/admin/subscriptions/{id}/upgrade - Force upgrade (support)
POST   /api/admin/subscriptions/{id}/credit  - Apply account credit
```

**Support:**
```
GET    /api/admin/support/tickets            - List support tickets
POST   /api/admin/support/tickets            - Create ticket
POST   /api/admin/support/tickets/{id}/assign - Assign to admin
POST   /api/admin/support/tickets/{id}/resolve - Mark resolved
GET    /api/admin/support/tickets/{id}/messages - Ticket conversation
```

**System:**
```
GET    /api/admin/system/health              - System health status
GET    /api/admin/system/logs                - Recent system logs
GET    /api/admin/system/performance         - Performance metrics
POST   /api/admin/system/maintenance         - Start maintenance mode
```

### Frontend Components

**Pages:**
1. **AdminDashboard.tsx** (400+ lines)
   - System health status
   - Key metrics (users, subscriptions, revenue)
   - Recent activity
   - Alerts and issues
   - Quick actions

2. **UserManagementPage.tsx** (450+ lines)
   - User table with columns: email, name, status, created_at, actions
   - Search and filters
   - Bulk actions (suspend, delete, export)
   - User detail modal with history
   - Action buttons (suspend, reset password, view projects)

3. **SubscriptionManagementPage.tsx** (350+ lines)
   - List all subscriptions grouped by tier
   - Show churn/active metrics
   - Tier configuration form
   - Manual intervention tools (apply credit, upgrade/downgrade)

4. **SupportTicketPage.tsx** (400+ lines)
   - Ticket list with status, priority, assigned admin
   - Ticket detail view with full conversation
   - Create/edit ticket form
   - Assign and update status
   - Canned responses template

5. **SystemMonitoringPage.tsx** (350+ lines)
   - API uptime/health status
   - Database performance metrics
   - Error rate chart
   - Recent system logs
   - Alert thresholds configuration

**Sidebar Menu:**
- Dashboard
- Users
- Subscriptions
- Support Tickets
- System Monitoring
- Logs & Audit Trail
- Settings

### Implementation Steps

1. **Week 1: Models & Auth**
   - Create 4 new models (AdminUser, SupportTicket, TicketMessage, SystemLog)
   - Create Alembic migration
   - Implement admin role middleware/decorator
   - Create audit logging

2. **Week 2: Backend**
   - Create repositories for admin tables
   - Implement AdminService (user management, ticket handling)
   - Build all admin API endpoints
   - Add system monitoring endpoints

3. **Week 3: Frontend**
   - Build 5 admin pages
   - Create admin navigation sidebar
   - Implement user list/detail flows
   - Build support ticket interface
   - Add system monitoring views

4. **Week 4: Polish & Security**
   - Add permission checks on all endpoints
   - Implement audit logging
   - Add rate limiting for admin actions
   - Test all admin workflows

### Effort Estimate

- Backend: 9 days (models, services, endpoints)
- Frontend: 7 days (pages, components, integration)
- Security: 1 day (permissions, audit logging)
- Testing: 1 day
- **Total: 18 days**

---

## 5. Error Tracking Integration (Production Critical)

**Status:** Not implemented (0%)
**Priority:** CRITICAL - Needed before production
**Effort:** 8-10 days
**Dependencies:** None (but critical for production)

### Overview

Integrate error tracking service (Sentry) to monitor production errors and get alerted to issues.

**Goals:**
- Catch all unhandled exceptions
- Track error frequency and patterns
- Group similar errors
- Alert team on critical errors
- Provide stack traces and context
- Monitor performance metrics

### Setup

**Sentry Integration:**
1. Create Sentry account
2. Create project for Socrates
3. Get DSN (Data Source Name)
4. Install SDK: `pip install sentry-sdk`

### Backend Implementation

**In `main.py`:**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
        LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
    ],
    traces_sample_rate=0.1,  # 10% of transactions for performance tracking
    environment=os.getenv("ENVIRONMENT", "development"),
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Sentry automatically captures this
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

**Error Context:**
```python
from sentry_sdk import set_context, capture_exception

# In route handlers:
@router.post("/api/projects")
async def create_project(request: CreateProjectRequest, services = Depends()):
    try:
        project = await services.project_service.create(request)
        # Set context for error tracking
        set_context("project", {
            "id": project.id,
            "name": project.name,
            "owner_id": project.owner_id
        })
        return project
    except Exception as e:
        capture_exception(e)
        raise
```

### Frontend Implementation

**Install:**
```bash
npm install @sentry/react @sentry/tracing
```

**In `main.tsx`:**

```typescript
import * as Sentry from "@sentry/react";
import { BrowserTracing } from "@sentry/tracing";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [
    new BrowserTracing({
      routingInstrumentation: Sentry.reactRouterV6Instrumentation(
        window.history
      ),
    }),
    new Sentry.Replay({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],
  tracesSampleRate: 0.1,
  environment: import.meta.env.MODE,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});

export const App = Sentry.withProfiler(AppComponent);
```

### Error Boundaries

**ErrorBoundary Component (already exists):**
```typescript
class ErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Capture to Sentry
    Sentry.captureException(error, { contexts: { react: errorInfo } });

    // Log locally
    console.error("React Error:", error, errorInfo);

    this.setState({ hasError: true, error });
  }

  render() {
    if (this.state.hasError) {
      return <ErrorPage error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

### Monitoring Dashboard

**Sentry provides:**
- Error dashboard with frequencies
- Performance metrics
- Release tracking
- Team alerts and notifications
- Custom dashboards
- Integration with Slack/email alerts

### Implementation Steps

1. **Day 1: Sentry Setup**
   - Create Sentry account and project
   - Get DSN
   - Add to .env.example

2. **Day 2: Backend Integration**
   - Install Sentry SDK
   - Configure in main.py
   - Add global exception handler
   - Add error context helpers

3. **Day 3: Frontend Integration**
   - Install Sentry React SDK
   - Configure in main.tsx
   - Wrap app with Sentry
   - Update ErrorBoundary

4. **Day 4: Monitoring & Testing**
   - Set up Sentry alerts
   - Configure team notifications
   - Test error tracking with sample errors
   - Verify stack traces appear in Sentry

5. **Day 5: Documentation**
   - Document error tracking workflow
   - Create runbook for handling errors
   - Set up on-call rotation

### Effort Estimate

- Setup: 2 days
- Backend integration: 2 days
- Frontend integration: 2 days
- Testing: 2 days
- **Total: 8 days**

### Key Configuration

**.env variables needed:**
```
SENTRY_DSN=https://xxxxx@sentry.io/project_id
SENTRY_ENVIRONMENT=production|staging|development
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_REPLAY_SAMPLE_RATE=0.1
```

---

## Implementation Timeline

### Phase 4A: Foundation (Weeks 1-2)
- **Week 1:** Payment system backend (models, services)
- **Week 2:** Analytics infrastructure (models, event tracking)

### Phase 4B: Core Features (Weeks 3-4)
- **Week 3:** Payment frontend, search backend
- **Week 4:** Analytics frontend, admin panel setup

### Phase 4C: Operations (Weeks 5-6)
- **Week 5:** Admin panel completion, search polish
- **Week 6:** Error tracking integration, testing

**Total Duration:** 4-5 weeks
**Recommended Start:** After customer intake feature (Phase 3) is complete

---

## Priority Ranking

1. **Payment System (CRITICAL)** - Blocks monetization
2. **Error Tracking (CRITICAL)** - Required before production
3. **Admin Panel (HIGH)** - Required for operations team
4. **Search System (CRITICAL)** - Essential UX feature
5. **Analytics (HIGH)** - Shows value to users

---

## Success Metrics

Once Phase 4 is complete:

✅ **Monetization Ready**
- Can accept customer payments
- Track and bill usage
- Generate invoices

✅ **Production Ready**
- Error tracking in place
- System monitoring enabled
- Admin team can manage platform

✅ **User Experience Complete**
- Users can search across platform
- Users see their analytics/ROI
- Customers have full self-service portal

✅ **Operations Capable**
- Admin panel for user management
- Support ticket system
- Billing and subscription management

---

## Next Steps

1. **Review this plan** - Confirm priorities and approach
2. **Estimate capacity** - Determine team size and timeline
3. **Create detailed tickets** - Break down into smaller tasks
4. **Begin Phase 4A** - Start with payment system
5. **Set up monitoring** - Prepare infrastructure

---

**Document Status:** Complete implementation blueprint ready for execution
**Last Updated:** October 24, 2025
