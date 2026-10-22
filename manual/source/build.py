"""Build the full ULA Barre manual (US Letter, spiral) as HTML for Chromium PDF output."""
import json, re, html, sys
from PIL import Image

PAGES = json.load(open('pages.json'))
IMGSIZE = json.load(open('imgsize.json'))
BLEED = len(sys.argv) > 1 and sys.argv[1] == 'print'

# ------------------------------------------------------------------ helpers
def esc(s): return html.escape(s, quote=False)

def runs_html(runs):
    out = []
    for r in runs:
        if 't' not in r: continue
        t = esc(r['t']).replace('\n', '<br>')
        if r.get('b') and t.strip(): t = f'<strong>{t}</strong>'
        if r.get('i') and t.strip(): t = f'<em>{t}</em>'
        out.append(t)
    s = ''.join(out)
    s = s.replace('</strong><strong>', '').replace('</em><em>', '')
    return re.sub(r'\s+', ' ', s).strip()

def ptext(b):
    if b['type'] != 'p': return ''
    return re.sub(r'[ \t]+', ' ', ''.join(r.get('t', '') for r in b['runs'])).strip()

def pimgs(b):
    if b['type'] == 'p': return [r['img'] for r in b['runs'] if 'img' in r]
    out = []
    for row in b['rows']:
        for c in row:
            for x in c['content']: out += pimgs(x)
    return out

def allbold(b):
    rs = [r for r in b['runs'] if r.get('t', '').strip()]
    return bool(rs) and all(r.get('b') for r in rs)

def cell_paras(c):
    out = []
    for x in c['content']:
        if x['type'] == 'p': out.append(x)
        else:
            for row in x['rows']:
                for cc in row: out += cell_paras(cc)
    return out

CONNECTORS = [' de ', ' del ', ' en ', ' y ', ' al ', ' con ']
def fix_case(t):
    if t.upper() != t: return t
    s = t.lower()
    s = s[0].upper() + s[1:]
    s = re.sub(r'\bula\b', 'ULA', s)
    s = s.replace('ULA barre', 'ULA Barre')
    return s

def title_html(t):
    t = fix_case(t).replace('\n', ' ')
    best = None
    for c in CONNECTORS:
        k = t.find(c)
        if k > 0 and (best is None or k < best[0]): best = (k, c)
    if best:
        k, c = best
        return f'{esc(t[:k + len(c)])}<em>{esc(t[k + len(c):])}</em>'
    return esc(t)

def strip_bullet(s):
    return re.sub(r'^(?:[•✓]\s*|\d{1,2}\.?\s+)', '', s).strip()

LABELS = {'PUNTOS CLAVE', 'RECUERDA', 'CLAVE ULA', 'VARIACIÓN', 'CÓMO ACTIVAR EL CORE', 'TRABAJO PRINCIPAL',
          'QUÉ OBSERVAR', 'CÓMO CORREGIR', 'PRINCIPIOS CLAVE', 'TIPOS DE FEEDBACK', 'EJEMPLOS DE CUES',
          'CLAVES PARA UNA BUENA TRANSICIÓN', 'SISTEMA DE PROGRESIÓN', 'VARIABLES QUE PUEDES INTRODUCIR',
          'ELEMENTOS A PLANIFICAR', 'CLAVES', 'TU PRESENCIA', 'ESTRUCTURA MUSICAL DE UNA CANCIÓN'}

def is_quote_text(s): return s[:1] in '«“"'
def unquote(s): return s.strip().strip('«»“”"').strip()

