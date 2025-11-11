# Phase 4 Critical Features - Plan Review & Analysis

**Review Date:** October 24, 2025
**Status:** Ready for Implementation with Recommended Adjustments
**Overall Assessment:** SOLID FOUNDATION WITH OPTIMIZATION OPPORTUNITIES

---

## Executive Summary

The Phase 4 plan is comprehensive and addresses all critical blockers for production launch. However, **several adjustments are recommended** to optimize timeline, reduce complexity, and mitigate risks.

**Key Findings:**
- ✅ All 5 features are well-designed with clear specifications
- ⚠️ Timeline estimates may be optimistic (~20% padding recommended)
- ⚠️ Some dependencies are not explicit enough
- 🔴 Analytics depends on Payment system event tracking (tight coupling)
- 🟡 Search implementation should start earlier (affects all features)
- ✅ Error Tracking is well-scoped and ready to implement immediately

**Recommendation:** Adjust implementation order and add risk mitigations

---

## 1. Payment & Billing System Review

### Strengths
✅ **Complete architecture:** 5 models cover all billing scenarios
✅ **Proper data types:** Using cents instead of floats (avoids precision issues)
✅ **Comprehensive Stripe integration:** Covers subscription lifecycle and webhooks
✅ **Good test coverage scope:** Mentions upgrade/downgrade/overage flows
✅ **Frontend includes all necessary flows:** Payment methods, invoices, usage tracking

### Issues & Concerns

#### Issue 1: Webhook Security [MEDIUM]
**Problem:** Stripe webhook endpoint mentioned but lacks detail
**Impact:** Unvalidated webhooks could corrupt billing data
**Mitigation:**
- Add `stripe-python` signature verification
- Implement webhook idempotency (webhook can be called multiple times)
- Add webhook event logging before processing

**Code Addition Needed:**
```python
# In webhook handler:
from stripe.error import SignatureVerificationError

@router.post("/api/billing/stripe-webhook")
async def stripe_webhook(request: Request, services: ServiceContainer = Depends()):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Log before processing
    log_webhook_event(event)

    # Check idempotency
    if webhook_already_processed(event['id']):
        return {"status": "already_processed"}

    # Process event
    await services.billing_service.process_stripe_webhook(event)
    return {"status": "success"}
```

---

#### Issue 2: Subscription Tier Updates [MEDIUM]
**Problem:** Plan doesn't cover how to update existing subscription tiers (pricing changes)
**Impact:** Can't adjust pricing without affecting historical data
**Recommendation:** Add versioning or audit trail

**Solution:**
```python
class SubscriptionTierVersion(BaseModel):
    """Track pricing history"""
    __tablename__ = "subscription_tier_version"

    id = Column(String(36), primary_key=True)
    tier_id = Column(String(36), ForeignKey("subscription_tier.id"))
    monthly_price = Column(Float)
    features = Column(JSON)
    valid_from = Column(DateTime)
    valid_to = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

#### Issue 3: Trial Period Not Defined [HIGH]
**Problem:** SubscriptionStatus includes TRIAL but trial logic not described
**Impact:** Unclear how trial subscriptions should be handled
**Recommendation:** Define trial workflow explicitly

**Add to Plan:**
```
Trial Subscription Flow:
1. New users get 14-day free trial automatically (TRIAL status)
2. After 14 days, subscription must be upgraded or ends
3. Trial users have full feature access
4. No payment method required for trial
5. Upgrade from trial shows prorated charges
```

---

#### Issue 4: Proration Logic Missing [MEDIUM]
**Problem:** Upgrading/downgrading mid-cycle needs prorated billing
**Impact:** Incorrect charges for plan changes
**Recommendation:** Add to BillingService with clear algorithm

**Add to Plan:**
```python
def calculate_proration(
    current_plan_price: float,
    new_plan_price: float,
    days_used: int,
    billing_cycle_days: int = 30
) -> float:
    """Calculate credit/debit for mid-cycle change"""
    daily_rate_current = current_plan_price / billing_cycle_days
    daily_rate_new = new_plan_price / billing_cycle_days
    days_remaining = billing_cycle_days - days_used

    credit = daily_rate_current * days_remaining
    charge = daily_rate_new * days_remaining

    return charge - credit  # Positive = charge, Negative = credit
