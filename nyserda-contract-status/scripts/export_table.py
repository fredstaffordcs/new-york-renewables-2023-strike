"""Per-round MW table behind the chart + headline breakdown, and a diff vs the 9/25 version."""
import pandas as pd
from pathlib import Path
O = str(Path(__file__).resolve().parents[1] / "output") + "/"
rows = pd.read_pickle(O + "rows_nypa.pkl"); nypa = pd.read_pickle(O + "nypa_only.pkl")
years = ["Pre-2017"] + [str(y) for y in range(2017, 2026)]
labels = ["Pre-2017*"] + [str(y) for y in range(2017, 2026)]

def s(mask): return round(rows[mask].mw.sum(), 2)
out = []
for y, lab in zip(years, labels):
    Y = rows.year == y
    out.append(dict(round_label=lab,
        operating_mw=s(Y & (rows.status == "Operational") & ~rows.linked),
        operating_rebid_mw=s(Y & (rows.status == "Operational") & rows.linked),
        under_construction_rebid_mw=s(Y & (rows.status == "Under Construction")),
        under_development_mw=s(Y & (rows.status == "Under Development") & ~rows.linked),
        under_development_rebid_mw=s(Y & (rows.status == "Under Development") & rows.linked),
        cancelled_linked_to_rebid_mw=s(Y & (rows.status == "Cancelled") & rows.linked),
        cancelled_mw=s(Y & (rows.status == "Cancelled") & ~rows.linked),
        total_mw=s(Y), of_which_offshore_mw=s(Y & (rows.seg == "offshore")),
        of_which_nypa_backed_mw=s(Y & rows.nypa_partner), nypa_new_site_mw=0.0, nypa_ex_nyserda_site_mw=0.0))
assert rows[rows.status == "Under Construction"].linked.all()
out.append(dict(round_label="NYPA‡ (no active NYSERDA contract)", operating_mw=0, operating_rebid_mw=0,
    under_construction_rebid_mw=0, under_development_mw=0, under_development_rebid_mw=0,
    cancelled_linked_to_rebid_mw=0, cancelled_mw=0, total_mw=round(nypa.mw.sum(), 2), of_which_offshore_mw=0,
    of_which_nypa_backed_mw=0, nypa_new_site_mw=nypa[nypa.kind == "new"].mw.sum(),
    nypa_ex_nyserda_site_mw=nypa[nypa.kind == "revived"].mw.sum()))
t = pd.DataFrame(out)
t.to_csv(O + "ny_renewable_status_by_round.csv", index=False, float_format="%.2f")

# headline: each site once
d = rows[~rows.replaced_later]
tot = d.mw.sum()
print("distinct total %.1f" % tot)
for st in ["Operational", "Under Construction", "Under Development", "Cancelled"]:
    v = d[d.status == st].mw.sum(); print(f"  {st:20s} {v:9.1f}  {100*v/tot:5.1f}%")

