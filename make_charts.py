"""Generate all portfolio visualizations -> visualizations/*.png"""
import sys; sys.path.insert(0, 'src')
import utils
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 130, "savefig.bbox": "tight",
    "font.size": 11, "axes.titlesize": 14, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linestyle": "-",
    "figure.facecolor": "white", "axes.facecolor": "white",
})
# Procurement palette: deep teal / slate / amber (not the usual blue/orange defaults)
INK   = "#0f2e3d"   # deep teal-ink
TEAL  = "#1f7a8c"   # primary
SLATE = "#5c7a89"   # secondary
AMBER = "#e0a458"   # highlight / warning
CLAY  = "#bf4e30"   # alert
MUTE  = "#c9d6db"   # tail / muted
GREEN = "#2a9d8f"
def usd(x, p): return f"${x/1e6:,.0f}M" if abs(x) >= 1e6 else f"${x:,.0f}"

NONADDR = ['Revenue Bonds','Pension Payable','Bond Principal','Bond Interest','Principle Retirement',
 'Employee Claims','Payroll - 3rd Party','Municipal Pension','Annexation','Utilities Receivable',
 'Interest Charges Past Due','Juror Compensation','Grant Contract','Subrecipient','Sub-Recipient','Receivable']

raw = utils.load_checkbook('data/raw/checkbook-2024.csv')
df  = utils.clean_spend(raw, verbose=False)
df['addressable'] = ~df['category'].str.contains('|'.join(NONADDR), case=False, na=False)
addr = df[df['addressable']].copy()
TOTAL = df['amount'].sum(); ADDR = addr['amount'].sum()
V = "visualizations"

# ---- 01 Addressable vs non-addressable waterfall-ish bar ----------------
fig, ax = plt.subplots(figsize=(9, 4.2))
na = TOTAL - ADDR
bars = ax.barh(["Total FY24\nvendor payments", "Non-addressable\n(debt · pension · payroll)", "Addressable\nprocurement"],
               [TOTAL, na, ADDR], color=[INK, SLATE, TEAL])
for b, v in zip(bars, [TOTAL, na, ADDR]):
    ax.text(v, b.get_y()+b.get_height()/2, f"  ${v/1e9:.2f}B ({v/TOTAL*100:.0f}%)",
            va="center", ha="left", fontweight="bold")
ax.set_xlim(0, TOTAL*1.15); ax.xaxis.set_major_formatter(mticker.FuncFormatter(usd))
ax.set_title("Only 56% of Houston's $6.67B is addressable procurement spend")
ax.set_xlabel("FY2024 spend")
plt.savefig(f"{V}/01_addressable_split.png"); plt.close()

# ---- 02 Pareto curve (addressable vendors) ------------------------------
abc = utils.abc_classify(addr, 'vendor')
fig, ax = plt.subplots(figsize=(9, 5))
x = abc['rank'].values; y = abc['cum_share'].values*100
ax.plot(x, y, color=TEAL, lw=2.4)
ax.axhline(80, color=CLAY, ls="--", lw=1.3)
n80 = int((abc['cum_share'] <= 0.80).sum())+1
ax.axvline(n80, color=CLAY, ls="--", lw=1.3)
ax.scatter([n80],[80], color=CLAY, zorder=5, s=60)
ax.annotate(f"{n80} vendors = 80% of spend\n({n80/len(abc)*100:.1f}% of the base)",
            (n80, 80), xytext=(n80+380, 55),
            arrowprops=dict(arrowstyle="->", color=INK), fontweight="bold")
ax.set_xlabel("Vendors ranked by spend"); ax.set_ylabel("Cumulative % of addressable spend")
ax.set_title("Pareto curve: a thin head of vendors carries the spend")
ax.set_xlim(0, len(abc)); ax.set_ylim(0, 101)
plt.savefig(f"{V}/02_pareto_curve.png"); plt.close()

