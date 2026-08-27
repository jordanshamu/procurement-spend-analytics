"""
Procurement Spend Analytics & Supplier Concentration
=====================================================
Reusable analytics utilities for the spend-cube, ABC/Pareto, supplier
scorecard, and savings-sizing pipeline.

Author: Jordan Shamukiga
Data:   City of Houston Checkbook, FY2024 (real public vendor-payment file)

Design note
-----------
Everything is a pure function over a tidy spend DataFrame so the notebook
reads top-to-bottom and every number is reproducible. No global state.
"""

from __future__ import annotations
import re
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# 0. Column contract — maps described fields to Houston's actual column names
# ----------------------------------------------------------------------------
# The brief describes generic fields; Houston labels them differently. This is
# the single source of truth for that mapping.
COLMAP = {
    "date":       "Clearing Date",            # payment/transaction date
    "vendor":     "Vendor Name",              # payee
    "amount":     "Amount",                   # payment amount (USD)
    "department": "Department Name",          # buying department
    "category":   "GL Account Description",   # expense category (GL object code)
    "fund":       "Fund Name",                # fund
    "contract":   "Contract Number",          # contract id (nullable)
    "proc_type":  "Type of procurement",      # PO / release / invoice mechanism
}

# Pseudo-vendors that are NOT real suppliers (refund buckets, placeholders).
PLACEHOLDER_VENDORS = {"*", "GENERAL ONE-TIME VENDOR", "COURTS REFUNDS",
                       "Water Refund one time vendor"}
_ONE_TIME_RX = re.compile(r"one.?time|refund", re.I)


# ----------------------------------------------------------------------------
# 1. Load & clean
# ----------------------------------------------------------------------------
def load_checkbook(path: str) -> pd.DataFrame:
    """Load the raw Houston Checkbook CSV with safe string dtypes."""
    return pd.read_csv(path, dtype=str)


