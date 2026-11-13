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
from pathlib import Path
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
      1. Drop exact-duplicate rows (repeat copies only; first copy kept).
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
# 1b. Gross-to-net reconciliation
# ----------------------------------------------------------------------------
def _scope_masks(df_raw: pd.DataFrame, nonaddr_patterns=()) -> dict:
    """Row masks over the RAW file that mirror the steps in clean_spend()."""
    amt = pd.to_numeric(df_raw[COLMAP["amount"]], errors="coerce")
    dup = df_raw.duplicated()
    pool = ~dup & ((df_raw[COLMAP["department"]] == "Constant In and Out")
                   | df_raw[COLMAP["category"]].str.contains(
                       "Vendor Disbursement", na=False))
    vend = df_raw[COLMAP["vendor"]]
    pseudo = (~dup & ~pool
              & (vend.isin(PLACEHOLDER_VENDORS)
                 | vend.str.contains(_ONE_TIME_RX, na=False)))
    inscope = ~dup & ~pool & ~pseudo
    if nonaddr_patterns:
        na = df_raw[COLMAP["category"]].str.contains(
            "|".join(nonaddr_patterns), case=False, na=False)
    else:
        na = pd.Series(False, index=df_raw.index)
    return {"amount": amt, "dup": dup, "pool": pool, "pseudo": pseudo,
            "inscope": inscope, "nonaddr": inscope & na,
            "addressable": inscope & ~na}


def spend_reconciliation(df_raw: pd.DataFrame, nonaddr_patterns=()) -> pd.DataFrame:
    """
    One table that walks the raw file down to the spend used in the analysis,
    with gross (positive) payments, refunds/reversals (negative amounts) and
    net shown side by side for every line.

    The analysis totals use the GROSS column: refunds and reversals are
    excluded from spend, and this table shows exactly how much that is.
    The three "removed" lines plus "in-scope" add back to the raw file.
    """
    m = _scope_masks(df_raw, nonaddr_patterns)
    amt = m["amount"]
    lines = [
        ("Raw file",                                    pd.Series(True, index=df_raw.index)),
        ("Removed: exact duplicates",                   m["dup"]),
        ("Removed: pool-cash check clearing",           m["pool"]),
        ("Removed: pseudo-vendors (one-time / refund)", m["pseudo"]),
        ("In-scope vendor payments",                    m["inscope"]),
        ("  of which non-addressable",                  m["nonaddr"]),
        ("  of which addressable procurement",          m["addressable"]),
    ]
    rows = []
    for label, mask in lines:
        a = amt[mask]
        rows.append({
            "line": label,
            "rows": int(mask.sum()),
            "gross_rows": int((a > 0).sum()),
            "gross_usd": round(float(a[a > 0].sum()), 2),
            "refund_reversal_rows": int((a < 0).sum()),
            "refunds_reversals_usd": round(float(a[a < 0].sum()), 2),
            "zero_rows": int((a == 0).sum()),
            "net_usd": round(float(a.sum()), 2),
        })
    return pd.DataFrame(rows)


