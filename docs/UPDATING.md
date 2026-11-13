# Updating the crosswalk with new data

This guide is for maintainers and for anyone who wants to extend the analysis with a newer NYISO queue file
or NYSERDA dataset. The detection script does the mechanical comparison; the judgment calls below are made
by hand.

## Setup

```bash
pip install -r requirements.txt
```

Keep downloaded source files in a separate directory from the scripts, and run Python with `-I` so that
nothing in the data directory can be imported as code. Never run scripts from inside a downloads folder.

## 1. NYISO interconnection queue (monthly)

Download the new queue file from <https://www.nyiso.com/interconnections>, then:

```bash
python3 -I scripts/crosswalk_update_toolkit.py nyiso NEW_QUEUE.xlsx workbooks/NY_RES_rebid_crosswalk.xlsx res.pkl
```

It prints sheet sanity checks, every roster row whose status differs from the latest NYISO column, re-tests
of the known no-match rows, and the new split of the 86 by status.

**File layout** (verified through September 2026; the script prints these each run, so re-check):

| Sheet | Header row (0-indexed) | Stage column |
|---|---|---|
| `Interconnection Queue` | 0 | index 16, header `Project Status #` (older files: `S`) |
| ` Cluster Projects` (**leading space**) | 0 | index 16 |
| `Withdrawn` | 0 | none |
| `Cluster Projects-Withdrawn` | 1 | none |
| `In Service` | 1 (two-row header) | none |

Blank-queue rows are filler. Duplicate queue positions have never occurred; investigate if one does.

To record the result in the workbook:

1. Append two columns at the far right of the roster: `NYISO interconnection status (M/D/YYYY)` and
   `Change vs <prior date> — notes`, copying styles from the previous pair.
2. Mark rows that changed from the prior column (red fill, bold white text) and explain each change in the
   notes column. Mark provisional matches amber.
3. Repoint the Summary section ⑤ formulas to the new column and update the dated titles and footnotes.

"In service" means energized, not in commercial operation. Say so in the note.

## 2. NYSERDA contracts (about quarterly)

Download the CSV from the [portal](https://data.ny.gov/Energy-Environment/Large-scale-Renewable-Projects-Reported-by-NYSERDA/dprp-55ye)
and compare it with the previous snapshot:

```bash
python3 -I scripts/crosswalk_update_toolkit.py nyserda NEW.csv PREV.csv workbooks/NY_RES_rebid_crosswalk.xlsx
```

The report covers data vintage, column renames, status labels, new solicitations, status changes, other field
changes, and a roster cross-check against every NYSERDA record that shares a roster row's queue number.

Conventions:

- The records are keyed on `(Project Name, Solicitation Name)`. About 14 legacy records have a numeric
  solicitation ID that shifts between snapshots; confirm these are off-roster.
- The roster tracks the **latest contract record for the project**. Check which record moved before editing: a
  cancelled original contract is not a cancelled re-bid.
- Expected exceptions in the cross-check: roster #44 (Sandy Creek is counted through the combined Greens
  Corners Solar Park contract) and #51 (Coeymans shares queue 570 with four older records).
- Do not reclassify a project's fate without reviewing the evidence.
- **Insert** the two new contract columns beside the latest contract column rather than appending, so the
  status history stays grouped. `openpyxl.insert_cols` does not update formulas on other sheets, merged ranges
  or column widths. Run the `refs` command first to list every formula that references roster columns:

```bash
python3 -I scripts/crosswalk_update_toolkit.py refs workbooks/NY_RES_rebid_crosswalk.xlsx
```

- Propagate status changes to the winners' "New status" column on the 2023 and 2024 Crosswalk tabs, to the
  Inflation Adjustment tab, to Built on original, and to award MW on the 2025 Proposals tab.

## 3. Other sources

- **NYPA dashboard.** Read the feature layer (cache-busting the request, and reconciling the feature count)
  and compare field by field against the stored read. Also check public reporting for each coded project.
  Record findings with a dated prefix. Never raise a match tier without a statement naming the project.
- **EIA 860M.** Filter `Plant State == 'NY'`, key on plant and generator ID, diff against the previous month,
  and note changes bearing on the 117. It corroborates and never overrides other sources.

## 4. Checks before publishing

1. Recalculate the workbook; confirm no formula errors. The formula count only goes up.
2. Recount the 86 by the new NYISO column with pandas; it must equal the Summary section ⑤ counts, and total
   MW must be 7,535.99.
3. The winners split from the latest contract column must match the sentence in the Summary.
4. Re-run the toolkit against the **output** workbook: NYISO should show no changes, and the NYSERDA
   cross-check should show only the two expected rows.
5. Diff the output against the previous workbook cell by cell; only intended cells should differ.
6. Run `scripts/export_derived_data.py` then `scripts/verify_headline_numbers.py`, and update the README if
   any published number changed.
7. Check that no local file paths, usernames or credentials appear in anything you commit.

## Open questions

These are unresolved and should be resolved explicitly rather than silently:

- **Flat Creek II (#61).** The RESRFP24-1 Flat Creek contract is 300 MW, equal to #24 (200 MW) plus #61
  (100 MW). #61 is classed Abandoned but may have been folded into the 2024 bid, which would change the
  count of 34.
- **Valcour Ellenburg RESRFP25-1 award (33.08 MW)** does not fit the incremental pattern the other awards do.
- **Roster #97** (Hecate Energy Greene County 1 and queue 569) is still provisional.
- **Watchlist:** Excelsior (#3) is In Service in NYISO but still Under Development in NYSERDA; High Bridge (#27)
  has a withdrawn queue position but a live contract; South Ripley (#25) and Orleans / Hemlock Ridge (#90) have
  cancelled contracts but active queue positions; Cider Solar (#2) keeps slipping its in-service date.
- **Pending price adjustments** on Flat Stone, Grassy Knoll, Hills and Watkins Road.
- **Unpublished strikes:** RESRFP24-1, and RESRFP25-1 wind and solar.
- **NYPA matches** remain unconfirmed for all Plan-flagged and Strong inferred rows.
