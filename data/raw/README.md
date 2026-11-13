# Raw source data

The main workbook's source files are not redistributed here (the `nyserda-contract-status/` folder does include its own copies of its three inputs); they belong to their publishers. Download them from the
original sources and keep them **outside** this repository tree (or in this folder, which is git-ignored).

| File | Where to get it |
|---|---|
| `Large-scale_Renewable_Projects_Reported_by_NYSERDA__Beginning_2004_YYYYMMDD.csv` | Export from the [NYSERDA Open NY dataset](https://data.ny.gov/Energy-Environment/Large-scale-Renewable-Projects-Reported-by-NYSERDA/dprp-55ye). The date in the filename is the download date; read the `Data Through Date` column for the data vintage. |
| `NYISO-Interconnection-Queue-MMDDYYYY.xlsx` | The current file linked from <https://www.nyiso.com/interconnections>. NYISO lists only the latest file. |
| `<month>_generator<year>.xlsx` (EIA 860M) | <https://www.eia.gov/electricity/data/eia860m/> |
| NYPA Renewables Dashboard | NYPA's public dashboard, which is backed by an ArcGIS feature layer. The roster's NYPA columns record what was read and when. |

The history of what each source showed at each date is preserved in the roster (`contract_status_*` and
`nyiso_status_*` columns), so the published workbook can be audited without the raw files.