# ------------------------------------------------------------------ semantic parse
def parse_page(n, blocks):
    pg = {'n': n, 'blocks': []}
    i = 0
    # chapter
    m = re.match(r'^(\d\d)\s*[/·]\s*(.+)$', ptext(blocks[0]))
    pg['chap'] = m.group(1); pg['chapname'] = fix_case(m.group(2).strip()); i = 1
    pg['title'] = ptext(blocks[1]) if blocks[1]['type'] == 'p' else ''
    # keep ULATtulo line breaks out
    pg['title'] = re.sub(r'\s+', ' ', ''.join(r.get('t', '') for r in blocks[1]['runs'])).strip()
    i = 2
    if i < len(blocks) and blocks[i]['type'] == 'p' and blocks[i]['style'] == 'ULACaptulo':
        pg['kicker'] = ptext(blocks[i]); i += 1
    rest = blocks[i:]
    B = pg['blocks']
    j = 0
    while j < len(rest):
        b = rest[j]
        if b['type'] == 'tbl':
            B.append(('tbl', b)); j += 1; continue
        t = ptext(b)
        if not t and pimgs(b):
            B.append(('figs', [{'img': x} for x in pimgs(b)])); j += 1; continue
        if not t: j += 1; continue
        up = t.upper() == t
        if up and t.rstrip(':') in LABELS:
            label = t.rstrip(':'); j += 1
            items = []
            while j < len(rest) and rest[j]['type'] == 'p':
                tt = ptext(rest[j]); st = rest[j]['style']
                if st == 'Listaconvietas' or re.match(r'^([•✓]|\d{1,2}\.?\s)', tt):
                    items.append(runs_html(rest[j]['runs'])); j += 1
                else: break
            if items:
                B.append(('list', label, [re.sub(r'^(?:<strong>)?\s*(?:[•✓]|\d{1,2}\.?)\s*(?:</strong>)?\s*', '', x) for x in items],
                          'num' if re.match(r'^\d', ptext(rest[j - 1])) else 'bul'))
            elif j < len(rest) and rest[j]['type'] == 'p' and ptext(rest[j]):
                nb = rest[j]
                kind = 'callout' if nb['style'] == 'ULADestacado' else 'note'
                B.append((kind, label, runs_html(nb['runs']))); j += 1
                # trailing plain line (p.14 "La modelo es la referencia visual.")
                if kind == 'callout' and j < len(rest) and rest[j]['type'] == 'p' and rest[j]['style'] is None and not rest[j]['num'] and ptext(rest[j]) and not ptext(rest[j]).isupper():
                    B[-1] = ('callout', label, B[-1][2], runs_html(rest[j]['runs'])); j += 1
            else:
                B.append(('label', label))
            continue
        if b['style'] == 'ULADestacado':
            B.append(('highlight', runs_html(b['runs']))); j += 1; continue
        if b['style'] == 'Listaconvietas' or re.match(r'^([•✓]|\d{1,2}\.?\s)', t):
            items = []
            numeric = bool(re.match(r'^\d', t))
            while j < len(rest) and rest[j]['type'] == 'p' and (rest[j]['style'] == 'Listaconvietas' or re.match(r'^([•✓]|\d{1,2}\.?\s)', ptext(rest[j]))):
                items.append(re.sub(r'^(?:[•✓]|\d{1,2}\.?)\s*', '', runs_html(rest[j]['runs']))); j += 1
            B.append(('list', None, items, 'num' if numeric else ('check' if t.startswith('✓') else 'bul'))); continue
        if is_quote_text(t):
            B.append(('quote', unquote(t))); j += 1; continue
        B.append(('p', runs_html(b['runs']), allbold(b), t)); j += 1
    return pg

SEM = [parse_page(k + 1, p) for k, p in enumerate(PAGES)]

# ------------------------------------------------------------------ renderers
def img_ar(name):
    w, h = IMGSIZE[name]; return w / h

def figure_row(items, arrow=False, frame=None):
    n = len(items)
    cls = f'figrow n{n}'
    out = [f'<div class="{cls}">']
    for k, it in enumerate(items):
        ar = img_ar(it['img'])
        fr = frame or ('arch' if ar < 1.02 and n <= 4 else 'rect')
        cap = ''
        if it.get('label') or it.get('desc'):
            num = f'<span class="i">{k + 1:02d}</span>' if n > 1 else ''
            lab = f'<span class="t">{esc(it.get("label", ""))}</span>' if it.get('label') else ''
            desc = f'<span class="d">{it["desc"]}</span>' if it.get('desc') else ''
            cap = f'<figcaption class="cap">{num}<span class="tx">{lab}{desc}</span></figcaption>'
        out.append(f'<figure class="fig"><div class="frame {fr}" data-ar="{ar:.4f}"><img src="img/{it["img"]}" alt=""></div>{cap}</figure>')
        if arrow and k == 0 and n == 2:
            out.append('<div class="arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M4 12h15M14 7l5 5-5 5"/></svg></div>')
    out.append('</div>')
    return ''.join(out)

def caption_from_cell(c):
    ps = [p for p in cell_paras(c) if ptext(p)]
    if not ps: return {}
    lab = ptext(ps[0])
    lab = re.sub(r'^\d\.\s*', '', lab)
    d = ' '.join(runs_html(p['runs']) for p in ps[1:])
    return {'label': lab.upper() if len(lab) < 40 else lab, 'desc': d}