def inscope_refunds(df_raw: pd.DataFrame, nonaddr_patterns=()) -> pd.DataFrame:
    """The negative-amount rows (refunds / reversals) that pass every other
    cleaning step — i.e. the rows dropped only because their amount is < 0."""
    m = _scope_masks(df_raw, nonaddr_patterns)
    keep = m["inscope"] & (m["amount"] < 0)
    out = df_raw[keep].copy()
    out["amount"] = m["amount"][keep]
    out["addressable"] = m["addressable"][keep]
    return out


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
      - payment_size_dispersion (CV)  std/mean of the vendor's payment amounts.
                               Variation in payment size only — a payment can
                               bundle many items or a partial invoice, so this
                               is NOT a measure of unit-price volatility.
      - active_months          breadth of relationship across the year
      - regularity_proxy       txns / active_months -> cadence (on-time proxy*)
      - n_categories/depts     how broadly the vendor is used
      - contract_coverage      share of the vendor's spend on rows that carry a
                               contract number. A blank contract number is a
                               coverage gap in this file, not evidence that the
                               payment was unauthorized or off-contract.

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
    sc["payment_size_dispersion"] = (sc["std_txn"] / sc["avg_txn"]).replace(
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
    demo. It is deterministic and loosely (negatively) tied to payment-size
    dispersion so the demo tells a coherent story. DO NOT use for real decisions.
    """
    rng = np.random.default_rng(seed)
    out = sc.copy()
    base = 92 - 18 * (out["payment_size_dispersion"].clip(0, 3) / 3)
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
    unlocks volume leverage. `savings_rate` is an ASSUMPTION, not something
    estimated from the data (the notebook runs 5% / 8% / 12% scenarios). It is
    applied to the *tail* spend that sits outside the top `keep_vendors` today,
    so the result is scenario sizing, not a forecast.
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


# ----------------------------------------------------------------------------
# 6. Privacy: mask payees that look like individual people
# ----------------------------------------------------------------------------
# The checkbook pays some private individuals directly (refunds, settlements,
# reimbursements, small contracts). Their names are public in the source file,
# but there is no reason to republish them in this repo's derived tables.
#
# Rule (deliberately over-masks): a payee name is kept only if it looks like an
# organisation — it contains a digit, '&', or one of the words below, or it is
# a single word. Any other name of 2-4 words is treated as a person and
# replaced with a numbered placeholder.
_BUSINESS_WORDS = set("""
INC INC. INCORPORATED LLC L.L.C. LLP LP L.P. LTD LTD. LIMITED CO CO. CORP CORP.
CORPORATION COMPANY COMPANIES PC P.C. PLLC PA P.A. JV GMBH NA N.A. TRUST
GROUP SERVICES SERVICE SOLUTIONS SUPPLY SUPPLIES ASSOCIATES ASSOCIATION ASSOC ASSN
SYSTEMS SYSTEM INTERNATIONAL ENGINEERING ENGINEERS CONSTRUCTION CONSTRUCTORS
CONTRACTORS CONTRACTING MANAGEMENT TECHNOLOGIES TECHNOLOGY TECH CONSULTING
CONSULTANTS ENTERPRISES ENTERPRISE INDUSTRIES INDUSTRIAL PRODUCTS PARTNERS
PARTNERSHIP HOLDINGS HOLDING EQUIPMENT ENVIRONMENTAL COMMUNICATIONS SOFTWARE DATA
NETWORK NETWORKS MEDIA DIGITAL PRINTING PUBLISHING PRODUCTIONS STUDIO STUDIOS
DESIGN ARCHITECTS ARCHITECTURE LABORATORIES LABS LAB MEDICAL HEALTH HEALTHCARE
DENTAL VETERINARY HOSPITAL CLINIC PHARMACY ELECTRIC ELECTRICAL PLUMBING ROOFING
MECHANICAL ENERGY POWER WATER WASTE RECYCLING TRUCK TRUCKS PARTS MOTORS AUTO
AUTOMOTIVE AVIATION SALES RENTAL RENTALS DISTRIBUTORS DISTRIBUTION DISTRIBUTING
MANUFACTURING FENCE SIGNS SECURITY SAFETY FIRE RESCUE HARDWARE INSTRUMENTS
CONTROLS CONTROL REALTY PROPERTIES PROPERTY DEVELOPMENT REDEVELOPMENT LAND HOMES
APARTMENTS HOTEL HOTELS RESORT RESTAURANT CATERING BANK FINANCIAL CAPITAL
INSURANCE ADVISORS FUND FOUNDATION INSTITUTE UNIVERSITY COLLEGE SCHOOL SCHOOLS
ACADEMY ISD DISTRICT MUD AUTHORITY AGENCY COUNTY CITY STATE DEPARTMENT DEPT OFFICE
BOARD COUNCIL COMMISSION GOVERNMENT MUNICIPAL PUBLIC NATIONAL AMERICAN AMERICA USA
TEXAS HOUSTON CENTER CENTRE CLUB SOCIETY ALLIANCE COALITION LEAGUE CHAPTER
COMMUNITY CIVIC NEIGHBORHOOD HOMEOWNERS OWNERS VILLAGE ESTATES MINISTRIES CHURCH
MUSEUM LIBRARY THEATRE THEATER ARTS ORCHESTRA SYMPHONY BALLET OPERA ZOO GOLF
SPORTS FITNESS TRAINING LEARNING EDUCATION RESEARCH ANALYTICS RESOURCES STAFFING
PERSONNEL MAINTENANCE JANITORIAL CLEANING LANDSCAPING LAWN TURF TREE POOL
TRAFFIC TRANSPORTATION TRANSIT LOGISTICS FREIGHT MOVING STORAGE TOWING GLASS
STEEL CONCRETE ASPHALT PAVING MATERIALS CHEMICAL CHEMICALS GAS OIL PETROLEUM FUEL
UNIFORMS FURNITURE OFFICE PRODUCTS MARKETING ADVERTISING REPORTING APPRAISAL
MEDIATION MEDIATIONS LAW LEGAL ATTORNEYS FIRM COURT POSTMASTER POSTAL UNITED GLOBAL
WORLDWIDE AND DIAGNOSTICS CONSERVANCY CONSERVATION CONDOMINIUMS TOWNHOMES
TOWNHOUSES TOWNHOUSE HOMEOWNER HOA CASITAS GARDENS SUPPORT CLEARINGHOUSE SDU CHILD
ENFORCEMENT INTERVENTION TV FM RADIO BROADCASTING NEWS TIMES PRESS PUBLICATIONS
VIDEO ARMY COMPUTERS COMPUTER WAREHOUSE WHSE DEPOT SPECIALTIES SPECIALIST
SPECIALISTS TESTING SHREDDING COMMERCIAL PROMOTIONS PROMOTIONAL CONCEPTS APPAREL
MOWING REMODELING BROTHERS BROTHER ENGINES TRANSMISSIONS TRANSMISSION LIFTS
MATERIAL HANDLING FLOORING PERFORMANCE CHEVROLET HILTON AIRPORT COMMITTEE
FEDERATION COMMONWEALTH CONFERENCE CHARITIES ORTHODOX LUTHERAN EVANGELICAL
HEADQUARTERS QUARTET PLAYERS PROGRAM DIST MGMT REDEVL IMPROVEMENT MOUNTAIN PIPE
PIPES TANK THERMAL DECORATING WELLNESS RECOVERY MENTORING MARKET DAILY ELECTRONICS
MILITARY BANKING CAREER ONLINE INVESTIGATORS TRANSLATION ART PROFESSIONAL
INFORMATION EXECUTIVE HORTICULTURAL CUSTODIAN ACCT GREATER ZONE REINVESTMENT
CONSTRUCCIONES SOUTHWEST
""".split())

# Organisations whose names read like people's names, checked by hand among the
# Class A/B payees. Everything else that trips the rule is masked.
_KNOWN_ORGANISATIONS = {"LINEBARGER HEARD GOGGAN GRAHAM", "WW GRAINGER"}


def looks_like_individual(name) -> bool:
    """True when a payee name looks like a private person (see rule above)."""
    if not isinstance(name, str) or not name.strip():
        return False
    base = name.upper().split(" - ")[0]          # "JANE DOE - COH1" -> "JANE DOE"
    if base.strip() in _KNOWN_ORGANISATIONS:
        return False
    if re.search(r"[0-9&@/]", base) or re.search(r"\bI ?S ?D\b", base):
        return False
    words = re.findall(r"[A-Z][A-Z'.\-]*", base)
    if len(words) < 2 or len(words) > 4:
        return False
    if any(w.strip(".,") in _BUSINESS_WORDS or w in _BUSINESS_WORDS for w in words):
        return False
    return True


def mask_individual_names(names: pd.Series,
                          prefix: str = "INDIVIDUAL PAYEE") -> pd.Series:
    """Replace person-like payee names with 'INDIVIDUAL PAYEE 0001', ... in the
    order they appear (so the number carries no information about the name)."""
    is_person = names.map(looks_like_individual)
    out = names.copy()
    out[is_person] = [f"{prefix} {i:04d}" for i in range(1, int(is_person.sum()) + 1)]
    return out


def export_tables(clean: pd.DataFrame,
                  addressable: pd.DataFrame,
                  abc: pd.DataFrame,
                  scorecard: pd.DataFrame,
                  fragmentation: pd.DataFrame,
                  reconciliation: pd.DataFrame | None = None,
                  proc_dir: str = "../data/processed",
                  report_dir: str = "../reports") -> dict:
    """Write the derived tables the README documents.

    Two destinations, on purpose:

      data/processed/  large intermediate frames. Regenerated on every run and
                       git-ignored, because they are only useful if you already
                       have the raw Houston extract.
      reports/         the small analyst-facing tables. These ARE committed,
                       so a reviewer who cannot download the 268k-row source file
                       can still read the ABC classification, the supplier
                       scorecard, the category fragmentation view and the
                       gross-to-net reconciliation.

    Payee names that look like private individuals are masked in every table
    written to reports/ (see mask_individual_names). data/processed/ is not
    masked because it is git-ignored and never leaves the machine.

    Returns a dict of {label: path} so the notebook can print what it wrote.
    """
    proc, rep = Path(proc_dir), Path(report_dir)
    proc.mkdir(parents=True, exist_ok=True)
    rep.mkdir(parents=True, exist_ok=True)

    written = {}

    clean.to_csv(proc / "spend_clean.csv", index=False)
    written["spend_clean"] = str(proc / "spend_clean.csv")

    addressable.to_csv(proc / "spend_addressable.csv", index=False)
    written["spend_addressable"] = str(proc / "spend_addressable.csv")

    abc = abc.assign(vendor=mask_individual_names(abc["vendor"]))
    abc.to_csv(rep / "abc_vendor_classification.csv", index=False)
    written["abc_vendor_classification"] = str(rep / "abc_vendor_classification.csv")

    # Top 50 only — the full scorecard is 3,701 rows and not worth committing.
    top50 = scorecard.head(50)
    top50 = top50.assign(vendor=mask_individual_names(top50["vendor"]))
    top50.to_csv(rep / "supplier_scorecard_top50.csv", index=False)
    written["supplier_scorecard_top50"] = str(rep / "supplier_scorecard_top50.csv")

    fragmentation.to_csv(rep / "category_fragmentation.csv", index=False)
    written["category_fragmentation"] = str(rep / "category_fragmentation.csv")

    if reconciliation is not None:
        reconciliation.to_csv(rep / "gross_to_net_reconciliation.csv", index=False)
        written["gross_to_net_reconciliation"] = str(rep / "gross_to_net_reconciliation.csv")

    return written
