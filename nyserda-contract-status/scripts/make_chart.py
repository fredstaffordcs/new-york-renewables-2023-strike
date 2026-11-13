"""
Static PNG chart: how little of NYSERDA's large-scale renewable contract capacity
(onshore Tier 1 + offshore wind ORECs) is operating, by solicitation year.

Data: build_data.py -> rows.pkl (NYSERDA dataset through 09/30/2026, incl. the
RESRFP25-1 contracts, + rebid links from NY_RES_rebid_crosswalk.xlsx);
build_nypa.py -> NYPA flags (NYPA_dashboard_roster_vs_NYSERDA.xlsx).
Offshore MW are added into the same bars without visual distinction.
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Liberation Sans"
plt.rcParams["hatch.linewidth"] = 1.0

OPERATING = "#1c5cab"
UNDERCON = "#a9c5ea"      # light tint of the operating blue: on its way
UC_HATCH = "#5f8ccb"
OP_HATCH = "#7fa8d9"      # lighter tint of the operating blue, for a rebid that's now built
UNDERDEV = "#dcdad3"
CANCELLED = "#a83f3f"
UD_HATCH = "#a3a097"
CX_HATCH = "#e6c3c3"
HATCH = "////"
TEXT_PRIMARY = "#141414"
TEXT_SECONDARY = "#54524c"
TEXT_MUTED = "#8f8d85"
SURFACE = "#ffffff"
GRID = "#e9e7e1"
RULE = "#d8d6cf"
NYPA = "#178f7e"          # teal: NYPA involvement
NYPA_HATCH = "#8fd0c4"

AS_OF = "Sept. 30, 2026"   # NYSERDA "Data Through Date"
from pathlib import Path
SP = str(Path(__file__).resolve().parents[1] / "output") + "/"
rows = pd.read_pickle(SP + "rows_nypa.pkl")      # NYSERDA rows + nypa_partner flag
nypa = pd.read_pickle(SP + "nypa_only.pkl")      # NYPA projects with no active NYSERDA contract
years = ["Pre-2017"] + [str(y) for y in range(2017, 2026)]
labels = ["Pre-2017*"] + [str(y) for y in range(2017, 2026)]

STATUS_STYLE = [  # (status, linked) -> fill, hatch colour; stacked bottom -> top
    ("Operational", False, OPERATING, None),
    ("Operational", True, OPERATING, OP_HATCH),
    ("Under Construction", False, UNDERCON, None),
    ("Under Construction", True, UNDERCON, UC_HATCH),
    ("Under Development", False, UNDERDEV, None),
    ("Under Development", True, UNDERDEV, UD_HATCH),
    ("Cancelled", True, CANCELLED, CX_HATCH),
    ("Cancelled", False, CANCELLED, None),
]

def mw(year, seg, status, linked):
    d = rows[(rows.year == year) & (rows.seg == seg) & (rows.status == status) & (rows.linked == linked)]
    return d.mw.sum()

operating = [rows[(rows.year == y) & (rows.status == "Operational")].mw.sum() for y in years]
total_mw  = [rows[rows.year == y].mw.sum() for y in years]

# Headline numbers count each site once: drop every earlier appearance of a
# site that was later replaced by a rebid award.
DISTINCT_MW = rows.mw.sum() - rows[rows.replaced_later].mw.sum()
by = lambda st: rows[rows.status == st].mw.sum()
OP_MW, UC_MW, UD_MW = by("Operational"), by("Under Construction"), by("Under Development")
CX_GONE_MW = rows[(rows.status == "Cancelled") & ~rows.replaced_later].mw.sum()
pct = lambda v: round(100 * v / DISTINCT_MW)
assert abs(OP_MW + UC_MW + UD_MW + CX_GONE_MW - DISTINCT_MW) < 0.01
assert rows[rows.status == "Under Construction"].is_rebid.all()
PARTNER_MW = rows[rows.nypa_partner].mw.sum()
NYPA_NEW_MW = nypa[nypa.kind == "new"].mw.sum()
NYPA_REV_MW = nypa[nypa.kind == "revived"].mw.sum()
partner_by_year = [rows[(rows.year == y) & rows.nypa_partner].mw.sum() for y in years]

fig = plt.figure(figsize=(11, 7.4), dpi=300)
fig.patch.set_facecolor(SURFACE)
AX_BOTTOM, AX_H = 0.225, 0.42
ax = fig.add_axes([0.085, AX_BOTTOM, 0.885, AX_H])
ax.set_facecolor(SURFACE)

x = list(range(len(years)))
bar_w = 0.62
YMAX, YSTEP = 7000, 1000
for gy in range(0, YMAX + 1, YSTEP):
    ax.axhline(gy, color=GRID, linewidth=1, zorder=0)

base = [0.0] * len(years)
bottom_color = [None] * len(years)
osw_blocks = []   # (x, bottom, height, fill) for outline + label
for seg in ["onshore", "offshore"]:
    seg_start = list(base)
    for status, linked, fill, hcolor in STATUS_STYLE:
        vals = [mw(y, seg, status, linked) for y in years]
        for i, v in enumerate(vals):
            if v > 0 and bottom_color[i] is None:
                bottom_color[i] = fill
        if hcolor:
            ax.bar(x, vals, width=bar_w, bottom=base, color=fill, hatch=HATCH,
                   edgecolor=hcolor, linewidth=0, zorder=3)
            ax.bar(x, vals, width=bar_w, bottom=base, fill=False,
                   edgecolor=SURFACE, linewidth=1.1, zorder=3.5)
        else:
            ax.bar(x, vals, width=bar_w, bottom=base, color=fill, zorder=3,
                   edgecolor=SURFACE, linewidth=1.1)
        if seg == "offshore":
            for i, v in enumerate(vals):
                if v > 0:
                    osw_blocks.append((i, base[i], v, fill))
        base = [bb + v for bb, v in zip(base, vals)]

# offshore: dark outline around each year's offshore block, labelled inside
for i, b0, h, fill in osw_blocks:
    ax.add_patch(plt.Rectangle((i - bar_w / 2, b0), bar_w, h, fill=False,
                               edgecolor=TEXT_PRIMARY, linewidth=1.6, zorder=5))
    dark = fill in (CANCELLED, OPERATING)
    ax.text(i, b0 + h / 2, "Offshore\nwind", ha="center", va="center", fontsize=8,
            fontweight="bold", color="white" if dark else TEXT_PRIMARY, zorder=6,
            linespacing=1.1, bbox=dict(boxstyle="round,pad=0.25", fc=fill, ec="none"))

# ---- NYPA: side strip = NYPA-partnered MW of that round's active contracts ----
STRIP_W = 0.09
for i, p in enumerate(partner_by_year):
    if p > 0:
        sx = i + bar_w / 2 + 0.03 + STRIP_W / 2
        ax.bar(sx, p, width=STRIP_W, color=NYPA, zorder=3, linewidth=0)
        ax.text(sx, p + 50, f"{p:,.0f}", ha="center", va="bottom", fontsize=8,
                color=NYPA, fontweight="bold", rotation=90)

# ---- NYPA column: projects with no active NYSERDA contract ----
NX = len(years) + 0.35
ax.axvline(len(years) - 0.35, color=RULE, linewidth=1, linestyle=(0, (3, 3)), zorder=1)
ax.bar(NX, NYPA_NEW_MW, width=bar_w, color=NYPA, zorder=3, edgecolor=SURFACE, linewidth=1.1)
ax.bar(NX, NYPA_REV_MW, width=bar_w, bottom=NYPA_NEW_MW, color=NYPA, hatch=HATCH,
       edgecolor=NYPA_HATCH, linewidth=0, zorder=3)
ax.bar(NX, NYPA_REV_MW, width=bar_w, bottom=NYPA_NEW_MW, fill=False,
       edgecolor=SURFACE, linewidth=1.1, zorder=3.5)
ax.text(NX, NYPA_NEW_MW + NYPA_REV_MW + 90, f"{NYPA_NEW_MW + NYPA_REV_MW:,.0f}",
        ha="center", va="bottom", fontsize=9.5, color=TEXT_SECONDARY)
for yc, txt in [(NYPA_NEW_MW / 2, f"{NYPA_NEW_MW:,.0f} MW\nnew sites"),
                (NYPA_NEW_MW + NYPA_REV_MW / 2, f"{NYPA_REV_MW:,.0f} MW at\nex-NYSERDA\nsites")]:
    ax.text(NX + bar_w / 2 + 0.07, yc, txt, ha="left", va="center", fontsize=8,
            color=NYPA, fontweight="bold", linespacing=1.1, zorder=6)

for i, (o, tot) in enumerate(zip(operating, total_mw)):
    ax.text(i, tot + 90, f"{tot:,.0f}", ha="center", va="bottom",
            fontsize=9.5, color=TEXT_SECONDARY)
    if o > 150:
        ax.text(i, o / 2, f"{o:,.0f}", ha="center", va="center",
                fontsize=9.5, color="white", fontweight="bold", zorder=4)
    else:
        ax.text(i, 110, f"{o:,.0f}", ha="center", va="bottom", fontsize=9.5,
                color=OPERATING if o > 0 else TEXT_SECONDARY, fontweight="bold", zorder=6,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none"))

ax.set_xticks(x + [NX])
ax.set_xticklabels(labels + ["NYPA\u2021"], fontsize=10, color=TEXT_PRIMARY)
ax.get_xticklabels()[-1].set_color(NYPA); ax.get_xticklabels()[-1].set_fontweight("bold")
ax.set_xlim(-0.6, NX + 1.25)
ax.set_xlabel(f"NYSERDA solicitation round  ·  bar colors show each contract's status as of {AS_OF}", fontsize=10, color=TEXT_SECONDARY, labelpad=8)
ax.set_ylim(0, YMAX * 1.04)
ax.set_yticks(range(0, YMAX + 1, YSTEP))
ax.set_yticklabels([f"{v:,}" for v in range(0, YMAX + 1, YSTEP)], fontsize=9.5,
                   color=TEXT_SECONDARY)
ax.set_ylabel("Renewable capacity (MW)", fontsize=10,
              color=TEXT_SECONDARY, labelpad=10)
for side in ["top", "right", "left"]:
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(RULE)
ax.tick_params(axis="both", length=0)

def legend_row(items, ly):
    lx = 0.0
    for kind, color, label in items:
        if kind == "solid":
            patch = dict(facecolor=color, edgecolor=color, linewidth=0)
        elif kind == "hatch":
            patch = dict(facecolor=SURFACE, hatch=HATCH, edgecolor=TEXT_MUTED, linewidth=0)
        else:  # outline
            patch = dict(facecolor=SURFACE, edgecolor=TEXT_PRIMARY, linewidth=1.4)
        ax.add_patch(plt.Rectangle((lx, ly), 0.022, 0.032, transform=ax.transAxes,
                                   clip_on=False, **patch))
        ax.text(lx + 0.032, ly + 0.016, label, transform=ax.transAxes,
                fontsize=10, color=TEXT_PRIMARY, va="center", ha="left")
        lx += 0.032 + 0.0075 * len(label) + 0.04

legend_row([("solid", OPERATING, "Operating"), ("solid", UNDERCON, "Under construction"),
            ("solid", UNDERDEV, "Under development"), ("solid", CANCELLED, "Cancelled")], 1.135)
legend_row([("hatch", None, "Hatched = cancelled award and its later rebid"),
            ("outline", None, "Outlined = offshore wind"), ("solid", NYPA, "NYPA-backed")], 1.065)

# ---- header ----
fig.text(0.085, 0.965, "NYSERDA & NYPA RENEWABLES SUPPORT  ·  NEW YORK STATE",
         fontsize=9, color=TEXT_MUTED, ha="left", va="top", fontweight="bold")
fig.text(0.97, 0.965, f"STATUS AS OF {AS_OF.upper()}", fontsize=9, color=TEXT_MUTED, ha="right", va="top",
         fontweight="bold")
fig.text(0.085, 0.935, "New York has put a lot of state support behind renewables",
         fontsize=18, fontweight="bold", color=TEXT_PRIMARY, ha="left", va="top")
subtitle = (
    f"Counting each site once, NYSERDA had contracted {DISTINCT_MW:,.0f} MW of large-scale renewables by {AS_OF}.\n"
    f"{pct(OP_MW)}% was operating, {pct(UC_MW)}% under construction and {pct(UD_MW)}% in development; {pct(CX_GONE_MW)}% had been cancelled. NYPA is\n"
    f"backing {PARTNER_MW:,.0f} MW of NYSERDA's active contracts (teal strips) and has lined up another {NYPA_NEW_MW + NYPA_REV_MW:,.0f} MW\n"
    f"of its own \u2014 {NYPA_REV_MW:,.0f} MW of it at sites whose NYSERDA contracts were cancelled."
)
fig.text(0.085, 0.885, subtitle, fontsize=11.5, color=TEXT_SECONDARY,
         ha="left", va="top", linespacing=1.6)
fig.add_artist(plt.Line2D([0.085, 0.97], [0.735, 0.735], color=RULE,
                          linewidth=1, transform=fig.transFigure))

# ---- footer ----
fig.add_artist(plt.Line2D([0.085, 0.97], [0.125, 0.125], color=RULE,
                          linewidth=1, transform=fig.transFigure))
fig.text(0.085, 0.107,
         "By Fred Stafford, @fredstaffordcs, PublicPowerReview.org  \u2022  chart assembled with Claude",
         fontsize=9, color=TEXT_MUTED, ha="left")
foot = [
    "Sources: NYSERDA Large-Scale Renewable Projects (data through 9/30/2026, incl. RESRFP25-1 contracts); "
    "NYISO interconnection queue (9/30/2026); EIA-860M (August 2026).",
    "All NYSERDA Tier 1 land-based awards (incl. repowers, upgrades, hydro, biogas, fuel cells) and offshore wind (OREC) awards, "
    "by solicitation name year. *Pre-2017: solicitations 2554/2985/3084/3257.",
    "Under construction: NYISO queue status 12 or EIA-860M status U/V; NYSERDA lists these as under development. Excelsior (280 MW) "
    "is energized (NYISO: in service) but not yet commercially operating.",
    "Hatched: a cancelled award whose site was later rebid, or the rebid itself (matched by queue, permitting case or "
    "NYSERDA bid rosters); add-ons to active awards aren't hatched.",
    "\u2021NYPA Renewables Dashboard (edited 9/30/2026), utility-scale wind & solar; excludes storage and distributed solar. Most entries are "
    "non-binding letters of intent; most NYSERDA matches inferred.",
]
for k, line in enumerate(foot):
    fig.text(0.085, 0.088 - 0.0175 * k, line, fontsize=7.5, color=TEXT_MUTED, ha="left")

out_path = SP + "ny_tier1_operating_chart.png"
fig.savefig(out_path, facecolor=SURFACE, dpi=300)
print("saved", out_path)

