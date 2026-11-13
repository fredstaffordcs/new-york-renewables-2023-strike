#!/usr/bin/env python3
"""Export the tidy CSV tables in data/derived/ from the crosswalk workbook.

The Excel workbook (workbooks/NY_RES_rebid_crosswalk.xlsx) is the working source of truth;
the CSVs are a convenience for people who would rather not open Excel. Re-run this script
whenever the workbook changes.

    python3 scripts/export_derived_data.py workbooks/NY_RES_rebid_crosswalk.xlsx data/derived

Values are read as last calculated by the spreadsheet application that saved the file
(openpyxl data_only=True), so open and save the workbook once after editing formulas.
Requires: openpyxl
"""
import csv
import re
import sys
from pathlib import Path

import openpyxl

ROSTER = "Project roster (117)"
HEADER_ROW = 4          # all data sheets: headers in row 4, data from row 5
ROSTER_LAST_ROW = 124

# Fixed roster columns -> machine-friendly names (see docs/DATA_DICTIONARY.md)
ROSTER_FIXED = {
    "#": "roster_num",
    "In the 86?": "in_petition_86",
    "Category / fate": "fate",
    "Project (as listed 1/30/2024)": "project_name",
    "Original round": "original_round",
    "Tech": "tech",
    "Developer": "developer",
    "County": "county",
    "MW": "mw",
    "Annual MWh": "annual_mwh",
    "Orig. REC $/MWh": "orig_rec_usd_mwh",
    "Price type": "price_type",
    "RESRFP23-1 outcome": "outcome_resrfp23_1",
    "RESRFP24-1 outcome": "outcome_resrfp24_1",
    "RESRFP25-1 outcome": "outcome_resrfp25_1",
    "Re-bid REC $/MWh": "rebid_rec_usd_mwh",
    "NYISO queue": "nyiso_queue_as_listed",
    "Art.10/94-c case": "permit_case",
}
NYPA_HEADERS = {
    "NYPA roster status": "nypa_roster_status",
    "NYPA project code": "nypa_project_code",
    "NYPA match confidence": "nypa_match_confidence",
    "NYPA match evidence & caveats": "nypa_match_evidence",
}
DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def iso(m):
    return f"{m.group(3)}_{int(m.group(1)):02d}_{int(m.group(2)):02d}"


def slug(text):
    if str(text).strip() == "#":
        return "num"
    s = re.sub(r"[^0-9a-zA-Z]+", "_", str(text).strip().lower()).strip("_")
    return s or "col"


def clean(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return repr(round(v, 10)).rstrip("0").rstrip(".") if v != int(v) else str(int(v))
    return str(v).replace("\r", " ").replace("\n", " ").strip()


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow([clean(x) for x in r])
    print(f"  wrote {path}  ({len(rows)} rows x {len(header)} cols)")


def roster_names(headers):
    """Map each roster header to a stable machine name; returns list of (name, is_nypa)."""
    names, last_status_date = [], None
    for h in headers:
        h = str(h).strip()
        if h in ROSTER_FIXED:
            names.append((ROSTER_FIXED[h], False))
            continue
        hit = next((v for k, v in NYPA_HEADERS.items() if h.startswith(k)), None)
        if hit:
            names.append((hit, True))
            continue
        m = DATE_RE.search(h)
        if h.startswith("Contract Status"):
            names.append((f"contract_status_{iso(m)}", False))
        elif h.startswith("Contract change vs"):
            names.append(("contract_change_notes_latest", False))
        elif h.startswith("NYISO interconnection status"):
            last_status_date = iso(m)
            names.append((f"nyiso_status_{last_status_date}", False))
        elif h.startswith("Change vs"):
            names.append((f"nyiso_change_notes_{last_status_date}", False))
        else:
            raise SystemExit(f"Unrecognised roster header {h!r}: update ROSTER_FIXED / rules in {__file__}")
    return names


def export_roster(wb, out):
    ws = wb[ROSTER]
    headers = [c.value for c in ws[HEADER_ROW]]
    headers = [h for h in headers if h is not None]
    names = roster_names(headers)
    rows = []
    for r in ws.iter_rows(min_row=HEADER_ROW + 1, max_row=ROSTER_LAST_ROW, max_col=len(headers), values_only=True):
        if r[0] is None or not str(r[0]).strip().isdigit():
            continue                      # separator / subtotal / total rows
        rows.append(list(r))
    assert len(rows) == 117, f"expected 117 roster rows, found {len(rows)}"

    core = [i for i, (n, nypa) in enumerate(names) if not nypa]
    write_csv(out / "roster_117.csv", [names[i][0] for i in core], [[r[i] for i in core] for r in rows])

    idx = {n: i for i, (n, _) in enumerate(names)}
    nypa_cols = [i for i, (n, nypa) in enumerate(names) if nypa]
    head = ["roster_num", "project_name", "in_petition_86", "mw", "fate"] + [names[i][0] for i in nypa_cols]
    body = [[r[idx[k]] for k in ("roster_num", "project_name", "in_petition_86", "mw", "fate")]
            + [r[i] for i in nypa_cols] for r in rows]
    write_csv(out / "nypa_overlap.csv", head, body)


def export_table(wb, sheet, filename, out, first_col_numeric=True, header_row=HEADER_ROW,
                 stop_at_blank=True, rename=None):
    ws = wb[sheet]
    headers = [c.value for c in ws[header_row] if c.value is not None]
    names = [(rename or {}).get(h, slug(h)) for h in headers]
    rows = []
    for r in ws.iter_rows(min_row=header_row + 1, max_col=len(headers), values_only=True):
        first = r[0]
        if first is None or (first_col_numeric and not str(first).strip().isdigit()):
            if stop_at_blank:
                break
            continue
        rows.append(list(r))
    write_csv(out / filename, names, rows)
    return len(rows)


def export_inflation(wb, out):
    ws = wb["Inflation Adjustment"]
    hdr_row = next(i for i in range(1, ws.max_row + 1) if ws.cell(row=i, column=1).value == "#"
                   and ws.cell(row=i, column=2).value == "Project")
    export_table(wb, "Inflation Adjustment", "price_adjustment_contracts.csv", out, header_row=hdr_row,
                 rename={"Idx strike (9/30/2026)": "index_strike_latest",
                         "Award strike (bid)": "award_strike_bid",
                         "Realized adj.": "realized_adjustment",
                         "Implied Index_T": "implied_index_t"})


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 1
    wb_path, out = Path(argv[1]), Path(argv[2])
    out.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.load_workbook(wb_path, data_only=True)
    print(f"Exporting from {wb_path.name}")
    export_roster(wb, out)
    n23 = export_table(wb, "2023 Crosswalk", "resrfp23_1_bids.csv", out)
    n24 = export_table(wb, "2024 Crosswalk", "resrfp24_1_bids.csv", out)
    assert (n23, n24) == (57, 36), f"unexpected bid counts: {n23}, {n24}"
    export_table(wb, "2025 Proposals (verified)", "resrfp25_1_proposals.csv", out,
                 rename={"2025 Proposal": "proposal_2025"})
    export_inflation(wb, out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
