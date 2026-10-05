# -*- coding: utf-8 -*-
"""按教案的「复习环节」重建 PPT 复习页（**问答成对**版）：
   每一组：问 → 答（答案精简到一行）→ 间隔行；组与组之间留白。
   内容多时自动续页，保持成对顺序。
"""
import io, os, re, glob, math

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.environ.get('COURSE_PROJ') or HERE
Q_LIMIT = 60          # 问题上限（约 1 行）
A_LIMIT = 200         # 答案上限：保留完整（≈44 字/行，最多 4 行）
CAP = 16              # 每页可用行数（含间隔行）
TRIMS = []            # 记录被精简过的答案，供人工复核


def review_section(t):
    m = re.search(r'(?m)^##\s*复习环节\s*$', t)
    if not m:
        return None
    rest = t[m.end():]
    n = re.search(r'(?m)^##\s', rest)
    return rest[:n.start()] if n else rest


def clean(txt):
    txt = txt.replace('**', '').replace('`', '')
    txt = re.sub(r'^\s*[*\-]\s+', '', txt)
    return re.sub(r'\s+', ' ', txt).strip()


OPEN = '（(【“"'
CLOSE = '）)】”"'


def _depths(s):
    dep = [0] * (len(s) + 1)
    d = 0
    for i, ch in enumerate(s):
        if ch in OPEN:
            d += 1
        elif ch in CLOSE:
            d = max(0, d - 1)
        dep[i + 1] = d
    return dep


def shorten(txt, limit):
    """精简到一行：整句 > 子句（不会切开括号）> 括号外硬截。"""
    txt = clean(txt)
    if len(txt) <= limit:
        return txt
    dep = _depths(txt)
    ends = [i + 1 for i, ch in enumerate(txt) if ch in '。！？' and dep[i + 1] == 0 and i + 1 <= limit]
    if ends:
        return txt[:max(ends)]
    cl = [i + 1 for i, ch in enumerate(txt) if ch in '；;，,、' and dep[i + 1] == 0 and i + 1 <= limit]
    br = [i + 1 for i, ch in enumerate(txt) if ch in '）)' and dep[i + 1] == 0 and i + 1 <= limit + 6]
    cands = cl + br
    if cands:
        return _tidy(txt[:max(cands)])
    ok = [p for p in range(1, limit + 1) if dep[p] == 0]
    p = max(ok) if ok else limit
    return _tidy(txt[:p])


def _tidy(out):
    """收尾：去掉未闭合括号/悬空函数名，补句号。"""
    out = re.sub(r'[（(][^）)]*$', '', out)
    out = re.sub(r'[A-Za-z_][A-Za-z0-9_.]*\(\s*\)$', '', out)
    out = out.rstrip('，,、；;：:— -')
    if not out.endswith(('。', '！', '？', '…')):
        out += '。'
    return out


def parse_qa(sec):
    if not sec:
        return []
    m = re.search(r'(?m)^###\s*知识点\s*$', sec)
    body = sec[m.end():] if m else sec
    n = re.search(r'(?m)^###\s', body)
    if n:
        body = body[:n.start()]
    items, cur = [], None
    for l in body.split('\n'):
        s = l.rstrip()
        if re.match(r'^\s*[*\-]\s+\*\*', s):
            if cur:
                items.append(cur)
            cur = [clean(re.sub(r'^\s*[*\-]\s+', '', s)), []]
        elif cur is not None and s.strip():
            cur[1].append(clean(s))
    if cur:
        items.append(cur)
    out = []
    for q, a in items:
        ans = ' '.join(x for x in a if x).strip()
        q2, a2 = shorten(q, Q_LIMIT), shorten(ans, A_LIMIT)
        if a2 != clean(ans):
            TRIMS.append((q2, ans, a2))
        out.append((q2, a2))
    return out


def chunk_pairs(qas):
    pages, cur, n = [], [], 0
    for q, a in qas:
        c = max(1, math.ceil(len(q) / 44.0)) + max(1, math.ceil(len(a) / 44.0)) + 1  # +1 为间隔行
        if cur and n + c > CAP:
            pages.append(cur); cur, n = [], 0
        cur.append((q, a)); n += c
    if cur:
        pages.append(cur)
    return pages


def build_pages(base_title, qas):
    chunks = chunk_pairs(qas)
    out = []
    for i, ch in enumerate(chunks):
        ttl = base_title + ('' if len(chunks) == 1 else '（%d/%d）' % (i + 1, len(chunks)))
        body = []
        for q, a in ch:
            body.append('- 问：%s' % q)
            body.append('- 答：%s' % a)
            body.append('<<gap>>')
        out.append((ttl, '\n'.join(body).rstrip('\n')))
    return out


def lesson_files(course, num):
    ppt = [x for x in glob.glob(os.path.join(PROJ, course, 'PPTs', course + '_' + num + '*')) if x.endswith('.md')]
    lp = glob.glob(os.path.join(PROJ, course, 'lesson_plans', course + '_' + num + '*'))
    return (ppt[0] if ppt else None), (lp[0] if lp else None)


def rebuild(course, num):
    ppt, lp = lesson_files(course, num)
    if not ppt or not lp:
        return 0
    qas = parse_qa(review_section(io.open(lp, encoding='utf-8').read()))
    if not qas:
        return 0
    t = io.open(ppt, encoding='utf-8').read()
    parts = re.split(r'(?m)^### (?=第\s*\d+\s*页)', t)
    head, body = parts[0], parts[1:]
    idx, base = None, '复习：上节要点回顾'
    for i, pg in enumerate(body):
        ti = pg.split('\n', 1)[0]
        if '复习' in ti:
            idx = i
            m = re.match(r'^第\s*\d+\s*页\s*·\s*(.*)$', ti.strip())
            base = re.sub(r'（(问题|答案)[^）]*）$', '', m.group(1).strip() if m else ti)
            base = re.sub(r'（\d+/\d+）$', '', base)
            break
    if idx is None:
        return 0
    body = [pg for pg in body if '复习' not in pg.split('\n', 1)[0]]
    new = ['第 _ 页 · %s\n%s' % (ttl, bd) for ttl, bd in build_pages(base, qas)]
    for k, nb in enumerate(new):
        body.insert(idx + k, nb)
    out = [head.rstrip('\n')]
    for i, pg in enumerate(body, 1):
        first, _, rest = pg.partition('\n')
        first = re.sub(r'^第\s*[_\d]+\s*页', '第 %d 页' % i, first.strip())
        out.append('### ' + first)
        if rest.strip():
            out.append(rest.strip('\n'))
    io.open(ppt, 'w', encoding='utf-8').write('\n\n'.join(out).rstrip('\n') + '\n')
    return len(new), len(qas)


if __name__ == '__main__':
    for course in ['MP2', 'MP3']:
        for num in ['%02d' % i for i in range(1, 13)]:
            r = rebuild(course, num)
            if r:
                print('%s-%s  复习 %d 问 -> %d 页' % (course, num, r[1], r[0]))
            else:
                print('%s-%s  跳过（教案无复习环节）' % (course, num))
    print('')
    print('被精简的答案: %d 条' % len(TRIMS))
    for q, a, b in TRIMS:
        print('  [%s]' % q[:26])
        print('     原: %s' % a)
        print('     现: %s' % b)