def table_figs(t):
    rows = t['rows']
    if all(pimgs({'type': 'tbl', 'rows': [[c]]}) for c in rows[0]):
        items = []
        for k, c in enumerate(rows[0]):
            it = {'img': pimgs({'type': 'tbl', 'rows': [[c]]})[0]}
            if len(rows) > 1 and k < len(rows[1]): it.update(caption_from_cell(rows[1][k]))
            items.append(it)
        return items
    return None

def list_html(label, items, kind, cols=None):
    cls = 'pts'
    n = len(items)
    if cols is None: cols = 2 if n >= 4 and max(len(re.sub('<.*?>', '', x)) for x in items) < 70 else 1
    lis = []
    for k, x in enumerate(items):
        mark = f'<span class="n">{k + 1:02d}</span>' if kind in ('num', 'bul') else '<span class="ck"><svg viewBox="0 0 16 16"><path d="M3 8.5l3 3 7-7" fill="none" stroke="currentColor" stroke-width="1.3"/></svg></span>'
        lis.append(f'<li>{mark}<span>{x}</span></li>')
    head = f'<div class="head"><span class="k">{esc(fix_case(label) if label else "")}</span></div>' if label else ''
    return f'<div class="{cls} c{cols}">{head}<ol>{"".join(lis)}</ol></div>'

def callout_html(label, text, extra=None):
    ex = f'<div class="ex">{extra}</div>' if extra else ''
    return f'<div class="key"><span class="q">&ldquo;</span><div class="k">{esc(fix_case(label))}</div><p>{text}</p>{ex}</div>'

def remember_eq(text, extra):
    # "Pierna base = estabilidad. Pierna de ejecución = movimiento."
    parts = [p.strip(' .') for p in re.sub('<.*?>', '', text).split('.') if '=' in p]
    eqs = ''.join(f'<div class="eq"><div class="a">{esc(a.strip())}</div><div class="b">= {esc(b.strip())}</div></div>' for a, b in (p.split('=') for p in parts))
    return f'<div class="remember"><div class="k">Recuerda</div>{eqs}<div class="note">{extra}</div></div>'

def highlight_html(text):
    return f'<div class="hl"><span class="bar"></span><p>{text}</p></div>'

def quote_html(text):
    return f'<div class="closing"><span class="orn">&#10022;</span><p>{esc(text)}</p></div>'