# ---- 03 ABC bars --------------------------------------------------------
summ = utils.abc_summary(abc, 'vendor')
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))
order = ['A','B','C']; cols = {'A':TEAL,'B':SLATE,'C':MUTE}
sm = summ.set_index('abc').loc[order]
a1.bar(order, sm['pct_entities']*100, color=[cols[k] for k in order])
a1.set_title("Share of vendors"); a1.set_ylabel("% of vendors")
for i,k in enumerate(order): a1.text(i, sm['pct_entities'][k]*100+1, f"{sm['pct_entities'][k]*100:.0f}%\n{int(sm['n_vendors'][k])}", ha="center", fontweight="bold")
a2.bar(order, sm['pct_spend']*100, color=[cols[k] for k in order])
a2.set_title("Share of spend"); a2.set_ylabel("% of spend")
for i,k in enumerate(order): a2.text(i, sm['pct_spend'][k]*100+1, f"{sm['pct_spend'][k]*100:.0f}%\n${sm['spend'][k]/1e6:,.0f}M", ha="center", fontweight="bold")
fig.suptitle("ABC segmentation — Class A: 4% of vendors, 80% of spend", fontweight="bold", y=1.02)
plt.savefig(f"{V}/03_abc_segmentation.png"); plt.close()

# ---- 04 Top 15 vendors --------------------------------------------------
top = abc.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(9.5, 6))
cols = [TEAL if s < 0.03 else AMBER for s in top['spend_share']]
ax.barh(top['vendor'].str.title().str.slice(0,34), top['amount']/1e6, color=cols)
for i,(v,s) in enumerate(zip(top['amount'], top['spend_share'])):
    ax.text(v/1e6, i, f"  ${v/1e6:.0f}M ({s*100:.1f}%)", va="center", fontweight="bold", fontsize=9)
ax.set_xlabel("Addressable spend ($M)")
ax.set_title("Top 15 addressable vendors — construction & utilities dominate")
plt.savefig(f"{V}/04_top_vendors.png"); plt.close()

# ---- 05 Top categories --------------------------------------------------
cat = utils.spend_cube(addr, 'category').head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(9.5, 6))
ax.barh(cat['category'].str.slice(0,38), cat['spend']/1e6, color=TEAL)
for i,v in enumerate(cat['spend']): ax.text(v/1e6, i, f"  ${v/1e6:.0f}M", va="center", fontsize=9, fontweight="bold")
ax.set_xlabel("Addressable spend ($M)")
ax.set_title("Top 15 expense categories (GL object)")
plt.savefig(f"{V}/05_top_categories.png"); plt.close()

# ---- 06 Seasonality -----------------------------------------------------
seas = utils.seasonality(addr)
fig, ax = plt.subplots(figsize=(10, 4.6))
months = pd.to_datetime(seas['month']+"-01")
cols = [CLAY if m == seas['spend'].max() else TEAL for m in seas['spend']]
ax.bar(range(len(seas)), seas['spend']/1e6, color=cols)
ax.set_xticks(range(len(seas))); ax.set_xticklabels([m.strftime("%b'%y") for m in months], rotation=45, ha="right")
avg = seas['spend'].mean()/1e6
ax.axhline(avg, color=SLATE, ls="--", lw=1.2, label=f"monthly avg ${avg:.0f}M")
peak_i = int(np.argmax(seas['spend'].values))
ax.annotate("Fiscal year-end\nsurge (+78% vs avg)", (peak_i, seas['spend'].max()/1e6),
            xytext=(peak_i-4.2, seas['spend'].max()/1e6*0.92),
            arrowprops=dict(arrowstyle="->", color=INK), fontweight="bold")
ax.set_ylabel("Spend ($M)"); ax.legend()
ax.set_title("Spend seasonality: a pronounced June fiscal-year-end spike")
plt.savefig(f"{V}/06_seasonality.png"); plt.close()

# ---- 07 Fragmentation scatter (bubble) ----------------------------------
frag = utils.fragmentation_table(addr, min_vendors=8)
frag = frag[frag['spend'] > 1e7]
fig, ax = plt.subplots(figsize=(9.5, 6))
sizes = (frag['spend']/frag['spend'].max()*1500)+30
sc = ax.scatter(frag['n_vendors'], frag['top3_share']*100, s=sizes,
                c=frag['hhi'], cmap="YlOrRd_r", alpha=0.75, edgecolor=INK, lw=0.5)
ax.axhline(50, color=SLATE, ls=":", lw=1)
ax.set_xlabel("Number of vendors in category"); ax.set_ylabel("Top-3 vendor share (%)")
ax.set_title("Fragmentation map: bottom-right = many vendors, low concentration")
for _, r in frag.sort_values('n_vendors', ascending=False).head(6).iterrows():
    ax.annotate(r['category'][:22], (r['n_vendors'], r['top3_share']*100),
                fontsize=8, xytext=(4,4), textcoords="offset points")
