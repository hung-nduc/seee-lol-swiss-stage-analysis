"""Step 2 - build the processed tables (CSV) and the HTML reports.

Reads  data/interim/records.json            (from parse_records.py)
       data/interim/scoreboards/LS*.json    (scoreboard transcriptions, one per played game)
       data/raw/opgg_ranks_2026-11-22.csv   (op.gg VN snapshot, season 2026)
Writes data/processed/*.csv and docs/*.html

Run:  python scripts/parse_records.py && python scripts/build.py
Only the standard library is needed for this step.
"""
import csv, json, statistics as st
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
PROC = DATA / 'processed'
ROLES = ['TOP', 'JG', 'MID', 'AD', 'SP']
ROLE_NAME = {'TOP': 'Top', 'JG': 'Jungle', 'MID': 'Mid', 'AD': 'Bot (ADC)', 'SP': 'Support'}
QUALIFIED = ['TT', 'LN', 'KGC', 'LHP', 'LXM', 'GOS', 'DMX', 'GLT']   # Excel KNOCKOUT sheet

# ---------------------------------------------------------------- ranks
TIERS = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND']
DIV = {'4': 0, '3': 1, '2': 2, '1': 3}


def rank_score(tier, lp):
    """Ladder value in divisions: Iron 4 = 0, Gold 4 = 12, Diamond 1 = 27, Master+ = 28 + LP/100."""
    if not tier:
        return None
    p = tier.upper().split()
    lp = int(lp or 0)
    if p[0] in ('MASTER', 'GRANDMASTER', 'CHALLENGER'):
        return 28 + lp / 100
    return TIERS.index(p[0]) * 4 + DIV[p[1]] + lp / 100


def rank_label(s):
    if s is None:
        return 'Unranked'
    if s >= 28:
        return f'Master {round((s - 28) * 100)} LP'
    i = int(s)
    return f'{TIERS[i // 4].title()} {4 - i % 4}'


# ---------------------------------------------------------------- champions
CHAMP_FIX = {
    'noctune': 'Nocturne', 'nortune': 'Nocturne', 'quiyana': 'Qiyana', 'qiana': 'Qiyana', 'neko': 'Neeko',
    'nekko': 'Neeko', 'jihn': 'Jhin', 'camile': 'Camille', 'rakkan': 'Rakan', 'alista': 'Alistar',
    'javan iv': 'Jarvan IV', 'jarvan': 'Jarvan IV', 'ramus': 'Rammus', 'leesin': 'Lee Sin', 'oriana': 'Orianna',
    'naultilus': 'Nautilus', 'gallio': 'Galio', 'ngộ không': 'Wukong', 'kaisa': "Kai'Sa", "kai'sa": "Kai'Sa",
    'mundo': 'Dr. Mundo', 'leblanc': 'LeBlanc', "cho'gath": "Cho'Gath", "k'sante": "K'Sante", "kog'maw": "Kog'Maw",
    'xin zhao': 'Xin Zhao', 'lee sin': 'Lee Sin', 'aurelion sol': 'Aurelion Sol', 'twisted fate': 'Twisted Fate',
    'miss fortune': 'Miss Fortune', 'tahm kench': 'Tahm Kench', 'dr. mundo': 'Dr. Mundo',
}


def champ(raw):
    if not raw or raw.strip() in ('', 'NULL'):
        return None
    k = raw.strip().replace('’', "'").lower()
    if k in CHAMP_FIX:
        return CHAMP_FIX[k]
    return ' '.join(w[:1].upper() + w[1:] for w in raw.strip().replace('’', "'").split())


def mins(t):
    a, b = t.split(':')
    return int(a) + int(b) / 60