```

---

### Questions to Address

1. **How are failed payments handled?**
   - Retry schedule?
   - When is account suspended?
   - Grace period?

2. **What happens at subscription cancellation?**
   - Refund policy?
   - Data retention?
   - Can customer reactivate?

3. **Invoice delivery**
   - Email immediately or daily batch?
   - PDF generation service?
   - Tax calculation (sales tax per state)?

---

### Effort Estimate Assessment
**Stated:** 30 days
**Recommended:** 35-40 days
**Rationale:**
- Webhook testing is complex (~3 days)
- Tax calculation adds complexity (~2 days)
- Proration logic testing (~2 days)
- Retry logic and edge cases (~3 days)

---

## 2. Analytics Dashboard Review

### Strengths
✅ **Good event tracking approach:** Flexible event_data JSON
✅ **3-layer metrics:** Events → Aggregate → Dashboard (proper separation)
✅ **Daily aggregation job:** Good for performance vs real-time trade-off
✅ **Admin analytics included:** Platform-wide metrics important for ops

### Critical Issues

#### Issue 1: Dependency on Payment System [HIGH]
**Problem:** Analytics depends on event tracking from Payment system
**Current Plan:** Events added in Week 1 (Payment), Analytics infrastructure Week 2
**Impact:** Tight coupling creates sequential dependency
**Risk:** If Payment delays, Analytics also delays

**Recommendation:**
- Analytics event infrastructure should be independent
- Define standard event schema immediately
- Payment system plugs into standard event system

**New Architecture:**
```python
# Create in Week 1, independent of Payment:
class EventSchema(BaseModel):
    """Standard event interface"""
    event_type: str  # page_view, action_completed, etc
    user_id: str
    resource_type: str  # project, analysis, subscription, etc
    resource_id: str
    metadata: Dict
    timestamp: datetime

# Analytics just consumes these standard events
# Payment system emits standard events
# Decouples the two systems
```

---

#### Issue 2: Aggregation Job Infrastructure [MEDIUM]
**Problem:** Plan mentions "celery task" but celery not in tech stack
**Current Stack:** FastAPI (no Celery/background jobs defined)
**Impact:** Unclear how to implement daily aggregation

**Recommendation:**
```python
# Option A: Use APScheduler (lightweight, built into FastAPI)
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=1)  # Run 1 AM daily
async def aggregate_daily_metrics():
    service = AnalyticsService(db_session)
    await service.aggregate_all_metrics(date.today() - timedelta(days=1))

# Start in main.py
scheduler.start()

# Option B: Use GitHub Actions for scheduled jobs (serverless)
# .github/workflows/analytics-aggregation.yml
name: Daily Analytics Aggregation
on:
  schedule:
    - cron: '0 1 * * *'
jobs:
  aggregate:
    runs-on: ubuntu-latest
    steps:
      - run: curl -X POST https://socrates.com/api/admin/analytics/aggregate
```

---

#### Issue 3: Real-time Analytics Missing [MEDIUM]
**Problem:** Daily aggregation means 24-hour delay on user dashboard
**User Experience:** Users see stale data (completed analysis not reflected immediately)
**Recommendation:**
- Aggregate daily for analytics
- Show real-time counts for user dashboard

**Solution:**
```python
# User Dashboard (real-time)
def get_user_dashboard(user_id: str):
    return {
        "total_projects": count_projects(user_id),  # Real query
        "total_analyses": count_analyses(user_id),   # Real query
        "quality_score": avg_quality_score(user_id)  # Real query
    }

# Analytics Dashboard (daily snapshot)
def get_user_analytics(user_id: str):
    return UserDashboardMetrics.query.filter(
        user_id=user_id
    ).order_by(date DESC).first()
```

---

#### Issue 4: Export Functionality Undefined [LOW]
**Problem:** "Export as CSV" mentioned but not specified
**Recommendation:** Add explicit CSV schema

```python
# Implement using pandas for CSV export
def export_analytics_to_csv(user_id: str) -> bytes:
    metrics = get_user_analytics(user_id)
    events = AnalyticsEvent.query.filter(user_id=user_id).all()

    df = pd.DataFrame([
        {
            'Date': event.timestamp,
            'Event Type': event.event_type,
            'Resource': event.resource_type,
            'Value': event.metadata
        }
        for event in events
    ])

    return df.to_csv(index=False).encode()
