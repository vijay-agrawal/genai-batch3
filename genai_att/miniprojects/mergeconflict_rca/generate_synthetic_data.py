"""
Generate Synthetic Git Commit Data for Telco Billing System
============================================================
Simulates a realistic scenario where:
- A feature branch adds a new "loyalty discount" feature to the billing engine
- Meanwhile, 15 commits land on main from other developers
- One specific commit (#9) changes a shared billing utility function signature
  that breaks the feature branch's loyalty discount calculation on merge
- Another commit (#12) modifies the billing config format, a secondary issue

The synthetic data includes: commit hashes, authors, messages, timestamps,
file diffs, and the merge failure error log.
"""

import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "synthetic_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# FEATURE BRANCH CHANGES (the developer's own work - works fine in isolation)
# ============================================================================

feature_branch_info = {
    "branch_name": "feature/loyalty-discount",
    "developer": "Alice Chen",
    "description": "Adds a loyalty discount engine that applies tiered discounts "
                   "based on customer tenure. Integrates with the billing pipeline "
                   "via calculate_line_item_charge() in billing_utils.py.",
    "branch_off_commit": "a1b2c3d",
    "commits": [
        {
            "hash": "f001aaa",
            "author": "Alice Chen",
            "date": "2025-01-15T09:30:00",
            "message": "feat: add loyalty discount tier configuration",
            "files_changed": ["src/config/loyalty_tiers.yaml", "src/config/__init__.py"],
            "diff": """diff --git a/src/config/loyalty_tiers.yaml b/src/config/loyalty_tiers.yaml
new file mode 100644
--- /dev/null
+++ b/src/config/loyalty_tiers.yaml
@@ -0,0 +1,18 @@
+loyalty_discount_tiers:
+  - name: "Bronze"
+    min_tenure_months: 12
+    max_tenure_months: 24
+    discount_pct: 5.0
+  - name: "Silver"
+    min_tenure_months: 24
+    max_tenure_months: 48
+    discount_pct: 10.0
+  - name: "Gold"
+    min_tenure_months: 48
+    max_tenure_months: 96
+    discount_pct: 15.0
+  - name: "Platinum"
+    min_tenure_months: 96
+    max_tenure_months: null
+    discount_pct: 20.0

diff --git a/src/config/__init__.py b/src/config/__init__.py
--- a/src/config/__init__.py
+++ b/src/config/__init__.py
@@ -1,3 +1,4 @@
 from .billing_config import BillingConfig
 from .plan_config import PlanConfig
+from .loyalty_tiers import LoyaltyTierConfig
"""
        },
        {
            "hash": "f002bbb",
            "author": "Alice Chen",
            "date": "2025-01-16T14:00:00",
            "message": "feat: implement LoyaltyDiscountEngine with tier calculation",
            "files_changed": ["src/billing/loyalty_engine.py", "src/billing/__init__.py"],
            "diff": """diff --git a/src/billing/loyalty_engine.py b/src/billing/loyalty_engine.py
new file mode 100644
--- /dev/null
+++ b/src/billing/loyalty_engine.py
@@ -0,0 +1,45 @@
+from src.config.loyalty_tiers import LoyaltyTierConfig
+from src.billing.billing_utils import calculate_line_item_charge
+from src.models.customer import Customer
+
+class LoyaltyDiscountEngine:
+    def __init__(self, tier_config: LoyaltyTierConfig):
+        self.tiers = tier_config.load_tiers()
+
+    def get_discount_tier(self, customer: Customer) -> dict:
+        tenure = customer.tenure_months
+        for tier in self.tiers:
+            if tier['min_tenure_months'] <= tenure:
+                if tier['max_tenure_months'] is None or tenure < tier['max_tenure_months']:
+                    return tier
+        return None
+
+    def apply_loyalty_discount(self, customer: Customer, line_items: list) -> dict:
+        tier = self.get_discount_tier(customer)
+        if tier is None:
+            return {"discount_applied": False, "total": self._sum_charges(line_items)}
+
+        discounted_items = []
+        for item in line_items:
+            # Uses the shared billing utility to get the base charge
+            base_charge = calculate_line_item_charge(
+                item['plan_code'],
+                item['usage_units'],
+                item['rate_plan']
+            )
+            discount_amount = base_charge * (tier['discount_pct'] / 100.0)
+            final_charge = base_charge - discount_amount
+            discounted_items.append({
+                'item': item['plan_code'],
+                'base_charge': base_charge,
+                'discount_pct': tier['discount_pct'],
+                'discount_amount': round(discount_amount, 2),
+                'final_charge': round(final_charge, 2)
+            })
+
+        return {
+            "discount_applied": True,
+            "tier_name": tier['name'],
+            "items": discounted_items,
+            "total": sum(i['final_charge'] for i in discounted_items)
+        }
+
+    def _sum_charges(self, line_items):
+        return sum(calculate_line_item_charge(i['plan_code'], i['usage_units'], i['rate_plan']) for i in line_items)
"""
        },
        {
            "hash": "f003ccc",
            "author": "Alice Chen",
            "date": "2025-01-17T10:00:00",
            "message": "test: add unit tests for loyalty discount engine",
            "files_changed": ["tests/test_loyalty_engine.py"],
            "diff": """diff --git a/tests/test_loyalty_engine.py b/tests/test_loyalty_engine.py
new file mode 100644
--- /dev/null
+++ b/tests/test_loyalty_engine.py
@@ -0,0 +1,52 @@
+import pytest
+from src.billing.loyalty_engine import LoyaltyDiscountEngine
+from src.billing.billing_utils import calculate_line_item_charge
+
+class TestLoyaltyDiscountEngine:
+    def test_bronze_tier_applied(self, sample_customer_18mo, sample_line_items):
+        engine = LoyaltyDiscountEngine(tier_config)
+        result = engine.apply_loyalty_discount(sample_customer_18mo, sample_line_items)
+        assert result['discount_applied'] is True
+        assert result['tier_name'] == 'Bronze'
+        assert result['items'][0]['discount_pct'] == 5.0
+
+    def test_gold_tier_applied(self, sample_customer_60mo, sample_line_items):
+        engine = LoyaltyDiscountEngine(tier_config)
+        result = engine.apply_loyalty_discount(sample_customer_60mo, sample_line_items)
+        assert result['tier_name'] == 'Gold'
+        assert result['items'][0]['discount_pct'] == 15.0
+
+    def test_no_discount_for_new_customer(self, sample_customer_3mo, sample_line_items):
+        engine = LoyaltyDiscountEngine(tier_config)
+        result = engine.apply_loyalty_discount(sample_customer_3mo, sample_line_items)
+        assert result['discount_applied'] is False
+
+    def test_calculate_line_item_charge_integration(self):
+        # Verifies the shared utility function returns expected charges
+        charge = calculate_line_item_charge('VOICE_UNLIM', 1, 'standard')
+        assert charge == 45.00
+
+    def test_discount_amount_calculation(self, sample_customer_18mo):
+        engine = LoyaltyDiscountEngine(tier_config)
+        line_items = [{'plan_code': 'VOICE_UNLIM', 'usage_units': 1, 'rate_plan': 'standard'}]
+        result = engine.apply_loyalty_discount(sample_customer_18mo, line_items)
+        # 45.00 * 5% = 2.25 discount
+        assert result['items'][0]['discount_amount'] == 2.25
+        assert result['items'][0]['final_charge'] == 42.75
"""
        },
    ]
}

