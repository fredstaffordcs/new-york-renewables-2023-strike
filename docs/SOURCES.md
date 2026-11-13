# Sources and data vintages

The analysis combines four public sources. Source data is not redistributed in this repository; see
[`data/raw/README.md`](../data/raw/README.md) for how to obtain it.

| Source | What it supplies | Vintages used |
|---|---|---|
| **NYSERDA**, [Large-scale Renewable Projects Reported by NYSERDA: Beginning 2004](https://data.ny.gov/Energy-Environment/Large-scale-Renewable-Projects-Reported-by-NYSERDA/dprp-55ye) (Open NY dataset `dprp-55ye`) | Contract status, MW, strike prices, solicitation, queue number | 1/30/2024, 3/31/2026, 6/11/2026, 9/30/2026 |
| **NYISO**, [Interconnection Queue](https://www.nyiso.com/interconnections) (monthly Excel file) | Queue status of each project, matched by queue position | 4/30/2026 through 9/30/2026 |
| **NYPA**, Renewables Dashboard (public ArcGIS feature layer) | Project codes, MW, town, developer, schedule | Layer edited 9/30/2026 (41 features) |
| **EIA**, [Form 860M](https://www.eia.gov/electricity/data/eia860m/) | Construction/operating status, corroboration only | September 2026 |

Other inputs: the Public Service Commission petition and order in Case 15-E-0302 (June 2023 petition,
denied 10/12/2023); NYSERDA solicitation award fact sheets; Article 10 / ORES permit records; and public
news reporting, cited in the workbook where used.

## Reading the vintages

- **NYSERDA files are named for their download date, not their data date.** A file downloaded on
  October 1, 2026 holds data through 9/30/2026. Always read the `Data Through Date` column.
- The NYSERDA dataset posts roughly quarterly; NYISO posts monthly. The two registries are independent and
  only bracket events (see the README caveats).
- Column names in the NYSERDA dataset change occasionally. As of 9/30/2026 `Inflation Adjustment` became
  `Price Adjustment` with identical values. The update toolkit flags any added or removed column.
- The status label `Canceled - Other` (American spelling) appears alongside `Cancelled`.

## Version history

| Workbook date | Change |
|---|---|
| Oct 2026 | NYSERDA through 9/30/2026 (first RESRFP25-1 contracts); NYISO 8/31 then 9/30/2026; NYPA dashboard columns added |
| 12 Nov 2026 | Notes refreshed (EIA September 860M corroboration, re-check dates). No counts changed. |

Latest upstream status when this was published (12 Nov 2026): the NYSERDA dataset was last refreshed
9/30/2026, NYISO's newest posted file was 9/30/2026, the NYPA layer was last edited 9/30/2026, and EIA's
September file was the latest. Next expected: NYISO 10/31 file, EIA October file (late November), a NYPA
quarter-end refresh (about late December) and the next NYSERDA quarterly refresh (about early January 2027).
