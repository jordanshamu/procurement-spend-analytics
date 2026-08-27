# Executive Summary: Procurement Spend Analytics & Supplier Concentration
## Turning a $6.7B Vendor-Payment File into a Sourcing Action Plan

**Prepared by:** Jordan Shamukiga, Procurement / Data Analyst
**Data:** City of Houston Checkbook, FY2024 (real public vendor-payment data, 267,983 records)
**Audience:** Procurement Leadership, Finance / Cost Control, Category Management

---

## The Business Problem

Every large buyer — a city, a manufacturer, a multi-plant operation — faces the same blind spot: **spend is recorded transaction-by-transaction, but decisions have to be made supplier-by-supplier and category-by-category.** Without that roll-up, negotiating leverage leaks away across hundreds of fragmented vendors, off-contract buying goes unnoticed, and money is spent at the worst possible time of year.

This analysis takes a real, 268,000-line record of every payment a large public buyer made in a fiscal year and turns it into the four answers a sourcing team actually needs: **where the money goes, who the critical suppliers are, where spend is dangerously fragmented, and how much a consolidation program is worth in dollars.**

---

## The First Finding Reframed Everything

The single largest "vendor" in the file is **a bank — $1.18 billion, 18% of all payments.** That is not something anyone can negotiate: it is debt-service and trustee cash movement. Add pension transfers, bond principal and interest, employee-claims payouts, and payroll reconciliation, and **44% of the $6.7B turns out to be financial plumbing, not procurement.**

Stripping it out leaves the number that matters: **$3.76 billion of addressable procurement spend** across **3,701 real suppliers and 278 expense categories.** Any analysis that skips this step over-reports the opportunity by nearly half. This correction is the difference between a credible sourcing plan and a misleading one.

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

**2. Off-contract leakage — the governance problem.**
Several suppliers with more than $20M in annual spend sit under 50% contract coverage — and they carry the highest price volatility on the board. Spend that large without contract discipline is both a compliance risk and a pricing risk.

**3. The fiscal-year-end flush — the timing problem.**
**June spending runs 78% above the monthly average.** This is the classic public-sector "use-it-or-lose-it" budget dump: money spent in a rush, at the worst time to negotiate, often single-sourced. It is entirely self-inflicted and entirely fixable.

---

## What It's Worth

Consolidating the fragmented tail across five indirect/services categories onto a small set of awarded, rate-carded suppliers is worth, on conservative assumptions:

| Scenario | Savings rate on consolidatable tail | Annual savings |
|---|---|---|
| Conservative floor | 5% | **~$19.9M** |
| **Base case** | **8%** | **~$31.8M** |
| Stretch | 12% | **~$47.7M** |

**Headline: roughly $32 million a year** — about 0.8% of addressable spend — with **Management Consulting alone delivering ~$24M of it.** This is before any savings from retiming the June flush or closing off-contract leakage, both of which add further upside that is harder to size precisely from public data.

---

## The Recommendation

| Action | Target | Impact |
|---|---|---|
| 🟢 **Consolidate now** | Management Consulting ($411M / 257 vendors) + 4 indirect categories | **~$32M/yr** |
| 🟠 **Scrutinize** | >$20M vendors under 50% contract coverage; re-code $100M+ of "Miscellaneous" spend | Risk reduction + visibility |
| 🔵 **Retime** | Shift discretionary buys out of the June flush into the Jan–Feb trough | Avoid year-end price premiums |
| 🟣 **Grow / protect** | Class-A construction & water-infrastructure primes | Strategic — SLAs, not savings |
| ⚪ **Rationalize the tail** | 3,206 vendors at 5% of spend → P-cards / catalog | Cut PO & admin overhead |

---

## What This Analysis Does *Not* Cover

- **Supplier quality and defect rates.** The single most important dimension of a real supplier scorecard — defect PPM, returns, inspection failures, on-time-in-full — lives in an internal ERP/QMS and **cannot come from public payment data.** It is deliberately out of scope; where an illustrative quality score appears, it is clearly flagged as synthetic and drives no recommendation.
- **True on-time delivery.** The file has no purchase-order-date versus payment-date pair, so delivery performance is approximated by payment *regularity* and labelled as a proxy.
- **Realized savings.** The dollar figures are opportunity sizes using standard strategic-sourcing ranges, not guaranteed outcomes — they scope the prize and justify the sourcing effort.

---

## For a Manufacturing / Plant Buyer Context

A city is a proxy for any large multi-category buyer. The transferable playbook is identical: **segment suppliers by spend (ABC), rationalize the long tail, monitor price dispersion, enforce contract coverage, and arbitrage fiscal timing.** The one piece to wire in on the inside is the ERP/QMS quality feed — that completes the supplier scorecard and turns this from a spend analysis into a full supplier-performance system.

---

*Full methodology, cleaning funnel, and reproducible code in `notebooks/procurement_spend_analysis.ipynb`. All metrics in `reports/spend_metrics.json`.*
*Contact: Jordan Shamukiga · [datascienceportfol.io/jordanshamu](https://datascienceportfol.io/jordanshamu)*