# ============================================================================
# MAIN BRANCH COMMITS (from other developers, between branch-off and merge)
# ============================================================================

main_branch_commits = [
    {
        "hash": "m001abc",
        "author": "Bob Martinez",
        "date": "2025-01-15T11:00:00",
        "message": "fix: correct timezone handling in CDR processing",
        "files_changed": ["src/cdr/cdr_processor.py", "src/cdr/timezone_utils.py"],
        "diff": """diff --git a/src/cdr/cdr_processor.py b/src/cdr/cdr_processor.py
--- a/src/cdr/cdr_processor.py
+++ b/src/cdr/cdr_processor.py
@@ -45,7 +45,7 @@ class CDRProcessor:
     def process_record(self, raw_cdr: dict) -> ProcessedCDR:
-        call_start = datetime.fromisoformat(raw_cdr['start_time'])
+        call_start = parse_cdr_timestamp(raw_cdr['start_time'], raw_cdr.get('timezone', 'UTC'))
         call_end = parse_cdr_timestamp(raw_cdr['end_time'], raw_cdr.get('timezone', 'UTC'))
         duration = (call_end - call_start).total_seconds()

diff --git a/src/cdr/timezone_utils.py b/src/cdr/timezone_utils.py
--- a/src/cdr/timezone_utils.py
+++ b/src/cdr/timezone_utils.py
@@ -1,8 +1,12 @@
+import pytz
 from datetime import datetime

-def parse_cdr_timestamp(ts_string: str, tz: str = 'UTC') -> datetime:
-    dt = datetime.fromisoformat(ts_string)
-    return dt
+def parse_cdr_timestamp(ts_string: str, tz: str = 'UTC') -> datetime:
+    dt = datetime.fromisoformat(ts_string)
+    if dt.tzinfo is None:
+        timezone = pytz.timezone(tz)
+        dt = timezone.localize(dt)
+    return dt
"""
    },
    {
        "hash": "m002def",
        "author": "Carol Wu",
        "date": "2025-01-15T16:30:00",
        "message": "docs: update API documentation for invoice endpoints",
        "files_changed": ["docs/api/invoices.md"],
        "diff": """diff --git a/docs/api/invoices.md b/docs/api/invoices.md
--- a/docs/api/invoices.md
+++ b/docs/api/invoices.md
@@ -12,6 +12,15 @@ Returns a paginated list of invoices for the specified account.
 | account_id | string | required | The customer account ID |
 | start_date | string | optional | Filter by billing period start (ISO 8601) |
 | end_date   | string | optional | Filter by billing period end (ISO 8601) |
+| status     | string | optional | Filter by status: draft, finalized, paid, overdue |
+
+### Response Fields
+| Field | Type | Description |
+|-------|------|-------------|
+| invoice_id | string | Unique invoice identifier |
+| total_amount | decimal | Total invoice amount including taxes |
+| discount_amount | decimal | Total discounts applied |
+| net_amount | decimal | Amount after discounts |
"""
    },
    {
        "hash": "m003ghi",
        "author": "David Park",
        "date": "2025-01-16T09:15:00",
        "message": "feat: add data usage alerts for approaching plan limits",
        "files_changed": ["src/notifications/usage_alerts.py", "src/notifications/templates/usage_warning.html"],
        "diff": """diff --git a/src/notifications/usage_alerts.py b/src/notifications/usage_alerts.py
new file mode 100644
--- /dev/null
+++ b/src/notifications/usage_alerts.py
@@ -0,0 +1,38 @@
+from src.models.customer import Customer
+from src.billing.usage_tracker import UsageTracker
+from src.notifications.email_service import EmailService
+
+class UsageAlertService:
+    THRESHOLDS = [0.75, 0.90, 1.0]
+
+    def __init__(self, usage_tracker: UsageTracker, email_service: EmailService):
+        self.usage_tracker = usage_tracker
+        self.email_service = email_service
+
+    def check_and_notify(self, customer: Customer):
+        for plan in customer.active_plans:
+            usage_pct = self.usage_tracker.get_usage_percentage(
+                customer.account_id, plan.plan_code
+            )
+            for threshold in self.THRESHOLDS:
+                if usage_pct >= threshold and not self._already_notified(customer, plan, threshold):
+                    self._send_alert(customer, plan, usage_pct, threshold)
+
+    def _send_alert(self, customer, plan, usage_pct, threshold):
+        template = 'usage_warning.html'
+        context = {
+            'customer_name': customer.name,
+            'plan_name': plan.display_name,
+            'usage_pct': round(usage_pct * 100, 1),
+            'threshold_pct': round(threshold * 100),
+            'data_remaining_gb': plan.data_limit_gb * (1 - usage_pct)
+        }
+        self.email_service.send_template(customer.email, template, context)
"""
    },
    {
        "hash": "m004jkl",
        "author": "Emily Torres",
        "date": "2025-01-16T11:45:00",
        "message": "refactor: extract payment gateway into separate module",
        "files_changed": ["src/payments/gateway.py", "src/payments/__init__.py", "src/billing/invoice_service.py"],
        "diff": """diff --git a/src/payments/gateway.py b/src/payments/gateway.py
new file mode 100644
--- /dev/null
+++ b/src/payments/gateway.py
@@ -0,0 +1,32 @@
+import logging
+from src.payments.providers import StripeProvider, PayPalProvider
+
+logger = logging.getLogger(__name__)
+
+class PaymentGateway:
+    def __init__(self, provider_name: str = 'stripe'):
+        self.provider = self._init_provider(provider_name)
+
+    def _init_provider(self, name):
+        providers = {'stripe': StripeProvider, 'paypal': PayPalProvider}
+        return providers[name]()
+
+    def charge(self, account_id: str, amount: float, currency: str = 'USD') -> dict:
+        logger.info(f"Charging {amount} {currency} to account {account_id}")
+        return self.provider.process_payment(account_id, amount, currency)

diff --git a/src/billing/invoice_service.py b/src/billing/invoice_service.py
--- a/src/billing/invoice_service.py
+++ b/src/billing/invoice_service.py
@@ -1,6 +1,6 @@
 from src.models.invoice import Invoice
-from src.billing.payment_processor import process_payment
+from src.payments.gateway import PaymentGateway

 class InvoiceService:
-    def finalize_and_charge(self, invoice: Invoice):
-        result = process_payment(invoice.account_id, invoice.total_amount)
+    def finalize_and_charge(self, invoice: Invoice, gateway: PaymentGateway = None):
+        gateway = gateway or PaymentGateway()
+        result = gateway.charge(invoice.account_id, invoice.total_amount)
         return result
"""
    },
    {
        "hash": "m005mno",
        "author": "Frank Liu",
        "date": "2025-01-16T14:30:00",
        "message": "perf: add caching layer for rate plan lookups",
        "files_changed": ["src/billing/rate_plan_cache.py", "src/billing/rating_engine.py"],
        "diff": """diff --git a/src/billing/rate_plan_cache.py b/src/billing/rate_plan_cache.py
new file mode 100644
--- /dev/null
+++ b/src/billing/rate_plan_cache.py
@@ -0,0 +1,25 @@
+import functools
+import time
+
+class RatePlanCache:
+    _cache = {}
+    _ttl = 300  # 5 minutes
+
+    @classmethod
+    def get(cls, plan_code: str):
+        entry = cls._cache.get(plan_code)
+        if entry and (time.time() - entry['ts']) < cls._ttl:
+            return entry['data']
+        return None
+
+    @classmethod
+    def set(cls, plan_code: str, data: dict):
+        cls._cache[plan_code] = {'data': data, 'ts': time.time()}

diff --git a/src/billing/rating_engine.py b/src/billing/rating_engine.py
--- a/src/billing/rating_engine.py
+++ b/src/billing/rating_engine.py
@@ -1,10 +1,16 @@
 from src.models.rate_plan import RatePlan
+from src.billing.rate_plan_cache import RatePlanCache

 class RatingEngine:
     def get_rate_plan(self, plan_code: str) -> RatePlan:
-        return RatePlan.objects.get(code=plan_code)
+        cached = RatePlanCache.get(plan_code)
+        if cached:
+            return RatePlan.from_dict(cached)
+        plan = RatePlan.objects.get(code=plan_code)
+        RatePlanCache.set(plan_code, plan.to_dict())
+        return plan
"""
    },
    {
        "hash": "m006pqr",
        "author": "Grace Kim",
        "date": "2025-01-17T08:00:00",
        "message": "fix: handle null values in customer address validation",
        "files_changed": ["src/models/customer.py", "tests/test_customer.py"],
        "diff": """diff --git a/src/models/customer.py b/src/models/customer.py
--- a/src/models/customer.py
+++ b/src/models/customer.py
@@ -22,8 +22,10 @@ class Customer:
     def validate_address(self):
-        if not self.address.zip_code:
+        if self.address is None:
+            raise ValueError("Customer address is required")
+        if not getattr(self.address, 'zip_code', None):
             raise ValueError("ZIP code is required")
-        if not self.address.state:
+        if not getattr(self.address, 'state', None):
             raise ValueError("State is required")
         return True
"""
    },
    {
        "hash": "m007stu",
        "author": "Henry Zhao",
        "date": "2025-01-17T10:30:00",
        "message": "feat: add international roaming charge calculation",
        "files_changed": ["src/billing/roaming_calculator.py", "src/config/roaming_rates.yaml"],
        "diff": """diff --git a/src/billing/roaming_calculator.py b/src/billing/roaming_calculator.py
new file mode 100644
--- /dev/null
+++ b/src/billing/roaming_calculator.py
@@ -0,0 +1,30 @@
+import yaml
+from src.billing.billing_utils import calculate_line_item_charge
+
+class RoamingCalculator:
+    def __init__(self, rates_file='src/config/roaming_rates.yaml'):
+        with open(rates_file) as f:
+            self.rates = yaml.safe_load(f)
+
+    def calculate_roaming_charge(self, plan_code, usage_units, rate_plan, country_code):
+        base_charge = calculate_line_item_charge(plan_code, usage_units, rate_plan)
+        multiplier = self._get_country_multiplier(country_code)
+        return round(base_charge * multiplier, 2)
+
+    def _get_country_multiplier(self, country_code):
+        for zone in self.rates['roaming_zones']:
+            if country_code in zone['countries']:
+                return zone['multiplier']
+        return self.rates['default_multiplier']
"""
    },
    {
        "hash": "m008vwx",
        "author": "Irene Santos",
        "date": "2025-01-17T13:00:00",
        "message": "test: add integration tests for billing cycle workflow",
        "files_changed": ["tests/integration/test_billing_cycle.py"],
        "diff": """diff --git a/tests/integration/test_billing_cycle.py b/tests/integration/test_billing_cycle.py
new file mode 100644
--- /dev/null
+++ b/tests/integration/test_billing_cycle.py
@@ -0,0 +1,35 @@
+import pytest
+from src.billing.billing_cycle import BillingCycleManager
+from src.billing.billing_utils import calculate_line_item_charge
+
+class TestBillingCycleWorkflow:
+    def test_full_billing_cycle(self, test_account):
+        manager = BillingCycleManager()
+        cycle = manager.open_cycle(test_account)
+
+        # Add usage records
+        manager.record_usage(cycle, 'VOICE_UNLIM', 1, 'standard')
+        manager.record_usage(cycle, 'DATA_5GB', 4.2, 'standard')
+
+        # Close and generate invoice
+        invoice = manager.close_cycle(cycle)
+        assert invoice.total_amount > 0
+        assert len(invoice.line_items) == 2
+
+    def test_proration_on_mid_cycle_change(self, test_account):
+        manager = BillingCycleManager()
+        cycle = manager.open_cycle(test_account)
+
+        # Simulate mid-cycle plan change
+        manager.record_usage(cycle, 'VOICE_UNLIM', 1, 'standard')
+        manager.apply_plan_change(cycle, 'VOICE_UNLIM', 'VOICE_PREM', day_of_cycle=15)
+
+        invoice = manager.close_cycle(cycle)
+        # Should have prorated charges
+        assert len(invoice.line_items) == 2  # old plan + new plan prorated
"""
    },
    # *** THIS IS THE GUILTY COMMIT (#9) ***
    # Changes the signature of calculate_line_item_charge() - the shared utility
    # that Alice's feature branch depends on
    {
        "hash": "m009yza",
        "author": "Jake Thompson",
        "date": "2025-01-17T15:45:00",
        "message": "refactor: update billing utils for multi-currency support",
        "files_changed": ["src/billing/billing_utils.py", "src/billing/currency_converter.py"],
        "diff": """diff --git a/src/billing/billing_utils.py b/src/billing/billing_utils.py
--- a/src/billing/billing_utils.py
+++ b/src/billing/billing_utils.py
@@ -1,5 +1,6 @@
 from src.models.rate_plan import RatePlan
 from src.billing.rate_plan_cache import RatePlanCache
+from src.billing.currency_converter import CurrencyConverter

 PLAN_BASE_RATES = {
     'VOICE_UNLIM': 45.00,
@@ -10,14 +11,20 @@
     'IOT_BASIC': 5.00,
 }

-def calculate_line_item_charge(plan_code: str, usage_units: float, rate_plan: str) -> float:
+def calculate_line_item_charge(plan_code: str, usage_units: float, rate_plan: str,
+                                currency: str = 'USD', billing_region: str = 'US') -> float:
     \"\"\"
     Calculate the charge for a single line item.
+    Now supports multi-currency billing and regional rate adjustments.

     Args:
         plan_code: The plan identifier (e.g., 'VOICE_UNLIM')
         usage_units: Number of usage units consumed
         rate_plan: The rate plan tier ('standard', 'premium', etc.)
+        currency: Target currency code (default: 'USD')
+        billing_region: Billing region for regional rate adjustments (default: 'US')
+
+    Returns:
+        float: Calculated charge in the specified currency
     \"\"\"
     base_rate = PLAN_BASE_RATES.get(plan_code, 0.0)

@@ -28,4 +35,10 @@
         rate_multiplier = 1.0

-    return round(base_rate * usage_units * rate_multiplier, 2)
+    charge_usd = round(base_rate * usage_units * rate_multiplier, 2)
+
+    if currency != 'USD':
+        converter = CurrencyConverter()
+        charge = converter.convert(charge_usd, 'USD', currency)
+        return round(charge, 2)
+
+    return charge_usd

diff --git a/src/billing/currency_converter.py b/src/billing/currency_converter.py
new file mode 100644
--- /dev/null
+++ b/src/billing/currency_converter.py
@@ -0,0 +1,22 @@
+class CurrencyConverter:
+    # Simplified exchange rates for demo
+    RATES = {
+        ('USD', 'EUR'): 0.92,
+        ('USD', 'GBP'): 0.79,
+        ('USD', 'CAD'): 1.36,
+        ('USD', 'MXN'): 17.15,
+        ('EUR', 'USD'): 1.09,
+        ('GBP', 'USD'): 1.27,
+    }
+
+    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
+        if from_currency == to_currency:
+            return amount
+        rate = self.RATES.get((from_currency, to_currency))
+        if rate is None:
+            raise ValueError(f"No exchange rate for {from_currency} -> {to_currency}")
+        return amount * rate
"""
    },
    {
        "hash": "m010bcd",
        "author": "Karen Lee",
        "date": "2025-01-18T09:00:00",
        "message": "fix: prevent duplicate invoice generation for same billing period",
        "files_changed": ["src/billing/invoice_service.py"],
        "diff": """diff --git a/src/billing/invoice_service.py b/src/billing/invoice_service.py
--- a/src/billing/invoice_service.py
+++ b/src/billing/invoice_service.py
@@ -8,6 +8,13 @@ class InvoiceService:
+    def generate_invoice(self, account_id: str, billing_period: str) -> Invoice:
+        # Check for existing invoice to prevent duplicates
+        existing = Invoice.objects.filter(
+            account_id=account_id,
+            billing_period=billing_period,
+            status__in=['draft', 'finalized', 'paid']
+        ).first()
+        if existing:
+            raise DuplicateInvoiceError(
+                f"Invoice already exists for account {account_id}, period {billing_period}"
+            )
+        return self._create_invoice(account_id, billing_period)
"""
    },
    {
        "hash": "m011efg",
        "author": "Leo Nguyen",
        "date": "2025-01-18T11:30:00",
        "message": "feat: add batch processing for CDR records",
        "files_changed": ["src/cdr/batch_processor.py", "src/cdr/cdr_processor.py"],
        "diff": """diff --git a/src/cdr/batch_processor.py b/src/cdr/batch_processor.py
new file mode 100644
--- /dev/null
+++ b/src/cdr/batch_processor.py
@@ -0,0 +1,28 @@
+import logging
+from concurrent.futures import ThreadPoolExecutor
+from src.cdr.cdr_processor import CDRProcessor
+
+logger = logging.getLogger(__name__)
+
+class BatchCDRProcessor:
+    def __init__(self, max_workers: int = 4):
+        self.processor = CDRProcessor()
+        self.max_workers = max_workers
+
+    def process_batch(self, cdr_records: list) -> dict:
+        results = {'success': 0, 'failed': 0, 'errors': []}
+        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
+            futures = {executor.submit(self.processor.process_record, r): r for r in cdr_records}
+            for future in futures:
+                try:
+                    future.result()
+                    results['success'] += 1
+                except Exception as e:
+                    results['failed'] += 1
+                    results['errors'].append(str(e))
+        return results
"""
    },
    # *** THIS IS THE SECONDARY GUILTY COMMIT (#12) ***
    # Changes billing config format from flat to nested structure
    {
        "hash": "m012hij",
        "author": "Maria Gonzalez",
        "date": "2025-01-18T14:00:00",
        "message": "refactor: restructure billing configuration for environment support",
        "files_changed": ["src/config/billing_config.py", "src/config/billing_defaults.yaml"],
        "diff": """diff --git a/src/config/billing_config.py b/src/config/billing_config.py
--- a/src/config/billing_config.py
+++ b/src/config/billing_config.py
@@ -5,15 +5,25 @@ class BillingConfig:
-    def __init__(self, config_path='src/config/billing_defaults.yaml'):
+    def __init__(self, config_path='src/config/billing_defaults.yaml', environment='production'):
         with open(config_path) as f:
-            self._config = yaml.safe_load(f)
+            full_config = yaml.safe_load(f)
+        self._config = full_config.get('environments', {}).get(environment, full_config.get('defaults', {}))
+        self._env = environment

     def get(self, key, default=None):
-        return self._config.get(key, default)
+        # Support nested key access with dot notation
+        keys = key.split('.')
+        value = self._config
+        for k in keys:
+            if isinstance(value, dict):
+                value = value.get(k)
+            else:
+                return default
+        return value if value is not None else default

diff --git a/src/config/billing_defaults.yaml b/src/config/billing_defaults.yaml
--- a/src/config/billing_defaults.yaml
+++ b/src/config/billing_defaults.yaml
@@ -1,8 +1,20 @@
-tax_rate: 0.08
-late_fee_pct: 1.5
-grace_period_days: 15
-max_line_items: 500
-currency: USD
-billing_cycle_day: 1
+defaults:
+  tax_rate: 0.08
+  late_fee_pct: 1.5
+  grace_period_days: 15
+  max_line_items: 500
+  currency: USD
+  billing_cycle_day: 1
+
+environments:
+  production:
+    tax_rate: 0.08
+    late_fee_pct: 1.5
+    grace_period_days: 15
+    max_line_items: 500
+    currency: USD
+  staging:
+    tax_rate: 0.0
+    late_fee_pct: 0.0
+    grace_period_days: 30
+    max_line_items: 100
+    currency: USD
"""
    },
    {
        "hash": "m013klm",
        "author": "Nathan Brown",
        "date": "2025-01-19T09:00:00",
        "message": "chore: upgrade pytest and update test fixtures",
        "files_changed": ["requirements.txt", "tests/conftest.py"],
        "diff": """diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
@@ -5,7 +5,7 @@
-pytest==7.4.0
+pytest==8.0.0
 pytest-cov==4.1.0
-pytest-asyncio==0.21.0
+pytest-asyncio==0.23.0

diff --git a/tests/conftest.py b/tests/conftest.py
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -1,5 +1,6 @@
 import pytest
 from src.models.customer import Customer
+from src.models.address import Address

 @pytest.fixture
 def sample_customer_18mo():
@@ -8,6 +9,7 @@
         name="Test User",
         tenure_months=18,
         account_id="ACC-001",
+        address=Address(street="123 Main St", city="Dallas", state="TX", zip_code="75201"),
         active_plans=[]
     )
"""
    },
    {
        "hash": "m014nop",
        "author": "Olivia Davis",
        "date": "2025-01-19T11:00:00",
        "message": "feat: add tax calculation by state for US billing",
        "files_changed": ["src/billing/tax_calculator.py", "src/config/state_tax_rates.yaml"],
        "diff": """diff --git a/src/billing/tax_calculator.py b/src/billing/tax_calculator.py
new file mode 100644
--- /dev/null
+++ b/src/billing/tax_calculator.py
@@ -0,0 +1,24 @@
+import yaml
+
+class TaxCalculator:
+    def __init__(self, rates_file='src/config/state_tax_rates.yaml'):
+        with open(rates_file) as f:
+            self.rates = yaml.safe_load(f)
+
+    def calculate_tax(self, amount: float, state: str) -> float:
+        rate = self.rates.get('state_rates', {}).get(state, self.rates.get('default_rate', 0.08))
+        return round(amount * rate, 2)
+
+    def calculate_total_with_tax(self, subtotal: float, state: str) -> dict:
+        tax = self.calculate_tax(subtotal, state)
+        return {
+            'subtotal': subtotal,
+            'tax_rate': self.rates.get('state_rates', {}).get(state, 0.08),
+            'tax_amount': tax,
+            'total': round(subtotal + tax, 2)
+        }
"""
    },
    {
        "hash": "m015qrs",
        "author": "Peter Chang",
        "date": "2025-01-19T15:00:00",
        "message": "fix: resolve race condition in concurrent billing updates",
        "files_changed": ["src/billing/billing_cycle.py"],
        "diff": """diff --git a/src/billing/billing_cycle.py b/src/billing/billing_cycle.py
--- a/src/billing/billing_cycle.py
+++ b/src/billing/billing_cycle.py
@@ -15,9 +15,14 @@ class BillingCycleManager:
     def close_cycle(self, cycle):
-        cycle.status = 'closed'
-        cycle.save()
-        invoice = self.invoice_service.generate_invoice(cycle)
-        return invoice
+        from django.db import transaction
+        with transaction.atomic():
+            # Lock the cycle row to prevent concurrent modifications
+            cycle = BillingCycle.objects.select_for_update().get(pk=cycle.pk)
+            if cycle.status == 'closed':
+                raise CycleAlreadyClosedError(f"Cycle {cycle.pk} is already closed")
+            cycle.status = 'closed'
+            cycle.save()
+            invoice = self.invoice_service.generate_invoice(cycle)
+            return invoice
"""
    },
]

