"""NYPA renewables roster (NYPA_dashboard_roster_vs_NYSERDA.xlsx, 10/23/2026 version;
dashboard edited 9/30/2026) mapped onto the
chart's NYSERDA rows. Utility-scale wind & solar only (storage portfolios, CAES
and distributed-scale solar excluded; the dashboard has no hydro)."""
import pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
D = str(ROOT / "data") + "/"
O = str(ROOT / "output") + "/"
rows = pd.read_pickle(O + "rows.pkl")
ros = pd.read_excel(D + "nypa_roster.xlsx", sheet_name="NYPA roster", header=3)
ros.columns = [str(c).strip() for c in ros.columns]
ros = ros[ros["NYPA code"].notna()].set_index("NYPA code")
assert len(ros) == 41 and ros.index.is_unique, len(ros)
ros["mw"] = pd.to_numeric(ros["MW (dashboard)"])

def rid(sol, name):
    m = rows[(rows.sol == sol) & (rows.name == name)]
    assert len(m) == 1, (sol, name, len(m)); return m.index[0]

# 1) NYPA partner on a NYSERDA contract that is still active (counted in the bars)
PARTNERED = {
    "B4": [("RESRFP24-1", "Fort Covington Solar Farm")], "B5": [("RESRFP24-1", "Two Rivers Solar Farm")],
    "C1": [("RESRFP24-1", "Mill Point Solar I")], "D3": [("RESRFP24-1", "Somers Solar")],
    "E3": [("RESRFP24-1", "Horseshoe Solar Energy Center")],
    "E9": [("RESRFP23-1", "Canisteo Wind Energy Center"), ("RESRFP25-1", "Canisteo Wind Energy Center")],
    "F3": [("RESRFP23-1", "Garnet Energy Center, LLC")], "F4": [("RESRFP23-1", "Trelina Solar Energy Center, LLC")],
    "N1": [("RESRFP25-1", "Rich Road Solar Energy Center")],
    "Q1": [("RESRFP25-1", "Hecate Energy Greene 1 LLC")], "Q2": [("RESRFP25-1", "Hecate Energy Greene 2 LLC")],
}
# 2) NYPA project at a site whose only NYSERDA contract(s) were cancelled
REVIVED = {"B6": ("RESRFP21-1", "Fort Edward Solar Farm"), "C2": ("RESRFP24-1", "South Ripley Solar"),
           "F1": ("RESRFP18-1", "Watkins Glen Solar Energy Center"), "F2": ("RESRFP19-1", "North Side Energy Center"),
           "J1": ("RESRFP18-1", "Hannacroix Solar Facility"), "L1": ("RESRFP22-1", "Riverside Solar"),
           "M1": ("RESRFP18-1", "Mohawk Solar")}
# 3) no NYSERDA award found
NEW = ["G1", "G2", "G3", "G4", "G18", "L2", "M2", "N3", "O2"]

assert set(ros[ros["Match confidence"] == "No NYSERDA award found"].index) == set(NEW)
rows["nypa_partner"] = False
for code, keys in PARTNERED.items():
    for k in keys:
        i = rid(*k); assert rows.loc[i, "status"] != "Cancelled", k
        rows.loc[i, "nypa_partner"] = True
for code, k in REVIVED.items():
    i = rid(*k); assert rows.loc[i, "status"] == "Cancelled" and not rows.loc[i, "replaced_later"], k

nypa = pd.DataFrame([dict(code=c, name=ros.loc[c, "Location (Dec-25 plan)"], mw=ros.loc[c, "mw"],
                          kind="revived" if c in REVIVED else "new",
                          confidence=ros.loc[c, "Match confidence"]) for c in list(REVIVED) + NEW])
if __name__ == "__main__":
    print(rows[rows.nypa_partner].groupby("year").mw.sum().round(1).to_dict(),
          "total partnered", round(rows[rows.nypa_partner].mw.sum(), 1))
    print(nypa.groupby("kind").mw.sum().to_dict(), "total", nypa.mw.sum())
    print(ros.loc[list(PARTNERED)+list(REVIVED), "Match confidence"].value_counts().to_dict())
    rows.to_pickle(O + "rows_nypa.pkl"); nypa.to_pickle(O + "nypa_only.pkl")