# ------------------------------------------------------------------ page content per type
def render_generic(pg):
    """Pages 1-74: text pages and exercise pages."""
    top, figs, lists, bottom, defs = [], [], [], [], []
    n = pg['n']
    blocks = pg['blocks']
    paras = [b for b in blocks if b[0] == 'p']
    # definition pages (6-9): term line followed by description
    if n in (6, 7, 8, 9):
        top.append(f'<p class="lead">{paras[0][1]}</p>')
        terms = paras[1:]
        items = [(re.sub('<.*?>', '', terms[k][1]), terms[k + 1][1]) for k in range(0, len(terms) - 1, 2)]
        cards = ''.join(f'<div class="feat"><span class="n">{k + 1:02d}</span><h3>{esc(a)}</h3><p>{b}</p></div>' for k, (a, b) in enumerate(items))
        defs.append(f'<div class="feats">{cards}</div>')
        hl = [b for b in blocks if b[0] == 'highlight']
        bottom.append(callout_html('La idea clave', hl[0][1]))
        return top, defs, [], bottom, 'text'
    if n == 5:
        top.append(f'<p class="lead">{paras[0][1]}</p>')
        lst = [b for b in blocks if b[0] == 'list'][0]
        pill = ''.join(f'<div class="pillar"><span class="n">{k + 1:02d}</span><span class="t">{esc(re.sub("<.*?>", "", x).rstrip("."))}</span></div>' for k, x in enumerate(lst[2]))
        mid = [f'<p class="body">{p[1]}</p>' for p in paras[2:]]
        hl = [b for b in blocks if b[0] == 'highlight']
        return top, [f'<div class="k-label">{esc(re.sub("<.*?>", "", paras[1][1]))}</div><div class="pillars">{pill}</div>' + ''.join(mid)], [], [callout_html('La idea clave', hl[0][1])], 'text'
    if n == 11:
        t = [b for b in blocks if b[0] == 'tbl'][0][1]
        top.append(f'<p class="lead">{paras[0][1]}</p>')
        rows = []
        for k, row in enumerate(t['rows']):
            img = pimgs({'type': 'tbl', 'rows': [[row[0]]]})[0]
            cap = caption_from_cell(row[1])
            rows.append(f'<div class="foot"><div class="fimg"><img src="img/{img}" alt=""></div><span class="n">{k + 1:02d}</span><div><div class="t">{esc(cap["label"])}</div><div class="d">{cap["desc"]}</div></div></div>')
        return top, [f'<div class="feet">{"".join(rows)}</div>'], [], [], 'text'

    extra = EXTRA_IMG.get(n)
    first = True
    for b in blocks:
        k = b[0]
        if k == 'p':
            if b[2]:  # bold-only stray label
                lists.append(f'<div class="k-label">{esc(fix_case(b[3]))}</div>'); continue
            plain = b[3]
            if first and len(plain) < 330:
                top.append(f'<p class="lead">{b[1]}</p>')
            else:
                top.append(f'<p class="body">{b[1]}</p>')
            first = False
        elif k == 'figs':
            figs.append(b[1])
        elif k == 'tbl':
            items = table_figs(b[1])
            if items: figs.append(items)
        elif k == 'list':
            lists.append(list_html(b[1], b[2], b[3]))
        elif k == 'label':
            # p24 style: ULADestacado "PUNTOS CLAVE" handled as highlight; plain label alone
            pass
        elif k == 'highlight':
            if b[1].upper() == b[1] and re.sub('<.*?>', '', b[1]).strip() in LABELS:
                lists.append(('pending-label', re.sub('<.*?>', '', b[1]).strip()))
            else:
                bottom.append(('hl', b[1]))
        elif k == 'callout':
            if b[1] == 'RECUERDA' and '=' in b[2] and len(b) > 3:
                bottom.append(remember_eq(b[2], b[3]))
            else:
                bottom.append(callout_html(b[1], b[2], b[3] if len(b) > 3 else None))
        elif k == 'note':
            bottom.append(f'<div class="note"><div class="k">{esc(fix_case(b[1]))}</div><p>{b[2]}</p></div>')
        elif k == 'quote':
            bottom.append(quote_html(b[1]))
    # fix lists that had a highlighted label before them (p.24)
    fixed = []
    pend = None
    for x in lists:
        if isinstance(x, tuple): pend = x[1]; continue
        if pend and x.startswith('<div class="pts'):
            x = x.replace('<ol>', f'<div class="head"><span class="k">{esc(fix_case(pend))}</span></div><ol>', 1); pend = None
        fixed.append(x)
    lists = fixed
    # highlight: text pages put it in a callout at bottom; image pages a soft quote
    out_bottom = []
    for x in bottom:
        if isinstance(x, tuple):
            out_bottom.append(callout_html('La idea clave', x[1]) if (not figs or extra) else highlight_html(x[1]))
        else: out_bottom.append(x)
    if extra and not figs: figs = [[{'img': extra}]]
    fig_html = []
    for items in figs:
        labels = ' '.join(i.get('label', '') for i in items).upper()
        arrow = len(items) == 2 and ('INICIAL' in labels or 'INICIO' in labels)
        fig_html.append(figure_row(items, arrow=arrow))
    # p10: highlight sits above image
    return top, fig_html, lists, out_bottom, ('ex' if figs else 'text')

def cells_text(row): return [' '.join(runs_html(p['runs']) for p in cell_paras(c) if ptext(p)) for c in row]