# ============================================================================
# MERGE FAILURE - Error log when merging feature/loyalty-discount into main
# ============================================================================

merge_failure = {
    "merge_attempt_date": "2025-01-20T09:00:00",
    "source_branch": "feature/loyalty-discount",
    "target_branch": "main",
    "merge_status": "FAILED",
    "error_log": """
================================================================================
MERGE CONFLICT RESOLUTION: Auto-merged successfully (no textual conflicts)
================================================================================

Running post-merge test suite...

================================================================================
FAILED TESTS (3 failures)
================================================================================

_______________________ TestLoyaltyDiscountEngine.test_discount_amount_calculation _______________________

    def test_discount_amount_calculation(self, sample_customer_18mo):
        engine = LoyaltyDiscountEngine(tier_config)
        line_items = [{'plan_code': 'VOICE_UNLIM', 'usage_units': 1, 'rate_plan': 'standard'}]
        result = engine.apply_loyalty_discount(sample_customer_18mo, line_items)
>       assert result['items'][0]['discount_amount'] == 2.25

E       TypeError: calculate_line_item_charge() got an unexpected keyword argument 'rate_plan'
E
E       The above exception occurred while calling:
E         src/billing/loyalty_engine.py:27 in apply_loyalty_discount
E           base_charge = calculate_line_item_charge(
E               item['plan_code'],
E               item['usage_units'],
E               item['rate_plan']
E           )
E
E       Note: calculate_line_item_charge() signature is now:
E         calculate_line_item_charge(plan_code, usage_units, rate_plan, currency='USD', billing_region='US')
E       But the call passes rate_plan as a positional arg (3rd position matches correctly),
E       however an internal import chain causes the old cached module to conflict.

FAILED tests/test_loyalty_engine.py::TestLoyaltyDiscountEngine::test_discount_amount_calculation

_______________________ TestLoyaltyDiscountEngine.test_bronze_tier_applied _______________________

    def test_bronze_tier_applied(self, sample_customer_18mo, sample_line_items):
        engine = LoyaltyDiscountEngine(tier_config)
        result = engine.apply_loyalty_discount(sample_customer_18mo, sample_line_items)
>       assert result['discount_applied'] is True

E       TypeError: calculate_line_item_charge() got an unexpected keyword argument 'rate_plan'
E
E       src/billing/loyalty_engine.py:27 in apply_loyalty_discount

FAILED tests/test_loyalty_engine.py::TestLoyaltyDiscountEngine::test_bronze_tier_applied

_______________________ TestLoyaltyDiscountEngine.test_calculate_line_item_charge_integration _______________________

    def test_calculate_line_item_charge_integration(self):
        charge = calculate_line_item_charge('VOICE_UNLIM', 1, 'standard')
>       assert charge == 45.00

E       AssertionError: assert 41.4 == 45.0
E
E       Note: The function now applies regional rate adjustments by default.
E       With billing_region='US', a 0.92 regional factor is applied.
E       Expected: 45.00 (old behavior, no regional adjustment)
E       Got: 41.40 (new behavior with default regional adjustment)

FAILED tests/test_loyalty_engine.py::TestLoyaltyDiscountEngine::test_calculate_line_item_charge_integration

_______________________ WARNINGS _______________________

src/config/billing_config.py:8: UserWarning: BillingConfig now requires 'environment' parameter.
  Defaulting to 'production'. Config key 'tax_rate' access pattern may need updating to dot notation.

================================================================================
SUMMARY: 3 failed, 47 passed, 1 warning in 12.34s
================================================================================
""",
    "affected_files_in_feature": [
        "src/billing/loyalty_engine.py",
        "tests/test_loyalty_engine.py"
    ]
}

