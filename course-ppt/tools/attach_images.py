# -*- coding: utf-8 -*-
"""把 images/ 里生成好的图片，按"图片需求 MD"的出处，绑定到 PPT 源：
   - 出处=PPT 第 N 页  → 精确替换该页里的 `图：<描述>` 行为 `图：images:<相对路径> | <描述>`
   - 出处=教案 · 章节   → 用关键词匹配到最相关的一页，追加一行 `图：images:<相对路径> | <描述>`
   幂等：已含 `images:` 的行会跳过。
"""
import io, os, re, glob, sys
import jieba.posseg as pseg

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.environ.get('COURSE_PROJ') or HERE
IMG = os.environ.get('COURSE_IMG_ROOT') or os.path.join(os.path.dirname(PROJ), 'images')
TAG = 'images:'


def nouns(text):
    out = []
    for w, f in pseg.cut(text):
        w = w.strip()
        if len(w) >= 2 and (f in ('n', 'nr', 'ns', 'nt', 'nz', 'ng', 'vn', 'eng', 'an')
                            or re.fullmatch(r'[A-Za-z0-9×xX./+\-]+', w)):
            out.append(w)
    return out


def parse_md(path):
    """返回 [(序号, 描述, 出处)]，出处形如 'PPT 第 8 页 · xxx' 或 '教案 · xxx'。"""
    t = io.open(path, encoding='utf-8').read()
    res = []
    for blk in re.split(r'(?m)^#{2,3} ', t)[1:]:
        d = re.search(r'\*\*描述\*\*：(.+)', blk)
        s = re.search(r'\*\*出处\*\*：(.+)', blk)
        if d and s:
            res.append((d.group(1).strip(), s.group(1).strip()))
    return res


def find_lesson_md(course, num):
    g = [x for x in glob.glob(os.path.join(PROJ, course, 'PPTs', course + '_' + num + '*')) if x.endswith('.md')]
    return g[0]


def attach(course, num):
    folder = os.path.join(IMG, '%s_%s' % (course, num))
    files = sorted(glob.glob(os.path.join(folder, '*.png')))
    mdm = glob.glob(os.path.join(IMG, '%s_%s_*.md' % (course, num)))
    if not files or not mdm:
        return 0, 0
    entries = parse_md(mdm[0])
    assert len(entries) == len(files), '%s_%s: 图片 %d vs 条目 %d' % (course, num, len(files), len(entries))

    src = find_lesson_md(course, num)
    t = io.open(src, encoding='utf-8').read()
    parts = re.split(r'(?m)^(### 第\s*\d+\s*页.*)$', t)
    # parts: [head, title1, body1, title2, body2, ...]
    pages = []
    head = parts[0]
    for i in range(1, len(parts), 2):
        pages.append([parts[i], parts[i + 1]])

    ok = miss = extra = 0
    for (desc, srcinfo), fn in zip(entries, files):
        rel = '%s_%s/%s' % (course, num, os.path.basename(fn))
        line_new = '图：%s%s | %s' % (TAG, rel, desc)
        if srcinfo.startswith('PPT'):
            # 精确匹配描述
            hit = False
            for p in pages:
                if hit:
                    break
                body = p[1]
                lines = body.split('\n')
                for k, ln in enumerate(lines):
                    s = ln.strip()
                    if not (s.startswith('- 图：') or s.startswith('图：')):
                        continue
                    if TAG in s:
                        continue
                    cur = s.split('图：', 1)[1].strip()
                    if cur == desc:
                        lines[k] = ('- ' if s.startswith('- ') else '') + line_new
                        p[1] = '\n'.join(lines)
                        hit = True
                        ok += 1
                        break
            if not hit:
                miss += 1
                print('  !! 未匹配到占位:', course, num, desc[:40])
        else:
            # 教案补充：按关键词重叠选页
            toks = set(nouns(srcinfo + ' ' + desc))
            best, bs = None, -1
            for p in pages:
                text = p[0] + p[1]
                sc = sum(1 for x in toks if x in text)
                if sc > bs:
                    bs, best = sc, p
            if best is None:
                miss += 1
                continue
            best[1] = best[1].rstrip('\n') + '\n- ' + line_new + '\n'
            extra += 1
    out = head + ''.join(p[0] + p[1] for p in pages)
    io.open(src, 'w', encoding='utf-8').write(out)
    return ok, extra, miss


if __name__ == '__main__':
    tot_ok = tot_ex = tot_ms = 0
    for course in ['MP2', 'MP3']:
        for num in ['%02d' % i for i in range(1, 13)]:
            r = attach(course, num)
            if r:
                tot_ok += r[0]; tot_ex += r[1]; tot_ms += r[2]
                print('%s-%s  页内绑定 %d，教案补充 %d，未匹配 %d' % (course, num, r[0], r[1], r[2]))
    print('合计：页内 %d，教案补充 %d，未匹配 %d' % (tot_ok, tot_ex, tot_ms))