def render_late(pg):
    """Pages 75-96: music & methodology, mostly tables."""
    n = pg['n']; blocks = pg['blocks']
    raw = [b for b in PAGES[n - 1][2:] if b['type'] == 'p' and ptext(b) and not is_quote_text(ptext(b))]
    paras = [{'t': ptext(b), 'h': runs_html(b['runs'])} for b in raw]
    tbls = [b[1] for b in blocks if b[0] == 'tbl']
    quotes = [b[1] for b in blocks if b[0] == 'quote']
    top = [f'<p class="lead">{paras[0]["h"]}</p>'] if paras else []
    mid, bot = [], []
    # quotes inside single-cell tables
    for t in list(tbls):
        if len(t['rows']) == 1 and len(t['rows'][0]) == 1:
            tx = ' '.join(ptext(p) for p in cell_paras(t['rows'][0][0]))
            if is_quote_text(tx): quotes.append(unquote(tx)); tbls.remove(t)

    def labelled(lbl):
        return f'<div class="k-label">{esc(fix_case(lbl))}</div>'

    if n in (75,):
        items = []
        for t in tbls:
            c = cell_paras(t['rows'][0][1]); items.append((ptext(c[0]), runs_html(c[1]['runs'])))
        mid.append('<div class="steps">' + ''.join(f'<div class="step"><span class="n">{k + 1:02d}</span><div><h3>{esc(fix_case(a))}</h3><p>{b}</p></div></div>' for k, (a, b) in enumerate(items)) + '</div>')
    elif n == 76:
        items = [cells_text(t['rows'][0])[1] for t in tbls]
        mid.append(list_html(None, items, 'num', cols=1).replace('class="pts', 'class="pts big'))
    elif n == 77:
        cards = []
        for row in tbls[0]['rows']:
            for c in row:
                ps = [p for p in cell_paras(c) if ptext(p)]
                cards.append((ptext(ps[0]), runs_html(ps[1]['runs'])))
        mid.append('<div class="cards c3">' + ''.join(f'<div class="card"><h3>{esc(a)}</h3><p>{b}</p></div>' for a, b in cards) + '</div>')
    elif n == 78:
        beats8 = ''.join(f'<span class="beat{" acc" if i in (1, 5) else ""}">{i}</span>' for i in range(1, 9))
        beats16 = ''.join(f'<span class="beat{" acc" if i in (1, 9) else ""}">{i}</span>' for i in range(1, 17))
        defs = [(paras[k]['t'], paras[k + 1]['h']) for k in (1, 3)]
        mid.append(f'''<div class="count">
          <div class="cblock"><div class="beats b8">{beats8}</div><div class="cl">Bloque de 8 tiempos</div><p>{defs[0][1]}</p></div>
          <div class="cblock"><div class="beats b16">{beats16}</div><div class="cl">Bloque de 16 tiempos</div><p>{defs[1][1]}</p></div>
        </div>''')
        song = tbls[-1]['rows']
        names = [ptext(cell_paras(c)[0]) for c in song[0]]
        times = [ptext(cell_paras(c)[0]).replace('\n', ' ') for c in song[1]]
        weights = [12, 32, 32, 32, 32, 24, 12]
        segs = ''.join(f'<div class="seg{" chorus" if nm == "Estribillo" else ""}" style="flex:{w}"><div class="sn">{esc(nm)}</div><div class="st">{esc(tm)}</div></div>' for nm, tm, w in zip(names, times, weights))
        mid.append(f'{labelled("Estructura musical de una canción")}<div class="song">{segs}</div><p class="body">{paras[-1]['h']}</p>')
    elif n == 79:
        items = [(re.sub(r'^\d\s+', '', paras[k]['t']), paras[k + 1]['h']) for k in range(1, len(paras) - 1, 2)]
        mid.append('<div class="steps">' + ''.join(f'<div class="step"><span class="n">{k + 1:02d}</span><div><h3>{esc(fix_case(a))}</h3><p>{b}</p></div></div>' for k, (a, b) in enumerate(items)) + '</div>')
    elif n in (80, 93):
        rows = tbls[0]['rows']
        head = cells_text(rows[0])
        body = [cells_text(r) for r in rows[1:]]
        th = ''.join(f'<th>{re.sub("<.*?>", "", h)}</th>' for h in head)
        tr = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in body)
        mid.append(f'<table class="dt t{len(head)}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>')
    elif n == 81:
        rows = [cells_text(r) for r in tbls[0]['rows']]
        mx = 18
        def mins(s):
            v = [int(x) for x in re.findall(r'\d+', re.sub('<.*?>', '', s))]; return sum(v) / len(v)
        tl = ''.join(f'<div class="tl"><span class="n">{re.sub("<.*?>", "", a)}</span><span class="nm">{re.sub("<.*?>", "", b)}</span><span class="bar"><i style="width:{mins(c) / mx * 100:.0f}%"></i></span><span class="tm">{re.sub("<.*?>", "", c)}</span></div>' for a, b, c in rows)
        mid.append(f'<div class="timeline">{tl}</div>')
        bot.append(f'<div class="note"><div class="k">Trabajo principal</div><p>{paras[-1]['h']}</p></div>')
    elif n in (82, 87):
        if n == 82:
            lst = [b for b in blocks if b[0] == 'list'][0]; items = lst[2]
        else:
            items = [re.sub(r'^✓\s*', '', cells_text(r)[0]) for r in tbls[0]['rows']]
            mid.append(labelled('Claves para una buena transición'))
        mid.append(list_html(None, items, 'check', cols=1).replace('class="pts', 'class="pts big'))
    elif n in (83, 89, 90, 91):
        lbl = [b for b in blocks if b[0] in ('label', 'list')][0]
        if n == 83:
            mid.append(list_html(lbl[1], lbl[2], 'num', cols=1).replace('class="pts', 'class="pts big'))
        else:
            label = [ptext(p) for p in PAGES[n - 1] if p['type'] == 'p' and ptext(p) in LABELS][0]
            items = [re.sub(r'^\d+\s*', '', cells_text(r)[0]) for r in tbls[0]['rows']]
            mid.append(list_html(label, items, 'num', cols=1).replace('class="pts', 'class="pts big'))
    elif n == 84:
        ls = [b for b in blocks if b[0] == 'list']
        mid.append('<div class="two">' + ''.join(list_html(l[1], l[2], 'bul', cols=1) for l in ls) + '</div>')
    elif n == 85:
        ls = [b for b in blocks if b[0] == 'list']
        types = []
        for x in ls[0][2]:
            s = re.sub('<.*?>', '', x)
            a, b = [y.strip() for y in s.split('—')]
            types.append((a, b))
        cards = ''.join(f'<div class="feat"><span class="n">{k + 1:02d}</span><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for k, (a, b) in enumerate(types))
        mid.append(f'{labelled("Tipos de feedback")}<div class="feats">{cards}</div>')
        cues = ''.join(f'<span class="cue">{esc(re.sub("<.*?>", "", x))}</span>' for x in ls[1][2])
        mid.append(f'{labelled("Ejemplos de cues")}<div class="cues">{cues}</div>')
    elif n == 86:
        rows = tbls[0]['rows']
        levels = []
        for r in rows[1:4]:
            s = ptext(cell_paras(r[0])[0]).split('\n')
            levels.append((s[0], s[1] if len(s) > 1 else ''))
        adapt = [strip_bullet(ptext(cell_paras(r[1])[0])) for r in rows[1:] if cell_paras(r[1]) and ptext(cell_paras(r[1])[0])]
        lv = ''.join(f'<div class="level"><span class="n">{k + 1}</span><div><h3>{esc(fix_case(a.split("·")[-1].strip()))}</h3><p>{esc(b)}</p></div></div>' for k, (a, b) in enumerate(levels))
        mid.append(f'<div class="two"><div>{labelled("Niveles")}<div class="levels">{lv}</div></div><div>{list_html("Formas de adaptar", adapt, "check", cols=1)}</div></div>')
    elif n == 88:
        steps = []
        for r in tbls[0]['rows']:
            s = ptext(cell_paras(r[0])[0]).split('\n')
            steps.append((s[0].split('·')[-1].strip(), s[1]))
        mid.append(labelled('Sistema de progresión') + '<div class="prog">' + ''.join(f'<div class="pstep"><span class="n">{k + 1}</span><h3>{esc(a)}</h3><p>{esc(b)}</p></div>' for k, (a, b) in enumerate(steps)) + '</div>')
        ls = [b for b in blocks if b[0] == 'list']
        mid.append(list_html(ls[0][1], ls[0][2], 'bul'))
    elif n == 92:
        cols = []
        for c in tbls[0]['rows'][0]:
            ps = [p for p in cell_paras(c) if ptext(p)]
            cols.append((ptext(ps[0]), [strip_bullet(ptext(p)) for p in ps[1:]]))
        mid.append('<div class="cols3">' + ''.join(f'<div class="ccol"><span class="n">{k + 1:02d}</span><h3>{esc(fix_case(a))}</h3><ul>{"".join(f"<li>{esc(x)}</li>" for x in it)}</ul></div>' for k, (a, it) in enumerate(cols)) + '</div>')
    elif n == 94:
        cols = []
        for t in tbls:
            ps = [p for p in cell_paras(t['rows'][0][0]) if ptext(p)]
            cols.append((ptext(ps[0]), [ptext(p) for p in ps[1:]]))
        mid.append('<div class="stairs">' + ''.join(f'<div class="ccol lv{k + 1}"><span class="n">{k + 1:02d}</span><h3>{esc(fix_case(a))}</h3><ul>{"".join(f"<li>{esc(x)}</li>" for x in it)}</ul></div>' for k, (a, it) in enumerate(cols)) + '</div>')
    elif n in (95, 96):
        cards = []
        for t in tbls:
            ps = [p for p in cell_paras(t['rows'][0][0]) if ptext(p)]
            cards.append((ptext(ps[0]), runs_html(ps[1]['runs'])))
        if n == 96:
            top = [f'<p class="sub">{esc(paras[0]["t"])}</p>', f'<p class="lead">{paras[1]["h"]}</p>']
        mid.append('<div class="cards c2 big">' + ''.join(f'<div class="card"><span class="n">{k + 1:02d}</span><h3>{esc(fix_case(a))}</h3><p>{b}</p></div>' for k, (a, b) in enumerate(cards)) + '</div>')
    if n == 83:
        pass
    # trailing plain quote paragraph (92, 93, 94 …) are parsed as 'quote' already
    for q in quotes: bot.append(quote_html(q))
    return top, mid, [], bot, 'late'

# ------------------------------------------------------------------ chapter / TOC data
chapters = []
for pg in SEM:
    if not chapters or chapters[-1]['num'] != pg['chap']:
        chapters.append({'num': pg['chap'], 'name': pg['chapname'], 'pages': []})
    chapters[-1]['pages'].append(pg)

EXTRA_IMG = {1: 'image36.jpg', 2: 'image20.jpg', 3: 'image126.jpg', 4: 'image24.jpg', 12: 'image99.jpg'}
OPENER_IMG = {'01': 'image138.jpg', '02': 'image42.jpg', '03': 'image12.jpg', '04': 'image32.jpg', '05': 'image33.jpg',
              '06': 'image91.jpg', '07': 'image115.jpg', '08': 'image123.jpg', '09': 'image139.jpg', '10': 'image122.jpg',
              '11': 'image46.jpg'}

# physical page numbering: 1 cover, 2 inside cover, 3-4 TOC, then per chapter opener + pages
phys = 5
for ch in chapters:
    ch['phys'] = phys; phys += 1
    for k, pg in enumerate(ch['pages']):
        pg['phys'] = phys; pg['sec'] = f"{ch['num']}.{k + 1}"; phys += 1
TOTAL = phys + 1  # inside back + back cover

# ------------------------------------------------------------------ page shells
def side(phys): return 'recto' if phys % 2 == 1 else 'verso'

def shell(phys, inner, cls='', chapnum=None, chapname=None, folio=True):
    s = side(phys)
    rh = ''
    if chapname:
        rh = f'<div class="runhead"><span class="ch"><b>{chapnum}</b>{esc(chapname)}</span><span class="brand">Método ULA Barre</span></div>'
    fo = f'<div class="folio"><span class="lbl">ULA Studio · Manual de formación</span><span class="dash"></span><span class="num">{phys}</span></div>' if folio else ''
    tab = ''
    if chapnum:
        idx = int(chapnum) - 1
        tab = f'<div class="tab" style="--i:{idx}"><span>{chapnum}</span></div>'
    return f'<section class="page {s} {cls}" data-p="{phys}">{tab}<div class="trim">{rh}{inner}{fo}</div></section>'

def content_page(pg):
    if pg['n'] >= 75: top, mid, lists, bottom, kind = render_late(pg)
    else: top, mid, lists, bottom, kind = render_generic(pg)
    kick = f'<div class="kicker">{esc(fix_case(pg["kicker"]))}</div>' if pg.get('kicker') else ''
    head = f'''<header class="ph">
      <div class="eyebrow"><span class="n">{pg["sec"]}</span><span class="rule"></span><span>{esc(pg["chapname"])}</span></div>
      <h1>{title_html(pg["title"])}</h1>{kick}</header>'''
    # p.10: highlight goes right under the intro
    if pg['n'] == 10:
        hl = [b for b in bottom if 'class="hl"' in b]
        bottom = [b for b in bottom if b not in hl]
        top += hl
    figzone = f'<div class="figzone">{"".join(mid)}</div>' if kind == 'ex' else f'<div class="midzone">{"".join(mid)}</div>'
    inner = f'''<div class="content {kind}">{head}<div class="intro">{"".join(top)}</div>{figzone}
      <div class="after">{"".join(lists)}{"".join(bottom)}</div></div>'''
    return shell(pg['phys'], inner, f'p{pg["n"]}', pg['chap'], pg['chapname'])

def opener(ch):
    secs = ''.join(f'<li><span class="sn">{p["sec"]}</span><span class="st">{esc(fix_case(p["title"]))}</span><span class="sp">{p["phys"]}</span></li>' for p in ch['pages'])
    cols = 2 if len(ch['pages']) > 8 else 1
    inner = f'''<div class="opener-in">
      <div class="o-top"><img class="o-logo" src="img/logo_cream.png" alt=""><span class="o-cap">Capítulo</span></div>
      <div class="o-num">{ch["num"]}</div>
      <h2 class="o-title">{title_html(ch["name"])}</h2>
      <div class="o-rule"></div>
      <ol class="o-secs c{cols}">{secs}</ol>
      <div class="o-photo"><div class="frame arch"><img src="img/{OPENER_IMG[ch["num"]]}" alt=""></div></div>
    </div>'''
    return shell(ch['phys'], inner, 'opener dark', ch['num'], None, folio=False)

def toc_pages():
    entries = []
    for ch in chapters:
        entries.append(f'<li class="tch"><span class="cn">{ch["num"]}</span><span class="ct">{esc(ch["name"])}</span><span class="cp">{ch["phys"]}</span></li>')
        for p in ch['pages']:
            entries.append(f'<li class="tsec"><span class="sn">{p["sec"]}</span><span class="st">{esc(fix_case(p["title"]))}</span><span class="dots"></span><span class="sp">{p["phys"]}</span></li>')
    # split roughly in half at a chapter boundary
    idx = [k for k, e in enumerate(entries) if 'class="tch"' in e]
    half = min(idx, key=lambda k: abs(k - len(entries) / 2))
    a, b = entries[:half], entries[half:]
    p1 = shell(3, f'''<div class="toc"><div class="eyebrow"><span class="rule"></span><span>Contenido</span></div><h1>Índice</h1>
        <ol class="tocl">{"".join(a)}</ol></div>''', 'tocpage')
    p2 = shell(4, f'<div class="toc cont"><ol class="tocl">{"".join(b)}</ol></div>', 'tocpage')
    return p1 + p2

def cover():
    inner = '''<div class="cover-in">
      <img class="c-logo" src="img/logo_cream.png" alt="ULA Studio Pilates &amp; Barre">
      <div class="c-photo"><div class="frame arch"><img src="img/image33.jpg" alt=""></div></div>
      <div class="c-text"><div class="c-kick">Manual de formación oficial</div>
      <h1 class="c-title">Método <em>ULA Barre</em></h1>
      <div class="c-sub">Técnica · Fuerza · Control · Música</div></div>
    </div>'''
    return f'<section class="page recto cover dark" data-p="1"><div class="trim">{inner}</div></section>'

def inside_cover():
    inner = '''<div class="ic">
      <img class="ic-logo" src="img/logo_choc.png" alt="">
      <div class="ic-t">Manual de formación<br><em>Método ULA Barre</em></div>
      <p class="ic-p">ULA Barre nace dentro de ULA Studio Pilates con una idea clara: crear una forma de entrenar que combine movimiento, control, fuerza y música en una experiencia dinámica y cuidada.</p>
      <div class="ic-foot">© ULA Studio · Pilates &amp; Barre<br>Documento de uso interno para la formación de instructoras e instructores.</div>
    </div>'''
    return f'<section class="page verso plain" data-p="2"><div class="trim">{inner}</div></section>'

def back_inside():
    inner = '''<div class="ic notes"><div class="eyebrow"><span class="rule"></span><span>Notas</span></div>
      <h1>Mis <em>notas</em></h1><div class="lines">''' + '<span></span>' * 22 + '</div></div>'
    return shell(TOTAL - 1, inner, 'plain')

def back_cover():
    inner = '''<div class="back-in">
      <p class="b-q">«La disciplina de hoy,<br><em>el bienestar de mañana.</em>»</p>
      <div class="b-rule"></div>
      <p class="b-p">ULA Barre une técnica, fuerza, control, música y una experiencia de movimiento coherente. La estructura es la base; la personalidad de quien imparte la clase hace que cada sesión sea única.</p>
      <img class="b-logo" src="img/logo_cream.png" alt="">
    </div>'''
    return f'<section class="page {side(TOTAL)} back dark" data-p="{TOTAL}"><div class="trim">{inner}</div></section>'

body = [cover(), inside_cover(), toc_pages()]
for ch in chapters:
    body.append(opener(ch))
    for pg in ch['pages']: body.append(content_page(pg))
body += [back_inside(), back_cover()]

css = open('style.css').read()
js = open('fit.js').read()
doc = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Método ULA Barre — Manual de formación</title>
<link rel="stylesheet" href="fonts.css"><style>{css}{'@page{ size:222.25mm 285.75mm; margin:0; }' if BLEED else ''}</style></head>
<body class="{'bleed' if BLEED else 'trimmed'}">{''.join(body)}<script>{js}</script></body></html>'''
open('out/manual_print.html' if BLEED else 'out/manual.html', 'w').write(doc)
print('pages', TOTAL)
