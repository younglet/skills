# -*- coding: utf-8 -*-
"""把 source_codes 里的任务代码注入 PPT 源：
   1) 复习页后插一页《代码回顾：上一讲核心代码》
   2) 小结页前插入本讲全部任务代码页（每个脚本 1~N 页）
"""
import io, os, re, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
VENDOR = ('nova-style', 'novajs', 'nova-chart.min', 'matrix-board.js', '中文转码工具',
          'ideas.md', 'steps.md', '.min.')

DIRS = {
 ('MP2','01'):'01_motor_rotation', ('MP2','02'):'02_novabot',
 ('MP2','03'):'03_wireless_remote_car', ('MP2','04'):'04_network_connection',
 ('MP2','05'):'05_function_call', ('MP2','06'):'06_voice_recognition',
 ('MP2','07'):'07_oled_screen', ('MP2','08'):'08_bitmap_and_animation',
 ('MP2','09'):'09_desktop_weather_station', ('MP2','10'):'10_novabot_build_1',
 ('MP2','11'):'11_novabot_build_2', ('MP2','12'):'12_novabot_build_3',
 ('MP3','01'):'01_novaserver_basics', ('MP3','02'):'02_web_basics',
 ('MP3','03'):'03_frontend_api', ('MP3','04'):'04_pomodoro_basics',
 ('MP3','05'):'05_pomodoro_config', ('MP3','06'):'06_pomodoro_stats',
 ('MP3','07'):'07_smart_planter_basics', ('MP3','08'):'08_smart_planter_web',
 ('MP3','09'):'09_smart_watering', ('MP3','10'):'10_pixel_matrix_basics',
 ('MP3','11'):'11_pixel_matrix_text', ('MP3','12'):'12_pixel_matrix_icons',
}
REVIEW = {
 ('MP2','01'):('MP2/source_codes/01_motor_rotation/05_mp1_review_button_control_led.py','MP1 的按钮控灯'),
 ('MP2','02'):('MP2/source_codes/01_motor_rotation/03_motor_basic.py','上一讲：Motor 类基础'),
 ('MP2','03'):('MP2/source_codes/02_novabot/05_diff_drive_car_6_motions.py','上一讲：六种动作'),
 ('MP2','04'):('MP2/source_codes/03_wireless_remote_car/05_remote_controller.py','上一讲：遥控器（发送端）'),
 ('MP2','05'):('MP2/source_codes/04_network_connection/06_weather_station.py','上一讲：WeatherStation'),
 ('MP2','06'):('MP2/source_codes/05_function_call/06_ai_led_main.py','上一讲：AI 点灯'),
 ('MP2','07'):('MP2/source_codes/06_voice_recognition/03_voice_control_led.py','上一讲：语音控灯'),
 ('MP2','08'):('MP2/source_codes/07_oled_screen/05_pointer_clock.py','上一讲：指针时钟'),
 ('MP2','09'):('MP2/source_codes/08_bitmap_and_animation/03_heart_beat.py','上一讲：心跳动画'),
 ('MP2','10'):('MP2/source_codes/09_desktop_weather_station/05_weather_station.py','上一讲：桌面气象站'),
 ('MP2','11'):('MP2/source_codes/10_novabot_build_1/05_voice_assistant.py','上一讲：device1 语音助手'),
 ('MP2','12'):('MP2/source_codes/11_novabot_build_2/03_dance.py','上一讲：编一段舞'),
 ('MP3','01'):('MP2/source_codes/12_novabot_build_3/01_link_boards/device2.py','MP2 收官：device2（小脑）'),
 ('MP3','02'):('MP3/source_codes/01_novaserver_basics/01_hello_server.py','上一讲：最小服务器'),
 ('MP3','03'):('MP3/source_codes/02_web_basics/06_static_dir/app.py','上一讲：static_dir 托管'),
 ('MP3','04'):('MP3/source_codes/03_frontend_api/05_nova_js_1/static/index.html','上一讲：nova-js 发请求'),
 ('MP3','05'):('MP3/source_codes/04_pomodoro_basics/06_main_loop.py','上一讲：主循环'),
 ('MP3','06'):('MP3/source_codes/05_pomodoro_config/06_config_page/app.py','上一讲：配置页'),
 ('MP3','07'):('MP3/source_codes/06_pomodoro_stats/06_stats_page/app.py','上一讲：统计页'),
 ('MP3','08'):('MP3/source_codes/07_smart_planter_basics/05_hardware_main.py','上一讲：花盆主程序'),
 ('MP3','09'):('MP3/source_codes/08_smart_planter_web/02_planter_server/app.py','上一讲：花盆服务器'),
 ('MP3','10'):('MP3/source_codes/09_smart_watering/03_strategy/app.py','上一讲：浇水策略'),
 ('MP3','11'):('MP3/source_codes/10_pixel_matrix_basics/03_icon_pattern.py','上一讲：像素图案'),
 ('MP3','12'):('MP3/source_codes/11_pixel_matrix_text/06_text_page/app.py','上一讲：文字页'),
}
PREF = {'MP2': os.path.join('MP2', 'PPTs', 'MP2_'),
        'MP3': os.path.join('MP3', 'PPTs', 'MP3_')}

# 少数讲原本没有“复习”页，这里补上
EXTRA_REVIEW = {
 ('MP2','01'): '''第 _ 页 · 复习：MP1 里学过什么
- 答：在 MP1 里，我们已经会了：用 LED 点灯、用 Button 读按键。
- 表：本节要接着用的老本事

| 会什么 | 代码长什么样 |
| --- | --- |
| 点亮 LED | led.on() / led.off() |
| 读按键 | btn.is_pressed() |

- 答：MP1 里还用 PWM 调过 LED 的亮度；这一次，我们用同样的 PWM 去调电机的转速。
- 问：这些和“电机转动”有什么关系？——电机转起来，本质上也是一组“开关 + 调速”。'''
}


