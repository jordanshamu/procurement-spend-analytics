# Executive Summary: Procurement Spend Analytics & Supplier Concentration
## Turning a $6.7B Vendor-Payment File into a Sourcing Action Plan

**Prepared by:** Jordan Shamukiga, Procurement / Data Analyst
**Data:** City of Houston Checkbook, FY2024 (real public vendor-payment data, 267,983 records)
**Audience:** Procurement Leadership, Finance / Cost Control, Category Management

---

## The Business Problem

Every large buyer — a city, a manufacturer, a multi-plant operation — faces the same blind spot: **spend is recorded transaction-by-transaction, but decisions have to be made supplier-by-supplier and category-by-category.** Without that roll-up, negotiating leverage leaks away across hundreds of fragmented vendors, gaps in contract coverage go unnoticed, and the timing of spend is never examined.

This analysis takes a real, 268,000-line record of every payment a large public buyer made in a fiscal year and turns it into the four answers a sourcing team actually needs: **where the money goes, who the critical suppliers are, where spend is dangerously fragmented, and how much a consolidation program is worth in dollars.**

---

## The First Finding Reframed Everything

The single largest "vendor" in the file is **a bank — $1.18 billion, 18% of all payments.** That is not something anyone can negotiate: it is debt-service and trustee cash movement. Add pension transfers, bond principal and interest, employee-claims payouts, and payroll reconciliation, and **44% of the $6.7B turns out to be financial plumbing, not procurement.**

Stripping it out leaves the number that matters: **$3.76 billion of addressable procurement spend** (gross; refunds and reversals of $654.5M in these categories are excluded — net is $3.11B, see the gross-to-net table in the README) across **3,701 real suppliers and 278 expense categories.** Any analysis that skips this step over-reports the opportunity by nearly half. This correction is the difference between a credible sourcing plan and a misleading one.

---

## Where the Money Goes: A Textbook Pareto Problem

Addressable spend is extraordinarily concentrated at the top and extraordinarily fragmented at the bottom:

- **160 suppliers — just 4.3% of the vendor base — account for 80% of spend.** These are the relationships that matter.
- **3,206 suppliers — 87% of the vendor base — together account for only 5% of spend.** Each one still requires a purchase order, an invoice, a payment, and a vendor record. The dollars are tiny; the administrative drag is not.

The top of the list is dominated by **heavy-construction and water-infrastructure partners** (Hensel Phelps, Houston Waterworks Team, Austin-Gilbane). These are strategic capital partners, not savings targets — they should be protected and held to milestones, not squeezed.

---

## The Three Problems Worth Fixing

**1. Fragmentation — the consolidation prize.**
The clearest opportunity is **Management Consulting Services: $411 million spread across 257 different vendors,** with the top three holding only 28% of the category. Roughly $297M sits in a long, uncoordinated tail. Four smaller service categories (architectural, temporary staffing, and two "miscellaneous services" buckets) show the same pattern at smaller scale.

**2. Contract-coverage gaps — the paperwork question.**
Eight suppliers with more than $20M in addressable spend have a contract number on under half of it. Several are public bodies or banks. A blank contract number means the payment is not linked to a contract in this file; it is not evidence of unauthorized spend. The next step is to check which of these payments should carry a contract reference.

**3. The June peak — a timing question.**
**In FY2024, June spending ran 78% above the monthly average.** That fits a fiscal-year-end budget push, but it is one year's pattern. Other years of the checkbook are needed before treating it as recurring, and the file has no prices, so it does not show whether June buys cost more.

---

## Scenario Sizing

Consolidating the fragmented tail across five indirect/services categories onto a small set of awarded, rate-carded suppliers sizes as follows. The tail pool ($397.4M) comes from the data; the savings rates are assumptions, not estimates.

| Scenario | Assumed savings rate on consolidatable tail | Annual savings (scenario) |
|---|---|---|
| Low | 5% | ~$19.9M |
| Mid | 8% | ~$31.8M |
| High | 12% | ~$47.7M |

At the assumed 8% rate the scenario is **~$31.8M a year** — about 0.8% of addressable spend — with **Management Consulting accounting for ~$23.8M of it.**

---

## The Recommendation

| Action | Target | Impact |
|---|---|---|
| 🟢 **Consolidate now** | Management Consulting ($411M / 257 vendors) + 4 indirect categories | ~$31.8M/yr scenario at an assumed 8% |
| 🟠 **Scrutinize** | >$20M vendors with contract numbers on under 50% of spend; re-code $100M+ of "Miscellaneous" spend | Better contract linkage + visibility |
| 🔵 **Check timing** | Compare the FY2024 June peak with other years before moving discretionary buys | Confirms whether the pattern recurs |
| 🟣 **Grow / protect** | Class-A construction & water-infrastructure primes | Strategic — SLAs, not savings |
| ⚪ **Rationalize the tail** | 3,206 vendors at 5% of spend → P-cards / catalog | Cut PO & admin overhead |

---

## What This Analysis Does *Not* Cover

- **Supplier quality and defect rates.** The single most important dimension of a real supplier scorecard — defect PPM, returns, inspection failures, on-time-in-full — lives in an internal ERP/QMS and **cannot come from public payment data.** It is deliberately out of scope; where an illustrative quality score appears, it is clearly flagged as synthetic and drives no recommendation.
- **True on-time delivery.** The file has no purchase-order-date versus payment-date pair, so delivery performance is approximated by payment *regularity* and labelled as a proxy.
- **Realized savings.** The dollar figures are scenario sizing from assumed 5% / 8% / 12% rates, not estimates or guaranteed outcomes.
- **Multi-year seasonality.** Only FY2024 is analysed, so the June peak is one year's pattern.

---

## For a Manufacturing / Plant Buyer Context

A city is a proxy for any large multi-category buyer. The transferable playbook is identical: **segment suppliers by spend (ABC), rationalize the long tail, monitor payment-size variation, check contract coverage, and examine spend timing.** The one piece to wire in on the inside is the ERP/QMS quality feed — that completes the supplier scorecard and turns this from a spend analysis into a full supplier-performance system.

---

*Full methodology, cleaning funnel, and reproducible code in `notebooks/procurement_spend_analysis.ipynb`. All metrics in `reports/spend_metrics.json`.*
*Contact: Jordan Shamukiga · [datascienceportfol.io/jordanshamu](https://datascienceportfol.io/jordanshamu)*
