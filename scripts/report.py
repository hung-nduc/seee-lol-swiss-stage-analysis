"""Static HTML reports (no external libraries, works offline and on GitHub Pages).

Called by build.py. Every chart is inline SVG; every table is sortable by clicking its header.
"""
import html, re, statistics as st
from collections import Counter, defaultdict
from pathlib import Path

E = html.escape
C = ['#3b6fd8', '#e08a2c', '#2fa37a', '#c0504d', '#8064a2', '#7f8c8d']   # series colours
MUTED = '#9aa3ad'
REPO_URL = 'https://github.com/hung-nduc/seee-lol-swiss-stage-analysis'
GH_MARK = ('<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" style="display:inline;width:16px;height:16px;vertical-align:-3px;margin-right:6px">'
           '<path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>')
PAGES = [('index.html', 'Overview'), ('a-team-scouting.html', 'A. Team scouting'),
         ('b-swiss-evaluation.html', 'B. Swiss Stage evaluation'), ('c-team-evaluation.html', 'C. Team evaluation'), ('d-quarterfinalists.html', 'D. Quarterfinalists')]

CSS = """
:root{--bg:#fff;--fg:#1d2330;--muted:#5d6675;--line:#e3e6eb;--panel:#f7f8fa;--ok:#1f8a5b;--warn:#b7701c;--bad:#c0392b;--accent:#3b6fd8}
@media (prefers-color-scheme:dark){:root{--bg:#14171c;--fg:#e6e8ec;--muted:#9aa3ad;--line:#2b313a;--panel:#1b1f26;--ok:#4cc38a;--warn:#e3a14f;--bad:#ef6b5e;--accent:#7aa2ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:24px 20px 80px}
nav.top{position:sticky;top:0;z-index:10;background:var(--bg);border-bottom:1px solid var(--line)}
nav.top .wrap{padding:10px 20px;display:flex;gap:18px;flex-wrap:wrap;align-items:center}
nav.top a{color:var(--muted);text-decoration:none;font-size:14px}nav.top a.on{color:var(--fg);font-weight:600}
nav.top .brand{font-weight:700;color:var(--fg);margin-right:auto}
.ghbtn{display:inline-flex;align-items:center;padding:4px 12px;border:1px solid var(--line);border-radius:999px;color:var(--fg)!important;text-decoration:none;font-size:13px;font-weight:600;background:var(--panel)}.ghbtn:hover{border-color:var(--accent)}
h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:34px;margin:8px 0 6px}
h2{font-size:22px;margin:44px 0 6px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:16px;margin:26px 0 6px}h4{font-size:14px;margin:14px 0 6px}
p{margin:6px 0 10px;max-width:80ch}.muted,.sub{color:var(--muted)}.sub{font-size:13px}
.toc{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;margin:10px 0 6px}.toc a{color:var(--accent);text-decoration:none}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}.grid.wide{grid-template-columns:repeat(auto-fit,minmax(520px,1fr))}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:12px 0}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.tile .v{font-family:Georgia,serif;font-size:30px;line-height:1.15}.tile .l{font-size:12px;color:var(--muted)}
ul.find{margin:8px 0;padding-left:20px}ul.find li{margin:4px 0;max-width:90ch}
.tw{overflow-x:auto;margin:8px 0}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap;vertical-align:top}
th{color:var(--muted);font-weight:600;cursor:pointer;user-select:none;position:sticky;top:0;background:var(--bg)}
.card th{background:var(--panel)}th.sorted-asc::after{content:" ▲"}th.sorted-desc::after{content:" ▼"}
td.n,th.n{text-align:right}td.wr{white-space:normal;min-width:220px}
tr.hl td{background:rgba(59,111,216,.08)}
.pill{display:inline-block;padding:0 8px;border-radius:99px;border:1px solid var(--line);font-size:12px}
.pill.ok{color:var(--ok);border-color:var(--ok)}.pill.warn{color:var(--warn);border-color:var(--warn)}.pill.bad{color:var(--bad);border-color:var(--bad)}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--muted);margin:4px 0 8px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
svg{display:block;width:100%;height:auto}svg text{fill:var(--muted);font-size:11px}svg .strong{fill:var(--fg);font-weight:600}
svg .grid line{stroke:var(--line)}svg .axis{stroke:var(--line)}
.rounds{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.round h4{margin:0 0 6px}.m{border:1px solid var(--line);border-radius:8px;padding:6px 8px;margin:6px 0;font-size:12.5px;background:var(--bg)}
.m .w{font-weight:700}.m .pool{color:var(--muted);font-size:11px}
details>summary{cursor:pointer;font-weight:600;margin:6px 0}
.teamcard h3{margin-top:4px}.kv{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;margin:4px 0 8px}.kv b{font-weight:600}
.radars{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}.radar-card h4{margin:0 0 4px}
footer{margin-top:60px;color:var(--muted);font-size:12px}
a{color:var(--accent)}
.rk{font-weight:600;white-space:nowrap}.rk i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:1px}
.ci{width:20px;height:20px;border-radius:4px;vertical-align:-5px;margin-right:6px}.cl{display:inline-block;margin:1px 8px 1px 0;white-space:nowrap}.cl .ci{width:18px;height:18px}
"""

JS = """
document.querySelectorAll('table.sortable').forEach(t=>{
  t.querySelectorAll('th').forEach((th,i)=>th.addEventListener('click',()=>{
    const tb=t.tBodies[0],rows=[...tb.rows],asc=!th.classList.contains('sorted-asc');
    t.querySelectorAll('th').forEach(h=>h.classList.remove('sorted-asc','sorted-desc'));th.classList.add(asc?'sorted-asc':'sorted-desc');
    const v=r=>{const c=r.cells[i];const s=c.dataset.v!==undefined?c.dataset.v:c.textContent.trim();const n=parseFloat(s.replace(/[,%+]/g,''));return isNaN(n)?s.toLowerCase():n};
    rows.sort((a,b)=>{const x=v(a),y=v(b);return (x>y?1:x<y?-1:0)*(asc?1:-1)});rows.forEach(r=>tb.append(r));
  }));
});
(function(){
  const R=window.RADAR; if(!R) return;
  const A=document.getElementById('ra'),B=document.getElementById('rb'),box=document.getElementById('radar-big'),tb=document.querySelector('#radar-tbl tbody');
  const teams=Object.keys(R.data).sort((x,y)=>R.data[y].p.reduce((a,b)=>a+b)-R.data[x].p.reduce((a,b)=>a+b));
  A.value=teams[0]; B.value=teams[1];
  const fmt=(i,v)=>{const k=R.axes[i]; if(k==='Gold/min'||k==='Gold diff'||k==='Dmg/min') return (k==='Gold diff'&&v>0?'+':'')+Math.round(v).toLocaleString(); if(k==='KP') return v+'%'; if(k==='Speed') return v.toFixed(1)+' min'; return v;};
  function draw(){
    const n=R.axes.length,S=420,c=S/2,r=c-70,NS='http://www.w3.org/2000/svg';
    const pt=(i,v)=>[c+r*v*Math.sin(2*Math.PI*i/n),c-r*v*Math.cos(2*Math.PI*i/n)];
    const svg=document.createElementNS(NS,'svg'); svg.setAttribute('viewBox',`0 0 ${S} ${S}`); svg.setAttribute('role','img'); svg.setAttribute('aria-label','Radar comparison of '+A.value+' and '+B.value);
    const el=(t,a)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);svg.append(e);return e;};
    [0.25,0.5,0.75,1].forEach(g=>el('polygon',{points:R.axes.map((_,i)=>pt(i,g).join(',')).join(' '),fill:'none',stroke:'var(--line)'}));
    R.axes.forEach((a,i)=>{const [x,y]=pt(i,1);el('line',{x1:c,y1:c,x2:x,y2:y,stroke:'var(--line)'});const [lx,ly]=pt(i,1.17);const t=el('text',{x:lx,y:ly,dy:'.35em','text-anchor':Math.abs(lx-c)<8?'middle':(lx>c?'start':'end')});t.textContent=a;});
    el('polygon',{points:R.axes.map((_,i)=>pt(i,0.5).join(',')).join(' '),fill:'none',stroke:'#9aa3ad','stroke-dasharray':'4 3'});
    [[A.value,R.colors[0]],[B.value,R.colors[1]]].forEach(([tm,col])=>{const p=R.data[tm].p;const g=el('polygon',{points:p.map((v,i)=>pt(i,Math.max(v,0.04)).join(',')).join(' '),fill:col,'fill-opacity':0.2,stroke:col,'stroke-width':2});
      p.forEach((v,i)=>{const [x,y]=pt(i,Math.max(v,0.04));const d=el('circle',{cx:x,cy:y,r:3.5,fill:col});const tt=document.createElementNS(NS,'title');tt.textContent=`${tm} — ${R.axes[i]}: ${fmt(i,R.data[tm].r[i])} (${Math.round(v*100)}th percentile)`;d.append(tt);});});
    box.replaceChildren(svg);
    document.getElementById('rha').textContent=A.value; document.getElementById('rhb').textContent=B.value;
    tb.replaceChildren(...R.axes.map((a,i)=>{const tr=document.createElement('tr');[a,fmt(i,R.data[A.value].r[i]),fmt(i,R.data[B.value].r[i]),fmt(i,R.med[i])].forEach((v,j)=>{const td=document.createElement('td');td.textContent=v;if(j)td.className='n';tr.append(td);});return tr;}));
  }
  A.onchange=draw;B.onchange=draw;draw();
})();
"""


def fmt(v, d=0):
    if v == '' or v is None:
        return '—'
    if isinstance(v, float):
        if d == 0:
            return f'{round(v):,}'
        t = f'{v:,.{d}f}'.rstrip('0').rstrip('.')
        return t
    if isinstance(v, int):
        return f'{v:,}'
    return str(v)


def table(cols, rows, sortable=True, hl=None, cls=''):
    """cols: list of (key, header, kind) kind in '', 'n', 'wrap'. rows: list of dicts. Values may be (display, sortval)."""
    h = ['<div class="tw"><table class="%s %s"><thead><tr>' % ('sortable' if sortable else '', cls)]
    for k, head, kind in cols:
        h.append(f'<th class="{"n" if kind == "n" else ""}">{E(head)}</th>')
    h.append('</tr></thead><tbody>')
    for r in rows:
        h.append(f'<tr class="{"hl" if hl and hl(r) else ""}">')
        for k, head, kind in cols:
            kc = 'wr' if kind == 'wrap' else kind
            v = r.get(k, '')
            if isinstance(v, tuple):
                disp, sv = v
                sv = round(sv, 6) if isinstance(sv, float) else sv
                h.append(f'<td class="{kc}" data-v="{E(str(sv))}">{disp}</td>')
            else:
                h.append(f'<td class="{kc}">{E(fmt(v, 2 if isinstance(v, float) else 0))}</td>')
        h.append('</tr>')
    h.append('</tbody></table></div>')
    return ''.join(h)


def pill(text, kind=''):
    return f'<span class="pill {kind}">{E(text)}</span>'


def legend(items):
    return '<div class="legend">' + ''.join(f'<span><i style="background:{c}"></i>{E(t)}</span>' for t, c in items) + '</div>'


def tw(s, px=6.6):
    return len(str(s)) * px



# ------------------------------------------------------------------ champion icons (Riot Data Dragon)
DD_VER = '16.23.1'   # Data Dragon build of patch 26.23
DD_EXC = {"Bel'Veth": 'Belveth', "Cho'Gath": 'Chogath', "Kai'Sa": 'Kaisa', "Kha'Zix": 'Khazix', 'LeBlanc': 'Leblanc', 'Wukong': 'MonkeyKing',
          'Nunu & Willump': 'Nunu', 'Renata Glasc': 'Renata', "Vel'Koz": 'Velkoz'}


def icon_url(name):
    cid = DD_EXC.get(name) or re.sub(r'[^A-Za-z]', '', name)
    return f'https://ddragon.leagueoflegends.com/cdn/{DD_VER}/img/champion/{cid}.png'


def ci(name, size=20):
    """Champion icon + name (icon hides itself when offline)."""
    return (f'<img class="ci" src="{icon_url(name)}" alt="" width="{size}" height="{size}" loading="lazy" onerror="this.remove()">'
            f'{E(name)}')


def ci_list(text):
    """'Ornn x3, Jhin' -> icons with counts."""
    if not text or text == '—':
        return '—'
    out = []
    for part in [x.strip() for x in str(text).split(',') if x.strip()]:
        m = re.match(r'^(.*?)(?: x(\d+))?$', part)
        name, n = m.group(1), m.group(2)
        out.append('<span class="cl">' + ci(name, 18) + (f' <span class="muted">×{n}</span>' if n else '') + '</span>')
    return ' '.join(out)


# ------------------------------------------------------------------ rank colours
TIER_COL = {'Iron': '#7d726c', 'Bronze': '#a8653d', 'Silver': '#8d9ba6', 'Gold': '#c9971f', 'Platinum': '#2f9e98', 'Plat': '#2f9e98',
            'Emerald': '#1e9e5e', 'Diamond': '#5b7ee6', 'Master': '#a157c2', 'Grandmaster': '#d0443a', 'Challenger': '#e2a900'}
TIER_ORDER = {t: i for i, t in enumerate(['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Emerald', 'Diamond', 'Master', 'Grandmaster', 'Challenger'])}


def rk(label):
    """Rank label coloured by tier: 'Gold 1' -> gold dot + gold text. Unranked/unknown stay plain."""
    label = str(label)
    tier = label.split()[0].title() if label else ''
    col = TIER_COL.get(tier)
    if not col:
        return f'<span class="muted">{E(label)}</span>'
    return f'<span class="rk" style="color:{col}"><i style="background:{col}"></i>{E(label)}</span>'


def rk_cell(label, extra='', sortval=None):
    """Table cell tuple: coloured rank + optional plain suffix (games, win rate)."""
    return (rk(label) + (f' <span class="muted">{E(extra)}</span>' if extra else ''), sortval if sortval is not None else -1)

# ------------------------------------------------------------------ charts
def hbar(rows, keys, colors=None, label_w=None, W=760, row_h=22, val_fmt=lambda v: fmt(v), xmax=None, ref=None, total=True, aria=''):
    """rows: list of dict(label, values=[...], tip, strong=bool)."""
    colors = colors or C
    has_icon = any(r.get('icon') for r in rows)
    lw = label_w or max(60, max(tw(r['label']) for r in rows) + 12) + (24 if has_icon else 0)
    H = len(rows) * row_h + 8
    mx = xmax or max(sum(v for v in r['values'] if v) for r in rows) or 1
    x = lambda v: lw + (W - lw - 50) * v / mx
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(aria)}">']
    if ref is not None:
        s.append(f'<line x1="{x(ref):.1f}" x2="{x(ref):.1f}" y1="0" y2="{H}" stroke="{MUTED}" stroke-dasharray="3 3"/>')
    for i, r in enumerate(rows):
        y = 4 + i * row_h
        s.append(f'<g><title>{E(r.get("tip", ""))}</title>')
        tx = lw - 8 - (24 if has_icon else 0)
        s.append(f'<text x="{tx}" y="{y + row_h / 2}" dy=".35em" text-anchor="end" class="{"strong" if r.get("strong") else ""}">{E(r["label"])}</text>')
        if r.get('icon'):
            sz = row_h - 4
            s.append(f'<image href="{r["icon"]}" x="{lw - 6 - sz}" y="{y + 2}" width="{sz}" height="{sz}" preserveAspectRatio="xMidYMid slice"/>')
        x0 = lw
        for j, v in enumerate(r['values']):
            if not v:
                continue
            w = x(v) - lw
            s.append(f'<rect x="{x0:.1f}" y="{y + 3}" width="{max(w, 0):.1f}" height="{row_h - 6}" rx="2" fill="{colors[j]}"/>')
            x0 += w
        if total:
            lab = r.get('total_label') or val_fmt(sum(v for v in r['values'] if v))
            s.append(f'<text x="{x0 + 5:.1f}" y="{y + row_h / 2}" dy=".35em">{E(lab)}</text>')
        s.append('</g>')
    s.append('</svg>')
    return ''.join(s)


def diverging(rows, W=760, row_h=22, aria='', fmtv=lambda v: f'{v:+,}'):
    lw = max(60, max(tw(r['label'], 7.5) for r in rows) + 14)
    H = len(rows) * row_h + 8
    mx = max(abs(r['value']) for r in rows) or 1
    mid = lw + (W - lw) / 2
    x = lambda v: mid + (W - lw - 80) / 2 * v / mx
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(aria)}"><line x1="{mid}" x2="{mid}" y1="0" y2="{H}" class="axis" stroke="{MUTED}"/>']
    for i, r in enumerate(rows):
        y = 4 + i * row_h
        v = r['value']
        x0, x1 = sorted([mid, x(v)])
        col = C[2] if v >= 0 else C[3]
        s.append(f'<g><title>{E(r.get("tip", ""))}</title><text x="{lw - 8}" y="{y + row_h / 2}" dy=".35em" text-anchor="end" class="{"strong" if r.get("strong") else ""}">{E(r["label"])}</text>')
        s.append(f'<rect x="{x0:.1f}" y="{y + 3}" width="{max(x1 - x0, 1):.1f}" height="{row_h - 6}" rx="2" fill="{col}"/>')
        tx = x(v) + 5 if v >= 0 else mid + 5
        s.append(f'<text x="{tx:.1f}" y="{y + row_h / 2}" dy=".35em" text-anchor="start">{E(fmtv(v))}</text></g>')
    s.append('</svg>')
    return ''.join(s)