plt.colorbar(sc, label="HHI (lower = more fragmented)")
plt.savefig(f"{V}/07_fragmentation_map.png"); plt.close()

# ---- 08 Consolidation savings ------------------------------------------
targets = ['Management Consulting Services','Architectural Services','Miscellaneous Support Services',
           'Miscellaneous Other Services & Charges','Temporary Personnel Services']
rows = [utils.size_consolidation_savings(addr, t, 3, 0.08) for t in targets if t in addr['category'].values]
sav = pd.DataFrame(rows).sort_values('estimated_savings')
fig, ax = plt.subplots(figsize=(9.5, 5))
ax.barh(sav['category'].str.slice(0,34), sav['estimated_savings']/1e6, color=GREEN)
for i,(v,tv) in enumerate(zip(sav['estimated_savings'], sav['tail_vendors'])):
    ax.text(v/1e6, i, f"  ${v/1e6:.1f}M  ({tv} tail vendors)", va="center", fontweight="bold", fontsize=9)
tot = sav['estimated_savings'].sum()
ax.set_xlabel("Estimated annual savings ($M) — 8% of consolidatable tail")
ax.set_title(f"Sized consolidation opportunity: ${tot/1e6:.0f}M/yr across 5 indirect categories")
plt.savefig(f"{V}/08_savings_opportunity.png"); plt.close()

# ---- 09 Supplier scorecard heat (top 15 addressable) --------------------
sc = utils.supplier_scorecard(addr, top_n=15)
metrics = ['total_spend','txns','avg_txn','price_dispersion','active_months','contract_coverage']
labels  = ['Total spend','Txn count','Avg ticket','Price disp. (CV)','Active months','Contract cov.']
norm = sc[metrics].copy()
for m in metrics: norm[m] = (sc[m]-sc[m].min())/(sc[m].max()-sc[m].min()+1e-9)
fig, ax = plt.subplots(figsize=(10, 6.5))
im = ax.imshow(norm.values, aspect="auto", cmap="BuPu")
ax.set_yticks(range(len(sc))); ax.set_yticklabels(sc['vendor'].str.title().str.slice(0,30))
ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=30, ha="right")
raw_vals = {'total_spend':lambda v:f"${v/1e6:.0f}M",'txns':lambda v:f"{int(v)}",
            'avg_txn':lambda v:f"${v/1e3:.0f}k",'price_dispersion':lambda v:f"{v:.1f}",
            'active_months':lambda v:f"{int(v)}",'contract_coverage':lambda v:f"{v*100:.0f}%"}
for i in range(len(sc)):
    for j,m in enumerate(metrics):
        ax.text(j, i, raw_vals[m](sc[m].iloc[i]), ha="center", va="center", fontsize=7.5,
                color="white" if norm.values[i,j]>0.55 else INK)
ax.set_title("Supplier scorecard — top 15 addressable vendors (color = relative rank)")
plt.savefig(f"{V}/09_supplier_scorecard.png"); plt.close()

# ---- 10 Price dispersion (illustrative quality overlay) -----------------
scq = utils.add_illustrative_quality(utils.supplier_scorecard(addr, top_n=40))
fig, ax = plt.subplots(figsize=(9.5, 5.5))
sizes = (scq['total_spend']/scq['total_spend'].max()*900)+25
sc2 = ax.scatter(scq['price_dispersion'], scq['quality_score_SYNTH'], s=sizes,
                 c=scq['regularity_proxy'], cmap="viridis", alpha=0.8, edgecolor=INK, lw=0.4)
ax.set_xlabel("Price dispersion (coefficient of variation) — REAL")
ax.set_ylabel("Quality score — SYNTHETIC / illustrative")
ax.set_title("Scorecard shape demo: price volatility vs (synthetic) quality")
ax.text(0.98, 0.03, "⚠ Quality axis is synthetic — ERP/QMS data out of scope for public spend",
        transform=ax.transAxes, ha="right", fontsize=8.5, style="italic", color=CLAY)
plt.colorbar(sc2, label="Payment regularity (txns/active month)")
plt.savefig(f"{V}/10_price_vs_quality_synth.png"); plt.close()

print("All charts written to", V)
import os
for f in sorted(os.listdir(V)): print("  ", f)