```

---

### Questions to Address

1. **What analytics are user-facing vs admin-only?**
   - Users see: Projects, analyses, quality trends
   - Admins see: Revenue, churn, feature adoption

2. **Retention policy?**
   - Keep detailed events forever?
   - Archive after X days?
   - GDPR right-to-be-forgotten implications?

3. **Custom date ranges?**
   - Only last 30/90/365 days?
   - Custom ranges for exports?
   - Compare periods (month-over-month)?

---

### Effort Estimate Assessment
**Stated:** 22 days
**Recommended:** 25-28 days
**Rationale:**
- Aggregation job infrastructure (~2 days)
- Real-time vs historical decision (~1 day)
- CSV export with complex data (~1 day)
- Charts with date range filtering (~2 days)

---

## 3. Search & Filter System Review

### Strengths
✅ **Comprehensive scope:** Covers projects, code, analyses, customers, users
✅ **Good UX features:** Autocomplete, keyboard shortcuts, saved searches
✅ **Pagination included:** Important for large result sets
✅ **Multiple search types:** Global and per-resource searches

### Critical Issue: Timing [HIGH]

#### Issue 1: Search Should Start Immediately [CRITICAL]
**Current Plan:** Search starts Week 3 (after Payment Week 1-2, Analytics Week 2-3)
**Problem:** Every other feature creates new data that should be searchable
**Impact:**
- Payment system built without search (Week 1-2)
- Analytics built without search (Week 2-3)
- Features will need retrofitting for search

**Recommendation: Start Search in Week 1 (parallel with Payment)**
- Search indexes created early
- Payment tables indexed from creation
- Analytics data indexed from creation
- No retrofitting needed

**Revised Timeline:**
```
Week 1 Parallel Work:
├─ Payment system (models, services)
├─ Analytics infrastructure (event schema)
└─ Search (indexes, SearchService, endpoints)

Week 2:
├─ Payment frontend
├─ Analytics aggregation
└─ Search UI components (SearchBar, Results)

Week 3:
├─ Admin panel (models, services)
├─ Analytics frontend dashboards
└─ Search polish (history, saved searches)

Week 4:
├─ Admin panel frontend
├─ Error tracking
└─ Testing & integration
```

---

#### Issue 2: SQLite Full-Text Search Limitations [MEDIUM]
**Problem:** Plan references PostgreSQL `postgresql_using='gin'` syntax
**Actual:** Project uses SQLite (from CLAUDE.md)
**Impact:** FTS implementation differs between databases

**SQLite Full-Text Search Solution:**
```python
# Use SQLite's built-in FTS5
from sqlalchemy import text

class ProjectSearchIndex(BaseModel):
    __tablename__ = "project_search_index"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), unique=True)
    search_text = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Create FTS5 virtual table separately (in migration)
def create_fts_table():
    db.execute(text("""
    CREATE VIRTUAL TABLE project_fts USING fts5(
        project_id,
        search_text,
        content=project_search_index,
        content_rowid=id
    )
    """))

# Query using FTS5
def search_projects(query: str, limit: int = 20):
    return db.execute(text("""
    SELECT p.* FROM projects p
    INNER JOIN project_fts ON project_fts.project_id = p.id
    WHERE project_fts MATCH :query
    LIMIT :limit
    """), {"query": query, "limit": limit})
```

---

#### Issue 3: Autocomplete Performance [MEDIUM]
**Problem:** Autocomplete needs to be fast (~100ms max)
**Risk:** Loading all suggestions could be slow with large datasets
**Recommendation:** Use prefix-based caching

```python
# Cache popular search terms
class SearchSuggestionCache:
    def __init__(self):
        self.cache = {}  # "proj" -> [project_names...]

    async def get_suggestions(self, prefix: str, limit: int = 10):
        if prefix in self.cache:
            return self.cache[prefix][:limit]

        # Query database
        suggestions = db.query(Project).filter(
            Project.name.ilike(f"{prefix}%")
        ).limit(limit).all()

        # Cache result
        self.cache[prefix] = [p.name for p in suggestions]

        return suggestions
```

---

#### Issue 4: Search Permissions [MEDIUM]
**Problem:** Plan doesn't address search permission filtering
**Risk:** Users could search for private projects of other users
**Recommendation:** Add permission checks

```python
async def search_projects(query: str, user_id: str):
    # Only return projects user has access to
    results = db.query(Project).filter(
        Project.name.ilike(f"%{query}%"),
        or_(
            Project.owner_id == user_id,  # User's own projects
            Project.shared_with.contains([user_id])  # Shared projects
        )
    ).all()

    return results