def vgroup(cats, series, colors=None, W=760, H=260, ymax=None, suffix='', aria='', labels=True):
    """cats: labels; series: list of (name, [values])."""
    colors = colors or C
    m = dict(t=20, b=30, l=10, r=10)
    mx = ymax or max(max(v for v in vals) for _, vals in series) * 1.15
    bw = (W - m['l'] - m['r']) / len(cats)
    gw = bw * 0.75 / len(series)
    y = lambda v: H - m['b'] - (H - m['b'] - m['t']) * v / mx
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(aria)}">']
    for i, c in enumerate(cats):
        cx = m['l'] + bw * i + bw * 0.125
        for j, (name, vals) in enumerate(series):
            v = vals[i]
            s.append(f'<g><title>{E(c)} — {E(name)}: {v}{suffix}</title><rect x="{cx + j * gw:.1f}" y="{y(v):.1f}" width="{gw - 2:.1f}" height="{y(0) - y(v):.1f}" rx="2" fill="{colors[j]}"/>'
                     + (f'<text x="{cx + j * gw + gw / 2 - 1:.1f}" y="{y(v) - 4:.1f}" text-anchor="middle">{v}{suffix}</text>' if labels else '') + '</g>')
        s.append(f'<text x="{m["l"] + bw * i + bw / 2:.1f}" y="{H - 10}" text-anchor="middle" class="strong">{E(c)}</text>')
    s.append('</svg>')
    return ''.join(s)


