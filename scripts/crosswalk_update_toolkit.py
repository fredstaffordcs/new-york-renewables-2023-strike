"""crosswalk_update_toolkit.py — detection helpers for updating NY_RES_rebid_crosswalk.xlsx.

Read docs/UPDATING.md first. This script DETECTS changes and prints reports; it does not edit
the workbook. Workbook edits are judgment calls made per the update guide.

Keep data files in a separate directory from this script and run with `python3 -I`, passing
data files as arguments:

  python3 -I crosswalk_update_toolkit.py nyiso   NEW_QUEUE.xlsx  WORKBOOK.xlsx  [OUT_RESULTS.pkl]
  python3 -I crosswalk_update_toolkit.py nyserda NEW.csv  PREV.csv  WORKBOOK.xlsx
  python3 -I crosswalk_update_toolkit.py refs    WORKBOOK.xlsx

`nyiso`   builds lookups from the queue file, crosswalks all 117 roster rows using the standing
          overrides below, compares against the roster's most recent NYISO status column, and
          (optionally) pickles a DataFrame [num, in86, name, mw, qp, prev, new, changed] that a
          build script can use to write the new column.
`nyserda` profiles a new NYSERDA dprp-55ye CSV against the previous snapshot: vintage, column
          renames, status changes, other field changes, new solicitations, and a roster cross-check
          (every roster row vs. every NYSERDA record sharing its queue number).
`refs`    lists every formula that references roster columns (run before inserting columns).

Requires pandas, openpyxl (pip install -r requirements.txt).
"""
import re
import sys
from collections import Counter

import openpyxl
import pandas as pd

ROSTER = 'Project roster (117)'

# ---------------------------------------------------------------- standing roster overrides
# Effective NYISO queue position by roster # (roster's own queue cell is wrong, blank or a placeholder).
EFF_QUEUE = {
    45: '572',   # Greene County 1   (roster shows placeholder 570)
    46: '573',   # Greene County 2   (roster shows placeholder 570)
    51: '570',   # Coeymans Solar  = NYISO "Albany County 1", in service
    97: '569',   # Hecate Energy Greene County 1 -> best match "Greene County" 50 MW (PROVISIONAL; generic name)
    87: '519',   # Canisteo Wind & Storage (roster queue blank)
    83: '1165',  # West River Solar
    109: '582',  # Sunny Knoll Solar
    110: '635',  # Rising Solar
    111: '563',  # Double Lock Solar
}
# Rows with no usable NYISO position: label written instead of a status.
NO_QUEUE = {
    96: '(no match)',                      # Cohocton Wind Project; only new cluster entries named "Cohocton" exist
    115: '(not in large-facility queue)',  # Hannacroix; roster "queue" 8360 is not a NYISO position
    117: '(not in large-facility queue)',  # Java Solar; roster "queue" 12380 is not a NYISO position
}
PROVISIONAL = {97}
# Queue positions legitimately shared by several roster rows (resolved by name/MW, all in service):
KNOWN_SHARED = {'234', '396'}
# Roster rows whose contract status intentionally differs from "latest record on its queue":
EXPECTED_XCHECK = {
    44: 'expected: Sandy Creek is counted via the combined Greens Corners Solar Park RESRFP25-1 contract (q864)',
    51: 'expected: q570 is shared by four 2016-RPS records; Coeymans\'s own record is the Operational one',
}