def readlines(p, a=0, b=None):
    with io.open(p, encoding='utf-8', errors='ignore') as f:
        L = f.read().replace('\r\n', '\n').split('\n')
    L = [x.rstrip() for x in L]
    while L and not L[0].strip():
        L.pop(0)
    while L and not L[-1].strip():
        L.pop()
    i = 0
    while i < len(L) and (L[i].strip() == '' or L[i].strip().startswith('#')):
        i += 1
    L = L[i:]
    return L[a:b]


def source_files(course, num):
    d = os.path.join(ROOT, course, 'source_codes', DIRS[(course, num)])
    out = []
    for root, _, fs in os.walk(d):
        for fn in fnnames(fs):
            if not fn.endswith(('.py', '.html', '.js', '.css')):
                continue
            if any(v in fn for v in VENDOR):
                continue
            rel = os.path.relpath(os.path.join(root, fn), d)
            rel = '/'.join(rel.split(os.sep))
            out.append(rel)
    return sorted(out)


def fnnames(fs):
    return sorted(fs)


def _is_block_start(s):
    return bool(re.match(r'^\s*(def |class |async def |@|while |for |if |try:|with )', s)) \
        or bool(re.match(r'^\s*#\s*[─=#*—-]{2,}', s))


def split_lines(lines, maxlen=20):
    n = len(lines); out = []; s = 0
    while n - s > maxlen:
        nch = (n - s + maxlen - 1) // maxlen
        ideal = s + (n - s) / nch
        lo = s + max(5, int((n - s) / nch * 0.5))
        best_i, best_key = None, None
        for i in range(lo, s + maxlen + 1):
            if i >= n:
                break
            prev, nxt = lines[i - 1], lines[i]
            sc = 0
            if prev.strip() == '':
                sc += 5
            if nxt.strip() == '':
                sc += 2
            if _is_block_start(nxt):
                sc += 4
            key = (sc, -abs(i - ideal))
            if best_key is None or key > best_key:
                best_key, best_i = key, i
        if best_i is None:
            best_i = s + maxlen
        out.append(lines[s:best_i]); s = best_i
    out.append(lines[s:])
    return out


def code_pages(title, lines, chunk=20):
    parts = split_lines(lines, chunk)
    total = len(parts)
    return [(title + ('' if total <= 1 else '（%d/%d）' % (i + 1, total)), '\n'.join(p))
            for i, p in enumerate(parts) if p]


def md_path(course, num):
    g = [x for x in glob.glob(PREF[course] + num + '*') if x.endswith('.md')]
    return g[0]


def renumber(pages_list):
    out = []
    for i, pg in enumerate(pages_list, 1):
        first, _, rest = pg.partition('\n')
        first = re.sub(r'^第\s*[_\d]+\s*页', '第 %d 页' % i, first.strip())
        out.append('### ' + first)
        if rest.strip():
            out.append(rest.strip('\n'))
    return out


def inject(course, num):
    path = md_path(course, num)
    t = io.open(path, encoding='utf-8').read()
    parts = re.split(r'(?m)^### (?=第\s*\d+\s*页)', t)
    head, body = parts[0], parts[1:]

    # 防止重复注入
    if any('代码回顾' in pg.split('\n', 1)[0] for pg in body):
        print('%s-%s 已注入过，跳过' % (course, num))
        return 0, len(body)

    # 若原本没有复习页，先补一页
    if not any('复习' in pg.split('\n', 1)[0] for pg in body):
        body.insert(1, EXTRA_REVIEW[(course, num)])

    rf, rt = REVIEW[(course, num)]
    rl = readlines(os.path.join(ROOT, rf))
    rblock = ['第 _ 页 · ' + tt + '\n```\n' + cc + '\n```\n' for tt, cc in code_pages('代码回顾：' + rt, rl)]
    ri = 1
    for i, pg in enumerate(body):
        if '复习' in pg.split('\n', 1)[0]:
            ri = i + 1
            break
    for k, b in enumerate(rblock):
        body.insert(ri + k, b)

    tblock = []
    files = source_files(course, num)
    if files:
        head_lines = ['第 _ 页 · 本节任务代码清单',
                      '- 表：本节脚本', '', '| 顺序 | 脚本文件 |', '| --- | --- |']
        for i, rel in enumerate(files, 1):
            head_lines.append('| %d | %s |' % (i, rel))
        tblock.append('\n'.join(head_lines))
    for rel in files:
        lines = readlines(os.path.join(ROOT, course, 'source_codes', DIRS[(course, num)], rel))
        for tt, cc in code_pages('代码：' + rel, lines):
            tblock.append('第 _ 页 · ' + tt + '\n```\n' + cc + '\n```\n')
    si = len(body)
    for i, pg in enumerate(body):
        if re.search(r'小结|拓展', pg.split('\n', 1)[0]):
            si = i
            break
    for k, b in enumerate(tblock):
        body.insert(si + k, b)

    newt = '\n\n'.join([head.rstrip('\n')] + renumber(body)).rstrip('\n') + '\n'
    io.open(path, 'w', encoding='utf-8').write(newt)
    return len(rblock) + len(tblock), len(renumber(body))


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'MP2'
    for (c, n) in sorted(DIRS):
        if c != which:
            continue
        add, tot = inject(c, n)
        print('%s-%s  +%d 页  (现 %d 页)' % (c, n, add, tot))