def write_csv(name, rows, fields=None):
    PROC.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0].keys())
    with open(PROC / f'{name}.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    print(f'  {name}.csv  {len(rows)} rows')


def main():
    records = {m['code']: m for m in json.loads((DATA / 'interim' / 'records.json').read_text(encoding='utf-8'))}
    boards = {}
    for f in sorted((DATA / 'interim' / 'scoreboards').glob('LS*.json')):
        d = json.loads(f.read_text(encoding='utf-8'))
        boards[d['code']] = d
    with open(DATA / 'raw' / 'opgg_ranks_2026-11-22.csv', encoding='utf-8') as f:
        ranks_raw = list(csv.DictReader(f))

    # ------------------------------------------------ players & ranks
    players = {}
    for r in ranks_raw:
        key = r['riot_id_opgg'] or r['riot_id_record']
        p = dict(team=r['team'], riot_id=key, riot_id_record=r['riot_id_record'])
        for q in ('solo', 'flex', 'r5'):
            w, l = int(r[f'{q}_wins'] or 0), int(r[f'{q}_losses'] or 0)
            p[f'{q}_tier'] = r[f'{q}_tier'] or ('' if r['riot_id_opgg'] else 'not found')
            p[f'{q}_lp'] = r[f'{q}_lp']
            p[f'{q}_games'] = w + l
            p[f'{q}_winrate'] = round(100 * w / (w + l)) if w + l else ''
            p[f'{q}_score'] = rank_score(r[f'{q}_tier'], r[f'{q}_lp'])
        players[key] = p
    by_name = {}
    for k in players:
        by_name[k.split('#')[0].replace(' ', '').lower()] = k
    by_record = {p['riot_id_record']: k for k, p in players.items()}

    def resolve(p):
        rid = p.get('riot', '')
        if rid in players:
            return rid
        if rid in by_record:
            return by_record[rid]
        nm = (p.get('name_on_screen') if rid.startswith('UNKNOWN') else rid.split('#')[0]) or ''
        nm = nm.replace(' ', '').lower()
        if nm.startswith('neirt'):
            return 'neirt17#trien'
        if 'phomai' in nm:
            return 'phong (no Riot ID; on screen: Phomai)'
        return by_name.get(nm)

    # ------------------------------------------------ matches
    matches = []
    for code in sorted(records):
        m = records[code]
        b = boards.get(code)
        dur = b['game_time'] if b else None
        matches.append(dict(code=code, round=m['round'], date=m['date'], scheduled=m['scheduled'], blue=m['blue'], red=m['red'],
                            winner=m['winner'], loser=m['loser'], result_type=m['result_type'],
                            winner_side='blue' if m['winner'] == m['blue'] else 'red',
                            game_time=dur or '', game_minutes=round(mins(dur), 2) if dur else '',
                            record_time=m['duration_raw'] if m['duration_raw'] and ':' in m['duration_raw'] else '',
                            screenshot=f'data/raw/screenshots/{code}.png' if b else '',
                            notes='; '.join(m['notes'])))
    # pools / standings
    rec = defaultdict(lambda: [0, 0])
    for m in matches:
        m['pool'] = '{}-{}'.format(*rec[m['blue']])
        rec[m['winner']][0] += 1
        rec[m['loser']][1] += 1
    opps = defaultdict(list)
    for m in matches:
        opps[m['blue']].append(m['red'])
        opps[m['red']].append(m['blue'])

    # ------------------------------------------------ games (team & player level)
    player_games, team_games = [], []
    lineup = {}
    for code, b in boards.items():
        m = records[code]
        gm = mins(b['game_time'])
        for t in b['teams']:
            opp = [o for o in b['teams'] if o is not t][0]
            side = 'blue' if t['team'] == m['blue'] else 'red'
            tdmg = sum(p['damage'] or 0 for p in t['players']) if all(p['damage'] is not None for p in t['players']) else None
            tgold = sum(p['gold'] for p in t['players'])
            ids = []
            for p in t['players']:
                pid = resolve(p)
                ids.append(pid)
                player_games.append(dict(
                    code=code, round=m['round'], team=t['team'], opponent=opp['team'], side=side, won=int(t['won']),
                    riot_id=pid, name_on_screen=p.get('name_on_screen', ''), role=p['role'], champion=p['champion'],
                    level=p.get('level', ''), kills=p['k'], deaths=p['d'], assists=p['a'],
                    kda=round((p['k'] + p['a']) / max(p['d'], 1), 2),
                    kill_participation=round(100 * (p['k'] + p['a']) / t['kills']) if t['kills'] else '',
                    damage=p['damage'] if p['damage'] is not None else '',
                    damage_per_min=round(p['damage'] / gm) if p['damage'] is not None else '',
                    damage_share=round(100 * p['damage'] / tdmg, 1) if tdmg else '',
                    gold=p['gold'], gold_per_min=round(p['gold'] / gm), gold_share=round(100 * p['gold'] / tgold, 1),
                    game_minutes=round(gm, 2)))
            lineup[(code, t['team'])] = ids
            team_games.append(dict(
                code=code, round=m['round'], team=t['team'], opponent=opp['team'], side=side, won=int(t['won']),
                game_time=b['game_time'], game_minutes=round(gm, 2), kills=t['kills'], deaths=t['deaths'], assists=t['assists'],
                kda=round((t['kills'] + t['assists']) / max(t['deaths'], 1), 2), gold=t['gold'], gold_per_min=round(t['gold'] / gm),
                gold_diff=t['gold'] - opp['gold'], kills_per_min=round(t['kills'] / gm, 2),
                damage=tdmg if tdmg is not None else '', layout=b.get('layout', 'standard')))
    team_games.sort(key=lambda r: (r['code'], r['team']))
    player_games.sort(key=lambda r: (r['code'], r['team'], ROLES.index(r['role'])))

    # tournament usage per player
    used = defaultdict(lambda: dict(games=0, roles=Counter(), champs=Counter()))
    for pg in player_games:
        u = used[pg['riot_id']]
        u['games'] += 1
        u['roles'][pg['role']] += 1
        u['champs'][pg['champion']] += 1
    for k, p in players.items():
        u = used.get(k)
        p['swiss_games'] = u['games'] if u else 0
        p['swiss_role'] = u['roles'].most_common(1)[0][0] if u else ''
        p['swiss_champions'] = ', '.join(f'{c} x{n}' if n > 1 else c for c, n in u['champs'].most_common()) if u else ''
        for q in ('solo', 'flex', 'r5'):
            p[f'{q}_label'] = rank_label(p[f'{q}_score']) if p[f'{q}_score'] is not None else ('Unranked' if p[f'{q}_tier'] != 'not found' else 'not found')

    # ------------------------------------------------ team scouting
    scouting = []
    for t in sorted(set(p['team'] for p in players.values())):
        ps = [p for p in players.values() if p['team'] == t and p['swiss_games'] > 0]

        def wavg(q):
            v = [(p[f'{q}_score'], p['swiss_games']) for p in ps if p[f'{q}_score'] is not None]
            return sum(a * b for a, b in v) / sum(b for a, b in v) if v else None
        so, fl, r5 = wavg('solo'), wavg('flex'), wavg('r5')
        sg = sum(p['solo_games'] for p in ps)
        fg = sum(p['flex_games'] for p in ps)
        rg = sum(p['r5_games'] for p in ps)
        tot = sg + fg + rg
        solos = [p for p in ps if p['solo_score'] is not None]
        best = max(solos, key=lambda p: p['solo_score']) if solos else None
        worst = min(solos, key=lambda p: p['solo_score']) if solos else None
        fs = round(100 * fg / tot) if tot else 0
        scouting.append(dict(
            team=t, swiss_record='{}-{}'.format(*rec[t]), swiss_wins=rec[t][0], qualified=int(t in QUALIFIED),
            players_used=len(ps), solo_score=round(so, 2) if so is not None else '', solo_avg=rank_label(so),
            flex_score=round(fl, 2) if fl is not None else '', flex_avg=rank_label(fl),
            r5_score=round(r5, 2) if r5 is not None else '', r5_avg=rank_label(r5), r5_ranked_players=sum(1 for p in ps if p['r5_score'] is not None),
            solo_unranked=sum(1 for p in ps if p['solo_score'] is None),
            best_player=f"{best['riot_id']} ({best['solo_label']})" if best else '',
            weakest_player=f"{worst['riot_id']} ({worst['solo_label']})" if worst else '',
            rank_spread=round(best['solo_score'] - worst['solo_score'], 1) if best else '',
            solo_games_total=sg, flex_games_total=fg, r5_games_total=rg,
            solo_games_per_player=round(sg / len(ps)), flex_games_per_player=round(fg / len(ps)),
            flex_share=fs, flex_regulars=sum(1 for p in ps if p['flex_games'] >= 50),
            flex_verdict='Heavy Flex' if fs >= 45 else 'Some Flex' if fs >= 25 else 'Mostly Solo/Duo'))
    order = sorted(scouting, key=lambda s: -(s['solo_score'] if s['solo_score'] != '' else -1))
    for i, s in enumerate(order, 1):
        s['rank_seed'] = i
    sc = {s['team']: s for s in scouting}

    # ------------------------------------------------ standings
    standings = []
    for t, (w, l) in rec.items():
        standings.append(dict(team=t, wins=w, losses=l, record=f'{w}-{l}', qualified=int(t in QUALIFIED),
                              buchholz=sum(rec[o][0] for o in opps[t]), rank_seed=sc[t]['rank_seed'], solo_avg=sc[t]['solo_avg'],
                              forfeit_wins=sum(1 for m in matches if m['winner'] == t and m['result_type'] != 'played'),
                              forfeit_losses=sum(1 for m in matches if m['loser'] == t and m['result_type'] != 'played')))
    standings.sort(key=lambda s: (-s['wins'], s['losses'], -s['buchholz'], s['rank_seed']))
    for i, s in enumerate(standings, 1):
        s['finish'] = i
        s['seed_vs_finish'] = s['rank_seed'] - i

    # rank gap / upsets
    for m in matches:
        if (m['code'], m['blue']) in lineup:
            def lscore(team):
                v = [players[k]['solo_score'] for k in lineup[(m['code'], team)] if k and players[k]['solo_score'] is not None]
                return sum(v) / len(v)
            ws, ls = lscore(m['winner']), lscore(m['loser'])
            m['rank_basis'] = 'lineup that played'
        else:
            ws, ls = sc[m['winner']]['solo_score'], sc[m['loser']]['solo_score']
            m['rank_basis'] = 'team average (no game)'
        m['winner_rank'], m['loser_rank'] = rank_label(ws), rank_label(ls)
        m['rank_gap'] = round(ws - ls, 2)
        m['upset'] = int(ws < ls and m['result_type'] == 'played')

    # ------------------------------------------------ drafts
    drafts = []
    for code in sorted(records):
        m = records[code]
        if m['result_type'] != 'played':
            continue
        b = boards[code]
        picks_by_team = {t['team']: [p['champion'] for p in t['players']] for t in b['teams']}
        for row in m['draft']:
            for side in ('blue', 'red'):
                team = m[side]
                for kind in ('ban', 'pick'):
                    raw = row[f'{side}_{kind}']
                    c = champ(raw)
                    if c:
                        drafts.append(dict(code=code, team=team, side=side, kind=kind, order=row['order'], champion=c,
                                           champion_raw=raw, renamed=int(c != raw.strip().replace('’', "'")), source='record'))
        # picks missing from the record are taken from the scoreboard
        for team, ch in picks_by_team.items():
            have = {d['champion'] for d in drafts if d['code'] == code and d['team'] == team and d['kind'] == 'pick'}
            for c in ch:
                if c not in have:
                    side = 'blue' if team == m['blue'] else 'red'
                    drafts.append(dict(code=code, team=team, side=side, kind='pick', order='', champion=c, champion_raw='',
                                       renamed=0, source='scoreboard'))
    # bans per team
    ban_rows = [d for d in drafts if d['kind'] == 'ban']

    # ------------------------------------------------ champions
    G = len(boards)
    cstat = defaultdict(lambda: dict(picks=0, wins=0, bans=0, roles=Counter(), teams=Counter(), k=0, d=0, a=0, dmg=[], blue=0))
    for pg in player_games:
        c = cstat[pg['champion']]
        c['picks'] += 1
        c['wins'] += pg['won']
        c['roles'][pg['role']] += 1
        c['teams'][pg['team']] += 1
        c['k'] += pg['kills']; c['d'] += pg['deaths']; c['a'] += pg['assists']
        if pg['damage_share'] != '':
            c['dmg'].append(pg['damage_share'])
    for d in ban_rows:
        cstat[d['champion']]['bans'] += 1
    champions = []
    for name, c in cstat.items():
        row = dict(champion=name, picks=c['picks'], bans=c['bans'], presence=c['picks'] + c['bans'],
                   presence_pct=round(100 * (c['picks'] + c['bans']) / G), wins=c['wins'],
                   winrate=round(100 * c['wins'] / c['picks']) if c['picks'] else '',
                   main_role=ROLE_NAME[c['roles'].most_common(1)[0][0]] if c['picks'] else '',
                   kda=round((c['k'] + c['a']) / max(c['d'], 1), 2) if c['picks'] else '',
                   avg_damage_share=round(st.mean(c['dmg']), 1) if c['dmg'] else '',
                   picked_by=', '.join(f'{t} x{n}' if n > 1 else t for t, n in c['teams'].most_common()))
        for r in ROLES:
            row[f'picks_{r}'] = c['roles'][r]
        champions.append(row)
    champions.sort(key=lambda r: (-r['presence'], -r['picks'], r['champion']))

    # ------------------------------------------------ roles
    role_stats = []
    full = [(code, t) for (code, t) in lineup if all(pg['damage_share'] != '' for pg in player_games if pg['code'] == code and pg['team'] == t)]
    topd = Counter()
    for code, t in full:
        rows = [pg for pg in player_games if pg['code'] == code and pg['team'] == t]
        topd[max(rows, key=lambda r: r['damage'])['role']] += 1
    for r in ROLES:
        rows = [pg for pg in player_games if pg['role'] == r and pg['damage_share'] != '']
        win = [x['damage_share'] for x in rows if x['won']]
        loss = [x['damage_share'] for x in rows if not x['won']]
        allr = [pg for pg in player_games if pg['role'] == r]
        role_stats.append(dict(
            role=ROLE_NAME[r], damage_share=round(st.mean(x['damage_share'] for x in rows), 1),
            damage_share_in_wins=round(st.mean(win), 1), damage_share_in_losses=round(st.mean(loss), 1),
            damage_per_min=round(st.mean(x['damage_per_min'] for x in rows)),
            gold_share=round(st.mean(x['gold_share'] for x in allr), 1), gold_per_min=round(st.mean(x['gold_per_min'] for x in allr)),
            damage_per_1k_gold=round(sum(x['damage'] for x in rows) / sum(x['gold'] for x in rows) * 1000),
            kda=round(sum(x['kills'] + x['assists'] for x in allr) / max(sum(x['deaths'] for x in allr), 1), 2),
            top_damage_count=topd[r], team_games_with_damage=len(full),
            unique_champions=len({x['champion'] for x in allr})))

    # ------------------------------------------------ kill participation (team index)
    # Team KP of one game = sum over the 5 players of (kills + assists) / (5 x team kills)
    #                     = the average player's share of the team's kills they took part in.
    def game_kp(code, team):
        xs = [pg for pg in player_games if pg['code'] == code and pg['team'] == team]
        tk = sum(x['kills'] for x in xs)
        return sum(x['kills'] + x['assists'] for x in xs) / (5 * tk) * 100 if tk else None
    for g in team_games:
        v = game_kp(g['code'], g['team'])
        g['kill_participation'] = round(v, 1) if v is not None else ''
    team_role_kp = []

    def team_kp(t):
        gs = [g for g in team_games if g['team'] == t and g['kill_participation'] != '']
        w = [g['kill_participation'] for g in gs if g['won']]
        l = [g['kill_participation'] for g in gs if not g['won']]
        pgs = [pg for pg in player_games if pg['team'] == t]
        tk = {g['code']: g['kills'] for g in team_games if g['team'] == t}
        role_kp = {}
        for r in ROLES:
            xs = [x for x in pgs if x['role'] == r and tk[x['code']]]
            role_kp[r] = round(100 * sum(x['kills'] + x['assists'] for x in xs) / sum(tk[x['code']] for x in xs), 1) if xs else None
            team_role_kp.append(dict(team=t, role=ROLE_NAME[r], games=len(xs), kill_participation=role_kp[r] if role_kp[r] is not None else '',
                                     kills=sum(x['kills'] for x in xs), assists=sum(x['assists'] for x in xs), team_kills=sum(tk[x['code']] for x in xs)))
        vals = {r: v for r, v in role_kp.items() if v is not None}
        hi = max(vals, key=vals.get); lo = min(vals, key=vals.get)
        return dict(kill_participation=round(st.mean(g['kill_participation'] for g in gs), 1),
                    kp_in_wins=round(st.mean(w), 1) if w else '', kp_in_losses=round(st.mean(l), 1) if l else '',
                    kp_most_involved=f'{ROLE_NAME[hi]} ({vals[hi]}%)', kp_least_involved=f'{ROLE_NAME[lo]} ({vals[lo]}%)',
                    kp_spread=round(vals[hi] - vals[lo], 1), **{f'kp_{r}': role_kp[r] if role_kp[r] is not None else '' for r in ROLES})

    # ------------------------------------------------ team stats
    team_stats = []
    for t in sorted({g['team'] for g in team_games}):
        gs = [g for g in team_games if g['team'] == t]
        K, D, A = (sum(g[x] for g in gs) for x in ('kills', 'deaths', 'assists'))
        wins = [g for g in gs if g['won']]
        losses = [g for g in gs if not g['won']]
        pgs = [pg for pg in player_games if pg['team'] == t]
        mvp = max(sorted({pg['riot_id'] for pg in pgs}), key=lambda k: (sum(x['kills'] + x['assists'] for x in pgs if x['riot_id'] == k) / max(sum(x['deaths'] for x in pgs if x['riot_id'] == k), 1)))
        team_stats.append(dict(
            team=t, games=len(gs), wins=len(wins), losses=len(losses), qualified=int(t in QUALIFIED),
            avg_game_minutes=round(st.mean(g['game_minutes'] for g in gs), 2),
            avg_win_minutes=round(st.mean(g['game_minutes'] for g in wins), 2) if wins else '',
            avg_loss_minutes=round(st.mean(g['game_minutes'] for g in losses), 2) if losses else '',
            avg_gold=round(st.mean(g['gold'] for g in gs)), avg_gold_per_min=round(st.mean(g['gold_per_min'] for g in gs)),
            avg_gold_diff=round(st.mean(g['gold_diff'] for g in gs)),
            avg_kills=round(K / len(gs), 1), avg_deaths=round(D / len(gs), 1), avg_assists=round(A / len(gs), 1),
            kda=round((K + A) / max(D, 1), 2), kills_per_min=round(st.mean(g['kills_per_min'] for g in gs), 2),
            blue_games=sum(1 for g in gs if g['side'] == 'blue'), red_games=sum(1 for g in gs if g['side'] == 'red'),
            best_kda_player=mvp, **team_kp(t)))
    team_stats.sort(key=lambda r: -r['avg_gold_per_min'])

    # ------------------------------------------------ player stats
    player_stats = []
    for k in sorted({pg['riot_id'] for pg in player_games}):
        pgs = [pg for pg in player_games if pg['riot_id'] == k]
        dm = [x for x in pgs if x['damage'] != '' and x['damage_share'] != '']
        K, D, A = (sum(x[f] for x in pgs) for f in ('kills', 'deaths', 'assists'))
        p = players[k]
        player_stats.append(dict(
            riot_id=k, team=p['team'], role=ROLE_NAME[Counter(x['role'] for x in pgs).most_common(1)[0][0]], games=len(pgs),
            wins=sum(x['won'] for x in pgs), kills=K, deaths=D, assists=A, kda=round((K + A) / max(D, 1), 2),
            avg_kill_participation=round(st.mean(x['kill_participation'] for x in pgs if x['kill_participation'] != '')) if any(x['kill_participation'] != '' for x in pgs) else '',
            damage_per_min=round(st.mean(x['damage_per_min'] for x in dm)) if dm else '',
            damage_share=round(st.mean(x['damage_share'] for x in dm), 1) if dm else '',
            gold_per_min=round(st.mean(x['gold_per_min'] for x in pgs)),
            champions=', '.join(f'{c} x{n}' if n > 1 else c for c, n in Counter(x['champion'] for x in pgs).most_common()),
            solo_rank=p['solo_label']))
    player_stats.sort(key=lambda r: (r['team'], ROLES.index([k for k, v in ROLE_NAME.items() if v == r['role']][0]), -r['games'], r['riot_id']))

    # side stats
    played = [m for m in matches if m['result_type'] == 'played']
    side_stats = [dict(side=s, games=len(played), wins=sum(1 for m in played if m['winner_side'] == s),
                       winrate=round(100 * sum(1 for m in played if m['winner_side'] == s) / len(played))) for s in ('blue', 'red')]

    # ------------------------------------------------ write CSVs
    print('data/processed:')
    write_csv('matches', matches, ['code', 'round', 'pool', 'date', 'scheduled', 'blue', 'red', 'winner', 'loser', 'winner_side', 'result_type',
                                   'game_time', 'game_minutes', 'record_time', 'winner_rank', 'loser_rank', 'rank_gap', 'rank_basis', 'upset', 'screenshot', 'notes'])
    write_csv('standings', standings)
    write_csv('team_games', team_games)
    write_csv('player_games', player_games)
    write_csv('drafts', drafts)
    pr = sorted(players.values(), key=lambda p: (p['team'], -(p['solo_score'] or -1)))
    write_csv('player_ranks', pr, ['team', 'riot_id', 'riot_id_record', 'swiss_games', 'swiss_role', 'swiss_champions',
                                   'solo_tier', 'solo_lp', 'solo_games', 'solo_winrate', 'solo_score', 'solo_label',
                                   'flex_tier', 'flex_lp', 'flex_games', 'flex_winrate', 'flex_score', 'flex_label',
                                   'r5_tier', 'r5_lp', 'r5_games', 'r5_winrate', 'r5_score', 'r5_label'])
    write_csv('team_scouting', sorted(scouting, key=lambda s: s['rank_seed']))
    write_csv('champions', champions)
    write_csv('role_stats', role_stats)
    write_csv('team_stats', team_stats)
    write_csv('team_role_kp', team_role_kp)
    write_csv('player_stats', player_stats)
    write_csv('side_stats', side_stats)
    issues = json.loads((Path(__file__).with_name('data_issues.json')).read_text(encoding='utf-8'))
    write_csv('data_issues', issues)

    # ------------------------------------------------ reports
    import sys; sys.path.insert(0, str(Path(__file__).parent)); import report
    report.build(ROOT / 'docs', dict(matches=matches, standings=standings, team_games=team_games, player_games=player_games,
                                     drafts=drafts, players=pr, scouting=sorted(scouting, key=lambda s: s['rank_seed']),
                                     champions=champions, role_stats=role_stats, team_stats=team_stats, player_stats=player_stats,
                                     side_stats=side_stats, issues=issues, team_role_kp=team_role_kp, rank_label=rank_label, qualified=QUALIFIED,
                                     role_name=ROLE_NAME, n_games=G))


if __name__ == '__main__':
    main()