def qnorm(v):
    """Normalize a queue position: '0591' / '591' / '591.0' / '1,198' -> '591'; cluster IDs kept as-is."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).replace(',', '').strip()
    if s in ('', 'nan', 'None'):
        return None
    if re.fullmatch(r'0*\d+(\.0)?', s):
        return str(int(float(s)))
    return s


# ---------------------------------------------------------------- NYISO
NYISO_SHEETS = [  # key, sheet name, header row (0-indexed), stage column index or None
    ('active', 'Interconnection Queue', 0, 16),
    ('inservice', 'In Service', 1, None),
    ('withdrawn', 'Withdrawn', 0, None),
    ('clust', ' Cluster Projects', 0, 16),            # note leading space in sheet name
    ('clustw', 'Cluster Projects-Withdrawn', 1, None),
]


def load_nyiso(path):
    xl = pd.ExcelFile(path)
    print('NYISO sheets:', xl.sheet_names)
    out = {}
    for key, sheet, hdr, stage in NYISO_SHEETS:
        if sheet not in xl.sheet_names:
            print(f'  !! sheet {sheet!r} missing — inspect the file layout before trusting results')
            out[key] = {}
            continue
        df = pd.read_excel(path, sheet_name=sheet, header=hdr, dtype=str)
        if stage is not None:
            print(f'  {sheet!r}: stage column header = {df.columns[stage]!r} (expect "Project Status #" or "S")')
        d, blank = {}, 0
        for _, r in df.iterrows():
            qp = qnorm(r.iloc[0])
            if qp is None:
                blank += 1
                if r.iloc[2] is not None and str(r.iloc[2]) != 'nan':
                    print(f'  !! {sheet}: row with project name but no queue position: {r.iloc[2]!r}')
                continue
            d[qp] = {'name': r.iloc[2], 'sp': r.iloc[4], 'stage': r.iloc[stage] if stage is not None else None}
        dupes = len(df) - blank - len(d)
        print(f'  {key:10s} rows={len(df):5d} blank-queue={blank:5d} unique={len(d):5d} dupes={dupes}')
        out[key] = d
    a = pd.read_excel(path, sheet_name='Interconnection Queue', header=0)
    if 'Last Updated Date' in a.columns:
        print('  max Last Updated Date (active sheet):', pd.to_datetime(a['Last Updated Date'], errors='coerce').max())
    return out


def nyiso_status(L, qp):
    if qp in L['active']:
        st = L['active'][qp]['stage']
        st = str(st).split('.')[0] if st is not None and str(st) != 'nan' else '?'
        return f'Active in queue (LFIP stage {st})'
    if qp in L['inservice']:
        return 'In service'
    if qp in L['withdrawn']:
        return 'Withdrawn from queue'
    return None


def _core(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    s = str(s).strip().replace(' (PROVISIONAL)', '')
    m = re.match(r'Active in queue \(LFIP stage (.+)\)', s)
    return ('active', m.group(1)) if m else (s.lower(),)


def load_roster(wb_path):
    d = pd.read_excel(wb_path, sheet_name=ROSTER, header=3)
    d.columns = [str(c).strip() for c in d.columns]
    d = d[pd.to_numeric(d['#'], errors='coerce').notna()].copy()
    d['#'] = d['#'].astype(int)
    d['qp'] = [EFF_QUEUE.get(n) or qnorm(v) for n, v in zip(d['#'], d['NYISO queue'])]
    assert len(d) == 117, f'expected 117 roster rows, got {len(d)}'
    return d


def latest_col(df, prefix):
    cols = [c for c in df.columns if c.startswith(prefix)]
    def key(c):
        m = re.search(r'\((\d+)/(\d+)/(\d{4})\)', c) or re.search(r'(\d+)/(\d+)/(\d{4})', c)
        return (int(m.group(3)), int(m.group(1)), int(m.group(2))) if m else (0, 0, 0)
    return sorted(cols, key=key)[-1] if cols else None


def cmd_nyiso(queue_path, wb_path, out_pkl=None):
    L = load_nyiso(queue_path)
    d = load_roster(wb_path)
    prev_col = latest_col(d, 'NYISO interconnection status')
    print(f'\nComparing against roster column: {prev_col!r}')
    shared = {q for q, n in Counter(q for k, q in zip(d['#'], d['qp']) if q and k not in NO_QUEUE).items() if n > 1}
    print('Shared queue positions among roster rows:', sorted(shared), '(expected', sorted(KNOWN_SHARED), ')')
    rows = []
    for _, r in d.iterrows():
        n = int(r['#'])
        prev = r[prev_col]
        prev = None if pd.isna(prev) else str(prev).strip()
        if n in NO_QUEUE:
            new = NO_QUEUE[n]
        elif not r['qp']:
            new = '(no queue # in roster)'
        else:
            new = nyiso_status(L, r['qp']) or '(not in current queue file)'
            if n in PROVISIONAL and new == 'Withdrawn from queue':
                new += ' (PROVISIONAL)'
        rows.append(dict(num=n, in86=r['In the 86?'], name=str(r['Project (as listed 1/30/2024)']),
                         mw=r['MW'], qp=r['qp'], prev=prev, new=new))
    res = pd.DataFrame(rows)
    res['changed'] = [_core(p) != _core(x) for p, x in zip(res['prev'], res['new'])]
    print(f'\n=== CHANGES vs {prev_col} ===')
    for _, x in res[res['changed']].iterrows():
        print(f"  #{x.num:>3} [{x.in86}] {x['name'][:38]:38} q{x.qp}: {x.prev}  -->  {x.new}")
    print('changed rows:', int(res['changed'].sum()))
    nf = res[res['new'] == '(not in current queue file)']
    if len(nf):
        print('\n!! roster queue numbers not found in any sheet (investigate by name/MW):')
        print(nf[['num', 'name', 'qp']].to_string(index=False))
    print('\nRe-test of static no-match rows:')
    for q in ('8360', '12380'):
        print(f'  q{q}:', 'FOUND — revisit NO_QUEUE' if any(q in L[k] for k in L) else 'still absent')
    for k in L:
        for q, v in L[k].items():
            if v['name'] and 'cohocton' in str(v['name']).lower():
                print(f'  Cohocton entries: [{k}] q{q} {v["name"]!r} {v["sp"]} MW stage={v["stage"]}')
    d86 = res[res['in86'] == 'Yes']
    def bucket(s):
        s = str(s)
        return ('Active' if s.startswith('Active') else 'In service' if s.startswith('In service')
                else 'Withdrawn' if s.startswith('Withdrawn') else 'Not in queue')
    print('\nThe 86 by new NYISO status:', d86['new'].map(bucket).value_counts().to_dict())
    if out_pkl:
        res.to_pickle(out_pkl)
        print('results pickled to', out_pkl)
    return res


# ---------------------------------------------------------------- NYSERDA
KEY = ['Project Name', 'Solicitation Name']


def cmd_nyserda(new_csv, prev_csv, wb_path):
    new = pd.read_csv(new_csv, dtype=str)
    old = pd.read_csv(prev_csv, dtype=str)
    print('NEW rows', len(new), 'Data Through Date', new['Data Through Date'].dropna().unique().tolist())
    print('OLD rows', len(old), 'Data Through Date', old['Data Through Date'].dropna().unique().tolist())
    added = [c for c in new.columns if c not in old.columns]
    removed = [c for c in old.columns if c not in new.columns]
    if added or removed:
        print('!! COLUMN CHANGES — added:', added, '| removed:', removed, '(check for renames)')
    print('NEW status labels:', new['Project Status'].value_counts(dropna=False).to_dict())
    for nm, df in (('NEW', new), ('OLD', old)):
        assert not df.duplicated(KEY).any(), f'{nm}: duplicate (Project Name, Solicitation Name) keys'
    print('New solicitations:', sorted(set(new['Solicitation Name'].dropna()) - set(old['Solicitation Name'].dropna())))
    m = old.merge(new, on=KEY, how='outer', suffixes=('_o', '_n'), indicator=True)
    lo, ro = m[m._merge == 'left_only'], m[m._merge == 'right_only']
    print(f'\nKey match: both={int((m._merge=="both").sum())} only-old={len(lo)} only-new={len(ro)}')
    if len(lo):
        print('Records only in OLD (often legacy Tier 2/hydro whose numeric "solicitation" ID shifts, or renames):')
        print(lo[KEY + ['Project Status_o', 'Interconnection Queue Number_o']].to_string(index=False))
    if len(ro):
        print('Records only in NEW:')
        print(ro[KEY + ['Project Status_n', 'New Renewable Capacity (MW)_n', 'Interconnection Queue Number_n']].to_string(index=False))
    b = m[m._merge == 'both']
    ch = b[b['Project Status_o'].fillna('') != b['Project Status_n'].fillna('')]
    print('\n=== STATUS CHANGES ===')
    print(ch[KEY + ['Project Status_o', 'Project Status_n', 'Renewable Technology_n', 'New Renewable Capacity (MW)_n',
                    'Interconnection Queue Number_n']].to_string(index=False) if len(ch) else '  (none)')
    skip = set(KEY) | {'Data Through Date', 'Georeference', 'Project Status'}
    cols = [c for c in old.columns if c in new.columns and c not in skip]
    print('\n=== OTHER FIELD CHANGES on matched records ===')
    n = 0
    for _, r in b.iterrows():
        for c in cols:
            a, z = r[c + '_o'], r[c + '_n']
            if not (pd.isna(a) and pd.isna(z)) and a != z:
                n += 1
                print(f"  {str(r['Project Name'])[:34]:34} {str(r['Solicitation Name']):>12} | {c}: {a!r} -> {z!r}")
    print('other-field changes:', n, '(watch especially Index (O)REC Strike Price, New Renewable Capacity, queue numbers)')

    # roster cross-check: every roster row vs every NYSERDA record sharing its queue position
    d = load_roster(wb_path)
    cs_col = latest_col(d, 'Contract Status')
    print(f'\n=== ROSTER CROSS-CHECK vs {cs_col!r} (latest solicitation on the queue = the tracked contract) ===')
    order = ['3257', 'RESRFP17-1', 'RESRFP18-1', 'RESRFP19-1', 'RESRFP20-1', 'RESRFP21-1', 'RESRFP22-1',
             'RESRFP23-1', 'RESRFP24-1', 'RESRFP25-1', 'RESRFP26-1', 'RESRFP27-1']
    for df in (new, old):
        df['q'] = df['Interconnection Queue Number'].map(qnorm)
    o = old.set_index(KEY)['Project Status']
    for _, r in d.iterrows():
        if not r['qp']:
            continue
        recs = new[new['q'] == r['qp']].copy()
        if recs.empty:
            continue
        recs['o'] = recs['Solicitation Name'].map(lambda s: order.index(s) if s in order else -1)
        recs = recs.sort_values('o')
        moved = any(o.get((x['Project Name'], x['Solicitation Name']), 'NEW') != x['Project Status'] for _, x in recs.iterrows())
        latest = recs.iloc[-1]['Project Status']
        mism = latest != r[cs_col]
        if moved or mism:
            desc = ' ; '.join(f"{x['Solicitation Name']}:{str(x['Project Name'])[:22]}="
                              f"{o.get((x['Project Name'], x['Solicitation Name']), 'NEW')}->{x['Project Status']}"
                              for _, x in recs.iterrows())
            print(f"  #{r['#']:>3} {str(r['Project (as listed 1/30/2024)'])[:28]:28} q{r['qp']:>5} "
                  f"roster={str(r[cs_col])[:17]:17}{'  <<MISMATCH' if mism else ''} | {desc}")
            if r['#'] in EXPECTED_XCHECK:
                print('        ^', EXPECTED_XCHECK[r['#']])
    print('Rows sharing queue 396/570/234 list several records — resolve by name, not "latest".')


# ---------------------------------------------------------------- formula refs
def cmd_refs(wb_path):
    wb = openpyxl.load_workbook(wb_path)
    pat = re.compile(r"'Project roster \(117\)'!\$?([A-Z]+)\$?\d+")
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith('='):
                    refs = re.findall(r'\$?([A-Z]+)\$?\d+', c.value) if ws.title == ROSTER else pat.findall(c.value)
                    if refs:
                        print(f'{ws.title}!{c.coordinate}: roster cols {sorted(set(refs))}')
    r = wb[ROSTER]
    print('Roster merges:', [str(m) for m in r.merged_cells.ranges])
    from openpyxl.utils import get_column_letter as L
    print('Roster headers (row 4):')
    for c in range(1, r.max_column + 1):
        print(f'  {L(c)}: {r.cell(row=4, column=c).value}')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == 'nyiso':
        cmd_nyiso(*args)
    elif cmd == 'nyserda':
        cmd_nyserda(*args)
    elif cmd == 'refs':
        cmd_refs(*args)
    else:
        print(__doc__); sys.exit(1)