```

---

### Questions to Address

1. **Case sensitivity?**
   - "Django" vs "django" - should both match?
   - Recommendation: Case-insensitive search

2. **Fuzzy matching?**
   - Typo tolerance ("projct" matches "project")?
   - Can implement with Levenshtein distance

3. **Search analytics?**
   - Track popular searches?
   - Track zero-result searches?
   - Recommendation: Yes - helps improve UX

---

### Effort Estimate Assessment
**Stated:** 15 days
**Current Estimate if starts Week 3:** 15-18 days
**Recommended (Week 1 start):** 12-14 days (parallelized work)
**Rationale:**
- Earlier start allows better parallelization
- FTS5 migration adds ~1 day but could be earlier
- Autocomplete optimization ~1 day
- Permission filtering ~1 day

---

## 4. Admin Panel Review

### Strengths
✅ **Comprehensive scope:** User management, subscriptions, support, monitoring
✅ **Role-based access:** 4 roles with clear separation
✅ **Support system included:** Important operational feature
✅ **System monitoring:** Health checks and logging included

### Issues & Concerns

#### Issue 1: Role-Based Access Control (RBAC) [HIGH]
**Problem:** Models define roles but plan lacks RBAC implementation details
**Impact:** All 5 pages could expose sensitive data to wrong roles
**Recommendation:** Define explicit permissions matrix

**Permission Matrix Needed:**
```
                | Super | Billing | Support | Analytics
User List       |  RW   |    -    |   R     |     -
Subscriptions   |  RW   |   RW    |    -    |     -
Support Tickets |  RW   |    -    |   RW    |     -
Analytics       |  RW   |    R    |    -    |    RW
System Logs     |  RW   |    -    |    R    |     -
```

**Implementation:**
```python
# Middleware to check permissions
@app.middleware("http")
async def check_admin_permission(request: Request, call_next):
    user = get_current_user(request)
    admin = AdminUser.get_by_user_id(user.id)

    if not admin:
        raise HTTPException(status_code=403, detail="Not admin")

    # Check if admin has permission for this endpoint
    required_perm = get_required_permission(request.url.path)
    if not admin.has_permission(required_perm):
        raise HTTPException(status_code=403, detail="Insufficient permission")

    return await call_next(request)
```

---

#### Issue 2: Audit Logging [MEDIUM]
**Problem:** Plan mentions "implement audit logging" but doesn't specify what to log
**Impact:** Can't trace who changed what and when
**Recommendation:** Add AuditLog model

```python
class AuditLog(BaseModel):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True)
    admin_id = Column(String(36), ForeignKey("admin_user.id"))
    action = Column(String(50))  # suspend_user, upgrade_subscription, etc
    resource_type = Column(String(50))  # user, subscription, ticket
    resource_id = Column(String(36))
    old_value = Column(JSON)  # Before state
    new_value = Column(JSON)  # After state
    reason = Column(Text)  # Why did admin do this?
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

#### Issue 3: Support Ticket Workflow [MEDIUM]
**Problem:** Ticket model exists but workflow not clearly defined
**Impact:** Unclear how tickets move through states
**Recommendation:** Define state machine

```
open → in_progress → resolved → closed
  ↑_______________________↓
   (can reopen if needed)

State Rules:
- open: Initial state, awaiting assignment
- in_progress: Assigned to admin, being worked on
- resolved: Solution provided, awaiting user confirmation
- closed: Issue resolved and confirmed (or abandoned)
```

---

#### Issue 4: User Suspension Logic Missing [MEDIUM]
**Problem:** Plan mentions "suspend user" but business logic undefined
**Impact:** Unclear what happens to suspended user's data/projects
**Recommendation:** Define suspension behavior

```python
async def suspend_user(user_id: str, reason: str):
    user = User.get(user_id)
    user.status = UserStatus.SUSPENDED
    user.suspension_reason = reason
    user.suspended_at = datetime.utcnow()

    # What happens to their projects?
    projects = Project.get_by_owner(user_id)
    for project in projects:
        project.is_archived = True  # Archive but keep
        # Don't delete - GDPR compliance

    # Notify user
    send_email(user.email, "Account Suspended", reason)

    db.commit()
```

---

### Questions to Address

1. **Admin action notifications?**
   - Should users be notified when suspended?
   - When password is reset?
   - Recommendation: Yes, for security transparency

2. **Bulk operations?**
   - Bulk suspend users by subscription tier?
   - Bulk export data?
   - Recommendation: Yes for operations efficiency

3. **Admin login audit trail?**
   - Log every admin login for security?
   - Track admin password changes?
   - Recommendation: Yes for compliance

---