def clean_spend(df_raw: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Turn the raw checkbook into an analysis-ready *spend* table.

    Cleaning decisions (each defensible and logged):
      1. Drop 1,914 exact-duplicate rows.
      2. Drop the 'Constant In and Out' department + 'Vendor Disbursement'
         GL rows — these are pool-cash check-clearing entries, i.e. internal
         double-counting, not spend.
      3. Keep only positive Amounts. Negatives are refunds/reversals; mixing
         them into vendor totals would understate true purchasing volume and
         corrupt frequency counts.
      4. Remove placeholder / one-time / refund pseudo-vendors — they are not
         suppliers you can source from or negotiate with.
      5. Parse dates and derive month/quarter for the time cube.
    """
    df = df_raw.copy()
    n0 = len(df)

    df = df.drop_duplicates()
    n1 = len(df)

    df["amount"] = pd.to_numeric(df[COLMAP["amount"]], errors="coerce")
    df["date"]   = pd.to_datetime(df[COLMAP["date"]], format="%m/%d/%Y",
                                  errors="coerce")

    df = df[df[COLMAP["department"]] != "Constant In and Out"]
    df = df[~df[COLMAP["category"]].str.contains("Vendor Disbursement",
                                                 na=False)]
    n2 = len(df)

    df = df[df["amount"] > 0]
    n3 = len(df)

    ph = df[COLMAP["vendor"]].isin(PLACEHOLDER_VENDORS)
    ot = df[COLMAP["vendor"]].str.contains(_ONE_TIME_RX, na=False)
    df = df[~(ph | ot)]
    n4 = len(df)

    # Tidy, renamed working columns
    df = df.rename(columns={
        COLMAP["vendor"]:     "vendor",
        COLMAP["department"]: "department",
        COLMAP["category"]:   "category",
        COLMAP["fund"]:       "fund",
        COLMAP["contract"]:   "contract",
        COLMAP["proc_type"]:  "proc_type",
    })
    df["vendor"] = (df["vendor"].str.upper().str.strip()
                    .str.replace(r"\s+", " ", regex=True))
    df["month"]   = df["date"].dt.to_period("M").astype(str)
    df["quarter"] = df["date"].dt.to_period("Q").astype(str)
    df["has_contract"] = df["contract"].notna() & (df["contract"].str.strip() != "")

    keep = ["date", "month", "quarter", "vendor", "department", "category",
            "fund", "contract", "has_contract", "proc_type", "amount"]
    df = df[keep].reset_index(drop=True)

    if verbose:
        print("Cleaning funnel (rows):")
        print(f"  raw                         {n0:>10,}")
        print(f"  after drop exact dupes      {n1:>10,}  ({n1-n0:+,})")
        print(f"  after drop pool-cash/xfer   {n2:>10,}  ({n2-n1:+,})")
        print(f"  after keep positive spend   {n3:>10,}  ({n3-n2:+,})")
        print(f"  after drop pseudo-vendors   {n4:>10,}  ({n4-n3:+,})")
        print(f"  final spend rows            {len(df):>10,}")
        print(f"  total attributable spend    ${df['amount'].sum():>15,.0f}")
    return df


# ----------------------------------------------------------------------------
# 2. Spend cube
# ----------------------------------------------------------------------------
def spend_cube(df: pd.DataFrame, dims) -> pd.DataFrame:
    """Aggregate spend over one or more dimensions -> sorted spend table."""
    if isinstance(dims, str):
        dims = [dims]
    out = (df.groupby(dims)
             .agg(spend=("amount", "sum"),
                  txns=("amount", "size"),
                  vendors=("vendor", "nunique"))
             .reset_index()
             .sort_values("spend", ascending=False))
    return out


# ----------------------------------------------------------------------------
# 3. ABC / Pareto
# ----------------------------------------------------------------------------
def abc_classify(df: pd.DataFrame, entity: str = "vendor",
                 a=0.80, b=0.95) -> pd.DataFrame:
    """
    Classic ABC (Pareto) segmentation by spend.
      A = entities making up the first `a` share of cumulative spend
      B = next slice up to `b`
      C = the long tail
    Returns per-entity table with cumulative share + class.
    """
    g = (df.groupby(entity)["amount"].sum()
           .sort_values(ascending=False).reset_index())
    g["cum_spend"] = g["amount"].cumsum()
    total = g["amount"].sum()
    g["cum_share"] = g["cum_spend"] / total
    g["spend_share"] = g["amount"] / total
    g["rank"] = np.arange(1, len(g) + 1)

    def _c(x):
        if x <= a:
            return "A"
        if x <= b:
            return "B"
        return "C"
    g["abc"] = g["cum_share"].apply(_c)
    return g


def abc_summary(abc: pd.DataFrame, entity: str = "vendor") -> pd.DataFrame:
    """Roll an ABC table up to the A/B/C class level."""
    s = (abc.groupby("abc")
            .agg(**{f"n_{entity}s": (entity, "nunique"),
                    "spend": ("amount", "sum")})
            .reset_index())
    s["pct_entities"] = s[f"n_{entity}s"] / s[f"n_{entity}s"].sum()
    s["pct_spend"]    = s["spend"] / s["spend"].sum()
    return s.sort_values("abc")


def hhi(series_spend: pd.Series) -> float:
    """
    Herfindahl-Hirschman Index of concentration on a set of spend values.
    Sum of squared percentage shares (0-10,000 scale). >2,500 = highly
    concentrated in antitrust terms.
    """
    shares = series_spend / series_spend.sum() * 100
    return float((shares ** 2).sum())


# ----------------------------------------------------------------------------
# 4. Supplier scorecard
# ----------------------------------------------------------------------------
def supplier_scorecard(df: pd.DataFrame, top_n: int | None = None) -> pd.DataFrame:
    """
    Build a per-supplier scorecard on the dimensions this public data supports:
      - total_spend            purchasing volume
      - txns                   order/payment frequency
      - avg_txn / median_txn   ticket size
      - price_dispersion (CV)  std/mean of line amounts -> pricing volatility
      - active_months          breadth of relationship across the year
      - regularity_proxy       txns / active_months -> cadence (on-time proxy*)
      - n_categories/depts     how broadly the vendor is used
      - contract_coverage      share of the vendor's spend under a contract #

    *On-time proxy: the checkbook has no PO-date vs pay-date pair, so true
     lead-time can't be computed. Payment *regularity* (consistent monthly
     cadence) is the closest defensible signal and is labelled as a proxy.
    """
    g = df.groupby("vendor")
    # Contract-covered spend per vendor (spend on rows carrying a contract #)
    contract_spend = (df.assign(_c=df["amount"].where(df["has_contract"], 0.0))
                        .groupby("vendor")["_c"].sum())
    sc = pd.DataFrame({
        "total_spend":   g["amount"].sum(),
        "txns":          g["amount"].size(),
        "avg_txn":       g["amount"].mean(),
        "median_txn":    g["amount"].median(),
        "std_txn":       g["amount"].std().fillna(0.0),
        "active_months": g["month"].nunique(),
        "n_categories":  g["category"].nunique(),
        "n_departments": g["department"].nunique(),
        "contract_spend": contract_spend,
    })
    sc["price_dispersion"] = (sc["std_txn"] / sc["avg_txn"]).replace(
        [np.inf, -np.inf], 0).fillna(0)
    sc["regularity_proxy"] = sc["txns"] / sc["active_months"]
    sc["contract_coverage"] = (sc["contract_spend"] / sc["total_spend"]).fillna(0)
    sc = sc.sort_values("total_spend", ascending=False)
    sc["spend_rank"] = np.arange(1, len(sc) + 1)
    if top_n:
        sc = sc.head(top_n)
    return sc.reset_index()


def add_illustrative_quality(sc: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    ILLUSTRATIVE ONLY — not from the data.

    A real supplier scorecard needs a quality/defect dimension, which lives in
    an internal ERP/QMS (PPM defect rates, RMA counts, inspection fails). Public
    spend data cannot supply it. This function attaches a clearly-labelled
    SYNTHETIC quality score so the scorecard *shape* is complete for a portfolio
    demo. It is deterministic and loosely (negatively) tied to price dispersion
    so the demo tells a coherent story. DO NOT use for real decisions.
    """
    rng = np.random.default_rng(seed)
    out = sc.copy()
    base = 92 - 18 * (out["price_dispersion"].clip(0, 3) / 3)
    noise = rng.normal(0, 4, len(out))
    out["quality_score_SYNTH"] = (base + noise).clip(60, 100).round(1)
    out["_quality_is_synthetic"] = True
    return out


