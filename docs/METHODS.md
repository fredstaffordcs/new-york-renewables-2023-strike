# Methods

## The population

The "86" are the onshore Tier 1 projects that held NYSERDA Renewable Energy Standard (RES) contracts and
were listed as under development in NYSERDA's January 30, 2024 snapshot of the Large-scale Renewable
Projects dataset, and that fall within the domain of ACE NY's June 2023 petition (PSC Case 15-E-0302).
The roster also carries 31 related projects outside that domain for context, for 117 rows in total.
The `in_petition_86` column separates them; every headline number uses the 86 only.

Total capacity of the 86 is 7,535.99 MW.

## Fate categories

Each of the 86 is assigned exactly one fate:

1. **Re-bid and won** in RESRFP23-1, RESRFP24-1 or RESRFP25-1: the project (or a recognisable successor)
   received a new NYSERDA award after the original contract was cancelled.
2. **Re-bid, not awarded** in RESRFP25-1: bid but did not win.
3. **Built on the original contract**: operational under its original award.
4. **Abandoned**: original contract cancelled and no re-bid found.

A project counts as a re-bid when award documents or NYSERDA records link the new award to the old one. The
evidence, such as a shared Article 10 / ORES case number, a shared NYISO queue position, or identical
capacity, developer and town, is recorded per row in the 2023 and 2024 Crosswalk tabs (`classification`,
`evidence_notes`). A project's fate is never reclassified without reviewing that evidence.

## Matching rules

- **NYISO status is matched on queue position, never on project name.** NYISO names are generic and change
  (two unrelated entries are both called "Flat Creek Solar"; an Orleans County project is now listed under its
  re-bid name). Substring name searches produce false positives.
- Queue positions are normalised (`0591`, `591`, `591.0` and `1,198` all compare as numbers).
- A status priority applies when a position appears on several sheets: Active, then In Service, then Withdrawn.
- **Standing overrides** are encoded in `scripts/crosswalk_update_toolkit.py`:
  - Several roster rows carried a placeholder or blank queue number; the true positions are recorded
    (see `EFF_QUEUE`).
  - Three rows have no usable NYISO position and are labelled instead of matched (`NO_QUEUE`).
  - Positions 234 and 396 are legitimately shared by several in-service projects.
  - Roster #97 (Hecate Energy Greene County 1 to position 569) is **provisional**, because the NYISO name
    is generic.
- **Contract status** follows the latest NYSERDA contract record for the project, meaning the latest
  solicitation among records sharing its queue number. Proposals are not contracts: a bid never inherits a
  contract status.

## Price comparison

- The comparison uses **award-time REC strike prices** ($/MWh): the original contract strike against the strike
  in the re-bid award. These are in the 2023/2024 Crosswalk tabs.
- Statistics (median, mean, MW-weighted mean, range) cover only projects where both strikes are known:
  18 of 20 RESRFP23-1 re-bids. Two projects with no published prior strike are excluded.
- Several contracts include a one-time **price adjustment** tied to a producer price index after award.
  These are tracked separately on the Inflation Adjustment tab and never overwrite the award-time strikes.
  The formula is

  `REC_adjusted = REC_bid × (0.25 + 0.75 × Index_T / Index_B)`, with `Index_B = 255.56`.

  Where NYSERDA has published an adjusted strike, `Index_T` is back-solved from it.
- RESRFP24-1 strikes and RESRFP25-1 wind and solar strikes are not yet public. They appear as `TBD`.

## NYPA overlap

The New York Power Authority publishes a renewables dashboard with project codes, MW, town, developer and
schedule, but not project names. Each of the 117 roster rows was compared to the dashboard and given a
confidence tier:

| Tier | Meaning |
|---|---|
| Confirmed | NYPA or a public announcement names the project. |
| Plan-flagged | NYPA's own plan says that code won a NYSERDA award in a specific round. |
| Strong inferred | Exact MW, town and developer match, with no naming statement. |
| Probable / Possible | Weaker or ambiguous. |

A tier is never raised without a statement from NYPA or the developer naming the project. NYPA match columns do
not affect a project's fate.

## Corroboration

EIA Form 860M (monthly) is used only to corroborate construction and operating status. It never overrides
NYISO or NYSERDA status.

## Known limits

See the open questions in [UPDATING.md](UPDATING.md#open-questions), notably the fate of "Flat Creek II"
(possibly folded into the 2024 Flat Creek bid), and one RESRFP25-1 award whose capacity does not fit the
incremental pattern of the others.
