# Data dictionary

All CSVs in `data/derived/` are generated from `workbooks/NY_RES_rebid_crosswalk.xlsx` by
`scripts/export_derived_data.py`. They are UTF-8, comma-separated, with one header row. Blank means no value.
`TBD` means the value exists but has not been published. Footer, total and separator rows are omitted.

## `roster_117.csv`: one row per project (117 rows; 86 in the petition)

| Column | Meaning |
|---|---|
| `roster_num` | Row number 1–117. 1–86 are the petition projects; 87–117 are related projects outside it. |
| `in_petition_86` | `Yes` if the project is one of the 86 petition projects. |
| `fate` | Outcome category (see [METHODS](METHODS.md)): re-bid and won (2023/2024/2025), re-bid and not awarded (2025), built on original contract, or abandoned. |
| `project_name` | Name as listed in NYSERDA's 1/30/2024 snapshot. |
| `original_round` | NYSERDA solicitation of the original contract. |
| `tech` | Technology (solar, wind, storage). |
| `developer`, `county` | As recorded in the original award. |
| `mw` | Capacity in MW. |
| `annual_mwh` | Expected annual generation in MWh. |
| `orig_rec_usd_mwh` | Original REC strike price, $/MWh. |
| `price_type` | Fixed or index REC. |
| `outcome_resrfp23_1`, `outcome_resrfp24_1`, `outcome_resrfp25_1` | `Won`, `Bid, lost` or `No bid` in each re-procurement. |
| `rebid_rec_usd_mwh` | Strike price in the re-bid award, $/MWh. `TBD` if unpublished. |
| `contract_status_YYYY_MM_DD` | NYSERDA contract status in the snapshot of that date: Under Development, Operational, Cancelled. |
| `contract_change_notes_latest` | What changed in the latest contract snapshot and why. |
| `nyiso_status_YYYY_MM_DD` | NYISO queue status in the file of that date: `Active in queue (LFIP stage N)`, `In service`, `Withdrawn from queue`, or a label if there is no usable position. `(PROVISIONAL)` marks a doubtful match. |
| `nyiso_change_notes_YYYY_MM_DD` | Explanation of any change relative to the previous month's file. |
| `nyiso_queue_as_listed` | The queue number as originally listed on the roster (some are wrong or placeholders; the corrected positions are in the toolkit's `EFF_QUEUE`). |
| `permit_case` | Article 10 or Section 94-c / ORES case number. |

## `nypa_overlap.csv`: roster rows compared with NYPA's renewables dashboard

`roster_num`, `project_name`, `in_petition_86`, `mw` and `fate` as above, plus:

| Column | Meaning |
|---|---|
| `nypa_roster_status` | `On NYPA dashboard`, `In Dec-2025 NYPA plan only (not on dashboard)`, `Formerly in NYPA plan (dropped)` or `No match identified`. |
| `nypa_project_code` | NYPA's letter-number code (for example `F3`). NYPA publishes codes, not names. |
| `nypa_match_confidence` | Confirmed, Plan-flagged, Strong inferred, Probable or Possible. See [METHODS](METHODS.md#nypa-overlap). |
| `nypa_match_evidence` | The evidence and caveats behind the match, with dated reporting checks. |

## `resrfp23_1_bids.csv`, `resrfp24_1_bids.csv`: one row per bid or award in the round

| Column | Meaning |
|---|---|
| `num` | Row number within the round. |
| `bid_awarded_project` | Project name in the new award. |
| `in_the_86` | Whether it descends from a petition project. |
| `outcome` | Award outcome. |
| `county`, `tech`, `new_proposed_developer` | New project details. |
| `new_status` | Latest NYSERDA contract status of the new award. |
| `new_proposed_mw`, `new_strike_mwh` | New capacity and strike ($/MWh; may be `TBD`). |
| `prior_round`, `prior_project`, `prior_status`, `prior_mw`, `prior_strike_mwh` | The original contract it replaces. |
| `strike_change` | New strike ÷ prior strike − 1. |
| `new_award_source`, `prior_award_source` | Where each figure comes from. |
| `classification` | How the link was classified (for example `Re-bid`). |
| `evidence_notes` | Evidence for the link. |
| `inflation_adj` | `Yes` if the contract has a one-time index price adjustment. |
| `prior_annual_mwh` | Expected annual MWh of the original contract. |

## `resrfp25_1_proposals.csv`: the 15 proposals in RESRFP25-1

`proposal_2025`, `tech`, `county_town`, `proposer`, `bid_mw`, `queue` (NYISO position), `ores_a10_case`,
`prior_nyserda_award_match`, `classification` (for example `Re-bid of abandoned`), `prior_annual_mwh`,
`resrfp25_1_result_9_23_2026` (result as announced), `result_note`, and `award_mw_9_30_2026_dataset` (award
capacity in the 9/30/2026 NYSERDA data).

## `price_adjustment_contracts.csv`: the 17 contracts with a one-time price adjustment

`project`, `round`, `status`, `mw`, `index_strike_latest` (latest published strike), `award_strike_bid`,
`realized_adjustment` (fractional increase from the award strike), `implied_index_t` (the producer price index
value implied by the adjustment; see the formula in [METHODS](METHODS.md#price-comparison)), and
`where_it_appears_in_this_workbook`.
