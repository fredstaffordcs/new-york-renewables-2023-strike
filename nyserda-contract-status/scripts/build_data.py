"""Build the per-row dataset for the chart from the NYSERDA Large-Scale Renewable
Projects file (data through 09/30/2026, which now carries the RESRFP25-1 contracts)
plus the rebid links in NY_RES_rebid_crosswalk.xlsx (10/23/2026 version)."""
import re, sys, pandas as pd, openpyxl
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 400)

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
D = str(ROOT / "data") + "/"
O = str(ROOT / "output") + "/"
df = pd.read_csv(D + "nyserda_20260930.csv")
DATA_THROUGH = df["Data Through Date"].iloc[0]
assert (df["Data Through Date"] == DATA_THROUGH).all() and DATA_THROUGH == "09/30/2026", DATA_THROUGH
MW = "New Renewable Capacity (MW)"
df[MW] = pd.to_numeric(df[MW].astype(str).str.replace(",", ""), errors="coerce")
df["sol"] = df["Solicitation Name"].astype(str).str.strip()
df["q"] = df["Interconnection Queue Number"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

YEAR = {"2554": "Pre-2017", "2985": "Pre-2017", "3084": "Pre-2017", "3257": "Pre-2017", "BRRFP23-1": "2023"}
for y in range(17, 26):
    YEAR[f"RESRFP{y}-1"] = f"20{y}"
for s in df["sol"].unique():
    m = re.match(r"ORECRFP(\d\d)-1", s)
    if m: YEAR[s] = "20" + m.group(1)

# Everything NYSERDA counts as a Tier 1 land-based award: new builds plus
# repowers, upgrades, return-to-service hydro, biogas and fuel cells.
onshore = df[(df["Eligibility"] == "Tier 1") & df["sol"].isin(YEAR)].copy()
onshore["seg"] = "onshore"
osw = df[(df["Eligibility"] == "OREC") & (df["Renewable Technology"] == "Offshore Wind")].copy()
osw["seg"] = "offshore"
rows = pd.concat([onshore, osw])
rows["year"] = rows["sol"].map(YEAR)
rows["status"] = rows["Project Status"].str.strip().replace({"Canceled - Other": "Cancelled"})
rows["name"] = rows["Project Name"].str.strip()
rows["mw"] = rows[MW]
rows = rows[["year", "sol", "seg", "name", "status", "mw", "q"]].reset_index(drop=True)
assert rows["mw"].notna().all(), rows[rows.mw.isna()]
assert rows["status"].isin(["Operational", "Under Development", "Cancelled"]).all(), rows.status.unique()
# RESRFP25-1: 13 contracts in the dataset; NYSERDA's announcement said "more than 719 MW"
r25 = rows[rows.sol == "RESRFP25-1"]
assert len(r25) == 13 and abs(r25.mw.sum() - 718.9) < 0.01, (len(r25), r25.mw.sum())

def rid(sol, name):
    m = rows[(rows.sol == sol) & (rows.name == name)]
    assert len(m) == 1, (sol, name, len(m))
    return m.index[0]

# ---- rebid links: (earlier row) -> (later row that replaces it)
links = []
# RESRFP23-1 and 24-1 winners from the crosswalk, matched to the NYSERDA row in
# the new round by queue number of the prior award, falling back to name.
wb = openpyxl.load_workbook(D + "crosswalk.xlsx", data_only=True)
for sheet, new_sol in [("2023 Crosswalk", "RESRFP23-1"), ("2024 Crosswalk", "RESRFP24-1")]:
    hdr = [c.value for c in wb[sheet][4]]
    assert hdr[1] == "Bid / awarded project" and hdr[3] == "Outcome" and hdr[10] == "Prior round" \
        and hdr[11] == "Prior project" and hdr[12] == "Prior status" and hdr[18] == "Classification", hdr
    for r in wb[sheet].iter_rows(min_row=5, values_only=True):
        if r[3] != "Won" or r[18] != "Re-bid" or r[12] != "Cancelled": continue
        old = rid(r[10], r[11])
        cand = rows[(rows.sol == new_sol) & (rows.q == rows.loc[old, "q"]) & (rows.q.notna()) & (rows.q != "nan")]
        if len(cand) != 1:
            key = re.sub(r"[^a-z]", "", r[1].lower())[:8]
            cand = rows[(rows.sol == new_sol) & rows.name.str.lower().str.replace(r"[^a-z]", "", regex=True).str.startswith(key)]
        assert len(cand) == 1, (sheet, r[1], len(cand))
        links.append((old, cand.index[0]))
# RESRFP25-1 re-bids (crosswalk '2025 Proposals (verified)'), now with dataset names
links += [(rid("RESRFP21-1", "Rich Road Solar Energy Center"), rid("RESRFP25-1", "Rich Road Solar Energy Center")),
          (rid("RESRFP17-1", "Flint Mine Solar"), rid("RESRFP25-1", "Flint Mine Solar")),
          (rid("RESRFP19-1", "Greens Corners Solar"), rid("RESRFP25-1", "Greens Corners Solar Park")),
          (rid("RESRFP19-1", "Sandy Creek Solar"), rid("RESRFP25-1", "Greens Corners Solar Park")),  # queue 843 folded into the 2025 bid
          (rid("3257", "Greene County 1"), rid("RESRFP25-1", "Hecate Energy Greene 1 LLC")),
          (rid("3257", "Greene County 2"), rid("RESRFP25-1", "Hecate Energy Greene 2 LLC"))]
# RESRFP22-1 rebids (outside the crosswalk's 23/24 tabs): same NYISO queue number
links += [(rid("RESRFP20-1", "Clear View Solar"), rid("RESRFP22-1", "Clear View Solar")),
          (rid("RESRFP20-1", "Hatchery Solar"), rid("RESRFP22-1", "Hatchery Solar")),
          (rid("RESRFP20-1", "Orleans Solar"), rid("RESRFP22-1", "Hemlock Ridge Solar"))]  # queue 950
# Hydro sites that were cancelled and came back (same facility, same developer)
links += [(rid("RESRFP22-1", "Dolgeville Hydro"), rid("RESRFP24-1", "Dolgeville Hydro")),
          (rid("3084", "Lyons Falls Mill Hydro"), rid("RESRFP17-1", "Lyons Falls Mill Redevelopment")),
          (rid("RESRFP17-1", "Lyons Falls Mill Redevelopment"), rid("RESRFP24-1", "Lyons Falls Mill Repower"))]
# Valcour 2024/2025 awards, Canisteo's 2025 award and the four RESRFP25-1 hydro
# repowers ADD capacity at sites whose earlier award is still active (or had no
# earlier Tier 1 award), so they are summed, not linked as rebids.
# Offshore: 2018 awards re-bid into the 2023 expedited round (same Article VII case)
links += [(rid("ORECRFP18-1", "Empire Wind 1"), rid("ORECRFP23-1", "Empire Wind")),
          (rid("ORECRFP18-1", "Sunrise Wind"), rid("ORECRFP23-1", "Sunrise Wind"))]

assert len(set(links)) == len(links)
earlier = {a for a, b in links}; later = {b for a, b in links}
rows["replaced_later"] = rows.index.isin(earlier)     # an earlier appearance of a site that came back
rows["is_rebid"] = rows.index.isin(later)             # a later appearance of a previously cancelled site
rows["linked"] = rows.replaced_later | rows.is_rebid
assert (rows.loc[list(earlier), "status"] == "Cancelled").all()

# ---- Under construction. NYSERDA's status field has no construction stage, so
# this comes from NYISO's queue (status 12 "Under Construction", 9/30/2026 file,
# per the crosswalk's roster column AK)
# or EIA-860M (status U/V, August 2026) -- either source is enough. No newer
# NYISO or EIA file has been added since; Baron Winds II, the one project that
# had crossed into operation ahead of NYSERDA, is now Operational in NYSERDA's
# own 9/30 data, so no "built ahead of NYSERDA" override is needed any more.
# Excelsior (q721) moved to NYISO's "In Service" sheet in the 9/30 queue. NYISO "In
# Service" = energized, not commercial operation (8/31 file gave COD 11-2026), and
# NYSERDA still lists it Under Development, so it stays "under construction" here.
UC = {("RESRFP23-1", n) for n in ["Alle-Catt Wind", "Cider Solar Farm", "Excelsior Energy Center LLC",
      "Dog Corners Solar", "Flat Hill Solar", "Valley Solar", "Scipio Solar", "Watkins Road Solar"]
      } | {("ORECRFP23-1", "Empire Wind"), ("ORECRFP23-1", "Sunrise Wind")}
for k in UC:
    assert rows.loc[rid(*k), "status"] == "Under Development", (k, rows.loc[rid(*k), "status"])
rows["uc"] = [(s_, n) in UC for s_, n in zip(rows.sol, rows.name)]
rows.loc[rows.uc, "status"] = "Under Construction"
assert rows.loc[rid("RESRFP23-1", "Baron Winds II"), "status"] == "Operational"
rows["built_ahead_of_nyserda"] = False

if __name__ == "__main__":
    print("data through", DATA_THROUGH, "| rows", len(rows), "| links", len(links))
    for a, b in links:
        print(f"  {rows.loc[a,'year']} {rows.loc[a,'name']} ({rows.loc[a,'mw']}) -> {rows.loc[b,'year']} {rows.loc[b,'name']} ({rows.loc[b,'mw']}, {rows.loc[b,'status']})")
    rows.to_pickle(O + "rows.pkl")
