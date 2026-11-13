"""Small checks for the reconciliation and name-masking helpers in src/utils.py."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import utils  # noqa: E402


def _raw(rows):
    cols = ["Clearing Date", "Vendor Name", "Amount", "Department Name",
            "GL Account Description", "Fund Name", "Contract Number",
            "Type of procurement"]
    return pd.DataFrame(rows, columns=cols).astype(str)


RAW = _raw([
    ["07/05/2023", "ACME SUPPLY INC", "100", "Parks", "Supplies", "GF", "C1", "PO"],
    ["07/05/2023", "ACME SUPPLY INC", "100", "Parks", "Supplies", "GF", "C1", "PO"],   # duplicate
    ["07/06/2023", "ACME SUPPLY INC", "-30", "Parks", "Supplies", "GF", "C1", "PO"],   # refund
    ["07/07/2023", "BIG BANK NA", "500", "Finance", "Bond Interest", "GF", "", "INV"],
    ["07/08/2023", "GENERAL ONE-TIME VENDOR", "40", "Parks", "Supplies", "GF", "", "INV"],
    ["07/09/2023", "POOL", "-10", "Constant In and Out", "Vendor Disbursement", "GF", "", "INV"],
])


def test_reconciliation_adds_up():
    r = utils.spend_reconciliation(RAW, ["Bond Interest"]).set_index("line")
    parts = ["Removed: exact duplicates", "Removed: pool-cash check clearing",
             "Removed: pseudo-vendors (one-time / refund)", "In-scope vendor payments"]
    assert r.loc[parts, "rows"].sum() == r.loc["Raw file", "rows"] == 6
    assert abs(r.loc[parts, "net_usd"].sum() - r.loc["Raw file", "net_usd"]) < 1e-6
    assert ((r["gross_usd"] + r["refunds_reversals_usd"] - r["net_usd"]).abs() < 1e-6).all()
    ins = r.loc["In-scope vendor payments"]
    assert ins["gross_usd"] == 600 and ins["refunds_reversals_usd"] == -30
    assert r.loc["  of which addressable procurement", "gross_usd"] == 100
    assert r.loc["  of which non-addressable", "gross_usd"] == 500


def test_reconciliation_gross_matches_clean_spend():
    clean = utils.clean_spend(RAW, verbose=False)
    r = utils.spend_reconciliation(RAW).set_index("line")
    assert r.loc["In-scope vendor payments", "gross_usd"] == clean["amount"].sum()
    assert r.loc["In-scope vendor payments", "gross_rows"] == len(clean)


def test_inscope_refunds():
    ref = utils.inscope_refunds(RAW)
    assert list(ref["amount"]) == [-30]


def test_masking_people_vs_businesses():
    people = ["JANE Q DOE", "JOHN SMITH JR", "MARIA LOPEZ - COH1", "SAM LEE DBA"]
    businesses = ["ACME SUPPLY INC", "SMITH & JONES", "HOUSTON ISD", "HUMBLE I S D",
                  "TDINDUSTRIES", "3M COMPANY", "WEAVER AND TIDWELL", "WW GRAINGER"]
    assert all(utils.looks_like_individual(n) for n in people)
    assert not any(utils.looks_like_individual(n) for n in businesses)


def test_mask_individual_names_numbering():
    s = pd.Series(["ACME SUPPLY INC", "JANE Q DOE", "JOHN SMITH"])
    out = utils.mask_individual_names(s)
    assert list(out) == ["ACME SUPPLY INC", "INDIVIDUAL PAYEE 0001", "INDIVIDUAL PAYEE 0002"]
