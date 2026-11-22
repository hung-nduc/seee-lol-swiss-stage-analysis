"""Step 1 - parse the 33 match records (PDF) and the Excel schedule.

Reads  data/raw/records/LS*.pdf, data/raw/schedule/swiss_schedule.xlsx
Writes data/interim/records.json

The Excel schedule is the final authority for teams and sides (blue/red).
Known gaps in the records are corrected here, each with a note; see
data/processed/data_issues.csv for the full list.
"""
import json, re
from pathlib import Path
import pdfplumber, openpyxl

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
OUT = ROOT / 'data' / 'interim' / 'records.json'


def schedule():
    wb = openpyxl.load_workbook(RAW / 'schedule' / 'swiss_schedule.xlsx', data_only=True)
    ws = wb['SWISS']
    out = {}
    for row in ws.iter_rows(min_row=3, values_only=True):
        for i in range(0, 30, 6):
            if i < len(row) and row[i]:
                out[row[i].strip()] = dict(blue=row[i + 1], red=row[i + 3], slot=row[i + 2])
    return out


def clean_id(s):
    s = re.sub(r'\s*#\s*', '#', s.strip())
    if '#' in s:
        n, t = s.split('#', 1)
        s = n.strip() + '#' + t.replace(' ', '')
    return s


def parse_pdf(path):
    with pdfplumber.open(path) as p:
        text = '\n'.join(pg.extract_text() or '' for pg in p.pages)
        tables = [t for pg in p.pages for t in pg.extract_tables()]
    rec = {}
    for k, pat in [('date', r'Ngày\s*:\s*(\S+)'), ('bracket', r'Nhánh thi đấu\s*:\s*(\S+)'),
                   ('code', r'Mã số trận đấu\s*:\s*(\S+)'),
                   ('duration', r'Thời gian trận đấu\s*:\s*([^\n]*?)\s*Đội thắng'), ('winner', r'Đội thắng\s*:\s*([^\n]*)')]:
        m = re.search(pat, text)
        rec[k + '_raw'] = m.group(1).strip() if m else None
    players, draft, pen, pause = [], [], [], []
    for t in tables:
        head = ' '.join(str(c) for c in t[0] if c)
        if 'Tên đội' in head:
            body = [[str(c).replace('\n', ' ') if c else '' for c in r] for r in t[3:]]
            (players if 'VẬN ĐỘNG' in str(t[1][0]) else draft).extend(body)
        elif 'XỬ PHẠT' in head:
            pen = [[str(c).replace('\n', ' ') for c in r] for r in t[2:] if any(c for c in r[1:])]
        elif 'TẠM DỪNG' in head:
            pause = [[str(c).replace('\n', ' ') for c in r] for r in t[2:] if any(c for c in r[1:])]
    rec.update(players_raw=players, draft_raw=draft, penalties=pen, pauses=pause)
    return rec


# Corrections confirmed by the organiser or recovered from screenshots
FORFEITS = {
    'LS21': ('HKG', 'ruling', 'HKG awarded the win by ruling; record still lists a draft'),
    'LS37': ('MSD', 'forfeit', 'LK did not show up'),
    'LS38': ('LN', 'forfeit', 'FTL did not show up'),
    'LS44': ('LHP', 'forfeit', 'CBK did not show up (record lists LHP roster on both sides)'),
    'LS46': ('ZEN', 'forfeit', 'VNT did not show up'),
}
FILL = {
    'LS45': dict(winner='LN', duration='29:08', note='winner and time missing in record; taken from screenshot'),
    'LS41': dict(duration='29:33', note='time missing in record; taken from screenshot'),
}


def main():
    sch = schedule()
    out = []
    for pdf in sorted((RAW / 'records').glob('LS*.pdf')):
        r = parse_pdf(pdf)
        code = re.search(r'LS\d\d', pdf.name).group(0)
        s = sch[code]
        m = dict(code=code, round=int(code[2]), blue=s['blue'], red=s['red'], scheduled=s['slot'],
                 date=r['date_raw'], bracket_raw=r['bracket_raw'], duration_raw=r['duration_raw'],
                 winner_raw=r['winner_raw'], penalties=r['penalties'], pauses=r['pauses'], notes=[])
        w = re.sub(r'[….\s]|\(.*?\)', '', r['winner_raw'] or '').replace('NGU', 'ZEN')
        m['winner'] = w or None
        m['result_type'] = 'played'
        if code in FORFEITS:
            m['winner'], m['result_type'], note = FORFEITS[code]
            m['notes'].append(note)
        if code in FILL:
            f = FILL[code]
            m['winner'] = f.get('winner', m['winner'])
            m['duration_raw'] = f.get('duration', m['duration_raw'])
            m['notes'].append(f['note'])
        m['loser'] = m['red'] if m['winner'] == m['blue'] else m['blue']
        # roster (record roles); empty for forfeits
        roster = {'blue': [], 'red': []}
        real_names = set()
        if m['result_type'] == 'played':
            for row in r['players_raw']:
                cells = [c for c in row if c]
                if len(cells) >= 5:
                    role = cells[0]
                    for side, (nm, rid) in (('blue', cells[1:3]), ('red', cells[3:5])):
                        real_names.add(nm)
                        if rid not in ('NULL', ''):
                            # real names are not stored (public repo): Riot ID only
                            roster[side].append(dict(role=role, riot=clean_id(rid)))
        m['roster'] = roster
        # redact real names that appear in pause / penalty notes
        for key in ('pauses', 'penalties'):
            for row in m[key]:
                for i, cell in enumerate(row):
                    for nm in real_names:
                        if nm and len(nm) > 3:
                            cell = cell.replace(nm, '[player]')
                    row[i] = cell
        # draft rows: [order, blue_ban, '', blue_pick, red_ban, red_pick] (layout varies slightly)
        draft = []
        for row in r['draft_raw']:
            cells = [c for c in row]
            vals = [c for c in cells[1:]]
            vals = [v for i, v in enumerate(vals) if not (i == 1 and v == '')] if len(vals) > 4 else vals
            vals = (vals + ['', '', '', ''])[:4]
            draft.append(dict(order=int(cells[0]) if cells[0].isdigit() else None,
                              blue_ban=vals[0], blue_pick=vals[1], red_ban=vals[2], red_pick=vals[3]))
        m['draft'] = draft
        out.append(m)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(out)} records -> {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