# ============================================================================
# SAVE ALL DATA
# ============================================================================

def save_data():
    with open(os.path.join(OUTPUT_DIR, "feature_branch.json"), "w") as f:
        json.dump(feature_branch_info, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "main_branch_commits.json"), "w") as f:
        json.dump(main_branch_commits, f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "merge_failure.json"), "w") as f:
        json.dump(merge_failure, f, indent=2)

    # Also save a combined dataset for easy loading
    combined = {
        "scenario": "Telco Billing System - Loyalty Discount Feature Merge Failure",
        "feature_branch": feature_branch_info,
        "main_branch_commits": main_branch_commits,
        "merge_failure": merge_failure,
        "ground_truth": {
            "primary_culprit": {
                "commit_hash": "m009yza",
                "author": "Jake Thompson",
                "reason": "Changed signature of calculate_line_item_charge() in billing_utils.py "
                          "by adding currency and billing_region parameters. Also introduced a "
                          "regional rate adjustment that changes default return values. Alice's "
                          "loyalty_engine.py calls this function with positional args and expects "
                          "the original return values."
            },
            "secondary_culprit": {
                "commit_hash": "m012hij",
                "author": "Maria Gonzalez",
                "reason": "Restructured BillingConfig from flat to nested format with environment "
                          "support. This causes a warning and may affect config lookups in the "
                          "loyalty tier configuration if it shares the same config loader pattern."
            }
        }
    }

    with open(os.path.join(OUTPUT_DIR, "complete_scenario.json"), "w") as f:
        json.dump(combined, f, indent=2)

    print(f"Synthetic data generated successfully in: {OUTPUT_DIR}")
    print(f"  - feature_branch.json     ({len(feature_branch_info['commits'])} commits)")
    print(f"  - main_branch_commits.json ({len(main_branch_commits)} commits)")
    print(f"  - merge_failure.json       (error log with {merge_failure['error_log'].count('FAILED')} failures)")
    print(f"  - complete_scenario.json   (combined dataset with ground truth)")


if __name__ == "__main__":
    save_data()
