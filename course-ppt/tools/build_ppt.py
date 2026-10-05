# -*- coding: utf-8 -*-
import os, re, io, glob, uuid, time
from xml.sax.saxutils import escape
from pptx import Presentation
from pptx.util import Inches, Pt, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "模板.pptx")
IMG_ROOT = os.environ.get("COURSE_IMG_ROOT") or os.path.join(os.path.dirname(HERE), "images")
FONT = "微软雅黑"
INK = RGBColor(0x22, 0x2A, 0x35)
GRAY = RGBColor(0x8A, 0x93, 0x9E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HEAD_BG = RGBColor(0xEA, 0xF1, 0xFF)
SUB = RGBColor(0x1D, 0x4E, 0xD8)
SEP = re.compile(r'^[\s\-:|]*$')
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u20E3]+", re.UNICODE)

FULL_L, FULL_W = Cm(1.7), Cm(22)
IMG_L, IMG_W = Cm(1.7), Cm(10)
TXT_L, TXT_W = Cm(13.7), Cm(10)


def clean(s):
    s = s.replace('`', '').replace('**', '')
    return EMOJI.sub('', s).strip()


def set_font(run, name=FONT):
    rPr = run._r.get_or_add_rPr()
    for tag in ('a:latin', 'a:ea', 'a:cs'):
        for el in rPr.findall(qn(tag)):
            rPr.remove(el)
        rPr.append(rPr.makeelement(qn(tag), {'typeface': name}))


def para_props(p):
    pPr = p._p.find(qn('a:pPr'))
    if pPr is None:
        pPr = p._p.makeelement(qn('a:pPr'), {})
        p._p.insert(0, pPr)
    pPr.set('hangingPunct', '1')
    pPr.set('eaLnBrk', '1')


def style(run, size, color=INK, bold=False):
    run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = color
    set_font(run)


def parse_lesson(path):
    text = io.open(path, encoding="utf-8").read()
    h = text.split("\n")[0].lstrip("#").strip()
    m = re.match(r'(MP\d)-(\d+)\s*·\s*(.*)', h)
    lid, topic = (m.group(1) + "-" + m.group(2), m.group(3).strip()) if m else (h, "")
    pages = []
    for p in re.split(r'(?m)^### (?=第\s*\d+\s*页)', text)[1:]:
        t, _, c = p.partition("\n")
        pages.append((re.sub(r'^第\s*\d+\s*页\s*·\s*', '', t).strip(), c))
    return lid, topic, pages


def kind_of(s):
    if s.startswith("🖼") or s.startswith("图"): return "img"
    if s.startswith("❓") or s.startswith("问：") or s.startswith("问:"): return "q"
    if s.startswith("✅"): return "ans"
    return "k"


def img_desc(s):
    for sep in ("图：", "图:"):
        if sep in s:
            return clean(s.split(sep, 1)[1])
    return clean(s)


def collect(content):
    raw = content.split("\n"); items = []; i = 0; part = 0
    while i < len(raw):
        s = raw[i].strip()
        if not s:
            if items:
                part += 1
            i += 1; continue
        if s.startswith("```"):
            buf = []; i += 1
            while i < len(raw) and not raw[i].strip().startswith("```"):
                buf.append(raw[i].rstrip()); i += 1
            i += 1
            items.append(("code", "\n".join(buf), part)); continue
        if s.startswith("- "):
            s = s[2:].strip()
        if s == "<<gap>>":          # 间隔行：问题组之间留白
            items.append(("gap", "", part)); i += 1; continue
        if s.startswith("页脚："):      # 页脚：底部小号灰色字
            items.append(("foot", s[3:].strip(), part)); i += 1; continue
        raw_s = s
        s = s.replace("**", "")
        if s.endswith("：") and len(s) <= 6 and not any(e in s for e in "🖼💡❓✅💻🧩"):
            i += 1; continue
        if s.startswith("|"):
            blk = []
            while i < len(raw) and raw[i].strip().startswith("|"):
                blk.append(raw[i].strip()); i += 1
            rows = []
            for b in blk:
                cells = [c.strip() for c in b.strip("|").split("|")]
                if cells and all(SEP.match(c) for c in cells if c != ""):
                    continue
                rows.append([clean(c) for c in cells])
            if rows:
                items.append(("tbl", rows, part))
            continue
        if s.startswith("### "):
            items.append(("h", clean(s[4:]), part)); i += 1; continue
        if s.startswith("（") and s.endswith("）"):
            i += 1; continue
        k = kind_of(raw_s)
        t = img_desc(raw_s) if k == "img" else clean(re.sub(r'^(问|答)[：:]\s*', '', raw_s))
        if not t:
            i += 1; continue
        items.append((k, t, part)); i += 1
    return items


