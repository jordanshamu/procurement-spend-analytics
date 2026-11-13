# 🏭 Procurement Spend Analytics & Supplier Concentration
### Spend-Cube · ABC/Pareto · Supplier Scorecard · Sized Consolidation Savings — on Real Public Spend Data

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-Executed%20Notebook-orange?logo=jupyter)](https://jupyter.org/)
[![pandas](https://img.shields.io/badge/pandas-Spend%20Cube-150458?logo=pandas)](https://pandas.pydata.org/)
[![Data](https://img.shields.io/badge/Data-Real%20(Houston%20Checkbook%20FY24)-2a9d8f)](https://data.houstontx.gov/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Portfolio](https://img.shields.io/badge/Portfolio-datascienceportfol.io%2Fjordanshamu-2c3e50)](https://datascienceportfol.io/jordanshamu)

> Analyst: [Jordan Shamukiga](https://github.com/jordanshamu) · [datascienceportfol.io/jordanshamu](https://datascienceportfol.io/jordanshamu)

---

## Business Context

Procurement is the largest controllable cost line in most manufacturing and public organizations. A plant or corporate buyer's core questions are always the same: **where does the money actually go, who are the critical suppliers, where is spend fragmented across too many vendors, and what can we consolidate to unlock volume leverage?**

This project answers those questions on a **real, 268k-row public spend file** — the City of Houston's FY2024 "Checkbook" of every vendor payment. A municipal government is a useful stand-in for a large multi-category buyer: hundreds of expense categories, thousands of suppliers, capital and indirect spend side by side. The techniques — **ABC segmentation, tail-spend rationalization, payment-size monitoring, contract-coverage checks, and spend-timing analysis** — transfer directly to a plant sourcing desk.

**This uses real data, not synthetic.** The one dimension public data cannot provide — supplier **quality/defect** rates from an internal ERP/QMS — is explicitly scoped out and flagged where an illustrative placeholder appears.

---

## Key Results

### Dataset (City of Houston Checkbook, FY2024 — real)

| Metric | Value |
|---|---|
| Raw rows | **267,983** |
| Date range | **2023-07-05 → 2024-06-28** (Houston FY2024) |
| Clean spend rows (after cleaning funnel) | 228,646 |
| Total FY24 vendor payments (gross, refunds excluded) | **$6.67B** |
| **Addressable procurement spend** | **$3.76B (56%)** |
| Non-addressable (debt · pension · payroll) removed | $2.91B (44%) |
| Addressable vendors / categories | **3,701 vendors · 278 GL categories** |

### Gross to net

All spend figures in this README are **gross**: positive payments only. Refunds and reversals (negative amounts) are excluded from totals. This table shows what that excludes. For each line, gross + refunds/reversals = net; the three "Removed" lines plus "In-scope" add back to the raw file. Source: `reports/gross_to_net_reconciliation.csv`.

| Line | Rows | Gross | Refunds & reversals | Net |
|---|---|---|---|---|
| Raw file | 267,983 | $6,767.2M | −$673.8M (14,364 rows) | $6,093.3M |
| Removed: exact duplicates | 1,226 | $2.4M | −$0.3M (8 rows) | $2.1M |
| Removed: pool-cash check clearing | 110 | $0.0M | −$18.6M (110 rows) | −$18.6M |
| Removed: pseudo-vendors (one-time / refund) | 23,914 | $95.3M | −$0.3M (160 rows) | $95.0M |
| **In-scope vendor payments** | 242,733 | **$6,669.5M** | −$654.7M (14,086 rows) | $6,014.8M |
| of which non-addressable | 20,583 | $2,907.9M | −$0.2M (104 rows) | $2,907.6M |
| of which **addressable procurement** | 222,150 | **$3,761.7M** | −$654.5M (13,982 rows) | $3,107.2M |

Row counts include 1 zero-amount row in the in-scope set. Of the −$654.7M in-scope refunds and reversals, −$597.1M (4,213 rows) is booked to one GL account, `General Vendor - Primary Reconciliation Account`; the notebook lists the rest by category. Because these negatives are excluded, gross addressable spend ($3.76B) is higher than net ($3.11B).

### Spend Concentration (ABC / Pareto, addressable)

| Class | Vendors | % of Vendors | Spend | % of Spend |
|---|---|---|---|---|
| **A** | 159 | 4.3% | $3.01B | **79.9%** |
| **B** | 336 | 9.1% | $567M | 15.1% |
| **C (tail)** | 3,206 | 86.6% | $188M | 5.0% |

> **160 of 3,701 vendors (4.3%) carry 80% of addressable spend.** The 3,206-vendor tail is only 5% of dollars but the bulk of the PO/admin burden.

### Headline Findings

| # | Finding | So what |
|---|---|---|
| 1 | **The biggest "vendor" is a bank.** The Bank of New York = $1.18B (18%) of raw payments — debt-service/trustee flows, not procurement. | You must separate addressable spend from financial plumbing first, or every number is wrong. |
| 2 | **Management Consulting is the fragmentation champion:** $411M across **257 vendors**, top-3 only 28%. | Largest single consolidation prize. |
| 3 | **In FY2024, June spend ran +78% above the monthly average** (January was the low, −28%). This is one fiscal year's pattern. | Check other years of the checkbook before treating it as recurring or moving buys. |
| 4 | **Contract-coverage gaps:** 8 vendors with >$20M addressable spend have a contract number on under 50% of it. Several are public bodies or banks. | A blank contract number is a gap in the file, not proof of unauthorized spend. Check which payments should link to a contract. |

### Consolidation Scenario Sizing

These are scenarios, not estimates from the data. The data gives the tail pool ($397.4M of spend outside the top 3 vendors in 5 indirect/services categories); the savings rates are assumptions.

| Scenario | Assumed savings rate on tail pool | Annual savings (scenario) |
|---|---|---|
| Low | 5% | ~$19.9M |
| Mid | 8% | ~$31.8M |
| High | 12% | ~$47.7M |

> At the assumed 8% rate the scenario is **~$31.8M/yr, ~0.8% of addressable spend**. All numbers computed at runtime and exported to `reports/spend_metrics.json`.

---

## Methodology

### 1. Honest Data Profiling
- Full schema, row count, date range, and per-field missingness printed before any analysis
- Field mapping: the brief's generic fields (date, vendor, amount, department, category) mapped to Houston's actual column names (e.g. expense category = `GL Account Description`)

### 2. Cleaning Funnel (every decision logged)
| # | Issue | Decision |
|---|---|---|
| 1 | 1,226 exact-duplicate rows (repeat copies; one copy of each kept) | Drop |
| 2 | Pool-cash `Vendor Disbursement` check-clearing | Drop — internal double-count |
| 3 | 14,364 negative amounts in the raw file (refunds/reversals) | Exclude from spend totals; reconciled in the gross-to-net table above |
| 4 | Placeholder / one-time / refund pseudo-vendors | Drop — not sourceable suppliers |
| 5 | Vendor name casing/whitespace variants | Normalize |

### 3. Addressable-Spend Correction
Strip debt service, bond principal/interest, pension transfers, employee-claims payouts, payroll reconciliation, and interfund/grant flows → **$3.76B addressable** from $6.67B gross.

### 4. Spend Cube
Tidy aggregation over any dimension (vendor · category · department · fund · month · procurement type).

### 5. ABC / Pareto & Concentration
- A/B/C classification by cumulative spend share (80/95 cut-offs)
- Pareto curve + "vendors to reach 80%"
- Herfindahl-Hirschman Index (HHI) for category-level concentration

### 6. Category & Time Segmentation
- Top categories by GL object code
- Monthly spend series → seasonality / fiscal-year-end effect

### 7. Supplier Scorecard (on dimensions public data supports)
Total spend · order/payment frequency · avg & median ticket · **payment-size dispersion (CV)** — how much a vendor's payment amounts vary, not a measure of price changes · active months · **contract coverage** — share of spend on payments that carry a contract number. A **payment-regularity proxy** stands in for on-time delivery (no PO-date vs pay-date pair exists in the file — stated explicitly, not faked). **Quality/defect is out of scope** for public data; a clearly-labelled synthetic score demonstrates scorecard *shape* only.

### 8. Fragmentation & Savings Sizing
Per-category vendor count, top-3 share, HHI, and tail-spend pool → scenario sizing at assumed 5% / 8% / 12% savings rates on the consolidatable tail.

### 9. Sourcing Recommendation
Named **consolidate / scrutinize / retime / grow / rationalize** calls with dollar impact.

---

## Visualizations

All plots auto-save to `visualizations/` on notebook run.

| # | File | Description |
|---|---|---|
| 01 | `01_addressable_split.png` | Addressable vs non-addressable spend |
| 02 | `02_pareto_curve.png` | Vendor Pareto curve (80% line) |
| 03 | `03_abc_segmentation.png` | ABC vendor/spend share bars |
| 04 | `04_top_vendors.png` | Top 15 addressable suppliers |
| 05 | `05_top_categories.png` | Top 15 GL expense categories |
| 06 | `06_seasonality.png` | Monthly spend, FY2024 only (June peak) |
| 07 | `07_fragmentation_map.png` | Category fragmentation bubble map |
| 08 | `08_savings_opportunity.png` | Consolidation scenario at an assumed 8% |
| 09 | `09_supplier_scorecard.png` | Top-15 supplier scorecard heatmap |
| 10 | `10_payment_size_vs_quality_synth.png` | Payment-size dispersion vs (synthetic) quality |

---

## Project Structure

```
procurement-spend-analytics/
├── data/
│   ├── raw/                     ← checkbook-2024.csv (NOT committed — see .gitignore)
│   └── processed/               ← spend_clean.csv, spend_addressable.csv (auto-generated)
├── notebooks/
│   └── procurement_spend_analysis.ipynb   ← fully executed, charts inline (8 sections)
├── src/
│   ├── __init__.py
│   └── utils.py                 ← reusable spend-analytics engine
├── reports/
│   ├── executive_summary.md     ← non-technical stakeholder summary
│   ├── spend_metrics.json       ← all headline metrics (auto-generated)
│   ├── supplier_scorecard_top50.csv      ┐
│   ├── abc_vendor_classification.csv     │ written by §7's export step
│   ├── category_fragmentation.csv        │ (utils.export_tables);
│   └── gross_to_net_reconciliation.csv   ┘ individual payee names masked
├── visualizations/              ← all plots (auto-saved on run)
├── make_charts.py               ← regenerates all figures
├── build_notebook.py            ← assembles & executes the notebook
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Getting Started

### Prerequisites
- Python 3.8+
- Jupyter Lab or Notebook

### Installation
```bash
git clone https://github.com/jordanshamu/procurement-spend-analytics.git
cd procurement-spend-analytics
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Data
This repo **does not commit the raw data** (see `.gitignore`). Download the City of Houston FY2024 Checkbook from the [Houston Open Data portal](https://data.houstontx.gov/) and place the CSV at:
```
data/raw/checkbook-2024.csv
```
The file used here has 18 columns including `Vendor Name`, `Amount`, `Clearing Date`, `Department Name`, `GL Account Description`, `Fund Name`, and `Contract Number`. The pipeline adapts to the columns that exist via the `COLMAP` in `src/utils.py`.

### Run
```bash
# Regenerate every figure:
python make_charts.py
# Rebuild & re-execute the notebook end-to-end:
python build_notebook.py
# Or open interactively:
jupyter lab notebooks/procurement_spend_analysis.ipynb
# Unit tests for the reconciliation and name-masking helpers (no raw data needed):
python -m pytest -q tests
```

### Use the engine directly
```python
from src import utils
raw  = utils.load_checkbook("data/raw/checkbook-2024.csv")
df   = utils.clean_spend(raw)
abc  = utils.abc_classify(df, "vendor")
card = utils.supplier_scorecard(df, top_n=25)
opp  = utils.size_consolidation_savings(df, "Management Consulting Services",
                                        keep_vendors=3, savings_rate=0.08)
```

---

## Technical Stack

| Tool | Purpose |
|---|---|
| Python 3.8+ | Core language |
| pandas · numpy | Spend cube, aggregation, ABC/HHI |
| matplotlib | All visualizations |
| nbformat · nbclient | Programmatic notebook execution |
| Jupyter | Interactive analysis |

---

## Scope & Honesty Notes

- **Real data only.** Every headline number derives from the raw checkbook at runtime.
- **On-time delivery** is approximated by *payment regularity* — the file has no PO-date/pay-date pair, so true lead-time is not computable. Labelled as a proxy throughout.
- **Quality/defect is out of scope** for public spend data (it lives in ERP/QMS). A synthetic quality field appears in exactly one chart, clearly flagged as illustrative, and never drives a recommendation.
- **Savings are scenario sizing**: assumed 5% / 8% / 12% rates applied to consolidatable tail spend. The rates are not estimated from this data.
- **Seasonality is one fiscal year.** The June peak is FY2024's pattern; other years of the checkbook are needed to call it recurring.
- **Contract coverage** measures whether a payment row carries a contract number. A blank is a coverage gap in the file, not evidence of unauthorized spend.
- **Individual payees are masked.** The checkbook pays some private individuals directly. In the committed `reports/` tables, payee names that look like a person's name are replaced with `INDIVIDUAL PAYEE nnnn` (`utils.mask_individual_names`; the rule over-masks some small businesses).

---

## Author

**Jordan Shamukiga** — Data Analyst · Business Analyst · Procurement Analytics

[![GitHub](https://img.shields.io/badge/GitHub-jordanshamu-181717?logo=github)](https://github.com/jordanshamu)
[![Portfolio](https://img.shields.io/badge/Portfolio-datascienceportfol.io-2c3e50)](https://datascienceportfol.io/jordanshamu)

## License
MIT — see [LICENSE](LICENSE).