### Effort Estimate Assessment
**Stated:** 18 days
**Recommended:** 22-25 days
**Rationale:**
- RBAC implementation not trivial (~3 days)
- Audit logging needs thought-through schema (~1 day)
- Support ticket workflow implementation (~2 days)
- User suspension edge cases (~1 day)
- Testing admin flows thoroughly (~2 days)

---

## 5. Error Tracking Integration Review

### Strengths
✅ **Sentry is right choice:** Industry standard, mature service
✅ **Good scope:** Backend, frontend, error boundaries
✅ **Performance monitoring included:** Traces and replays
✅ **Realistic timeline:** 8 days is reasonable

### Minor Issues

#### Issue 1: Sensitive Data Masking [MEDIUM]
**Problem:** Sentry captures all data by default (could include passwords, tokens)
**Impact:** Security risk if sensitive data in errors
**Recommendation:** Configure Sentry to scrub sensitive fields

```python
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[...],
    before_send=scrub_sensitive_data,  # Add filter function
)

def scrub_sensitive_data(event, hint):
    """Remove sensitive fields from errors"""
    if 'request' in event:
        if 'data' in event['request']:
            # Scrub passwords, tokens, etc
            event['request']['data'] = {
                k: '***REDACTED***' if k in ['password', 'token'] else v
                for k, v in event['request']['data'].items()
            }
    return event
```

---

#### Issue 2: Release Tracking [LOW]
**Problem:** Plan doesn't mention Sentry releases feature
**Value:** Helps correlate errors with code changes
**Recommendation:** Add release tracking

```python
sentry_sdk.init(
    dsn=...,
    release=os.getenv('APP_VERSION', 'development'),
    environment=os.getenv('ENVIRONMENT', 'development'),
)

# Tag errors with commit hash for production
@router.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": os.getenv('APP_VERSION'),
        "commit": os.getenv('GIT_COMMIT_HASH'),
        "sentry_enabled": bool(os.getenv('SENTRY_DSN'))
    }
```

---

#### Issue 3: Alert Configuration [MEDIUM]
**Problem:** Plan mentions "set up alerts" but doesn't specify what constitutes an alert
**Recommendation:** Define alert thresholds

```
Alert Triggers:
1. New error type appears (new bug)
2. Error rate > 5% of requests
3. Response time > 2000ms (performance degradation)
4. Database connection pool exhausted
5. API rate limit approached
6. Authentication failures spike (attack attempt)
```

---

### Effort Estimate Assessment
**Stated:** 8 days
**Recommended:** 8-10 days
**Rationale:**
- Sentry setup is straightforward
- +1 day for sensitive data scrubbing
- +1 day for alert configuration and testing

---

## Overall Implementation Order - REVISED

### Recommended Sequence (Parallel Work)

**Week 1 - Foundation (Parallel)**
- [ ] Create core models: Subscription, Analytics, Search, Admin, Audit tables
- [ ] Generate Alembic migration for all new tables
- [ ] Set up Sentry integration (fastest to get value)
- [ ] Create standard EventSchema for analytics

**Week 2 - Backend Services (Sequential)**
- [ ] BillingService + StripeIntegrationService (~4 days)
- [ ] AnalyticsService + AnalyticsAggregationJob (~2 days)
- [ ] SearchService + SearchIndexing (~2 days)

**Week 3 - API Routes**
- [ ] Payment API endpoints (~2 days)
- [ ] Analytics API endpoints (~1 day)
- [ ] Search API endpoints (~1 day)
- [ ] Admin API endpoints (~2 days)

**Week 4 - Frontend (Parallel)**
- [ ] Payment components (BillingPage, UpgradeModal) (~3 days)
- [ ] Analytics dashboards (~3 days)
- [ ] Search UI (SearchBar, Results) (~2 days)

**Week 5 - Frontend Completion**
- [ ] Admin panel pages (~4 days)
- [ ] Integration testing (~1 day)
- [ ] Error tracking validation (~1 day)

**Week 6 - Polish & Testing**
- [ ] End-to-end testing (~2 days)
- [ ] Performance testing (~1 day)
- [ ] Documentation (~1 day)
- [ ] Buffer for issues (~2 days)

**Total: 6 weeks (35-40 developer-days of actual work)**

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Stripe API rate limits in testing | Medium | Low | Use Stripe test mode, implement rate limiting |
| SQLite FTS5 performance issues | Low | Medium | Index strategically, test with real data volume |
| Webhook reliability | Medium | High | Add retry logic, webhook logging, verification |
| Analytics aggregation delays | Medium | Low | Implement real-time counts, cache results |
| Permission system complexity | Medium | High | Define permission matrix early, thorough testing |
| Error tracking data bloat | Low | Medium | Set aggressive cleanup policies, sampling |