def split_static_anim(items):
    has_q = any(k == "q" for k, _, _ in items)
    multi = max((p for _, _, p in items), default=0) >= 1
    static, anim = [], []
    for k, t, p in items:
        if k in ("img", "tbl", "code", "h", "gap", "foot"):
            static.append((k, t))
        elif k == "ans":
            anim.append((k, t))
        elif has_q and k != "q":
            anim.append((k, t))
        elif (not has_q) and multi and p >= 1:
            anim.append((k, t))
        else:
            static.append((k, t))
    return static, anim


def del_slides(prs):
    lst = prs.slides._sldIdLst
    for s in list(lst):
        prs.part.drop_rel(s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'))
        lst.remove(s)


def write_para(tf, idx, text, size, bold=False, color=INK, mono=False, sp=4):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    para_props(p); p.text = text; p.space_after = Pt(sp)
    for r in p.runs:
        style(r, size, color, bold)
        if mono:
            r.font.name = 'Consolas'; set_font(r, 'Consolas')
    return p


def tbox(slide, items, left, top, w, h, base):
    tb = slide.shapes.add_textbox(left, top, w, h)
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.TOP
    idx = 0
    for k, t in items:
        if k == "gap":
            write_para(tf, idx, "", base, sp=18)
        elif k == "img":
            write_para(tf, idx, "【图片占位】应插入图片：" + t, 11, color=GRAY)
        elif k == "h":
            write_para(tf, idx, t, base + 2, bold=True, color=SUB)
        else:
            write_para(tf, idx, t, base, bold=(k == "q"))
        idx += 1
    return tb


def add_table(slide, rows, left, top, width, height):
    nrow = len(rows); ncol = max(len(r) for r in rows)
    shp = slide.shapes.add_table(nrow, ncol, left, top, width, height)
    tbl = shp.table
    each = int(width / ncol)
    for c in range(ncol):
        tbl.columns[c].width = each
    for r in range(nrow):
        for c in range(ncol):
            cell = tbl.cell(r, c)
            cell.text = rows[r][c] if c < len(rows[r]) else ""
            cell.margin_left = Cm(0.12); cell.margin_right = Cm(0.12)
            cell.margin_top = Cm(0.04); cell.margin_bottom = Cm(0.04)
            for p in cell.text_frame.paragraphs:
                para_props(p)
                for run in p.runs:
                    style(run, 11, INK, bold=(r == 0))
            if r == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = HEAD_BG
    return shp


def code_font_size(n):
    return 12 if n <= 14 else (11 if n <= 20 else 10)


def resolve_img(text):
    """`images:<相对路径> | <描述>` -> (绝对路径 或 None, 描述)"""
    s = text.strip()
    if s.startswith("images:"):
        rel, _, desc = s[len("images:"):].partition("|")
        p = os.path.join(IMG_ROOT, rel.strip().replace("/", os.sep))
        return p, desc.strip()
    return None, s


def add_photo(slide, path, left, top, width, height):
    """按比例把图片放进 (left,top,width,height) 并居中。"""
    try:
        from PIL import Image
        iw, ih = Image.open(path).size
    except Exception:
        iw, ih = 16, 9
    ar = (iw / float(ih)) if ih else 16 / 9.0
    bar = (width / float(height)) if height else 16 / 9.0
    if ar > bar:
        pw = width; ph = int(width / ar)
    else:
        ph = height; pw = int(height * ar)
    return slide.shapes.add_picture(path, int(left + (width - pw) / 2),
                                    int(top + (height - ph) / 2), pw, ph)


def add_footer(slide, text):
    """幻灯片底部：微软雅黑 10pt 灰色小字（说明对应环节/步骤）。"""
    if not text:
        return
    tb = slide.shapes.add_textbox(FULL_L, Inches(5.2), FULL_W, Inches(0.32))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; para_props(p); p.alignment = PP_ALIGN.RIGHT
    r = p.add_run(); r.text = text
    style(r, 10, GRAY)
    return tb


def place_img(slide, raw, left, top, width, height):
    """有真图就插图，否则退回文字占位。"""
    path, desc = resolve_img(raw)
    if path and os.path.exists(path):
        return add_photo(slide, path, left, top, width, height)
    tbox(slide, [("img", desc)], left, top, width, height, 11)
    return None


def add_code(slide, code, left, top, width, height):
    lines = code.split("\n")
    size = code_font_size(len(lines))
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.clear()
    for i, ln in enumerate(lines[:20]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para_props(p); p.text = EMOJI.sub('', ln); p.space_after = Pt(0)
        for r in p.runs:
            style(r, size, INK); r.font.name = 'Consolas'; set_font(r, 'Consolas')
    return tb


def timing_xml_paras(shape_id, idxs):
    """按段落逐个淡入（用于复习页：点一下出现一条答案）。"""
    c = [10]
    def nid():
        c[0] += 1; return str(c[0])
    def tgt(i):
        return ('<p:tgtEl><p:spTgt spid="%s"><p:txEl>'
                '<p:pRg st="%d" end="%d"/></p:txEl></p:spTgt></p:tgtEl>' % (shape_id, i, i))
    eff = []
    for k, i in enumerate(idxs):
        node = "clickEffect" if k == 0 else "afterEffect"
        eff.append(
            '<p:par><p:cTn id="%s" presetID="10" presetClass="entr" presetSubtype="0" '
            'fill="hold" nodeType="%s"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            '<p:childTnLst>'
            '<p:set><p:cBhvr><p:cTn id="%s" dur="1" fill="hold"><p:stCondLst>'
            '<p:cond delay="0"/></p:stCondLst></p:cTn>%s'
            '<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            '<p:to><p:strVal val="visible"/></p:to></p:set>'
            '<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="%s" dur="350"/>%s'
            '</p:cBhvr></p:animEffect>'
            '</p:childTnLst></p:cTn></p:par>'
            % (nid(), node, nid(), tgt(i), nid(), tgt(i)))
    return (
        '<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:tnLst>'
        '<p:par><p:cTn id="%s" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
        '<p:seq concurrent="1" nextAc="seek"><p:cTn id="%s" dur="indefinite" nodeType="mainSeq">'
        '<p:childTnLst>'
        '<p:par><p:cTn id="%s" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
        '<p:childTnLst><p:par><p:cTn id="%s" fill="hold"><p:stCondLst><p:cond delay="0"/>'
        '</p:stCondLst><p:childTnLst>%s</p:childTnLst></p:cTn></p:par></p:childTnLst>'
        '</p:cTn></p:par></p:childTnLst></p:cTn>'
        '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        '</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'
        % (nid(), nid(), nid(), nid(), ''.join(eff)))


def timing_xml(shape_ids):
    c = [10]
    def nid():
        c[0] += 1; return str(c[0])
    eff = []
    for i, spid in enumerate(shape_ids):
        node = "clickEffect" if i == 0 else "afterEffect"
        eff.append(
            '<p:par><p:cTn id="%s" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="%s">'
            '<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            '<p:set><p:cBhvr><p:cTn id="%s" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            '<p:tgtEl><p:spTgt spid="%s"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            '<p:to><p:strVal val="visible"/></p:to></p:set>'
            '<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="%s" dur="450"/>'
            '<p:tgtEl><p:spTgt spid="%s"/></p:tgtEl></p:cBhvr></p:animEffect>'
            '<p:anim calcmode="lin" valueType="num"><p:cBhvr additive="base"><p:cTn id="%s" dur="450" fill="hold"/>'
            '<p:tgtEl><p:spTgt spid="%s"/></p:tgtEl><p:attrNameLst><p:attrName>ppt_y</p:attrName></p:attrNameLst></p:cBhvr>'
            '<p:tavLst><p:tav tm="0"><p:val><p:strVal val="#ppt_y+0.08"/></p:val></p:tav>'
            '<p:tav tm="100000"><p:val><p:strVal val="#ppt_y"/></p:val></p:tav></p:tavLst></p:anim>'
            '</p:childTnLst></p:cTn></p:par>'
            % (nid(), node, nid(), spid, nid(), spid, nid(), spid))
    return (
        '<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:tnLst>'
        '<p:par><p:cTn id="%s" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
        '<p:seq concurrent="1" nextAc="seek"><p:cTn id="%s" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
        '<p:par><p:cTn id="%s" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>'
        '<p:par><p:cTn id="%s" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
        '%s</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>'
        '</p:childTnLst></p:cTn>'
        '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        '</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'
        % (nid(), nid(), nid(), nid(), "".join(eff)))


def cover_bg(slide, path, sw, sh):
    """封面背景图：按"覆盖"方式铺满整页（超出部分被幻灯片裁掉）。"""
    try:
        from PIL import Image
        iw, ih = Image.open(path).size
    except Exception:
        return
    ar = (iw / float(ih)) if ih else 16 / 9.0
    bar = sw / float(sh)
    if ar > bar:
        ph = sh; pw = int(sh * ar)
    else:
        pw = sw; ph = int(sw / ar)
    slide.shapes.add_picture(path, int((sw - pw) / 2), int((sh - ph) / 2), pw, ph)


def add_cover(prs, layout, lid, topic, img=None):
    s = prs.slides.add_slide(layout)
    if img and os.path.exists(img):
        cover_bg(s, img, prs.slide_width, prs.slide_height)
    tb = s.shapes.add_textbox(Inches(1.28), Inches(2.15), Inches(7.53), Inches(2.6))
    tf = tb.text_frame; tf.word_wrap = True
    p1 = tf.paragraphs[0]; para_props(p1); p1.alignment = PP_ALIGN.CENTER
    r1 = p1.add_run(); r1.text = lid; style(r1, 54, WHITE); r1.font._rPr.set('spc', '225')
    p2 = tf.add_paragraph(); para_props(p2); p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run(); r2.text = topic; style(r2, 54, WHITE); r2.font._rPr.set('spc', '225')


def add_content(prs, layout, title, items):
    s = prs.slides.add_slide(layout)
    if s.shapes.title is not None:
        s.shapes.title.text = title
        for p in s.shapes.title.text_frame.paragraphs:
            para_props(p)
            for r in p.runs:
                set_font(r)
    for ph in list(s.placeholders):
        if ph.placeholder_format.idx == 10:
            ph._element.getparent().remove(ph._element)

    rv = ("复习" in title)          # 复习页：全部静态、且保持原序（问答成对）
    if rv:
        static = [(k, t) for k, t, _ in items]
        anim = []
    else:
        static, anim = split_static_anim(items)

    imgs = [t for k, t in static if k == "img"]
    tbls = [t for k, t in static if k == "tbl"]
    codes = [t for k, t in static if k == "code"]
    static_txt = [(k, t) for k, t in static if k not in ("img", "tbl", "code", "foot")]
    foots = [t for k, t in static if k == "foot"]

    # 复习页：问题静态，答案逐条淡入（段落级动画）
    if rv and not (imgs or tbls or codes):
        aidx = [i for i, (k, _) in enumerate(static)
                if k == "k" and i > 0 and static[i - 1][0] == "q"]
        if aidx:
            ab = tbox(s, static, FULL_L, Inches(1.45), FULL_W, Inches(3.7), 12)
            s._element.append(parse_xml(timing_xml_paras(ab.shape_id, aidx)))
            return
    anim_ids = []

    # 模块参考页：按顺序排版（小标题 -> 表 -> 小标题 -> 代码）
    if tbls or codes:
        y = Inches(1.3)
        buf = []
        def flush(buf, yy):
            if not buf:
                return yy
            hh = Inches(0.34) * len(buf) + Inches(0.16)
            tbox(s, buf[:], FULL_L, yy, FULL_W, hh, 14)
            return yy + hh + Inches(0.06)
        for k, t in static:
            if k in ("k", "q", "ans", "h"):
                buf.append((k, t))
            elif k == "tbl":
                y = flush(buf, y); buf = []
                hh = Inches(0.42) * len(t)
                add_table(s, t, FULL_L, y, FULL_W, hh)
                y = y + hh + Inches(0.12)
            elif k == "img":
                y = flush(buf, y); buf = []
                place_img(s, t, FULL_L, y, FULL_W, Inches(2.3))
                y = y + Inches(2.4)
            elif k == "code":
                y = flush(buf, y); buf = []
                n = len(t.split("\n"))
                code_h = Inches(0.0185) * max(n, 1) * (code_font_size(n) / 10.0) + Inches(0.25)
                add_code(s, t, FULL_L, y, FULL_W, code_h)
                y = y + code_h + Inches(0.12)
        flush(buf, y)
        add_footer(s, " ｜ ".join(foots))
        return

    if anim:
        if imgs:
            if len(imgs) >= 2:
                place_img(s, imgs[0], IMG_L, Inches(1.35), IMG_W, Inches(1.75))
                place_img(s, imgs[1], IMG_L, Inches(3.2), IMG_W, Inches(1.75))
                anim += [("k", "图片：" + resolve_img(x)[1]) for x in imgs[2:]]
            else:
                place_img(s, imgs[0], IMG_L, Inches(1.35), IMG_W, Inches(3.6))
            if static_txt:
                tbox(s, static_txt, TXT_L, Inches(1.4), TXT_W, Inches(1.55), 13)
                ab = tbox(s, anim, TXT_L, Inches(3.05), TXT_W, Inches(1.9), 12)
            else:
                ab = tbox(s, anim, TXT_L, Inches(1.4), TXT_W, Inches(3.55), 13)
        else:
            if static_txt:
                tbox(s, static_txt, FULL_L, Inches(1.4), FULL_W, Inches(1.6), 16)
                ab = tbox(s, anim, FULL_L, Inches(3.1), FULL_W, Inches(2.05), 14)
            else:
                ab = tbox(s, anim, FULL_L, Inches(1.45), FULL_W, Inches(3.7), 15)
        anim_ids = [ab.shape_id]
    else:
        if imgs:
            if len(imgs) >= 2:
                place_img(s, imgs[0], IMG_L, Inches(1.35), IMG_W, Inches(1.75))
                place_img(s, imgs[1], IMG_L, Inches(3.2), IMG_W, Inches(1.75))
                static_txt += [("k", "图片：" + resolve_img(x)[1]) for x in imgs[2:]]
            else:
                place_img(s, imgs[0], IMG_L, Inches(1.35), IMG_W, Inches(3.6))
            tbox(s, static_txt, TXT_L, Inches(1.4), TXT_W, Inches(3.55), 13)
        else:
            tbox(s, static_txt, FULL_L, Inches(1.45), FULL_W, Inches(3.7), 12 if rv else 15)

    add_footer(s, " ｜ ".join(foots))

    if anim_ids:
        s._element.append(parse_xml(timing_xml(anim_ids)))


def inject_sections(prs, sections):
    ids = [int(e.get('id')) for e in prs.slides._sldIdLst]
    out = ['<p:extLst xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
           'xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main">',
           '<p:ext uri="{521415D9-36F7-43E2-AB2F-B90AF26B5E84}"><p14:sectionLst>']
    pos = 0
    for name, n in sections:
        out.append('<p14:section name="%s" id="{%s}"><p14:sldIdLst>' % (escape(name), str(uuid.uuid4()).upper()))
        for i in ids[pos:pos + n]:
            out.append('<p14:sldId id="%d"/>' % i)
        out.append('</p14:sldIdLst></p14:section>'); pos += n
    out.append('</p14:sectionLst></p:ext></p:extLst>')
    el = parse_xml("".join(out)); pres = prs.part._element
    for e in pres.findall(qn('p:extLst')): pres.remove(e)
    pres.append(el)


def save_retry(prs, path, tries=5):
    for _ in range(tries):
        try:
            prs.save(path); return path
        except PermissionError:
            time.sleep(1.2)
    alt = path.replace('.pptx', '_fixed.pptx')
    prs.save(alt); return alt


def build(course):
    src = os.path.join(HERE, course, "PPTs")
    files = [f for f in sorted(glob.glob(os.path.join(src, course + "_*.md")))
             if os.path.basename(f) != "README.md"]
    prs = Presentation(TPL); del_slides(prs)
    lay = {l.name: l for m in prs.slide_masters for l in m.slide_layouts}
    cover = lay.get("1_自定义版式", prs.slide_layouts[0])
    cont = lay.get("3_自定义版式", prs.slide_layouts[-1])
    secs = []
    for f in files:
        lid, topic, pages = parse_lesson(f)
        n0 = len(prs.slides._sldIdLst)
        cimg = None
        for ttl, content in pages:
            if "封面" in ttl:
                m = re.search(r'图：\s*(images:[^\n]+)', content)
                if m:
                    cimg, _ = resolve_img(m.group(1).strip())
        add_cover(prs, cover, lid, topic, cimg)
        for title, content in pages:
            if "封面" in title: continue
            add_content(prs, cont, title, collect(content))
        secs.append(("%s %s" % (lid, topic), len(prs.slides._sldIdLst) - n0))
    inject_sections(prs, secs)
    saved = save_retry(prs, os.path.join(HERE, course, "PPTs", "%s_PPT.pptx" % course))
    print("%s: %d 页, %d sections -> %s" % (course, len(prs.slides._sldIdLst), len(secs), saved))


for c in ["MP2", "MP3"]:
    build(c)
print("done")