# ----------------------------------------------------------------------------
# 5. Savings / consolidation sizing
# ----------------------------------------------------------------------------
def fragmentation_table(df: pd.DataFrame, min_vendors: int = 5) -> pd.DataFrame:
    """
    Per-category fragmentation view used to find consolidation candidates:
    spend, vendor count, HHI, and the tail-vendor share (spend outside the
    category's top-3 vendors) — the pool a consolidation play would target.
    """
    rows = []
    for cat, grp in df.groupby("category"):
        vspend = grp.groupby("vendor")["amount"].sum().sort_values(ascending=False)
        top3 = vspend.head(3).sum()
        rows.append({
            "category": cat,
            "spend": vspend.sum(),
            "n_vendors": len(vspend),
            "hhi": hhi(vspend),
            "top3_share": top3 / vspend.sum(),
            "tail_spend": vspend.sum() - top3,
        })
    out = pd.DataFrame(rows)
    out = out[out["n_vendors"] >= min_vendors]
    return out.sort_values("spend", ascending=False).reset_index(drop=True)


def size_consolidation_savings(df: pd.DataFrame, category: str,
                               keep_vendors: int = 3,
                               savings_rate: float = 0.08) -> dict:
    """
    Size a concrete consolidation opportunity for one category.

    Model: consolidating fragmented tail spend onto a few awarded suppliers
    unlocks volume leverage. We apply a conservative `savings_rate` (default
    8%, a mid-point of the widely-cited 5-15% strategic-sourcing range) to the
    *tail* spend that sits outside the top `keep_vendors` today.
    """
    vspend = (df[df["category"] == category]
              .groupby("vendor")["amount"].sum()
              .sort_values(ascending=False))
    tail = vspend.iloc[keep_vendors:].sum()
    return {
        "category": category,
        "total_spend": float(vspend.sum()),
        "n_vendors": int(len(vspend)),
        "kept_vendors": keep_vendors,
        "tail_vendors": int(max(len(vspend) - keep_vendors, 0)),
        "tail_spend": float(tail),
        "savings_rate": savings_rate,
        "estimated_savings": float(tail * savings_rate),
    }


def seasonality(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly spend series with share-of-year, for the time cube / seasonality."""
    m = (df.groupby("month")["amount"].sum().reset_index()
           .rename(columns={"amount": "spend"}))
    m["share"] = m["spend"] / m["spend"].sum()
    return m