---

## Dependencies Between Features

```
Payment System ─────────┐
                        ├──→ Billing Operations Ready
Search System ──────────┘

Analytics ──────────────────→ User ROI Visibility

Admin Panel ────────────────→ Operations Team Ready

Error Tracking ─────────────→ Production Monitoring Ready
```

**Critical Path:**
1. Payment System (blocks billing operations)
2. Analytics (blocks ROI metrics)
3. Admin Panel (blocks ops team)

**Can be Parallel:**
- Search System (doesn't block others)
- Error Tracking (can be added anytime)

---

## Success Criteria

Once Phase 4 is complete, verify:

**Payment System**
- [ ] Can create free trial subscription
- [ ] Can upgrade to paid plan
- [ ] Can downgrade plan with proration
- [ ] Stripe webhooks fire and process correctly
- [ ] Invoices generated and sent
- [ ] Usage limits enforced (overage prevention)

**Analytics**
- [ ] Events tracked for all major user actions
- [ ] Daily aggregation job runs successfully
- [ ] User dashboard shows real-time metrics
- [ ] Admin dashboard shows platform KPIs
- [ ] Export to CSV works correctly

**Search**
- [ ] Global search finds all resource types
- [ ] Autocomplete is fast (<100ms)
- [ ] Permissions filtering works
- [ ] Search history saved
- [ ] Keyboard shortcuts responsive

**Admin Panel**
- [ ] Super admin can access all pages
- [ ] Role-based access controls enforced
- [ ] User suspension removes access
- [ ] Support ticket workflow functional
- [ ] Audit logs track all admin actions

**Error Tracking**
- [ ] Unhandled exceptions captured
- [ ] Stack traces appear in Sentry
- [ ] Performance metrics tracked
- [ ] Alerts configured and tested
- [ ] Team notifications working

---

## Recommended Immediate Actions

1. **This Week**
   - [ ] Create detailed tech spec for Payment system (fill in webhook details, trial logic, tax handling)
   - [ ] Define analytics event schema (standard format all systems emit)
   - [ ] Design RBAC permission matrix for admin panel
   - [ ] Create Sentry project and get DSN

2. **Next Week**
   - [ ] Set up Stripe test account
   - [ ] Create all new database models
   - [ ] Run Alembic migration
   - [ ] Begin Payment service implementation

3. **Before Starting**
   - [ ] Confirm SQLite vs PostgreSQL (plan assumes PostgreSQL FTS)
   - [ ] Clarify tax calculation requirements
   - [ ] Determine email service for invoice delivery
   - [ ] Plan APScheduler setup for daily jobs

---

## Questions Needing Clarification

**For Product Team:**
1. Free trial duration? (14, 30, unlimited days?)
2. Can customers downgrade mid-cycle?
3. Refund policy for annual subscriptions?
4. Minimum contract term?

**For Design Team:**
1. Admin panel theme (dark/light)?
2. Analytics chart types (line, bar, pie)?
3. Search UI placement (top nav, sidebar)?

**For Operations:**
1. Who has admin access initially?
2. Support ticket SLA?
3. Tax handling per state/country?
4. Preferred email service (SendGrid, AWS SES)?

---

## Assumptions Made in Plan

1. **No multi-currency support** - Only USD pricing
2. **No annual subscriptions** - Only monthly
3. **No metered billing** - Only seat-based limits
4. **SQLite production use** - Plan mentioned SQLite but FTS may be slow at scale
5. **Email delivery assumed** - No SMS, in-app notifications only
6. **Single timezone** - All dates in UTC
7. **No PCI hosting** - Using Stripe hosted pages (not custom payment form)

---

## Document Status

**Status:** READY FOR IMPLEMENTATION
**Last Updated:** October 24, 2025
**Confidence Level:** HIGH (85%)
**Recommended Start Date:** Immediately after Phase 3 completion

---

## Sign-off Checklist

Before implementation begins, confirm:

- [ ] All 5 business requirements approved
- [ ] Timeline expectations realistic with team
- [ ] Database (SQLite vs PostgreSQL) confirmed
- [ ] Stripe account ready with test/live keys
- [ ] Sentry account created with DSN
- [ ] Team capacity for 6-week sprint confirmed
- [ ] All clarifying questions answered
- [ ] Risk mitigations acceptable
- [ ] Success criteria understood