def scatter(pts, xlab, ylab, W=760, H=400, xfmt=lambda v: f'{v:g}', yfmt=lambda v: f'{v:,.0f}', aria='', fit=None, r=6):
    """pts: dict(x, y, label, color, tip)."""
    m = dict(t=16, r=60, b=44, l=60)
    xs = [p['x'] for p in pts]; ys = [p['y'] for p in pts]
    import math
    def nice(lo, hi):
        pad = (hi - lo) * 0.08 or 1
        lo, hi = lo - pad, hi + pad
        raw = (hi - lo) / 5
        mag = 10 ** math.floor(math.log10(raw))
        step = min((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw))
        return math.floor(lo / step) * step, math.ceil(hi / step) * step, step
    x0, x1, xs_ = nice(min(xs), max(xs)); y0, y1, ys_ = nice(min(ys), max(ys))
    xt = [x0 + i * xs_ for i in range(int(round((x1 - x0) / xs_)) + 1)]
    yt = [y0 + i * ys_ for i in range(int(round((y1 - y0) / ys_)) + 1)]
    X = lambda v: m['l'] + (W - m['l'] - m['r']) * (v - x0) / (x1 - x0)
    Y = lambda v: H - m['b'] - (H - m['b'] - m['t']) * (v - y0) / (y1 - y0)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(aria)}"><g class="grid">']
    for xv in xt:
        s.append(f'<line x1="{X(xv):.1f}" x2="{X(xv):.1f}" y1="{m["t"]}" y2="{H - m["b"]}"/>')
    for yv in yt:
        s.append(f'<line x1="{m["l"]}" x2="{W - m["r"]}" y1="{Y(yv):.1f}" y2="{Y(yv):.1f}"/>')
    s.append('</g>')
    for xv in xt:
        s.append(f'<text x="{X(xv):.1f}" y="{H - m["b"] + 16}" text-anchor="middle">{E(xfmt(xv))}</text>')
    for yv in yt:
        s.append(f'<text x="{m["l"] - 6}" y="{Y(yv):.1f}" dy=".35em" text-anchor="end">{E(yfmt(yv))}</text>')
    s.append(f'<text x="{(W) / 2}" y="{H - 6}" text-anchor="middle" class="strong">{E(xlab)}</text>')
    s.append(f'<text transform="translate(14,{H / 2}) rotate(-90)" text-anchor="middle" class="strong">{E(ylab)}</text>')
    placed = []
    P = [(X(p['x']), Y(p['y']), p) for p in pts]
    def hit(b):
        return any(b[0] < q[2] and b[2] > q[0] and b[1] < q[3] and b[3] > q[1] for q in placed) or \
               any(b[0] - 5 < px < b[2] + 5 and b[1] - 5 < py < b[3] + 5 for px, py, _ in P)
    for px, py, p in sorted(P, key=lambda t: t[1]):
        s.append(f'<g><title>{E(p.get("tip", ""))}</title><circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{p.get("color", C[0])}" fill-opacity=".85"/></g>')
    if fit:
        a, b_ = fit
        s.append(f'<line x1="{X(x0):.1f}" y1="{Y(a + b_ * x0):.1f}" x2="{X(x1):.1f}" y2="{Y(a + b_ * x1):.1f}" stroke="{MUTED}" stroke-dasharray="5 4"/>')
    for px, py, p in sorted(P, key=lambda t: t[1]):
        if not p['label']:
            continue
        w = tw(p['label'], 7) + 2
        for dx, dy in [(9, 0), (-9 - w, 0), (9, -13), (9, 13), (-9 - w, -13), (-9 - w, 13), (9, -26), (9, 26), (-9 - w, 26), (-9 - w, -26)]:
            b = (px + dx, py + dy - 6, px + dx + w, py + dy + 6)
            if not hit(b):
                break
        placed.append(b)
        if dy:
            s.append(f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{(b[0] if dx > 0 else b[2]):.1f}" y2="{py + dy:.1f}" stroke="{MUTED}" stroke-width=".6"/>')
        s.append(f'<text x="{b[0]:.1f}" y="{py + dy:.1f}" dy=".35em" class="strong">{E(p["label"])}</text>')
    s.append('</svg>')
    return ''.join(s)


def rank_chart(teams, W=760, row_h=26, rank_label=None):
    """Solo/Duo bar + Flex dot + 5s diamond on a ladder axis (Iron 4 = 0 … Master = 28)."""
    lw = 70
    H = len(teams) * row_h + 34
    lo, hi = 4, 32
    X = lambda v: lw + (W - lw - 16) * (min(max(v, lo), hi) - lo) / (hi - lo)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Average Solo/Duo, Flex and Ranked 5s rank per team"><g class="grid">']
    ticks = [(4, 'Bronze 4'), (8, 'Silver 4'), (12, 'Gold 4'), (16, 'Plat 4'), (20, 'Emerald 4'), (24, 'Diamond 4'), (28, 'Master')]
    for v, l in ticks:
        s.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="0" y2="{H - 28}"/>')
    s.append('</g>')
    for v, l in ticks:
        s.append(f'<text x="{X(v):.1f}" y="{H - 10}" text-anchor="middle">{l}</text>')
    for i, t in enumerate(teams):
        y = i * row_h
        tip = f"{t['team']} ({t['swiss_record']}) — Solo/Duo {t['solo_avg']}, Flex {t['flex_avg']}, Ranked 5s {t['r5_avg']}"
        s.append(f'<g><title>{E(tip)}</title><text x="{lw - 8}" y="{y + row_h / 2}" dy=".35em" text-anchor="end" class="{"strong" if t["qualified"] else ""}">{"✓ " if t["qualified"] else ""}{E(t["team"])}</text>')
        if t['solo_score'] != '':
            s.append(f'<rect x="{X(lo):.1f}" y="{y + 5}" width="{X(t["solo_score"]) - X(lo):.1f}" height="{row_h - 10}" rx="2" fill="{C[0]}"/>')
            right = max(X(v) for v in (t['solo_score'], t['flex_score'], t['r5_score']) if v != '') + 9
            lab = E(t['solo_avg'])
            tcol = TIER_COL.get(t['solo_avg'].split()[0].title(), MUTED)
            if right + tw(lab, 5.8) < W:
                s.append(f'<text x="{right:.1f}" y="{y + row_h / 2}" dy=".35em" style="font-size:10px;font-weight:600;fill:{tcol}">{lab}</text>')
            else:
                s.append(f'<text x="{X(lo) + 6:.1f}" y="{y + row_h / 2}" dy=".35em" style="font-size:10px;fill:#fff">{lab}</text>')
        if t['flex_score'] != '':
            s.append(f'<circle cx="{X(t["flex_score"]):.1f}" cy="{y + row_h / 2}" r="5.5" fill="{C[1]}" stroke="var(--bg)" stroke-width="1.5"/>')
        if t['r5_score'] != '':
            cx, cy = X(t['r5_score']), y + row_h / 2
            s.append(f'<path d="M{cx},{cy - 6} L{cx + 6},{cy} L{cx},{cy + 6} L{cx - 6},{cy} Z" fill="{C[2]}" stroke="var(--bg)"/>')
        s.append('</g>')
    s.append('</svg>')
    return ''.join(s)


def histogram(values, bins, W=760, H=200, label=lambda a, b: f'{a}–{b}', aria=''):
    counts = [sum(1 for v in values if a <= v < b) for a, b in bins]
    mx = max(counts) or 1
    bw = (W - 20) / len(bins)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{E(aria)}">']
    for i, ((a, b), c) in enumerate(zip(bins, counts)):
        h = (H - 50) * c / mx
        x = 10 + i * bw
        s.append(f'<g><title>{label(a, b)}: {c}</title><rect x="{x + 3:.1f}" y="{H - 30 - h:.1f}" width="{bw - 6:.1f}" height="{h:.1f}" rx="2" fill="{C[0]}"/>'
                 f'<text x="{x + bw / 2:.1f}" y="{H - 34 - h:.1f}" text-anchor="middle">{c}</text>'
                 f'<text x="{x + bw / 2:.1f}" y="{H - 12}" text-anchor="middle">{E(label(a, b))}</text></g>')
    s.append('</svg>')
    return ''.join(s)



# ------------------------------------------------------------------ radar
# tournament stats only (no pre-tournament rank)
RADAR_AXES = [('kda', 'KDA', 1), ('avg_gold_per_min', 'Gold/min', 1), ('avg_gold_diff', 'Gold diff', 1), ('kill_participation', 'KP', 1),
              ('avg_damage_per_min', 'Dmg/min', 1), ('avg_game_minutes', 'Speed', -1)]


def radar_values(T, scouting):
    """Percentile of each team on each axis among the 16 teams (0 = lowest, 1 = highest). 'Speed' is reversed game time."""
    rows = {t['team']: dict(t) for t in T}
    out = {t: [] for t in rows}
    raw = {t: [] for t in rows}
    for key, _, sign in RADAR_AXES:
        vals = sorted(rows[t][key] * sign for t in rows)
        n = len(vals)
        for t in rows:
            v = rows[t][key] * sign
            below = sum(1 for x in vals if x < v); eq = sum(1 for x in vals if x == v)
            out[t].append(round((below + (eq - 1) / 2) / (n - 1), 3))
            raw[t].append(rows[t][key])
    return out, raw


def radar_svg(axes, series, size=260, labels=True, aria=''):
    """series: list of (values 0..1, colour, fill_opacity, dashed)."""
    import math
    pad = 52 if labels else 10
    c = size / 2; r = c - pad
    n = len(axes)
    pt = lambda i, v: (c + r * v * math.sin(2 * math.pi * i / n), c - r * v * math.cos(2 * math.pi * i / n))
    s = [f'<svg viewBox="0 0 {size} {size}" role="img" aria-label="{E(aria)}">']
    for ring in (0.25, 0.5, 0.75, 1):
        s.append('<polygon points="%s" fill="none" stroke="var(--line)"/>' % ' '.join('%.1f,%.1f' % pt(i, ring) for i in range(n)))
    for i, a in enumerate(axes):
        x, y = pt(i, 1)
        s.append(f'<line x1="{c}" y1="{c}" x2="{x:.1f}" y2="{y:.1f}" stroke="var(--line)"/>')
        if labels:
            lx, ly = pt(i, 1.18)
            anchor = 'middle' if abs(lx - c) < 8 else ('start' if lx > c else 'end')
            s.append(f'<text x="{lx:.1f}" y="{ly:.1f}" dy=".35em" text-anchor="{anchor}" style="font-size:10px">{E(a)}</text>')
    for vals, col, op, dashed in series:
        pts = ' '.join('%.1f,%.1f' % pt(i, max(v, 0.04)) for i, v in enumerate(vals))
        dash = 'stroke-dasharray="4 3"' if dashed else ''
        s.append(f'<polygon points="{pts}" fill="{col}" fill-opacity="{op}" stroke="{col}" stroke-width="{1.2 if dashed else 2}" {dash}/>')
    s.append('</svg>')
    return ''.join(s)


# ------------------------------------------------------------------ page shell
def page(fname, title, lede, body, toc=()):
    nav = ''.join(f'<a href="{f}" class="{"on" if f == fname else ""}">{E(t)}</a>' for f, t in PAGES)
    tocs = ('<div class="toc">' + ''.join(f'<a href="#{a}">{E(t)}</a>' for a, t in toc) + '</div>') if toc else ''
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} — SEEE LoL Swiss Stage 2026</title><style>{CSS}</style></head><body>
<nav class="top"><div class="wrap"><span class="brand">SEEE LoL 2026 · Swiss Stage</span>{nav}<a class="ghbtn" href="{REPO_URL}" target="_blank" rel="noopener">{GH_MARK}GitHub</a></div></nav>
<div class="wrap"><h1>{E(title)}</h1><p class="muted">{lede}</p>{tocs}{body}
<footer>Source code and data: <a href="{REPO_URL}">{REPO_URL.replace('https://', '')}</a>. Built by <code>scripts/build.py</code> from the match records, the post-game scoreboards and an op.gg (VN) snapshot taken 22 Nov 2026.
Raw and processed data: <code>data/</code>. Hover any bar or dot for its value; click a table header to sort.<br>
Champion icons from Riot Games' Data Dragon. This project isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.</footer></div>
<script>{JS}</script></body></html>"""


# ------------------------------------------------------------------ A. scouting
def page_a(d):
    sc, players, rl = d['scouting'], d['players'], d['rank_label']
    q = d['qualified']
    top8 = {s['team'] for s in sc[:8]}
    both = len(top8 & set(q))
    heavy = [s for s in sc if s['flex_verdict'] == 'Heavy Flex']
    r5p = [p for p in players if p['r5_score'] is not None]
    mostly = sorted([s for s in sc if s['flex_verdict'] == 'Mostly Solo/Duo'], key=lambda s: s['flex_share'])
    spread = sorted([s for s in sc if s['rank_spread'] != ''], key=lambda s: -s['rank_spread'])
    unr = [s for s in sc if s['solo_unranked']]
    finds = [
        f"<b>{E(sc[0]['team'])}</b> fields the strongest Solo/Duo lineup ({rk(sc[0]['solo_avg'])}), followed by "
        + ', '.join(f"<b>{E(s['team'])}</b> ({E(s['solo_avg'])})" for s in sc[1:3]) + f". The gap from #3 to #4 ({E(sc[3]['team'])}, {E(sc[3]['solo_avg'])}) is about {sc[2]['solo_score'] - sc[3]['solo_score']:.0f} divisions.",
        f"{both} of the 8 quarter-finalists were also among the 8 highest-ranked lineups.",
        f"Ranked 5s (tournament mode) is barely used: only {len(r5p)} of {len(players)} players have a 5s rank (" + ', '.join(f"{E(p['riot_id'])} – {E(p['team'])}" for p in r5p) + ").",
        f"Teams leaning on Flex: " + ', '.join(f"<b>{E(s['team'])}</b> ({s['flex_share']}% of ranked games)" for s in heavy) +
        f". The top teams mostly grind Solo/Duo: " + ', '.join(f"{E(s['team'])} {s['flex_share']}%" for s in mostly[:4]) + '.',
        f"Widest skill gaps inside a team: " + ', '.join(f"<b>{E(s['team'])}</b> ({s['rank_spread']:.0f} divisions, from {E(s['best_player'])} to {E(s['weakest_player'])})" for s in spread[:3]) + '.',
        "Teams with players who have no 2026 Solo/Duo rank (their average leans on fewer players): " + ', '.join(f"{E(s['team'])} ({s['solo_unranked']})" for s in unr) + '.',
    ]
    body = ['<h2 id="findings">Key findings</h2><ul class="find">' + ''.join(f'<li>{f}</li>' for f in finds) + '</ul>']

    body.append('<h2 id="ranks">Average rank by team</h2><p class="sub">Average over the players who actually played in the Swiss Stage, weighted by games played. Players with no 2026 rank in a queue are left out of that queue. ✓ = reached the quarter-finals.</p>')
    body.append('<div class="card">' + legend([('Solo/Duo (bar)', C[0]), ('Flex (dot)', C[1]), ('Ranked 5s (diamond)', C[2])]) + rank_chart(sc) + '</div>')

    cols = [('rank_seed', '#', 'n'), ('team', 'Team', ''), ('team_name', 'Name', ''), ('swiss_record', 'Swiss', ''), ('solo', 'Solo/Duo avg', ''), ('flex', 'Flex avg', ''),
            ('r5', 'Ranked 5s avg', ''), ('r5_ranked_players', '5s-ranked players', 'n'), ('players_used', 'Players used', 'n'),
            ('solo_unranked', 'Solo unranked', 'n'), ('best_player', 'Highest ranked', ''), ('weakest_player', 'Lowest ranked', ''), ('rank_spread', 'Spread (div.)', 'n')]
    rows = [dict(s, solo=(rk(s['solo_avg']), s['solo_score']), flex=(rk(s['flex_avg']), s['flex_score']), r5=(rk(s['r5_avg']), s['r5_score'] if s['r5_score'] != '' else -1),
                 team=(('✓ ' if s['qualified'] else '') + E(s['team']), s['team'])) for s in sc]
    body.append('<h3>Scouting table</h3>' + table(cols, rows))

    body.append('<h2 id="activity">Ranked activity in 2026</h2><p class="sub">Season-2026 ranked games (wins + losses) per player, averaged over the players each team used. A large number of games means a more reliable rank.</p>')
    act = sorted(sc, key=lambda s: -(s['solo_games_per_player'] + s['flex_games_per_player']))
    body.append('<div class="card">' + legend([('Solo/Duo games per player', C[0]), ('Flex games per player', C[1]), ('Ranked 5s games per player', C[2])]) +
                hbar([dict(label=s['team'], values=[s['solo_games_per_player'], s['flex_games_per_player'], round(s['r5_games_total'] / s['players_used'])],
                           tip=f"{s['team']}: {s['solo_games_per_player']} Solo, {s['flex_games_per_player']} Flex, {s['r5_games_total']} Ranked 5s in total", strong=s['qualified']) for s in act],
                     [0, 1, 2], aria='Ranked games per player by queue') + '</div>')

    body.append('<h2 id="flex">Are teams practising in Ranked Flex?</h2><p>Flex share = a team\'s Flex games as a share of all its 2026 ranked games. Flex regulars = players with at least 50 Flex games this season. '
                'op.gg only shows each player\'s own totals, not who they queued with, so a high share suggests the team practises together but doesn\'t prove it.</p>')
    fl = sorted(sc, key=lambda s: -s['flex_share'])
    body.append('<div class="card">' + legend([('Flex share of ranked games (%) — dashed line at 45% = heavy Flex; 25–44% = some Flex', C[1])]) +
                hbar([dict(label=s['team'], values=[s['flex_share']], tip=f"{s['team']}: {s['flex_share']}% Flex, {s['flex_regulars']} Flex regulars — {s['flex_verdict']}", strong=s['qualified']) for s in fl],
                     [0], colors=[C[1]], xmax=100, ref=45, val_fmt=lambda v: f'{v}%', aria='Flex share by team') + '</div>')
    cols = [('team', 'Team', ''), ('flex_share', 'Flex share %', 'n'), ('flex_regulars', 'Flex regulars', 'n'), ('flex_games_total', 'Flex games (team total)', 'n'),
            ('solo_games_total', 'Solo games (team total)', 'n'), ('r5_games_total', 'Ranked 5s games', 'n'), ('verdict', 'Verdict', '')]
    body.append(table(cols, [dict(s, verdict=(pill(s['flex_verdict'], 'ok' if s['flex_verdict'] == 'Heavy Flex' else 'warn' if s['flex_verdict'] == 'Some Flex' else ''), s['flex_share'])) for s in fl]))

    body.append('<h2 id="distribution">Rank distribution of all players</h2><p class="sub">Solo/Duo tier of every player who played at least one Swiss game.</p>')
    tiers = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Emerald', 'Diamond', 'Master']
    cnt = Counter((p['solo_label'].split()[0] if p['solo_score'] is not None else 'Unranked') for p in players if p['swiss_games'])
    body.append('<div class="card">' + hbar([dict(label=t, values=[cnt.get(t, 0)], tip=f'{t}: {cnt.get(t, 0)} players') for t in tiers + ['Unranked']], [0], aria='Players per Solo/Duo tier') + '</div>')

    body.append('<h2 id="teams">Team by team</h2><p class="sub">Every player who played, with Solo/Duo, Flex and Ranked 5s for season 2026 (tier · LP · games · win rate) and the champions they played in the Swiss Stage.</p>')
    for s in sorted(sc, key=lambda s: s['team']):
        ps = [p for p in players if p['team'] == s['team']]
        ps.sort(key=lambda p: (['TOP', 'JG', 'MID', 'AD', 'SP', ''].index(p['swiss_role']), -p['swiss_games']))

        def qcell(p, qn):
            if p[f'{qn}_score'] is None:
                return rk_cell(p[f'{qn}_label'], f'· {p[f"{qn}_games"]} g' if p[f'{qn}_games'] else '', -1)
            return rk_cell(p[f'{qn}_label'], f"· {p[f'{qn}_games']} g · {p[f'{qn}_winrate']}%", p[f'{qn}_score'])
        rows = [dict(role=d['role_name'].get(p['swiss_role'], '—'), riot=p['riot_id'], g=p['swiss_games'], solo=qcell(p, 'solo'), flex=qcell(p, 'flex'), r5=qcell(p, 'r5'),
                     champs=(ci_list(p['swiss_champions']), p['swiss_champions'])) for p in ps]
        cols = [('role', 'Role', ''), ('riot', 'Riot ID', ''), ('g', 'Swiss games', 'n'), ('solo', 'Solo/Duo', ''), ('flex', 'Flex', ''), ('r5', 'Ranked 5s', ''), ('champs', 'Champions in Swiss', 'wrap')]
        qual = pill('Quarter-finalist', 'ok') if s['qualified'] else pill('Eliminated', '')
        body.append(f'<div class="card teamcard" id="team-{E(s["team"])}"><h3>{E(tn(s["team"]))} <span class="muted">· Swiss {E(s["swiss_record"])} · rank #{s["rank_seed"]} of 16</span> {qual}</h3>'
                    f'<div class="kv"><span>Solo/Duo {rk(s["solo_avg"])}</span><span>Flex {rk(s["flex_avg"])}</span><span>Ranked 5s {rk(s["r5_avg"])}</span>'
                    f'<span>Flex share <b>{s["flex_share"]}%</b> ({E(s["flex_verdict"])})</span><span>Spread <b>{s["rank_spread"]} div.</b></span><span>Players used <b>{s["players_used"]}</b></span></div>'
                    + table(cols, rows) + '</div>')
    toc = [('findings', 'Key findings'), ('ranks', 'Average rank'), ('activity', 'Ranked activity'), ('flex', 'Flex practice'), ('distribution', 'Rank distribution'), ('teams', 'Team by team')]
    return page('a-team-scouting.html', 'A. Team scouting',
                'Each team\'s strength from season-2026 ranked data on op.gg (VN): average Solo/Duo, Flex and Ranked 5s rank, ranked games played, and whether teams practise in Flex.',
                ''.join(body), toc)



def meta_section(d):
    mp, tlist = d['meta_picks'], d['tierlist']
    q = set(d['qualified'])
    classes = ['Meta (tier 1-2)', 'Viable (tier 3)', 'Off-meta (tier 4-5)', 'Off-role (not in op.gg list)']
    ccol = [C[2], C[0], C[1], C[3]]
    n = len(mp)
    cnt = Counter(x['meta_class'] for x in mp)
    wr = lambda xs: round(100 * sum(x['won'] for x in xs) / len(xs)) if xs else None
    cps = [x for x in mp if x['pick_timing'] == 'counter-pick' and x['matchup']]
    fav = [x for x in cps if x['matchup'] == 'favourable']
    unf = [x for x in cps if x['matchup'] == 'unfavourable']
    body = ['<h2 id="meta">Meta analysis (patch 26.22 / 26.23)</h2>'
            '<p>Round 1 was played on <b>patch 26.22</b> and rounds 2–5 on <b>26.23</b>. Every pick is compared with op.gg\'s solo-queue statistics for the same patch and position '
            '(all servers; op.gg labels these patches 16.22 and 16.23). <b>Meta</b> = op.gg tier 1–2 in that position, <b>Viable</b> = tier 3, <b>Off-meta</b> = tier 4–5, '
            '<b>Off-role</b> = not in op.gg\'s list for that position at all (a flex or pocket pick, like Ziggs bot or Zed top).</p>'
            '<p><b>Counter-picks</b>: from the record\'s pick order and the standard draft (B1 · R1 R2 · B2 B3 · R3 · R4 · B4 B5 · R5), the player who locked in after his lane opponent counter-picked. '
            'The <b>matchup win rate</b> is op.gg\'s win rate of that champion against the lane opponent in that position and patch: ≥52% favourable, ≤48% unfavourable, otherwise even. '
            'Solo-queue matchups are a guide, not a law: under 100 games the figure is noisy and is marked. '
            '<i>Assumption:</i> the five picks in each record are listed in the order the team locked them in. The records don\'t say so explicitly.</p>']
    body.append('<div class="tiles">' + ''.join(f'<div class="tile"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in [
        (f"{round(100 * cnt[classes[0]] / n)}%", f'of {n} picks were meta (tier 1–2)'),
        (f"{round(100 * (cnt[classes[2]] + cnt[classes[3]]) / n)}%", 'off-meta or off-role'),
        (f"{wr([x for x in mp if x['meta_class'] == classes[0]])}%", 'win rate of meta picks'),
        (f"{wr([x for x in mp if x['meta_class'] in classes[2:]])}%", 'win rate of off-meta / off-role picks'),
        (f"{len(fav)}/{len(cps)}", 'counter-picks with a favourable matchup'),
        (f"{wr(fav)}%", 'win rate when the counter-pick was favourable')]) + '</div>')

    # per team meta-forward index
    teams = sorted({x['team'] for x in mp})
    rows, bars = [], []
    for t in teams:
        xs = [x for x in mp if x['team'] == t]
        c = Counter(x['meta_class'] for x in xs)
        tiers = [x['tier'] for x in xs if x['tier'] != '']
        cp = [x for x in xs if x['pick_timing'] == 'counter-pick' and x['matchup']]
        mw = [x['matchup_win_rate'] for x in xs if x['matchup_win_rate'] != '']
        rows.append(dict(team=(('✓ ' if t in q else '') + E(t), t), picks=len(xs), meta=(f"{round(100 * c[classes[0]] / len(xs))}%", c[classes[0]] / len(xs)),
                         avg_tier=round(st.mean(tiers), 2) if tiers else '', offmeta=c[classes[2]], offrole=c[classes[3]],
                         pop=round(st.mean(x['opgg_pick_rate'] for x in xs if x['opgg_pick_rate'] != ''), 1),
                         cp=len(cp), cpfav=(f"{sum(1 for x in cp if x['matchup'] == 'favourable')}/{len(cp)}", sum(1 for x in cp if x['matchup'] == 'favourable') / max(len(cp), 1)),
                         mwr=(f"{st.mean(mw):.1f}%", st.mean(mw)) if mw else ('—', 0)))
        bars.append(dict(label=t, strong=t in q, values=[c[k] / len(xs) * 100 for k in classes],
                         tip=f"{t}: " + ', '.join(f"{k.split(' (')[0]} {c[k]}" for k in classes)))
    bars.sort(key=lambda b: -b['values'][0])
    body.append('<h3 id="meta-teams">How meta-forward was each team?</h3><p class="sub">Share of each team\'s picks in each class. Sorted by the meta share — the "meta-forward index".</p>'
                '<div class="card">' + legend(list(zip(['Meta (tier 1–2)', 'Viable (tier 3)', 'Off-meta (tier 4–5)', 'Off-role'], ccol))) +
                hbar(bars, [0, 1, 2, 3], colors=ccol, xmax=100, total=False, aria='Pick classes per team') + '</div>')
    body.append(table([('team', 'Team', ''), ('picks', 'Picks', 'n'), ('meta', 'Meta share', 'n'), ('avg_tier', 'Avg op.gg tier', 'n'), ('offmeta', 'Off-meta picks', 'n'),
                       ('offrole', 'Off-role picks', 'n'), ('pop', 'Avg op.gg pick rate %', 'n'), ('cp', 'Counter-picks', 'n'), ('cpfav', 'Favourable counter-picks', 'n'),
                       ('mwr', 'Avg matchup win rate', 'n')], sorted(rows, key=lambda r: -r['meta'][1])))

    # did it matter?
    rows = []
    for k in classes:
        xs = [x for x in mp if x['meta_class'] == k]
        rows.append(dict(c=k, n=len(xs), w=sum(x['won'] for x in xs), wr=(f'{wr(xs)}%' if xs else '—', wr(xs) or 0)))
    rows2 = []
    for k in ('favourable', 'even', 'unfavourable'):
        for timing in ('counter-pick', 'blind'):
            xs = [x for x in mp if x['matchup'] == k and x['pick_timing'] == timing]
            rows2.append(dict(c=f'{k} · {timing}', n=len(xs), w=sum(x['won'] for x in xs), wr=(f'{wr(xs)}%' if xs else '—', wr(xs) or 0)))
    body.append('<h3 id="meta-result">Did meta and matchups decide games?</h3><div class="grid"><div class="card"><h4>Tournament win rate by pick class</h4>' +
                table([('c', 'Class', ''), ('n', 'Picks', 'n'), ('w', 'Won', 'n'), ('wr', 'Win rate', 'n')], rows, sortable=False) +
                '</div><div class="card"><h4>Tournament win rate by lane matchup</h4>' +
                table([('c', 'Matchup · timing', ''), ('n', 'Picks', 'n'), ('w', 'Won', 'n'), ('wr', 'Win rate', 'n')], rows2, sortable=False) +
                '<p class="sub">Each lane appears twice (once per side), so favourable and unfavourable mirror each other.</p></div></div>')

    # most picked with tiers
    pc = Counter(x['champion'] for x in mp)
    tiers_of = defaultdict(dict)
    for x in mp:
        tiers_of[x['champion']].setdefault(x['patch'], set()).add(f"{x['role']} T{x['tier']}" if x['tier'] != '' else f"{x['role']} off-role")
    rows = []
    for c, k in pc.most_common(20):
        xs = [x for x in mp if x['champion'] == c]
        mw = [x['matchup_win_rate'] for x in xs if x['matchup_win_rate'] != '']
        rows.append(dict(c=(ci(c), c), k=k, wr=(f'{wr(xs)}%', wr(xs)), t22='; '.join(sorted(tiers_of[c].get('26.22', []))) or '—', t23='; '.join(sorted(tiers_of[c].get('26.23', []))) or '—',
                         mw=(f'{st.mean(mw):.1f}%', st.mean(mw)) if mw else ('—', 0)))
    body.append('<h3 id="meta-champs">Most-picked champions and their meta tier</h3>' +
                table([('c', 'Champion', ''), ('k', 'Picks', 'n'), ('wr', 'Tournament WR', 'n'), ('t22', 'Patch 26.22 (round 1)', 'wrap'), ('t23', 'Patch 26.23 (rounds 2–5)', 'wrap'),
                       ('mw', 'Avg matchup WR', 'n')], rows))

    # meta gaps: tier-1 champions never picked
    picked = {(x['patch'], x['role'], x['champion']) for x in mp}
    rows = []
    for role_name in d['role_name'].values():
        for patch in ('26.22', '26.23'):
            t1 = [t for t in tlist if t['patch'] == patch and t['position'] == role_name and t['tier'] == 1]
            used = [t['champion'] for t in t1 if any(x['champion'] == t['champion'] and x['role'] == role_name for x in mp if x['patch'] == patch)]
            unused = [t['champion'] for t in t1 if t['champion'] not in used]
            rows.append(dict(r=role_name, p=patch, n=len(t1), used=(ci_list(', '.join(used)) if used else '—', ''), unused=(ci_list(', '.join(unused)) if unused else '—', '')))
    body.append('<h3 id="meta-gaps">Tier-1 champions: picked or ignored?</h3><p class="sub">op.gg tier-1 champions in each position, and whether anyone played them in that position on that patch. '
                'Bans are not counted here (see Ban & pick above).</p>' +
                table([('r', 'Position', ''), ('p', 'Patch', ''), ('n', 'Tier-1 champions', 'n'), ('used', 'Picked', 'wrap'), ('unused', 'Never picked', 'wrap')], rows, sortable=False))

    # off-meta / off-role list
    rows = [dict(code=x['code'], team=x['team'], role=x['role'], c=(ci(x['champion']), x['champion']), o=(ci(x['lane_opponent']), x['lane_opponent']), cls=x['meta_class'].split(' (')[0],
                 t=x['tier'] if x['tier'] != '' else '—', res=(pill('Win', 'ok') if x['won'] else pill('Loss', 'bad'), x['won']))
            for x in mp if x['meta_class'] in classes[2:]]
    body.append('<h3 id="meta-off">Off-meta and off-role picks</h3><p class="sub">Pocket picks and flex picks; who played them and how they went.</p>'
                '<details class="card"><summary>Show all %d off-meta / off-role picks</summary>' % len(rows) +
                table([('code', 'Match', ''), ('team', 'Team', ''), ('role', 'Position', ''), ('c', 'Champion', ''), ('o', 'Lane opponent', ''), ('cls', 'Class', ''), ('t', 'Tier', 'n'), ('res', 'Result', '')], rows) + '</details>')

    # counter-picks
    rows = [dict(code=x['code'], team=x['team'], role=x['role'], c=(ci(x['champion']), x['champion']), o=(ci(x['lane_opponent']), x['lane_opponent']), slot=f"{x['opponent_slot']} → {x['draft_slot']}",
                 mwr=(f"{x['matchup_win_rate']:.1f}%" + ('' if x['matchup_reliable'] else ' *'), x['matchup_win_rate']), g=x['matchup_games'],
                 m=(pill(x['matchup'], 'ok' if x['matchup'] == 'favourable' else 'bad' if x['matchup'] == 'unfavourable' else ''), x['matchup']),
                 res=(pill('Win', 'ok') if x['won'] else pill('Loss', 'bad'), x['won'])) for x in sorted(cps, key=lambda x: -x['matchup_win_rate'])]
    body.append('<h3 id="meta-counters">Counter-picks</h3><p class="sub">Every lane where one side picked after the other. Slot = draft order of the opponent\'s pick → the counter-pick (1–10). '
                '* = fewer than 100 games in op.gg\'s matchup sample.</p><div class="card">' +
                hbar([dict(label=t, values=[sum(1 for x in cps if x['team'] == t and x['matchup'] == 'favourable'),
                                            sum(1 for x in cps if x['team'] == t and x['matchup'] == 'even'),
                                            sum(1 for x in cps if x['team'] == t and x['matchup'] == 'unfavourable')], strong=t in q,
                           tip=f"{t}: favourable / even / unfavourable counter-picks") for t in teams], [0, 1, 2], colors=[C[2], MUTED, C[3]], aria='Counter-pick quality by team') +
                legend([('Favourable', C[2]), ('Even', MUTED), ('Unfavourable', C[3])]) + '</div>'
                '<details class="card"><summary>All %d counter-picks</summary>' % len(rows) +
                table([('code', 'Match', ''), ('team', 'Team', ''), ('role', 'Position', ''), ('c', 'Counter-pick', ''), ('o', 'Into', ''), ('slot', 'Slots', ''),
                       ('mwr', 'Matchup WR', 'n'), ('g', 'Games', 'n'), ('m', 'Matchup', ''), ('res', 'Result', '')], rows) + '</details>')
    return ''.join(body)



def draft_section(d):
    mp, drafts = d['meta_picks'], d['drafts']
    roles = list(d['role_name'].values())
    known = [x for x in mp if x['draft_slot'] != '']
    games = len({x['code'] for x in known})
    body = ['<h2 id="draft">Draft priorities</h2><p>Which positions and champions teams secured first. This uses the same assumption as the meta analysis: '
            'each record lists a team\'s picks in lock-in order, in the standard draft <b>B1 · R1 R2 · B2 B3 · R3</b> (phase 1) and <b>R4 · B4 B5 · R5</b> (phase 2). '
            f'Bans are split the same way: a team\'s first three listed bans are phase 1, the last two phase 2. {games} games have a usable draft (LS33 has none).</p>']
    # slot x role heat table
    slot_names = {1: 'B1', 2: 'R1', 3: 'R2', 4: 'B2', 5: 'B3', 6: 'R3', 7: 'R4', 8: 'B4', 9: 'B5', 10: 'R5'}
    cnt = Counter((x['draft_slot'], x['role']) for x in known)
    def heat(v, tot):
        a = v / tot if tot else 0
        return (f'<span style="display:inline-block;min-width:40px;padding:1px 6px;border-radius:4px;background:rgba(59,111,216,{0.08 + 0.7 * a:.2f})">{v}</span>', v)
    rows = []
    for sl in range(1, 11):
        tot = sum(cnt[(sl, r)] for r in roles)
        top = Counter(x['champion'] for x in known if x['draft_slot'] == sl).most_common(3)
        row = dict(slot=(f'<b>{slot_names[sl]}</b> <span class="muted">#{sl}</span>', sl), tot=tot,
                   ch=(' '.join(f'<span class="cl">{ci(c, 18)}{" <span class=muted>×%d</span>" % n if n > 1 else ""}</span>' for c, n in top), ''))
        for r in roles:
            row[r] = heat(cnt[(sl, r)], tot)
        rows.append(row)
    body.append('<h3 id="draft-slots">Which position is picked in each slot</h3><p class="sub">Count of picks per draft slot and position over the usable games; darker = more common. '
                'Positions picked early were treated as priority; positions picked last were usually saved for counter-picks.</p>' +
                table([('slot', 'Slot', ''), ('tot', 'Picks', 'n')] + [(r, r, 'n') for r in roles] + [('ch', 'Most picked champions', 'wrap')], rows, sortable=False))
    # average slot per role
    avg = {r: st.mean(x['draft_slot'] for x in known if x['role'] == r) for r in roles}
    body.append('<div class="grid"><div class="card"><h4>Average pick slot per position (1 = first pick, 10 = last)</h4>' +
                hbar([dict(label=r, values=[round(avg[r], 2)], tip=f'{r}: average slot {avg[r]:.2f}') for r in sorted(roles, key=lambda r: avg[r])],
                     [0], colors=[C[4]], W=460, xmax=10, val_fmt=lambda v: f'{v:.1f}', aria='Average pick slot per position') + '</div>')
    # first picks
    b1 = Counter(x['champion'] for x in known if x['draft_slot'] == 1)
    r12 = Counter(x['champion'] for x in known if x['draft_slot'] in (2, 3))
    fp_w = [x for x in known if x['draft_slot'] == 1]
    body.append('<div class="card"><h4>First picks</h4><p class="sub">Blue side\'s first pick (B1) and red side\'s answer (R1 + R2).</p>'
                f'<p><b>B1</b> ({len(fp_w)} games, blue won {sum(x["won"] for x in fp_w)}): ' + ci_list(', '.join(f'{c} x{n}' if n > 1 else c for c, n in b1.most_common())) + '</p>'
                '<p><b>R1–R2</b>: ' + ci_list(', '.join(f'{c} x{n}' if n > 1 else c for c, n in r12.most_common(12))) + '</p></div></div>')
    # bans by phase and side
    bans = [x for x in drafts if x['kind'] == 'ban' and x['order'] not in ('', None)]
    rows = []
    for side in ('blue', 'red'):
        for ph, rng in (('Phase 1 (bans 1–3)', (1, 2, 3)), ('Phase 2 (bans 4–5)', (4, 5))):
            c = Counter(x['champion'] for x in bans if x['side'] == side and int(x['order']) in rng)
            rows.append(dict(side=side.title(), ph=ph, n=sum(c.values()), top=(ci_list(', '.join(f'{k} x{v}' if v > 1 else k for k, v in c.most_common(8))), '')))
    first = Counter(x['champion'] for x in bans if int(x['order']) == 1)
    body.append('<h3 id="draft-bans">Ban priorities</h3><div class="card"><p class="sub">Most frequent bans by side and phase. Phase 1 bans remove the strongest or most-feared picks; '
                'phase 2 bans target the opponent\'s remaining positions.</p>' +
                table([('side', 'Side', ''), ('ph', 'Phase', ''), ('n', 'Bans', 'n'), ('top', 'Most banned', 'wrap')], rows, sortable=False) +
                '<p><b>Very first ban</b> of each team: ' + ci_list(', '.join(f'{k} x{v}' if v > 1 else k for k, v in first.most_common(10))) + '</p></div>')
    return ''.join(body)

# ------------------------------------------------------------------ B. Swiss evaluation
def page_b(d):
    M, S, champs, roles, pg, drafts = d['matches'], d['standings'], d['champions'], d['role_stats'], d['player_games'], d['drafts']
    G = d['n_games']
    played = [m for m in M if m['result_type'] == 'played']
    ups = sorted([m for m in played if m['upset']], key=lambda m: m['rank_gap'])
    sides = {s['side']: s for s in d['side_stats']}
    picked = [c for c in champs if c['picks']]
    banned = [c for c in champs if c['bans']]
    once = [c for c in picked if c['picks'] == 1]
    rs = sorted(roles, key=lambda r: -r['damage_share'])
    elim_hi = [s for s in S if not s['qualified'] and s['rank_seed'] <= 8]
    in_lo = [s for s in S if s['qualified'] and s['rank_seed'] > 8]
    gm = [m['game_minutes'] for m in played]
    fast = min(played, key=lambda m: m['game_minutes']); slow = max(played, key=lambda m: m['game_minutes'])
    finds = [
        f"The higher-ranked lineup won <b>{len(played) - len(ups)} of {len(played)}</b> played games; only {len(ups)} went against rank. 5 matches were decided without a game (4 no-shows, 1 ruling).",
        f"<b>Most surprising result: {E(ups[1]['code'])}</b> – the 2-2 elimination decider: {E(ups[1]['winner'])} ({rk(ups[1]['winner_rank'])}) beat {E(ups[1]['loser'])} ({rk(ups[1]['loser_rank'])}) in {E(ups[1]['game_time'])} "
        f"and knocked out the {'%d' % [s for s in S if s['team'] == ups[1]['loser']][0]['rank_seed']}th-ranked team. "
        f"The largest rank gap overcome was {E(ups[0]['code'])} ({E(ups[0]['winner'])} over {E(ups[0]['loser'])}, {abs(ups[0]['rank_gap']):.1f} divisions), but {E(ups[0]['winner'])}'s average rests on only 3 ranked players.",
        f"Seeding by rank vs. result: " + ', '.join(f"{E(s['team'])} (rank #{s['rank_seed']}) missed the quarter-finals" for s in elim_hi) + '; ' +
        ', '.join(f"{E(s['team'])} (rank #{s['rank_seed']}) made it" for s in in_lo) + '.',
        f"Side: blue won {sides['blue']['wins']} of {sides['blue']['games']} played games ({sides['blue']['winrate']}%), red {sides['red']['wins']} ({sides['red']['winrate']}%).",
        f"Games lasted {st.mean(gm):.1f} min on average (median {st.median(gm):.1f}); fastest {E(fast['code'])} {E(fast['game_time'])}, longest {E(slow['code'])} {E(slow['game_time'])}.",
        f"<b>{len(picked)}</b> different champions were picked and <b>{len(banned)}</b> banned across {G} games; {len(once)} champions were picked only once. "
        f"Most contested (appearance = picked or banned): " + ', '.join(f"{E(c['champion'])} {c['appearance_rate']:.0f}%" for c in sorted(champs, key=lambda c: (-c['appearance_rate'], -c['pick_rate']))[:5]) + ' of games.',
        f"Damage is carried by <b>{E(rs[0]['role'])}</b> and <b>{E(rs[1]['role'])}</b> ({rs[0]['damage_share']}% and {rs[1]['damage_share']}% of team damage). "
        f"Top laners were the team's #1 damage dealer {[r for r in roles if r['role'] == 'Top'][0]['top_damage_count']} times, Mid {[r for r in roles if r['role'] == 'Mid'][0]['top_damage_count']} times. "
        f"The ADC takes the most gold ({[r for r in roles if r['role'].startswith('Bot')][0]['gold_share']}%) but deals {[r for r in roles if r['role'].startswith('Bot')][0]['damage_share']}% of damage.",
    ]
    mp = d['meta_picks']
    _m = [x for x in mp if x['meta_class'].startswith('Meta')]
    _cf = [x for x in mp if x['pick_timing'] == 'counter-pick' and x['matchup'] == 'favourable']
    _tm = Counter(); _tn = Counter()
    for x in mp:
        _tn[x['team']] += 1; _tm[x['team']] += x['meta_class'].startswith('Meta')
    _mf = sorted(_tn, key=lambda t: -_tm[t] / _tn[t])
    finds.append(f"<b>Meta:</b> {round(100 * len(_m) / len(mp))}% of picks were op.gg tier 1–2 for their patch (26.22 in round 1, 26.23 after). "
                 f"Most meta-forward: {E(_mf[0])} ({round(100 * _tm[_mf[0]] / _tn[_mf[0]])}%); least: {E(_mf[-1])} ({round(100 * _tm[_mf[-1]] / _tn[_mf[-1]])}%). "
                 f"Meta picks won {round(100 * sum(x['won'] for x in _m) / len(_m))}% and counter-picks into a favourable solo-queue matchup won only "
                 f"{round(100 * sum(x['won'] for x in _cf) / len(_cf))}% ({sum(x['won'] for x in _cf)}/{len(_cf)}): at this level the player gap mattered more than the draft.")
    body = ['<h2 id="findings">Key findings</h2><ul class="find">' + ''.join(f'<li>{f}</li>' for f in finds) + '</ul>']

    # standings
    body.append('<h2 id="standings">Final standings</h2><p class="sub">Ordered by record, then Buchholz (sum of opponents\' wins), then rank seed. "Seed vs finish" = rank seed minus finishing place (positive = did better than rank suggests).</p>')
    cols = [('finish', '#', 'n'), ('team', 'Team', ''), ('team_name', 'Name', ''), ('record', 'Record', ''), ('buchholz', 'Buchholz', 'n'), ('forfeit_wins', 'Wins by forfeit/ruling', 'n'),
            ('forfeit_losses', 'Losses by forfeit/ruling', 'n'), ('rank_seed', 'Rank seed', 'n'), ('solo_avg', 'Solo/Duo avg', ''), ('svf', 'Seed vs finish', 'n'), ('q', 'Result', '')]
    body.append(table(cols, [dict(s, solo_avg=(rk(s['solo_avg']), -s['rank_seed']), svf=(f"{s['seed_vs_finish']:+d}", s['seed_vs_finish']), q=(pill('Quarter-finals', 'ok') if s['qualified'] else pill('Eliminated'), s['qualified'])) for s in S],
                      hl=lambda r: r['qualified']))
    body.append('<div class="card"><h4>Seed vs finish</h4>' + diverging([dict(label=s['team'], value=s['seed_vs_finish'], strong=s['qualified'],
                                                                                tip=f"{s['team']}: rank seed #{s['rank_seed']}, finished #{s['finish']}") for s in sorted(S, key=lambda s: -s['seed_vs_finish'])],
                                                                         aria='Rank seed minus finishing place') + '</div>')

    # rounds
    body.append('<h2 id="rounds">Round by round</h2><p class="sub">Winner in bold. Pools show both teams\' record before the match. No pairing was repeated.</p><div class="rounds">')
    for rd in range(1, 6):
        body.append(f'<div class="round card"><h4>Round {rd}</h4>')
        for m in [m for m in M if m['round'] == rd]:
            b = '<span class="w">%s</span>' % E(m['blue']) if m['winner'] == m['blue'] else E(m['blue'])
            r = '<span class="w">%s</span>' % E(m['red']) if m['winner'] == m['red'] else E(m['red'])
            tag = pill('forfeit' if m['result_type'] == 'forfeit' else 'ruling', '') if m['result_type'] != 'played' else (pill('upset', 'warn') if m['upset'] else '')
            body.append(f'<div class="m"><span class="pool">{E(m["code"])} · pool {E(m["pool"])} · {E(m["game_time"] or "no game")}</span><br>{b} <span class="muted">vs</span> {r} {tag}</div>')
        body.append('</div>')
    body.append('</div>')

    # all results
    body.append('<h2 id="results">All results with rank gap</h2><p class="sub">Rank gap = winner\'s average Solo/Duo rank minus loser\'s, in divisions, for the five players who played (team average for matches without a game). Negative = the lower-ranked side won.</p>')
    cols = [('code', 'Match', ''), ('round', 'Rd', 'n'), ('pool', 'Pool', ''), ('blue', 'Blue', ''), ('red', 'Red', ''), ('winner', 'Winner', ''), ('winner_rank', 'Winner rank', ''),
            ('loser_rank', 'Loser rank', ''), ('gap', 'Rank gap', 'n'), ('game_time', 'Time', ''), ('type', 'Note', ''), ('notes', 'Record notes', 'wrap')]
    body.append(table(cols, [dict(m, winner_rank=(rk(m['winner_rank']), 0), loser_rank=(rk(m['loser_rank']), 0), gap=(f"{m['rank_gap']:+.1f}", m['rank_gap']), type=(pill('upset', 'warn') if m['upset'] else pill(m['result_type']) if m['result_type'] != 'played' else pill('as expected', 'ok'), m['upset']))
                             for m in M], hl=lambda r: r['upset']))

    body.append('<h2 id="surprise">The most surprising results</h2>')
    for m in ups:
        mpg = [x for x in pg if x['code'] == m['code']]
        lines = []
        for team in (m['winner'], m['loser']):
            xs = [x for x in mpg if x['team'] == team]
            k = sum(x['kills'] for x in xs); dd = sum(x['deaths'] for x in xs); g = sum(x['gold'] for x in xs)
            star = max(xs, key=lambda x: (x['kills'] + x['assists']) / max(x['deaths'], 1))
            lines.append(f"<b>{E(team)}</b>: {k} kills, {dd} deaths, {g:,} gold — best KDA {E(star['riot_id'])} on {E(star['champion'])} ({star['kills']}/{star['deaths']}/{star['assists']})")
        body.append(f'<div class="card"><h3>{E(m["code"])} · Round {m["round"]} (pool {E(m["pool"])}) · {E(tn(m["winner"]))} beat {E(tn(m["loser"]))} in {E(m["game_time"])}</h3>'
                    f'<p>{E(m["winner"])} lineup: {rk(m["winner_rank"])} · {E(m["loser"])} lineup: {rk(m["loser_rank"])} · gap {m["rank_gap"]:+.1f} divisions.</p><ul class="find">' + ''.join(f'<li>{l}</li>' for l in lines) + '</ul></div>')

    # side & length
    body.append('<h2 id="sides">Sides and game length</h2><div class="grid">')
    body.append('<div class="card"><h4>Wins by side (played games)</h4>' + hbar([dict(label='Blue', values=[sides['blue']['wins']], tip=f"Blue {sides['blue']['wins']} wins"),
                                                                                 dict(label='Red', values=[sides['red']['wins']], tip=f"Red {sides['red']['wins']} wins")], [0], colors=[C[0]], W=400) + '</div>')
    bins = [(a, a + 3) for a in range(21, 42, 3)]
    body.append('<div class="card"><h4>Game length (minutes)</h4>' + histogram(gm, bins, W=440, aria='Game length distribution') + '</div></div>')

    # champions
    body.append('<h2 id="champions">Ban & pick</h2>')
    body.append('<div class="tiles">' + ''.join(f'<div class="tile"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in [
        (len(picked), 'different champions picked'), (len(banned), 'different champions banned'), (len(once), 'picked only once'),
        (len([c for c in picked if not c['bans']]), 'picked but never banned'), (G, 'games with picks'), (len({x['code'] for x in drafts if x['kind'] == 'ban'}), 'games with bans recorded')]) + '</div>')
    body.append('<p class="sub">Picks and positions come from the scoreboards; bans from the match records (LS33 has no bans recorded, LS15 only 3, LS32 one missing).</p>')
    body.append('<p class="sub"><b>Pick %</b> = share of the 28 played games in which the champion was picked, <b>Ban %</b> = banned, <b>Appearance %</b> = picked or banned '
                '(a champion can\'t be both in one game, so Appearance = Pick + Ban). Bans are missing for LS33 and partly for LS15 and LS32, so ban rates are slightly understated.</p>')
    top = sorted(champs, key=lambda c: (-c['appearance_rate'], -c['pick_rate'], c['champion']))[:20]
    body.append('<div class="card"><h4>Most contested champions — appearance % per match</h4>' + legend([('Pick %', C[0]), ('Ban %', C[1])]) +
                hbar([dict(label=c['champion'], icon=icon_url(c['champion']), values=[c['pick_rate'], c['ban_rate']], total_label=f"{c['appearance_rate']}%",
                           tip=f"{c['champion']}: appeared in {c['appearance_rate']}% of games — picked {c['pick_rate']}% (won {c['wins']} of {c['picks']}), banned {c['ban_rate']}%") for c in top],
                     [0, 1], xmax=100, val_fmt=lambda v: f'{v:.1f}%', aria='Top 20 champions by appearance rate') + '</div>')
    rows = [dict(champion=(ci(c['champion']), c['champion']), ap=(f"{c['appearance_rate']}%", c['appearance_rate']), pr=(f"{c['pick_rate']}%", c['pick_rate']),
                 br=(f"{c['ban_rate']}%", c['ban_rate']), picks=c['picks'], bans=c['bans'], wr=(f"{c['winrate']}%" if c['winrate'] != '' else '—', c['winrate'] if c['winrate'] != '' else -1),
                 main=c['main_role']) for c in sorted(champs, key=lambda c: (-c['appearance_rate'], -c['pick_rate'], c['champion']))]
    body.append('<h4>Pick, ban and appearance rate per champion</h4>' +
                '<details class="card" open><summary>Top 30 (click a header to sort; full list below in “Every champion”)</summary>' +
                table([('champion', 'Champion', ''), ('ap', 'Appearance %', 'n'), ('pr', 'Pick %', 'n'), ('br', 'Ban %', 'n'), ('picks', 'Picks', 'n'), ('bans', 'Bans', 'n'),
                       ('wr', 'Win rate when picked', 'n'), ('main', 'Main position', '')], rows[:30]) + '</details>')

    body.append('<h3 id="by-position">Picks by position</h3><p class="sub">Each position\'s most-picked champions with their win rate in this stage.</p><div class="grid">')
    for code, name in d['role_name'].items():
        cnt = Counter(x['champion'] for x in pg if x['role'] == code)
        wins = Counter(x['champion'] for x in pg if x['role'] == code and x['won'])
        rows = [dict(c=(ci(c), c), n=n, w=wins[c], wr=(f'{round(100 * wins[c] / n)}%', 100 * wins[c] / n), cn=c) for c, n in cnt.most_common()]
        body.append(f'<div class="card"><h4>{E(name)} — {len(cnt)} different champions</h4>' +
                    hbar([dict(label=r['cn'], icon=icon_url(r['cn']), values=[r['n']], tip=f"{r['cn']}: {r['n']} picks, {r['w']} wins") for r in rows[:10]], [0], W=420, row_h=20) +
                    f'<details><summary>All {len(rows)} champions</summary>' + table([('c', 'Champion', ''), ('n', 'Picks', 'n'), ('w', 'Wins', 'n'), ('wr', 'Win rate', 'n')], rows) + '</details></div>')
    body.append('</div>')

    body.append('<h3 id="team-bans">What each team banned</h3><p class="sub">Most frequent bans per team (from the records) — useful for draft prep against them.</p>')
    tb = defaultdict(Counter)
    tp = defaultdict(Counter)
    for x in drafts:
        if x['kind'] == 'ban':
            tb[x['team']][x['champion']] += 1
    for x in pg:
        tp[x['team']][x['champion']] += 1
    rows = [dict(team=t, bans=sum(tb[t].values()), top=(ci_list(', '.join(f'{c} x{n}' if n > 1 else c for c, n in tb[t].most_common(6))), ''),
                 picks=(ci_list(', '.join(f'{c} x{n}' if n > 1 else c for c, n in tp[t].most_common(6))), '')) for t in sorted(tp)]
    body.append(table([('team', 'Team', ''), ('bans', 'Bans recorded', 'n'), ('top', 'Most banned', 'wrap'), ('picks', 'Most picked', 'wrap')], rows))

    body.append('<h3 id="champ-table">Every champion</h3>')
    cols = [('champion', 'Champion', ''), ('appearance_rate', 'Appearance %', 'n'), ('pick_rate', 'Pick %', 'n'), ('ban_rate', 'Ban %', 'n'), ('picks', 'Picks', 'n'), ('bans', 'Bans', 'n'), ('wins', 'Wins', 'n'), ('winrate', 'Win rate %', 'n'),
            ('main_role', 'Main position', ''), ('picks_TOP', 'Top', 'n'), ('picks_JG', 'Jg', 'n'), ('picks_MID', 'Mid', 'n'), ('picks_AD', 'Bot', 'n'), ('picks_SP', 'Sup', 'n'),
            ('kda', 'KDA', 'n'), ('avg_damage_share', 'Dmg share %', 'n'), ('picked_by', 'Picked by', 'wrap')]
    body.append('<details class="card"><summary>Show all %d champions</summary>' % len(champs) +
                table(cols, [dict(c, champion=(ci(c['champion']), c['champion']), picked_by=c['picked_by']) for c in champs]) + '</details>')

    body.append(meta_section(d))
    body.append(draft_section(d))

    # damage
    body.append('<h2 id="damage">Which position carries the damage?</h2><p class="sub">Damage to champions from the scoreboards; 26 of the 28 games have a damage column (LS13 and LS33 do not), and one LS18 value was hidden by a tooltip.</p>')
    order = [r['role'] for r in roles]
    body.append('<div class="card">' + legend([('Share of team damage', C[0]), ('Share of team gold', C[1])]) +
                vgroup(order, [('Damage share', [r['damage_share'] for r in roles]), ('Gold share', [r['gold_share'] for r in roles])], suffix='%', aria='Damage and gold share by position') + '</div>')
    body.append('<div class="card"><h4>Damage share in wins vs losses</h4>' + legend([('In wins', C[2]), ('In losses', C[3])]) +
                vgroup(order, [('Wins', [r['damage_share_in_wins'] for r in roles]), ('Losses', [r['damage_share_in_losses'] for r in roles])], colors=[C[2], C[3]], suffix='%', H=220) + '</div>')
    cols = [('role', 'Position', ''), ('damage_share', 'Dmg share %', 'n'), ('damage_share_in_wins', 'in wins %', 'n'), ('damage_share_in_losses', 'in losses %', 'n'), ('damage_per_min', 'Dmg / min', 'n'),
            ('gold_share', 'Gold share %', 'n'), ('gold_per_min', 'Gold / min', 'n'), ('damage_per_1k_gold', 'Dmg per 1k gold', 'n'), ('kda', 'KDA', 'n'),
            ('top_damage_count', '#1 damage on team', 'n'), ('unique_champions', 'Different champions', 'n')]
    body.append(table(cols, roles))
    body.append('<h3>Top damage dealers by position</h3><p class="sub">Average damage per minute, players with at least 2 games with a damage column.</p><div class="grid wide">')
    for code, name in d['role_name'].items():
        agg = defaultdict(list)
        for x in pg:
            if x['role'] == code and x['damage_per_min'] != '':
                agg[(x['riot_id'], x['team'])].append(x)
        rows = sorted([dict(p=f'{k[0]} ({k[1]})', dpm=round(st.mean(v['damage_per_min'] for v in xs)), sh=round(st.mean(v['damage_share'] for v in xs if v['damage_share'] != ''), 1), g=len(xs))
                       for k, xs in agg.items() if len(xs) >= 2], key=lambda r: -r['dpm'])[:5]
        body.append(f'<div class="card"><h4>{E(name)}</h4>' + table([('p', 'Player', ''), ('g', 'Games', 'n'), ('dpm', 'Dmg/min', 'n'), ('sh', 'Dmg share %', 'n')], rows, sortable=False) + '</div>')
    body.append('</div>')

    toc = [('findings', 'Key findings'), ('standings', 'Standings'), ('rounds', 'Round by round'), ('results', 'All results'), ('surprise', 'Surprises'), ('sides', 'Sides & length'),
           ('champions', 'Ban & pick'), ('by-position', 'Picks by position'), ('team-bans', 'Team bans'), ('champ-table', 'Every champion'), ('meta', 'Meta analysis'), ('meta-counters', 'Counter-picks'), ('draft', 'Draft priorities'), ('damage', 'Damage by position')]
    return page('b-swiss-evaluation.html', 'B. Swiss Stage evaluation',
                '33 matches over 5 rounds (16–22 Nov 2026): 28 played, 4 forfeits, 1 ruling. Results against rank, surprises, ban & pick, meta and counter-picks on patches 26.22/26.23, and which position carries the damage.',
                ''.join(body), toc)


# ------------------------------------------------------------------ C. team evaluation
def page_c(d):
    T, TG, PS, pg = d['team_stats'], d['team_games'], d['player_stats'], d['player_games']
    q = set(d['qualified'])
    byk = sorted(T, key=lambda t: -t['kda'])
    byg = sorted(T, key=lambda t: -t['avg_gold_per_min'])
    longest = max(T, key=lambda t: t['avg_game_minutes'])
    shortest = min(T, key=lambda t: t['avg_game_minutes'])
    bygd = sorted(T, key=lambda t: -t['avg_gold_diff'])
    bykp = sorted(T, key=lambda t: -t['kill_participation'])
    kp_win = round(st.mean(g['kill_participation'] for g in TG if g['won'] and g['kill_participation'] != ''), 1)
    kp_loss = round(st.mean(g['kill_participation'] for g in TG if not g['won'] and g['kill_participation'] != ''), 1)
    finds = [
        f"Best team KDA: <b>{E(byk[0]['team'])}</b> ({byk[0]['kda']}), then {E(byk[1]['team'])} ({byk[1]['kda']}) and {E(byk[2]['team'])} ({byk[2]['kda']}). Worst: {E(byk[-1]['team'])} ({byk[-1]['kda']}).",
        f"Highest gold per minute: <b>{E(byg[0]['team'])}</b> ({byg[0]['avg_gold_per_min']:,}), {E(byg[1]['team'])} ({byg[1]['avg_gold_per_min']:,}), {E(byg[2]['team'])} ({byg[2]['avg_gold_per_min']:,}); lowest {E(byg[-1]['team'])} ({byg[-1]['avg_gold_per_min']:,}).",
        f"Biggest average gold lead at the end: <b>{E(bygd[0]['team'])}</b> ({bygd[0]['avg_gold_diff']:+,}); biggest deficit {E(bygd[-1]['team'])} ({bygd[-1]['avg_gold_diff']:+,}).",
        f"Longest games on average: {E(longest['team'])} ({longest['avg_game_minutes']:.1f} min); shortest: {E(shortest['team'])} ({shortest['avg_game_minutes']:.1f} min).",
        "Total gold mostly tracks game length, so gold per minute is the fairer comparison; both are shown.",
        f"Highest team kill participation (KP): <b>{E(bykp[0]['team'])}</b> ({bykp[0]['kill_participation']}%), {E(bykp[1]['team'])} ({bykp[1]['kill_participation']}%) and {E(bykp[2]['team'])} ({bykp[2]['kill_participation']}%) — their kills involve most of the team. "
        f"Lowest: {E(bykp[-1]['team'])} ({bykp[-1]['kill_participation']}%). Across all teams KP averaged {kp_win}% in wins and {kp_loss}% in losses.",
    ]
    body = ['<h2 id="findings">Key findings</h2><ul class="find">' + ''.join(f'<li>{f}</li>' for f in finds) + '</ul>']
    body.append('<p class="sub">Played games only (forfeits and the LS21 ruling have no game). KDA = (kills + assists) ÷ deaths over all of a team\'s games. Gold diff = team gold minus opponent gold at the end.</p>')
    cols = [('team', 'Team', ''), ('team_name', 'Name', ''), ('games', 'Games', 'n'), ('wins', 'W', 'n'), ('losses', 'L', 'n'), ('avg_game_minutes', 'Avg time (min)', 'n'), ('avg_win_minutes', 'Avg win time', 'n'),
            ('avg_loss_minutes', 'Avg loss time', 'n'), ('avg_gold', 'Avg total gold', 'n'), ('avg_gold_per_min', 'Gold / min', 'n'), ('avg_gold_diff', 'Avg gold diff', 'n'),
            ('avg_kills', 'Kills / g', 'n'), ('avg_deaths', 'Deaths / g', 'n'), ('avg_assists', 'Assists / g', 'n'), ('kda', 'KDA', 'n'), ('kill_participation', 'KP %', 'n'), ('kills_per_min', 'Kills / min', 'n'), ('avg_damage_per_min', 'Dmg / min', 'n'), ('best_kda_player', 'Best KDA player', '')]
    body.append('<h2 id="table">Team comparison</h2>' + table(cols, [dict(t, team=(('✓ ' if t['qualified'] else '') + E(t['team']), t['team'])) for t in T], hl=lambda r: r['qualified']))

    body.append('<h2 id="time-gold">Game time and gold</h2><div class="card">' + legend([('Quarter-finalist', C[0]), ('Eliminated', MUTED)]) +
                scatter([dict(x=t['avg_game_minutes'], y=t['avg_gold_per_min'], label=t['team'], color=C[0] if t['qualified'] else MUTED,
                              tip=f"{t['team']}: {t['avg_game_minutes']:.1f} min, {t['avg_gold_per_min']:,} gold/min, {t['wins']}-{t['losses']}") for t in T],
                        'Average game time (min)', 'Gold per minute', xfmt=lambda v: f'{v:.0f}', aria='Game time vs gold per minute') + '</div>')
    body.append('<div class="grid"><div class="card"><h4>Average total gold per game</h4>' +
                hbar([dict(label=t['team'], values=[t['avg_gold']], strong=t['qualified'], tip=f"{t['team']}: {t['avg_gold']:,} gold in {t['avg_game_minutes']:.1f} min") for t in sorted(T, key=lambda t: -t['avg_gold'])], [0], W=460) + '</div>')
    body.append('<div class="card"><h4>Average game time (min)</h4>' +
                hbar([dict(label=t['team'], values=[t['avg_game_minutes']], strong=t['qualified'], tip=f"{t['team']}: wins {t['avg_win_minutes']} / losses {t['avg_loss_minutes']} min") for t in sorted(T, key=lambda t: -t['avg_game_minutes'])],
                     [0], colors=[C[4]], W=460, val_fmt=lambda v: f'{v:.1f}') + '</div></div>')

    body.append('<h2 id="kda">KDA and gold difference per game</h2><div class="grid"><div class="card"><h4>Team KDA</h4>' +
                hbar([dict(label=t['team'], values=[t['kda']], strong=t['qualified'], tip=f"{t['team']}: {t['avg_kills']}/{t['avg_deaths']}/{t['avg_assists']} per game") for t in byk], [0], colors=[C[2]], W=460, val_fmt=lambda v: f'{v:.2f}') + '</div>')
    body.append('<div class="card"><h4>Average end-of-game gold difference</h4>' +
                diverging([dict(label=t['team'], value=t['avg_gold_diff'], strong=t['qualified'], tip=f"{t['team']}: {t['avg_gold_diff']:+,}") for t in bygd], W=460) + '</div></div>')
    body.append('<div class="card"><h4>Kills, deaths and assists per game</h4>' + legend([('Kills', C[0]), ('Deaths', C[3]), ('Assists', C[1])]) +
                vgroup([t['team'] for t in byk], [('Kills', [t['avg_kills'] for t in byk]), ('Deaths', [t['avg_deaths'] for t in byk]), ('Assists', [t['avg_assists'] for t in byk])],
                       colors=[C[0], C[3], C[1]], H=280, W=900, aria='Kills deaths assists per game', labels=False) + '</div>')

    # radars
    pv, raw = radar_values(T, d['scouting'])
    axes = [a[1] for a in RADAR_AXES]
    avg = [0.5] * len(axes)
    body.append('<h2 id="radar">Team profiles (radar)</h2><p>Each axis is the team\'s <b>percentile among the 16 teams</b>: the edge is the best team on that stat, the centre the worst, and the dashed outline is the middle of the field (50th percentile). '
                'Only tournament stats are used: KDA, gold per minute, end-of-game gold difference, kill participation (KP), team damage to champions per minute (games with a damage column only) and <b>Speed</b> (average game time reversed: shorter games score higher). '
                'Percentiles keep one extreme team from squashing everyone else; see the tables above for the actual values.</p>')
    # interactive compare
    import json as _json
    data = {t: dict(p=pv[t], r=raw[t]) for t in pv}
    teams_sorted = sorted(pv)
    opts = ''.join(f'<option value="{E(t)}">{E(tn(t))}</option>' for t in teams_sorted)
    body.append('<div class="card"><h4>Compare two teams</h4><div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:4px 0 6px">'
                f'<label><i style="display:inline-block;width:10px;height:10px;background:{C[0]};border-radius:2px"></i> <select id="ra">{opts}</select></label>'
                f'<label><i style="display:inline-block;width:10px;height:10px;background:{C[1]};border-radius:2px"></i> <select id="rb">{opts}</select></label></div>'
                '<div class="grid"><div id="radar-big" style="max-width:460px"></div><div class="tw"><table id="radar-tbl"><thead><tr><th>Stat</th><th class="n" id="rha"></th><th class="n" id="rhb"></th><th class="n">Field median</th></tr></thead><tbody></tbody></table></div></div></div>')
    med = []
    for i in range(len(axes)):
        vals = sorted(raw[t][i] for t in raw); m = len(vals)
        med.append(round((vals[m // 2] + vals[(m - 1) // 2]) / 2, 2))
    body.append('<script>window.RADAR=' + _json.dumps(dict(axes=axes, data=data, med=med, colors=[C[0], C[1]], qual=sorted(q)), ensure_ascii=False) + ';</script>')
    # small multiples
    body.append('<h3>All 16 teams</h3><p class="sub">In final standings order. Blue = quarter-finalist, grey = eliminated; dashed = field median (50th percentile). Percentiles use played games only.</p><div class="radars">')
    fin = {s['team']: s['finish'] for s in d['standings']}
    order_t = sorted(T, key=lambda t: fin[t['team']])
    rec = {s['team']: s['swiss_record'] for s in d['scouting']}
    for t in order_t:
        col = C[0] if t['team'] in q else C[5]
        best = [axes[i] for i, v in enumerate(pv[t['team']]) if v >= 0.8]
        worst = [axes[i] for i, v in enumerate(pv[t['team']]) if v <= 0.2]
        note = ('Strong: ' + ', '.join(best) if best else '') + (' · ' if best and worst else '') + ('Weak: ' + ', '.join(worst) if worst else '')
        body.append(f'<div class="card radar-card"><h4>{E(t["team"])} <span class="muted">· Swiss {E(rec[t["team"]])}</span></h4><div class="sub">{E(TEAM_NAME.get(t["team"], ""))}</div>' +
                    radar_svg(axes, [(avg, MUTED, 0, True), (pv[t['team']], col, 0.25, False)], size=260, aria=f'{t["team"]} profile') +
                    f'<p class="sub" style="margin:2px 0 0">{E(note) or "Around the middle on every axis"}</p></div>')
    body.append('</div>')


    # ---------------- rank vs performance
    prof = d['profile']
    solo = {p['riot_id']: p['solo_score'] for p in d['players']}
    lab = {p['riot_id']: p['solo_label'] for p in d['players']}
    keys = ['kda', 'kill_participation', 'damage_per_min', 'damage_share', 'gold_per_min', 'deaths_per_game']
    perf = {}
    for r in prof:
        if r['games'] < 2:
            continue
        vals = [r[f'pct_{k}'] for k in keys if r[f'pct_{k}'] != '']
        if not vals:
            continue
        cur = perf.get(r['riot_id'])
        if cur is None or r['games'] > cur['games']:
            perf[r['riot_id']] = dict(r, perf=st.mean(vals))
    pts = [dict(id=k, team=v['team'], role=v['role'], x=solo[k], y=v['perf'], games=v['games']) for k, v in perf.items() if solo.get(k) is not None]
    n_ = len(pts); mx = st.mean(p['x'] for p in pts); my = st.mean(p['y'] for p in pts)
    b1 = sum((p['x'] - mx) * (p['y'] - my) for p in pts) / sum((p['x'] - mx) ** 2 for p in pts); a1 = my - b1 * mx
    sx = st.pstdev(p['x'] for p in pts); sy = st.pstdev(p['y'] for p in pts)
    corr = b1 * sx / sy
    for p in pts:
        p['res'] = p['y'] - (a1 + b1 * p['x'])
    over = sorted(pts, key=lambda p: -p['res'])[:8]; under = sorted(pts, key=lambda p: p['res'])[:8]
    named = {p['id'] for p in over[:5] + under[:5]}
    body.append('<h2 id="rank-perf">Rank vs tournament performance</h2><p>Each dot is a player with at least 2 games in one position. '
                '<b>x</b> = Solo/Duo rank (season 2026, from Part A). <b>y</b> = performance index: the average of the six percentiles from the player radars '
                '(KDA, KP, damage/min, damage share, gold/min, survival), each ranked within the player\'s position. The dashed line is what rank alone predicts; '
                f'dots above it out-performed their rank. Correlation between rank and performance: <b>r = {corr:.2f}</b> ({n_} players).</p>')
    ticks = {0: 'Iron 4', 4: 'Bronze 4', 8: 'Silver 4', 12: 'Gold 4', 16: 'Plat 4', 20: 'Emerald 4', 24: 'Diamond 4', 28: 'Master'}
    body.append('<div class="card">' + legend([('Quarter-finalist', C[0]), ('Eliminated', MUTED)]) +
                scatter([dict(x=p['x'], y=p['y'], label=(p['id'].split('#')[0] if p['id'] in named else ''), color=C[0] if p['team'] in q else MUTED,
                              tip=f"{p['id']} ({p['team']}, {p['role']}): {lab[p['id']]}, performance {p['y']:.0f}/100, {'+' if p['res'] >= 0 else ''}{p['res']:.0f} vs rank") for p in pts],
                        'Solo/Duo rank', 'Performance index (0–100)', H=440, r=5, fit=(a1, b1),
                        xfmt=lambda v: (f'Master {round((v - 28) * 100)} LP' if v >= 28 else f"{['Iron', 'Bronze', 'Silver', 'Gold', 'Plat', 'Emerald', 'Diamond'][int(v) // 4]} {4 - int(v) % 4}") if v >= 0 else '',
                        yfmt=lambda v: f'{v:.0f}' if v >= 0 else '', aria='Rank versus performance') + '</div>')
    cols = [('p', 'Player', ''), ('team', 'Team', ''), ('role', 'Pos.', ''), ('g', 'G', 'n'), ('rank', 'Solo/Duo', ''), ('perf', 'Performance', 'n'), ('res', 'vs rank', 'n')]
    mk = lambda p: dict(p=p['id'], team=p['team'], role=p['role'], g=p['games'], rank=(rk(lab[p['id']]), p['x']), perf=(f"{p['y']:.0f}", p['y']), res=(f"{p['res']:+.0f}", p['res']))
    body.append('<div class="grid wide"><div class="card"><h4>Out-performed their rank</h4>' + table(cols, [mk(p) for p in over], sortable=False) + '</div>'
                '<div class="card"><h4>Under-performed their rank</h4>' + table(cols, [mk(p) for p in under], sortable=False) + '</div></div>')

    # full table: every player, main position (most games)
    pl = {p['riot_id']: p for p in d['players']}
    mainp = {}
    for r in prof:
        cur = mainp.get(r['riot_id'])
        if cur is None or r['games'] > cur['games']:
            mainp[r['riot_id']] = r
    def q_(p, qn):
        if p[f'{qn}_score'] is None:
            return rk_cell('Unranked', f"· {p[f'{qn}_games']} g" if p[f'{qn}_games'] else '', -1)
        return rk_cell(p[f'{qn}_label'], f"· {p[f'{qn}_games']} g · {p[f'{qn}_winrate']}%", p[f'{qn}_score'])
    def pc(r, k):
        v = r[f'pct_{k}']
        return ('—', -1) if v == '' else (f'{v}', v)
    full = []
    for pid, r in mainp.items():
        p = pl.get(pid)
        vals = [r[f'pct_{k}'] for k in keys if r[f'pct_{k}'] != '']
        perf_v = st.mean(vals) if vals else None
        sc = p['solo_score'] if p else None
        exp = a1 + b1 * sc if sc is not None else None
        diff = perf_v - exp if (perf_v is not None and exp is not None) else None
        small = r['games'] < 2
        if diff is None:
            verdict = ('No Solo/Duo rank', '')
        elif diff >= 10:
            verdict = ('Over-performed', 'ok')
        elif diff <= -10:
            verdict = ('Under-performed', 'bad')
        else:
            verdict = ('As expected', '')
        vtxt = pill(verdict[0], verdict[1]) + (' <span class="pill warn">1 game</span>' if small else '')
        full.append(dict(p=pid, team=(('✓ ' if r['team'] in q else '') + E(r['team']), r['team']), role=r['role'], g=r['games'],
                         solo=q_(p, 'solo') if p else ('—', -1), flex=q_(p, 'flex') if p else ('—', -1),
                         exp=(f'{exp:.0f}' if exp is not None else '—', exp if exp is not None else -999),
                         perf=(f'{perf_v:.0f}' if perf_v is not None else '—', perf_v if perf_v is not None else -999),
                         diff=(f'{diff:+.0f}' if diff is not None else '—', diff if diff is not None else -999),
                         v=(vtxt, diff if diff is not None else -999),
                         kda=pc(r, 'kda'), kp=pc(r, 'kill_participation'), dpm=pc(r, 'damage_per_min'), dsh=pc(r, 'damage_share'), gpm=pc(r, 'gold_per_min'), surv=pc(r, 'deaths_per_game')))
    full.sort(key=lambda x: -x['diff'][1])
    vc = Counter(x['v'][0].split('</span>')[0].split('>')[-1] for x in full)
    body.append('<h3 id="rank-perf-table">Every player: rank vs tournament performance</h3>'
                '<p class="sub"><b>Expected</b> = the performance index the player\'s Solo/Duo rank predicts (the dashed line above). <b>Actual</b> = his performance index in his main position. '
                '<b>Gap</b> = actual − expected; ±10 or more counts as over- or under-performing. The six columns on the right are his percentiles within the position '
                '(Survival = fewer deaths). Players with one game are flagged: their numbers are a single game. Sorted by gap; click any header to re-sort.</p>'
                f'<p class="sub">{vc.get("Over-performed", 0)} over-performed, {vc.get("As expected", 0)} as expected, {vc.get("Under-performed", 0)} under-performed, '
                f'{vc.get("No Solo/Duo rank", 0)} without a Solo/Duo rank.</p>' +
                '<details class="card" open><summary>All %d players</summary>' % len(full) +
                table([('p', 'Player', ''), ('team', 'Team', ''), ('role', 'Pos.', ''), ('g', 'G', 'n'), ('solo', 'Solo/Duo (2026)', ''), ('flex', 'Flex (2026)', ''),
                       ('exp', 'Expected', 'n'), ('perf', 'Actual', 'n'), ('diff', 'Gap', 'n'), ('v', 'Verdict', ''),
                       ('kda', 'KDA', 'n'), ('kp', 'KP', 'n'), ('dpm', 'Dmg/min', 'n'), ('dsh', 'Dmg %', 'n'), ('gpm', 'Gold/min', 'n'), ('surv', 'Survival', 'n')], full) + '</details>')
    # export
    d['_rank_perf_rows'] = [dict(riot_id=x['p'], team=x['team'][1], role=x['role'], games=x['g'], solo=x['solo'][0], expected=x['exp'][0], actual=x['perf'][0],
                                 gap=x['diff'][0], verdict=re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', x['v'][0])).strip()) for x in full]

    # ---------------- game flow & stomps
    games = defaultdict(list)
    for g in TG:
        games[g['code']].append(g)
    flow = []
    for code, gs in sorted(games.items()):
        w = [g for g in gs if g['won']][0]; l = [g for g in gs if not g['won']][0]
        flow.append(dict(code=code, winner=w['team'], loser=l['team'], mins=w['game_minutes'], time=w['game_time'], lead=w['gold_diff'],
                         kd=w['kills'] - l['kills'], w=w, l=l))
    cls = lambda f: 'Stomp' if f['lead'] >= 10000 else 'Clear' if f['lead'] >= 5000 else 'Close' if f['lead'] >= 0 else 'Comeback'
    cc = Counter(cls(f) for f in flow)
    body.append('<h2 id="flow">Game flow: stomps and close games</h2><p>The scoreboard only shows the end of each game, so a game is judged by the <b>winner\'s gold lead at the end</b>: '
                '<b>stomp</b> ≥ 10,000, <b>clear</b> 5,000–9,999, <b>close</b> under 5,000, and <b>comeback</b> if the winner finished behind on gold.</p>')
    body.append('<div class="tiles">' + ''.join(f'<div class="tile"><div class="v">{cc.get(k, 0)}</div><div class="l">{k.lower()} games</div></div>' for k in ('Stomp', 'Clear', 'Close', 'Comeback')) +
                f'<div class="tile"><div class="v">{st.median(f["lead"] for f in flow):,.0f}</div><div class="l">median winning gold lead</div></div></div>')
    bins = [(-10000, 0), (0, 2500), (2500, 5000), (5000, 7500), (7500, 10000), (10000, 15000), (15000, 20000), (20000, 30000)]
    body.append('<div class="grid"><div class="card"><h4>Winner\'s gold lead at the end</h4>' +
                histogram([f['lead'] for f in flow], bins, W=460, label=lambda a, b: f'{a // 1000:+d}k–{b // 1000}k' if a < 0 else f'{a // 1000}–{b // 1000}k', aria='Winner gold lead histogram') + '</div>')
    body.append('<div class="card"><h4>Game length vs winning gold lead</h4>' +
                scatter([dict(x=f['mins'], y=f['lead'], label='', color={'Stomp': C[2], 'Clear': C[0], 'Close': C[1], 'Comeback': C[3]}[cls(f)],
                              tip=f"{f['code']}: {f['winner']} beat {f['loser']} in {f['time']} with {f['lead']:+,} gold") for f in flow],
                        'Game length (min)', 'Winner gold lead', W=460, H=300, r=5, xfmt=lambda v: f'{v:.0f}', aria='Game length vs gold lead') +
                legend([('Stomp', C[2]), ('Clear', C[0]), ('Close', C[1]), ('Comeback', C[3])]) + '</div></div>')
    rows = [dict(code=f['code'], w=f['winner'], l=f['loser'], t=f['time'], lead=(f"{f['lead']:+,}", f['lead']), k=f"{f['w']['kills']}–{f['l']['kills']}",
                 c=(pill(cls(f), 'ok' if cls(f) == 'Stomp' else 'warn' if cls(f) in ('Close', 'Comeback') else ''), f['lead'])) for f in sorted(flow, key=lambda f: f['lead'])]
    body.append('<details class="card"><summary>All 28 games by winning gold lead (closest first)</summary>' +
                table([('code', 'Match', ''), ('w', 'Winner', ''), ('l', 'Loser', ''), ('t', 'Time', ''), ('lead', 'Gold lead', 'n'), ('k', 'Kills', ''), ('c', 'Type', '')], rows) + '</details>')
    # win rate by game length (team level) and what separates winners
    lb = [(0, 25), (25, 30), (30, 35), (35, 99)]
    lrows = []
    for a, b in lb:
        fs = [f for f in flow if a <= f['mins'] < b]
        lrows.append(dict(b=f'{a}–{b} min' if b < 99 else f'{a}+ min', n=len(fs), lead=(f"{st.median(f['lead'] for f in fs):,.0f}" if fs else '—', 0),
                          k=(f"{st.mean(f['w']['kills'] + f['l']['kills'] for f in fs):.1f}" if fs else '—', 0)))
    sep = []
    for key, labl in [('kills', 'Kills'), ('deaths', 'Deaths (fewer)'), ('gold', 'Gold'), ('damage', 'Damage to champions'), ('kill_participation', 'Team KP'), ('assists', 'Assists')]:
        pairs = [(f['w'][key], f['l'][key]) for f in flow if f['w'][key] != '' and f['l'][key] != '']
        better = sum(1 for wv, lv in pairs if (wv < lv if key == 'deaths' else wv > lv))
        sep.append(dict(s=labl, n=len(pairs), p=(f'{round(100 * better / len(pairs))}%', better / len(pairs)),
                        w=(f'{st.mean(p[0] for p in pairs):,.0f}' if key in ('gold', 'damage') else f'{st.mean(p[0] for p in pairs):,.1f}', 0),
                        l=(f'{st.mean(p[1] for p in pairs):,.0f}' if key in ('gold', 'damage') else f'{st.mean(p[1] for p in pairs):,.1f}', 0)))
    body.append('<div class="grid"><div class="card"><h4>By game length</h4>' +
                table([('b', 'Length', ''), ('n', 'Games', 'n'), ('lead', 'Median winning gold lead', 'n'), ('k', 'Total kills per game', 'n')], lrows, sortable=False) +
                '<p class="sub">Shorter games are usually stomps; long games are closer on gold.</p></div>'
                '<div class="card"><h4>What separates winners from losers</h4>' +
                table([('s', 'Stat', ''), ('p', 'Winner was ahead', 'n'), ('w', 'Winner avg', 'n'), ('l', 'Loser avg', 'n'), ('n', 'Games', 'n')], sep, sortable=False) +
                '<p class="sub">Share of games in which the winning team had more of each stat (fewer deaths). Damage uses the 25 games where both teams have a damage total.</p></div></div>')

    # kill participation
    body.append('<h2 id="kp">Kill participation (KP)</h2><p>KP is the share of a team\'s kills that a player took part in (kills + assists ÷ team kills). '
                '<b>Team KP</b> is the average of its five players\' KP in a game, averaged over the team\'s games. A high value means fights are played together, '
                'with kills shared across the map. A low value means kills come from isolated plays, or that one or two players do most of the killing. '
                '<b>Read it next to kills per game</b>: a team that gets very few kills (MSD, 5 per game) shows a high KP simply because every kill is a group effort.</p>')
    body.append('<div class="grid"><div class="card"><h4>Team KP (average per game)</h4>' +
                hbar([dict(label=t['team'], values=[t['kill_participation']], strong=t['qualified'],
                           tip=f"{t['team']}: {t['kill_participation']}% (wins {t['kp_in_wins'] or '—'}%, losses {t['kp_in_losses'] or '—'}%)") for t in bykp],
                     [0], colors=[C[4]], W=460, xmax=100, val_fmt=lambda v: f'{v}%', aria='Team kill participation') + '</div>')
    both = [t for t in T if t['kp_in_wins'] != '' and t['kp_in_losses'] != '']
    body.append('<div class="card"><h4>KP in wins vs losses</h4><p class="sub">Only teams with both a win and a loss in played games.</p>' + legend([('In wins', C[2]), ('In losses', C[3])]) +
                vgroup([t['team'] for t in both], [('Wins', [t['kp_in_wins'] for t in both]), ('Losses', [t['kp_in_losses'] for t in both])],
                       colors=[C[2], C[3]], W=460, H=240, ymax=100, aria='KP in wins and losses', labels=False) + '</div></div>')
    # heat table team x position
    def heat(v):
        if v == '' or v is None:
            return ('—', -1)
        a = max(0, min(1, (v - 40) / 50))
        return (f'<span style="display:inline-block;min-width:46px;padding:1px 6px;border-radius:4px;background:rgba(128,100,162,{0.12 + 0.6 * a:.2f})">{v}%</span>', v)
    rows = [dict(team=(('✓ ' if t['qualified'] else '') + E(t['team']), t['team']), kp=(f"{t['kill_participation']}%", t['kill_participation']),
                 top=heat(t['kp_TOP']), jg=heat(t['kp_JG']), mid=heat(t['kp_MID']), ad=heat(t['kp_AD']), sp=heat(t['kp_SP']),
                 most=t['kp_most_involved'], least=t['kp_least_involved'], spread=t['kp_spread']) for t in bykp]
    body.append('<div class="card"><h4>KP by position inside each team</h4><p class="sub">Share of the team\'s kills each position took part in, over all played games. '
                'Spread = most involved minus least involved position; a big spread means one position is cut off from the team\'s fights (often a side-laning top).</p>' +
                table([('team', 'Team', ''), ('kp', 'Team KP', 'n'), ('top', 'Top', 'n'), ('jg', 'Jungle', 'n'), ('mid', 'Mid', 'n'), ('ad', 'Bot', 'n'), ('sp', 'Support', 'n'),
                       ('most', 'Most involved', ''), ('least', 'Least involved', ''), ('spread', 'Spread (pts)', 'n')], rows) + '</div>')
    # top KP per position (players with >= 2 games): (kills + assists) / team kills, summed over their games
    tkills = {(g['code'], g['team']): g['kills'] for g in TG}
    body.append('<h3 id="kp-top">Highest KP by position</h3><p class="sub">Players with at least 2 played games. KP = (kills + assists) ÷ team kills, summed over all their games. '
                'Kills per game shows how many kills there were to take part in.</p><div class="grid wide">')
    for code, name in d['role_name'].items():
        agg = defaultdict(lambda: [0, 0, 0, set()])
        for x in pg:
            if x['role'] == code:
                a = agg[(x['riot_id'], x['team'])]
                a[0] += x['kills'] + x['assists']; a[1] += tkills[(x['code'], x['team'])]; a[2] += 1; a[3].add(x['champion'])
        rows = sorted([dict(p=f'{k[0]}', t=k[1], g=v[2], kp=(f'{100 * v[0] / v[1]:.1f}%', 100 * v[0] / v[1]), tk=round(v[1] / v[2], 1))
                       for k, v in agg.items() if v[2] >= 2 and v[1]], key=lambda r: -r['kp'][1])[:5]
        body.append(f'<div class="card"><h4>{E(name)}</h4>' + table([('p', 'Player', ''), ('t', 'Team', ''), ('g', 'G', 'n'), ('kp', 'KP', 'n'), ('tk', 'Team kills / game', 'n')], rows, sortable=False) + '</div>')
    body.append('</div>')
    body.append('<h3 id="kp-best-game">Best single-game KP by position</h3><p class="sub">Highest KP in one game, among games where the team got at least 10 kills.</p><div class="grid wide">')
    for code, name in d['role_name'].items():
        xs = [(100 * (x['kills'] + x['assists']) / tkills[(x['code'], x['team'])], x) for x in pg if x['role'] == code and tkills[(x['code'], x['team'])] >= 10]
        xs.sort(key=lambda r: (-r[0], -tkills[(r[1]['code'], r[1]['team'])]))
        rows = [dict(p=x['riot_id'], t=x['team'], m=x['code'], c=x['champion'], kda=f"{x['kills']}/{x['deaths']}/{x['assists']}",
                     tk=tkills[(x['code'], x['team'])], kp=(f'{v:.1f}%', v)) for v, x in xs[:5]]
        body.append(f'<div class="card"><h4>{E(name)}</h4>' + table([('p', 'Player', ''), ('t', 'Team', ''), ('m', 'Match', ''), ('c', 'Champion', ''), ('kda', 'K/D/A', ''),
                                                                     ('tk', 'Team kills', 'n'), ('kp', 'KP', 'n')], rows, sortable=False) + '</div>')
    body.append('</div>')
    rkp = defaultdict(list)
    for r in d['team_role_kp']:
        if r['kill_participation'] != '':
            rkp[r['role']].append(r['kill_participation'])
    body.append('<div class="card"><h4>Average KP by position (all teams)</h4>' +
                hbar([dict(label=r, values=[round(st.mean(v), 1)], tip=f'{r}: {round(st.mean(v), 1)}% across 16 teams') for r, v in rkp.items()],
                     [0], colors=[C[4]], xmax=100, val_fmt=lambda v: f'{v}%', aria='Average KP by position') + '</div>')

    # leaderboards
    body.append('<h2 id="players">Player leaderboards</h2><p class="sub">Players with at least 2 games. Damage figures exclude LS13 and LS33. A game with 0 deaths counts KDA as kills + assists.</p><div class="grid wide">')
    elig = [p for p in PS if p['games'] >= 2]
    for key, title, f in [('kda', 'KDA', lambda v: f'{v:.2f}'), ('damage_per_min', 'Damage per minute', lambda v: f'{v:,}'), ('damage_share', 'Share of team damage %', lambda v: f'{v}'),
                          ('gold_per_min', 'Gold per minute', lambda v: f'{v:,}'), ('avg_kill_participation', 'Kill participation %', lambda v: f'{v}')]:
        rows = sorted([p for p in elig if p[key] != ''], key=lambda p: -p[key])[:10]
        body.append(f'<div class="card"><h4>{E(title)}</h4>' + table([('riot_id', 'Player', ''), ('team', 'Team', ''), ('role', 'Pos.', ''), ('games', 'G', 'n'), ('v', title, 'n')],
                                                                     [dict(p, v=(f(p[key]), p[key])) for p in rows], sortable=False) + '</div>')
    body.append('</div>')
    cols = [('team', 'Team', ''), ('role', 'Pos.', ''), ('riot_id', 'Player', ''), ('solo_rank', 'Solo/Duo', ''), ('games', 'G', 'n'), ('wins', 'W', 'n'), ('kills', 'K', 'n'), ('deaths', 'D', 'n'),
            ('assists', 'A', 'n'), ('kda', 'KDA', 'n'), ('avg_kill_participation', 'KP %', 'n'), ('damage_per_min', 'Dmg/min', 'n'), ('damage_share', 'Dmg %', 'n'), ('gold_per_min', 'Gold/min', 'n'), ('champions', 'Champions', 'wrap')]
    body.append('<details class="card"><summary>All %d players</summary>' % len(PS) + table(cols, [dict(p, champions=(ci_list(p['champions']), p['champions']), solo_rank=(rk(p['solo_rank']), 0)) for p in PS]) + '</details>')

    # per-team logs
    body.append('<h2 id="logs">Team by team: every game</h2>')
    for t in sorted(T, key=lambda t: t['team']):
        gs = [g for g in TG if g['team'] == t['team']]
        rows = [dict(g, res=(pill('Win', 'ok') if g['won'] else pill('Loss', 'bad'), g['won']), gd=(f"{g['gold_diff']:+,}", g['gold_diff']), kda_s=f"{g['kills']}/{g['deaths']}/{g['assists']}") for g in gs]
        cols = [('code', 'Match', ''), ('round', 'Rd', 'n'), ('opponent', 'Opponent', ''), ('side', 'Side', ''), ('res', 'Result', ''), ('game_time', 'Time', ''), ('gold', 'Gold', 'n'),
                ('gold_per_min', 'Gold/min', 'n'), ('gd', 'Gold diff', 'n'), ('kda_s', 'K/D/A', ''), ('kda', 'KDA', 'n'), ('kill_participation', 'KP %', 'n')]
        ps = [dict(p, champions=(ci_list(p['champions']), p['champions'])) for p in PS if p['team'] == t['team']]
        pcols = [('role', 'Pos.', ''), ('riot_id', 'Player', ''), ('games', 'G', 'n'), ('kda', 'KDA', 'n'), ('avg_kill_participation', 'KP %', 'n'), ('damage_per_min', 'Dmg/min', 'n'), ('damage_share', 'Dmg %', 'n'),
                 ('gold_per_min', 'Gold/min', 'n'), ('champions', 'Champions', 'wrap')]
        body.append(f'<div class="card teamcard" id="team-{E(t["team"])}"><h3>{E(tn(t["team"]))} <span class="muted">· {t["wins"]}-{t["losses"]} in played games · KDA {t["kda"]} · KP {t["kill_participation"]}% · {t["avg_gold_per_min"]:,} gold/min</span></h3>'
                    + table(cols, rows) + '<h4>Players</h4>' + table(pcols, ps) + '</div>')
    toc = [('findings', 'Key findings'), ('table', 'Comparison'), ('time-gold', 'Time & gold'), ('kda', 'KDA & gold diff'), ('radar', 'Radar profiles'), ('rank-perf', 'Rank vs performance'), ('rank-perf-table', 'Rank vs performance table'), ('flow', 'Game flow & stomps'), ('kp', 'Kill participation'), ('kp-top', 'Top KP by position'), ('kp-best-game', 'Best KP game'), ('players', 'Player leaderboards'), ('logs', 'Every game')]
    return page('c-team-evaluation.html', 'C. Team evaluation',
                'How each team played: game time, total gold, gold per minute, gold difference, KDA and kill participation per game, plus player leaderboards and a log of every game.',
                ''.join(body), toc)



# ------------------------------------------------------------------ D. quarterfinalists
P_AXES = [('kda', 'KDA'), ('kill_participation', 'KP'), ('damage_per_min', 'Dmg/min'), ('damage_share', 'Dmg %'), ('gold_per_min', 'Gold/min'), ('deaths_per_game', 'Survival')]
DAYS = {'T2': 'Mon', 'T3': 'Tue', 'T4': 'Wed', 'T5': 'Thu', 'T6': 'Fri', 'T7': 'Sat', 'CN': 'Sun'}


def when(sched):
    parts = [x.strip() for x in str(sched).split(',')]
    if len(parts) == 3:
        return f"{DAYS.get(parts[1], parts[1])} {parts[2]}/2026, {parts[0].replace('h', ':')}"
    return str(sched)


def page_d(d):
    prof, ko, T, M, S = d['profile'], d['knockout'], d['team_stats'], d['matches'], d['standings']
    rank = {p['riot_id']: p['solo_label'] for p in d['players']}
    tstat = {t['team']: t for t in T}
    st_ = {s['team']: s for s in S}
    pv, raw = radar_values(T, d['scouting'])
    t_axes = [a[1] for a in RADAR_AXES]
    order_roles = list(d['role_name'].values())
    pa = [a[1] for a in P_AXES]
    mid = [0.5] * len(pa)

    def pvals(r):
        return [(r[f'pct_{k}'] / 100 if r[f'pct_{k}'] != '' else 0) for k, _ in P_AXES]

    def main_players(team):
        out = {}
        for role in order_roles:
            xs = [r for r in prof if r['team'] == team and r['role'] == role]
            if xs:
                out[role] = max(xs, key=lambda r: (r['games'], r['riot_id']))
        return out

    body = []
    # bracket
    rows = [dict(code=k['code'], a=tn(k['advantage']), b=tn(k['disadvantage']), when=when(k['scheduled']), semi=k['semi'] + (' (balanced pairing)' if k['balanced'] else ''),
                 ra=f"{st_[k['advantage']]['record']} · #{st_[k['advantage']]['finish']}", rb=f"{st_[k['disadvantage']]['record']} · #{st_[k['disadvantage']]['finish']}") for k in ko]
    body.append('<h2 id="bracket">Quarter-final bracket</h2><p class="sub">From the Excel KNOCKOUT sheet. The advantage side is the higher Swiss finisher. '
                'Semi-final 1 = winners of LKQ1 and LKQ2 (Sat 28/11, 09:00); semi-final 2 = winners of LKQ3 and LKQ4 (Sat 28/11, 13:00).</p>' +
                table([('code', 'Match', ''), ('a', 'Advantage', ''), ('ra', 'Swiss', ''), ('b', 'Disadvantage', ''), ('rb', 'Swiss', ''), ('when', 'When', ''), ('semi', 'Then', '')], rows, sortable=False))
    body.append('<h2 id="read">How to read the player radars</h2><p>Six tournament stats per player: <b>KDA</b>, <b>KP</b> (kill participation), <b>Dmg/min</b> (damage to champions per minute), '
                '<b>Dmg %</b> (share of team damage), <b>Gold/min</b> and <b>Survival</b> (deaths per game, reversed: fewer deaths = further out). '
                'Each axis is a <b>percentile among all players of the same position</b> in the Swiss Stage (players with at least 2 games there), so a support is compared with supports. '
                'Outer edge = best in that position, dashed ring = position median. Damage uses only games with a damage column (not LS13, LS33). '
                'A player with 1 game is marked <i>small sample</i>. Hover a radar for the actual values.</p>')

    def player_card(r, col):
        vals = pvals(r)
        tip = ' · '.join(f"{lab} {r[k]}{'%' if k in ('kill_participation', 'damage_share') else ''} ({r[f'pct_{k}']}th)" for k, lab in P_AXES if r[k] != '')
        flag = ' <span class="pill warn">small sample</span>' if r['games'] < 2 else ''
        strong = [lab for (k, lab), v in zip(P_AXES, vals) if r[f'pct_{k}'] != '' and v >= 0.8]
        weak = [lab for (k, lab), v in zip(P_AXES, vals) if r[f'pct_{k}'] != '' and v <= 0.2]
        note = ('Strong: ' + ', '.join(strong) if strong else '') + (' · ' if strong and weak else '') + ('Weak: ' + ', '.join(weak) if weak else '')
        svg = radar_svg(pa, [(mid, MUTED, 0, True), (vals, col, 0.25, False)], size=250, aria=f"{r['riot_id']} profile")
        svg = svg.replace('<svg ', '<svg ', 1).replace('>', f'><title>{E(tip)}</title>', 1)
        return (f'<div class="card radar-card"><h4>{E(r["role"])} · {E(r["riot_id"])}{flag}</h4>'
                f'<div class="sub">{r["games"]} games ({r["wins"]}W) · Solo/Duo {rk(rank.get(r["riot_id"], "—"))}</div>' + svg +
                f'<div class="kv" style="font-size:12px"><span>K/D/A <b>{r["kills"]}/{r["deaths"]}/{r["assists"]}</b></span><span>KDA <b>{r["kda"]}</b></span><span>KP <b>{r["kill_participation"]}%</b></span>'
                f'<span>Dmg/min <b>{fmt(r["damage_per_min"])}</b></span><span>Dmg <b>{fmt(r["damage_share"])}%</b></span><span>Gold/min <b>{r["gold_per_min"]}</b></span><span>Deaths/g <b>{r["deaths_per_game"]}</b></span></div>'
                f'<p class="sub" style="margin:2px 0">{E(note) or "Around the middle of the position"}</p><div class="sub" style="margin:0">{ci_list(r["champions"])}</div></div>')

    def team_block(team, col):
        t = tstat[team]
        path = [m for m in M if team in (m['blue'], m['red'])]
        steps = ' → '.join(f"{'W' if m['winner'] == team else 'L'} vs {m['red'] if m['blue'] == team else m['blue']}" + (' (ff)' if m['result_type'] != 'played' else '') for m in path)
        ps = sorted([r for r in prof if r['team'] == team], key=lambda r: (order_roles.index(r['role']), -r['games']))
        h = [f'<div class="card"><h3 id="team-{E(team)}">{E(tn(team))} <span class="muted">· Swiss {E(st_[team]["record"])} · finished #{st_[team]["finish"]}</span></h3>'
             f'<div class="kv"><span>Path: <b>{E(steps)}</b></span></div>'
             f'<div class="kv"><span>KDA <b>{t["kda"]}</b></span><span>Gold/min <b>{t["avg_gold_per_min"]:,}</b></span><span>Gold diff <b>{t["avg_gold_diff"]:+,}</b></span>'
             f'<span>KP <b>{t["kill_participation"]}%</b></span><span>Dmg/min <b>{fmt(t["avg_damage_per_min"])}</b></span><span>Avg time <b>{t["avg_game_minutes"]:.1f} min</b></span></div>'
             '<div class="radars">'
             f'<div class="card radar-card"><h4>Team profile</h4><div class="sub">Percentile among the 16 teams (as in Part C)</div>' +
             radar_svg(t_axes, [([0.5] * len(t_axes), MUTED, 0, True), (pv[team], col, 0.25, False)], size=250, aria=f'{team} team profile') + '</div>']
        h += [player_card(r, col) for r in ps]
        h.append('</div></div>')
        return ''.join(h)

    toc = [('bracket', 'Bracket'), ('read', 'How to read')]
    for k in ko:
        a, b = k['advantage'], k['disadvantage']
        anchor = k['code'].lower()
        toc.append((anchor, f"{k['code']} {a} vs {b}"))
        body.append(f'<h2 id="{anchor}">{E(k["code"])} · {E(a)} vs {E(b)} <span class="muted" style="font-size:15px;font-weight:400">· {E(when(k["scheduled"]))}</span></h2>'
                    f'<p class="muted" style="margin-top:-2px">{E(tn(a))} ⚔️ {E(tn(b))}</p>')
        sa, sb = tstat[a], tstat[b]
        lines = []
        for key, lab, f in [('kda', 'KDA', lambda v: f'{v}'), ('avg_gold_per_min', 'gold/min', lambda v: f'{v:,}'), ('kill_participation', 'KP', lambda v: f'{v}%'),
                            ('avg_damage_per_min', 'damage/min', lambda v: f'{v:,}'), ('avg_game_minutes', 'avg game', lambda v: f'{v:.1f} min')]:
            lines.append(f'{lab}: {E(a)} {f(sa[key])} vs {E(b)} {f(sb[key])}')
        body.append('<p class="sub">' + ' · '.join(lines) + '</p>')
        body.append(team_block(a, C[0]))
        body.append(team_block(b, C[1]))
        # lane matchups
        ma, mb = main_players(a), main_players(b)
        body.append(f'<div class="card"><h3>Lane matchups</h3><p class="sub">Each team\'s main player in each position (most games there). {legend([(a, C[0]), (b, C[1])])}</p><div class="radars">')
        for role in order_roles:
            if role in ma and role in mb:
                ra, rb = ma[role], mb[role]
                svg = radar_svg(pa, [(mid, MUTED, 0, True), (pvals(ra), C[0], 0.18, False), (pvals(rb), C[1], 0.18, False)], size=250, aria=f'{role}: {ra["riot_id"]} vs {rb["riot_id"]}')
                edge_a = sum(1 for k, _ in P_AXES if ra[f'pct_{k}'] != '' and rb[f'pct_{k}'] != '' and ra[f'pct_{k}'] > rb[f'pct_{k}'])
                edge_b = sum(1 for k, _ in P_AXES if ra[f'pct_{k}'] != '' and rb[f'pct_{k}'] != '' and rb[f'pct_{k}'] > ra[f'pct_{k}'])
                def fv(k, v):
                    if v == '':
                        return '—'
                    return {'kda': f'{v:.2f}', 'kill_participation': f'{v}%', 'damage_share': f'{v}%', 'deaths_per_game': f'{v:.2f}',
                            'damage_per_min': f'{v:,}', 'gold_per_min': f'{v:,}'}[k]
                labs = {'deaths_per_game': 'Deaths / game'}
                rows = ''.join(f'<tr><td>{labs.get(k, lab)}</td><td class="n">{fv(k, ra[k])}</td><td class="n">{fv(k, rb[k])}</td></tr>' for k, lab in P_AXES)
                body.append(f'<div class="card radar-card"><h4>{E(role)}</h4><div class="sub">{E(ra["riot_id"])} vs {E(rb["riot_id"])} · ahead on {edge_a} vs {edge_b} axes</div>{svg}'
                            f'<table><thead><tr><th>Stat</th><th class="n">{E(a)}</th><th class="n">{E(b)}</th></tr></thead><tbody>{rows}</tbody></table></div>')
        body.append('</div></div>')

    # ---------------- champion pools
    pg = d['player_games']
    body.append('<h2 id="pools">Champion pools</h2><p>How deep each quarter-finalist\'s champion pool was in the Swiss Stage. <b>Pool</b> = different champions played; '
                '<b>Main share</b> = how often the player\'s most-played champion came out. A one-trick (main share 75%+ over 3+ games) is easy to ban out; '
                'a deep pool is harder to draft against. Bans that targeted the player\'s champions show how opponents read him.</p>')
    trows = []
    for k in ko:
        for t in (k['advantage'], k['disadvantage']):
            xs = [x for x in pg if x['team'] == t]
            c = Counter(x['champion'] for x in xs)
            banned_vs = Counter(x['champion'] for x in d['drafts'] if x['kind'] == 'ban' and x['team'] != t and x['code'] in {y['code'] for y in xs})
            trows.append(dict(team=(E(tn(t)), t), qf=k['code'], g=len({x['code'] for x in xs}), picks=len(xs), uniq=len(c), ratio=(f'{len(c) / len(xs):.0%}', len(c) / len(xs)),
                              top=(ci_list(', '.join(f'{a} x{b}' if b > 1 else a for a, b in c.most_common(5))), ''),
                              bv=(ci_list(', '.join(f'{a} x{b}' if b > 1 else a for a, b in banned_vs.most_common(5))), '')))
    body.append('<div class="card"><h4>Team pools</h4>' +
                table([('team', 'Team', ''), ('qf', 'QF', ''), ('g', 'Games', 'n'), ('picks', 'Picks', 'n'), ('uniq', 'Different champions', 'n'), ('ratio', 'Variety', 'n'),
                       ('top', 'Most played', 'wrap'), ('bv', 'Banned against them', 'wrap')], trows) +
                '<p class="sub">Variety = different champions ÷ picks; 100% means no champion was repeated.</p></div>')
    prow = []
    for k in ko:
        for t in (k['advantage'], k['disadvantage']):
            for r in sorted([r for r in prof if r['team'] == t], key=lambda r: (order_roles.index(r['role']), -r['games'])):
                xs = [x for x in pg if x['riot_id'] == r['riot_id'] and x['team'] == t]
                c = Counter(x['champion'] for x in xs)
                main_c, main_n = c.most_common(1)[0]
                share = main_n / len(xs)
                roles_played = sorted({x['role'] for x in xs})
                tag = 'one-trick' if share >= 0.75 and len(xs) >= 3 else ('flex' if len(roles_played) > 1 else ('deep' if len(c) == len(xs) and len(xs) >= 3 else ''))
                prow.append(dict(team=t, role=r['role'], p=r['riot_id'], g=len(xs), uniq=len(c), share=(f'{share:.0%}', share),
                                 champs=(ci_list(', '.join(f'{a} x{b}' if b > 1 else a for a, b in c.most_common())), ''),
                                 pos=', '.join(d['role_name'][x] for x in roles_played),
                                 tag=(pill(tag, 'warn' if tag == 'one-trick' else 'ok' if tag in ('deep', 'flex') else '') if tag else '', tag)))
                if r['riot_id'] in [y['p'] for y in prow[:-1]] and prow[-1]['team'] == t:
                    prow.pop()
    body.append('<details class="card" open><summary>Player pools (quarter-finalists)</summary>' +
                table([('team', 'Team', ''), ('role', 'Pos.', ''), ('p', 'Player', ''), ('g', 'Games', 'n'), ('uniq', 'Pool', 'n'), ('share', 'Main share', 'n'),
                       ('champs', 'Champions', 'wrap'), ('pos', 'Positions played', ''), ('tag', '', '')], prow) + '</details>')
    toc.append(('pools', 'Champion pools'))
    return page('d-quarterfinalists.html', 'D. Quarterfinalists',
                'The 8 teams in the quarter-finals (23–27 Nov 2026): each team\'s Swiss path and profile, a six-stat radar for every player, and head-to-head lane matchups for each quarter-final.',
                ''.join(body), toc)


# ------------------------------------------------------------------ index
def page_index(d):
    M, S = d['matches'], d['standings']
    played = [m for m in M if m['result_type'] == 'played']
    ups = [m for m in played if m['upset']]
    files = [('matches.csv', 'One row per match: teams, sides, winner, result type, time, rank gap, upset flag'),
             ('teams.csv', 'Team code, full name, Swiss record and whether it reached the quarter-finals'),
             ('standings.csv', 'Final Swiss standings with Buchholz and rank seed'),
             ('team_games.csv', 'One row per team per played game: K/D/A, gold, gold diff, time'),
             ('player_games.csv', 'One row per player per played game: champion, position, K/D/A, damage, gold, shares'),
             ('drafts.csv', 'Every ban and pick (bans from records, picks from records + scoreboards), raw and cleaned names'),
             ('player_ranks.csv', 'op.gg season-2026 Solo/Duo, Flex, Ranked 5s per player, plus Swiss games and champions'),
             ('team_scouting.csv', 'Team average ranks, ranked activity and Flex practice'),
             ('champions.csv', 'Picks, bans, presence, win rate, positions per champion'),
             ('role_stats.csv', 'Damage and gold share per position'),
             ('team_stats.csv', 'Per-team averages over played games, incl. team kill participation (KP) and KP by position'),
             ('team_role_kp.csv', 'Kill participation per team and position'),
             ('player_position_profile.csv', 'Per player and position: six radar stats and their percentile within the position'),
             ('rank_vs_performance.csv', 'Per player: Solo/Duo rank, expected vs actual tournament performance, gap and verdict'),
             ('player_stats.csv', 'Per-player totals and averages'),
             ('side_stats.csv', 'Blue vs red wins'),
             ('data_issues.csv', 'Every gap found in the data and how it was handled')]
    body = [f'<p><a class="ghbtn" href="{REPO_URL}" target="_blank" rel="noopener">{GH_MARK}View the code &amp; data on GitHub</a></p>']
    body += [f'<div class="tiles">' + ''.join(f'<div class="tile"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in [
        (16, 'teams'), (33, 'matches'), (len(played), 'games played'), (len(M) - len(played), 'forfeits / rulings'), (len(ups), 'upsets vs rank'), (90, 'players looked up on op.gg')]) + '</div>']
    body.append('<div class="grid">' + ''.join(f'<a class="card" style="text-decoration:none;color:inherit" href="{f}"><h3>{E(t)}</h3><p class="muted">{E(x)}</p></a>' for f, t, x in [
        ('a-team-scouting.html', 'A. Team scouting', 'Average Solo/Duo, Flex and Ranked 5s rank per team, ranked games in 2026, Flex practice, rank spread, and every roster in detail.'),
        ('b-swiss-evaluation.html', 'B. Swiss Stage evaluation', 'Standings, round by round, results against rank, the most surprising result, ban & pick by position, and which position carries the damage.'),
        ('c-team-evaluation.html', 'C. Team evaluation', 'Game time, total gold, gold per minute, gold difference, KDA and kill participation per game for every team, player leaderboards and full game logs.'),
        ('d-quarterfinalists.html', 'D. Quarterfinalists', 'The 8 quarter-finalists: Swiss path, team profile, a six-stat radar for every player and head-to-head lane matchups for each quarter-final.')]) + '</div>')
    body.append('<h2 id="standings">Final standings</h2>' + table([('finish', '#', 'n'), ('team', 'Team', ''), ('team_name', 'Name', ''), ('record', 'Record', ''), ('buchholz', 'Buchholz', 'n'), ('rank_seed', 'Rank seed', 'n'),
                                                                   ('q', 'Result', '')], [dict(s, q=(pill('Quarter-finals', 'ok') if s['qualified'] else pill('Eliminated'), s['qualified'])) for s in S], hl=lambda r: r['qualified']))
    body.append('<h2 id="teams">Teams and round-1 pairings</h2><div class="card"><ul class="find" style="columns:2;column-gap:32px">' +
                ''.join(f'<li><b>{E(tn(m["blue"]))}</b> ⚔️ <b>{E(tn(m["red"]))}</b> <span class="muted">({E(m["code"])})</span></li>' for m in M if m['round'] == 1) + '</ul></div>')
    body.append('<h2 id="data">Data</h2><p>All tables are in <code>data/processed/</code> as CSV (UTF-8). Raw sources are in <code>data/raw/</code>; scoreboard transcriptions in <code>data/interim/scoreboards/</code>.</p>')
    body.append(table([('f', 'File', ''), ('x', 'Contents', 'wrap')], [dict(f=(f'<a href="../data/processed/{f}">{f}</a>', f), x=x) for f, x in files], sortable=False))
    body.append('<h2 id="method">Method</h2><ul class="find">'
                '<li><b>Results</b> come from the 33 match records (PDF). The Excel schedule is the final authority for teams and sides.</li>'
                '<li><b>Game stats</b> were transcribed from the 28 post-game scoreboards. Each team\'s kills, deaths, assists and gold were checked against the totals in the scoreboard header.</li>'
                '<li><b>Ranks</b> are an op.gg (VN) snapshot from 22 Nov 2026 for season 2026: current tier, LP, and wins + losses per queue. They are not pre-tournament ranks.</li>'
                '<li><b>Team rank</b> = average of the players who actually played, weighted by Swiss games. Ladder: Iron 4 = 0 … Gold 4 = 12 … Diamond 1 = 27, Master = 28 + LP/100.</li>'
                '<li><b>Upset</b> = a played game won by the lineup with the lower average Solo/Duo rank.</li></ul>')
    body.append('<h2 id="gaps">Data gaps and how they were handled</h2>' + table([('area', 'Area', ''), ('matches', 'Matches', 'wrap'), ('issue', 'Issue', 'wrap'), ('handling', 'Handling', 'wrap')], d['issues'], sortable=False))
    return page('index.html', 'SEEE LoL Championship 2026 — Swiss Stage review',
                'Scouting, Swiss Stage evaluation and team evaluation for the 16-team student Swiss Stage (16–22 Nov 2026).', ''.join(body),
                [('standings', 'Standings'), ('teams', 'Teams'), ('data', 'Data files'), ('method', 'Method'), ('gaps', 'Data gaps')])


TEAM_NAME = {}


def tn(code):
    """'Full Name (CODE)'."""
    n = TEAM_NAME.get(code)
    return f'{n} ({code})' if n and n != code else str(code)


def build(out: Path, d):
    TEAM_NAME.update(d.get('team_names', {}))
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in [('index.html', page_index), ('a-team-scouting.html', page_a), ('b-swiss-evaluation.html', page_b), ('c-team-evaluation.html', page_c), ('d-quarterfinalists.html', page_d)]:
        (out / name).write_text(fn(d), encoding='utf-8')
        print(f'  docs/{name}')
    if d.get('_rank_perf_rows'):
        import csv
        rows = d['_rank_perf_rows']
        with open(out.parent / 'data' / 'processed' / 'rank_vs_performance.csv', 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        print(f'  data/processed/rank_vs_performance.csv  {len(rows)} rows')
