# -*- coding: utf-8 -*-
"""把任务代码页"贴到对应环节旁边"：
   - 删掉讲末的"代码：xxx"页 与"本节任务代码清单"页
   - 按 MAPPING，把每个脚本的代码页插到指定锚点页的后面
   - 重新编号
锚点用页面标题的子串匹配；同名多页时取**最后一页**（如"Motor 驱动"取到"使用示例"那页）。
"""
import io, os, re, glob, sys, difflib

SIM = 0.85        # 与已展示脚本相似度 ≥ 此值
ADD_MAX = 6       # 且新增/修改行数 ≤ 此值 -> 不再重复贴代码

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
sys.path.insert(0, HERE)
import inject_codes as ic  # 复用其中的 REVIEW（代码回顾用哪个脚本）
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
PREF = {'MP2': os.path.join('MP2', 'PPTs', 'MP2_'),
        'MP3': os.path.join('MP3', 'PPTs', 'MP3_')}

M = {
('MP2','01'): [
  ('复习：MP1 的按钮怎么读', ['04_mp1_review_button_basic.py']),
  ('实验 1：用程序控制电机正反转', ['01_h_bridge_forward_reverse.py']),
  ('应用：用 PWM 给电机调速', ['02_pwm_motor.py']),
  ('Motor 驱动', ['03_motor_basic.py']),
  ('编程任务：按钮启停与旋钮调速', ['06_button_control_motor.py', '07_knob_control_motor.py',
                                 'EX1_bidirectional_knob.py', 'EX2_diff_drive_spin.py']),
],
('MP2','02'): [
  ('知识点：什么是"封装"', ['01_motor_car.py', '02_simple_car.py', '03_car_with_params.py']),
  ('DiffDriveCar 驱动', ['04_diff_drive_car.py']),
  ('编程任务 1：测试 6 种基本动作', ['05_diff_drive_car_6_motions.py']),
  ('编程任务 2：走正方形轨迹', ['06_diff_drive_car_square.py', 'EX1_diff_drive_car_figure_eight.py',
                            'EX2_diff_drive_car_speed_test.py']),
],
('MP2','03'): [
  ('第一步：知道自己是谁', ['01_get_mac.py']),
  ('第二步：怎么把消息发出去', ['02_send_case/student.py', '02_send_case/teacher.py']),
  ('第三步：角色互换', ['03_receive_case/student.py', '03_receive_case/teacher.py']),
  ('第四步：点对点与 peer 配对', ['04_point_to_point/receiver.py', '04_point_to_point/sender.py']),
  ('第五步：遥控控制器', ['05_remote_controller.py']),
  ('第六步：遥控小车', ['06_remote_car.py', 'EX1_espnow_callback.py', 'EX2_espnow_bidirectional.py']),
],
('MP2','04'): [
  ('知识点：boot.py 启动机制', ['04_boot_start.py']),
  ('WiFi 模块', ['01_wifi_connect.py', '03_novamp_wifi_timesync.py']),
  ('TimeSyncer 模块', ['02_ntp_time_sync.py']),
  ('requests 模块', ['05_weather_requests.py']),
  ('WeatherStation 天气模块', ['06_weather_station.py']),
],
('MP2','05'): [
  ('知识点：一次请求长什么样', ['01_deepseek_hello.py', '02_chat_loop.py']),
  ('知识点：为什么发送时要把字典变成 JSON', ['03_json_roundtrip.py']),
  ('ChatBot 模块', ['04_chatbot_basic.py']),
  ('Function Call 为什么要发两轮', ['05_function_call_probe.py']),
  ('编程任务：AI 控制的智能灯', ['06_ai_led_main.py', 'EX1_ai_motor_speed.py']),
],
('MP2','06'): [
  ('知识点：命令词表的规律', ['01_read_raw_bytes.py']),
  ('SU03T 模块', ['02_su03t_driver.py']),
  ('编程任务：语音控制 LED', ['03_voice_control_led.py', 'EX1_voice_control_car.py', 'EX2_ai_assistant.py']),
],
('MP2','07'): [
  ('machine.I2C 模块', ['01_i2c_scan.py']),
  ('SSD1306 驱动', ['02_hello_oled.py', '03_draw_shapes.py']),
  ('编程任务 1：NTP 时钟显示', ['04_ntp_clock.py']),
  ('编程任务 2：指针时钟', ['05_pointer_clock.py', 'EX1_status_panel.py']),
],
('MP2','08'): [
  ('知识点：从方格纸到 8 个字节', ['02_heart_by_hand.py']),
  ('framebuf 模块', ['01_heart_bitmap.py']),
  ('NAF 模块', ['03_heart_beat.py']),
  ('应用：用网页工具转一个 NAF', ['EX1_heart_by_formula.py']),
],
('MP2','09'): [
  ('VTX316 语音合成模块', ['01_vtx316_say_hello.py', '02_vtx316_full_usage.py']),
  ('知识点：天气数据与图标代码', ['03_weather_driver.py', '05_weather_station.py']),
  ('知识点：动画和文字怎么同屏', ['04_weather_naf.py']),
  ('编程任务：桌面气象站完整版', ['EX1_dht11_indoor.py', 'EX2_button_speak.py', 'EX3_ai_advice.py']),
],
('MP2','10'): [
  ('听得见：SU03T', ['01_su03t_commands.py']),
  ('编程任务：device1 语音助手', ['02_query_weather.py', '03_query_time.py', '04_tell_joke.py',
                                '05_voice_assistant.py', 'EX1_my_command.py']),
],
('MP2','11'): [
  ('编程任务 1：让眼睛动起来', ['01_eyes_show.py']),
  ('编程任务 2：五个基础动作', ['02_basic_moves.py']),
  ('编程任务 3：编一段舞', ['03_dance.py', 'EX1_my_dance.py']),
],
('MP2','12'): [
  ('编程任务 1：连接两块板', ['01_link_boards/device1.py', '01_link_boards/device2.py']),
  ('编程任务 2：加待机状态', ['02_idle_state/device1.py', '02_idle_state/device2.py']),
  ('编程任务 3：加表演命令', ['03_perform/device1.py', '03_perform/device2.py',
                           'EX1_my_idle_actions/device1.py', 'EX1_my_idle_actions/device2.py']),
],
('MP3','01'): [
  ('编程任务 1：让开发板当上服务器', ['01_hello_server.py']),
  ('知识点：把一个网址拆开看', ['05_inspect_request.py', '07_route_params.py']),
  ('知识点：路由就是一张配对表', ['02_multi_routes.py']),
  ('知识点：用 GET 控制 LED 开关', ['03_set_led_via_get.py']),
  ('知识点：POST——把数据装在请求体里', ['04_set_brightness_via_post.py']),
  ('知识点：RESTful 的四种方法', ['06_restful_methods.py']),
],
('MP3','02'): [
  ('编程任务 1：写出你的第一张网页', ['01_html_only/index.html']),
  ('老师现场敲一遍', ['02_raw_css/index.html']),
  ('知识点：什么是 nova-style', ['03_intro_nova_style/index.html']),
  ('编程任务 2：贴上现成的名字', ['04_use_nova_style/index.html']),
  ('知识点：什么是 send_file', ['05_send_file/app.py', '05_send_file/index.html']),
  ('知识点：什么是 static_dir', ['06_static_dir/app.py', '06_static_dir/static/index.html']),
  ('编程任务 3：把页面交给服务器', ['EX1_local_hostname/boot.py']),
],
('MP3','03'): [
  ('知识点：用 <a> 标签发 GET', ['01_a_tag/app.py', '01_a_tag/static/index.html']),
  ('知识点：用 <form> 表单发请求', ['02_form_action/app.py', '02_form_action/static/index.html']),
  ('第一步：先把请求发出去', ['03_javascript_1/app.py', '03_javascript_1/static/index.html']),
  ('第二步：再把页面改掉', ['04_javascript_2/app.py', '04_javascript_2/static/index.html']),
  ('知识点：什么是 nova-js', ['05_nova_js_1/app.py', '05_nova_js_1/static/index.html']),
  ('知识点：什么是 nova-js 的"响应式"', ['06_nova_js_2/app.py', '06_nova_js_2/static/index.html',
                                  '07_nova_js_3/app.py', '07_nova_js_3/static/index.html']),
  ('练习：把输入框换成滑块', ['08_slider/app.py', '08_slider/static/index.html']),
],
('MP3','04'): [
  ('第一步：常量与配置', ['01_imports_config.py']),
  ('知识点：为什么要设计"状态"', ['02_global_state.py']),
  ('知识点：正确的写法——算差，不睡', ['03_tick_function.py']),
  ('知识点：怎么把数字画到屏幕上', ['04_render_function.py']),
  ('知识点：硬件初始化', ['05_hardware_setup.py']),
  ('知识点：主循环', ['06_main_loop.py']),
],
('MP3','05'): [
  ('知识点：为什么要"封装成类"', ['01_simple_clock/app.py', '01_simple_clock/lib/tomato_clock.py']),
  ('知识点：为什么主循环要塞给服务器', ['02_novaserver_task/app.py', '03_tomato_server_task/app.py',
                              '03_tomato_server_task/lib/tomato_clock.py']),
  ('知识点：为什么要用 nova.api', ['04_resource_demo/app.py', '04_resource_demo/static/index.html']),
  ('编程任务：配置页', ['06_config_page/app.py', '06_config_page/lib/tomato_clock.py',
                   '06_config_page/static/index.html']),
],
('MP3','06'): [
  ('知识点：为什么这份文件叫 boot.py', ['01_time_sync/boot.py']),
  ('知识点：给一个现成的类加功能', ['02_tomato_stats/app.py', '02_tomato_stats/lib/tomato_clock.py']),
  ('知识点：什么是 nova-db', ['03_nova_db/app.py']),
  ('编程任务：把账本存进文件', ['04_tomato_db/app.py', '04_tomato_db/lib/tomato_clock.py']),
  ('知识点：什么是 nova-chart', ['05_nova_chart/static/index.html']),
  ('编程任务：统计页与面板', ['06_stats_page/app.py', '06_stats_page/lib/tomato_clock.py',
                        '06_stats_page/static/index.html', '07_dashboard/app.py',
                        '07_dashboard/lib/tomato_clock.py', '07_dashboard/static/index.html']),
],
('MP3','07'): [
  ('知识点：这盆花要盯着哪几个数', ['01_imports_config.py']),
  ('知识点：程序要记住什么', ['02_global_state.py']),
  ('知识点：怎么读——三个传感器脾气不一样', ['03_read_sensors.py']),
  ('知识点：怎么看得见（调试输出）', ['04_update_display.py']),
  ('知识点：update() 再叠一层', ['05_hardware_main.py']),
],
('MP3','08'): [
  ('知识点：为什么要"收进类"', ['01_class_planter/app.py', '01_class_planter/lib/smart_planter.py']),
  ('知识点：什么是"轮询"', ['03_poll_demo/main.py', '03_poll_demo/static/index.html']),
  ('编程任务：让服务器来驱动', ['02_planter_server/app.py', '02_planter_server/lib/smart_planter.py']),
  ('编程任务：传感器页', ['04_sensor_page/app.py', '04_sensor_page/lib/smart_planter.py',
                    '04_sensor_page/static/index.html']),
  ('知识点：实时曲线是怎么"滚"起来的', ['05_sensor_chart/app.py', '05_sensor_chart/lib/smart_planter.py',
                              '05_sensor_chart/static/index.html', '05_sensor_chart/static/soil.html',
                              '05_sensor_chart/static/temp.html', '05_sensor_chart/static/humid.html',
                              '05_sensor_chart/static/light.html']),
],
('MP3','09'): [
  ('编程任务：加一个"手动浇水"入口', ['01_loop_demo/static/index.html', '02_watering_records/app.py',
                              '02_watering_records/lib/smart_planter.py',
                              '02_watering_records/static/index.html']),
  ('编程任务：让策略可配', ['03_strategy/app.py', '03_strategy/lib/smart_planter.py',
                     '03_strategy/static/index.html']),
  ('编程任务：两条路由 + 页面表单', ['04_dashboard/app.py', '04_dashboard/lib/smart_planter.py',
                            '04_dashboard/static/index.html']),
],
('MP3','10'): [
  ('知识点：一颗灯怎么亮', ['01_neopixel_basics.py']),
  ('知识点：坐标怎么变序号', ['02_8x8_mapping.py']),
  ('知识点：怎么画一张图', ['03_icon_pattern.py']),
  ('知识点：让它动起来', ['04_animation.py']),
  ('知识点：反过来——当个沙漏用', ['05_hourglass.py']),
],
('MP3','11'): [
  ('RGBMatrix 模块', ['01_rgb_matrix_basics/app.py']),
  ('编程任务：显示数字', ['02_show_number/app.py']),
  ('编程任务：数字页面', ['03_number_page/app.py', '03_number_page/static/index.html']),
  ('知识点：一行只能放两个字符', ['04_show_text/app.py']),
  ('知识点：文字太长怎么办', ['05_scroll_text/app.py']),
  ('编程任务：文字页面', ['06_text_page/app.py', '06_text_page/static/index.html']),
],
('MP3','12'): [
  ('知识点：内置图标', ['01_icon_library/app.py']),
  ('知识点：网页画板', ['02_web_control/app.py', '02_web_control/static/index.html']),
  ('编程任务：保存我的图标', ['03_my_icon/app.py', '03_my_icon/static/index.html']),
  ('知识点：把三样凑到一页', ['04_dashboard/app.py', '04_dashboard/static/index.html']),
],
}


def strip_header(L):
    """去掉文件顶部的注释头（# ...）与空行——顶部注释不搬进课件。"""
    i = 0
    while i < len(L):
        s = L[i].strip()
        if s == '' or s.startswith('#'):
            i += 1
        else:
            break
    return L[i:]


def _short(t, n=26):
    """截到 n 字以内，优先在标点/括号处断开（空格仅作备用）。"""
    t = t.strip().replace(',', '，')
    if len(t) <= n:
        return t
    cut = max(t.rfind(s, 0, n) for s in '，,。；;：:、（(【')
    if cut <= 6:
        cut = t.rfind(' ', 0, n)
    t = t[:cut] if cut > 6 else t[:n]
    return t.rstrip('，,。；;：:、（(【 ')


def script_title(fp, rel, atitle=''):
    """代码页标题：优先脚本头注释的“功能描述”，否则用所在环节名，最后才是文件名。"""
    try:
        head = io.open(fp, encoding='utf-8', errors='ignore').read().split('\n')[:6]
    except Exception:
        head = []
    for l in head:
        m = re.match(r'#\s*(?:功能描述|功能)\s*[:：]\s*(.+)', l.strip())
        if m:
            return _short(re.sub(r'第\s*\d+\s*步[：:\s]*', '', m.group(1)))
    t = re.sub(r'^(知识点|应用|练习|实验\s*\d*|编程任务\s*\d*|第[一二三四五六七八九十]+步)\s*[：:]\s*',
               '', atitle).strip()
    if t:
        return _short(t)
    stem = os.path.splitext(os.path.basename(rel))[0]
    return _short(re.sub(r'^\d+[_-]', '', stem))


def readlines(p):
    with io.open(p, encoding='utf-8', errors='ignore') as f:
        L = f.read().replace('\r\n', '\n').split('\n')
    L = [x.rstrip() for x in L]
    while L and not L[0].strip():
        L.pop(0)
    while L and not L[-1].strip():
        L.pop()
    return strip_header(L)


def _is_block_start(s):
    return bool(re.match(r'^\s*(def |class |async def |@|while |for |if |try:|with )', s)) \
        or bool(re.match(r'^\s*#\s*[─=#*—-]{2,}', s))


def split_lines(lines, maxlen=20):
    """按 ≤maxlen 行切分；优先在逻辑边界（空行 / def / 注释分段）断开，并尽量均衡。"""
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
    g = [x for x in glob.glob(os.path.join(ROOT, PREF[course] + num + '*')) if x.endswith('.md')]
    return g[0]


def place(course, num):
    path = md_path(course, num)
    t = io.open(path, encoding='utf-8').read()
    parts = re.split(r'(?m)^### (?=第\s*\d+\s*页)', t)
    head, body = parts[0], parts[1:]

    # 1) 删掉旧的任务代码页、清单页，以及旧的"代码回顾"页（稍后按 20 行重建）
    body = [pg for pg in body
            if not re.match(r'^第\s*\d+\s*页\s*·\s*代码：', pg.split('\n', 1)[0])
            and '任务代码清单' not in pg.split('\n', 1)[0]
            and '代码回顾：' not in pg.split('\n', 1)[0]]

    # 1.5) 重建"代码回顾"页（紧跟复习页）
    rf, rt = ic.REVIEW[(course, num)]
    rb = code_pages('代码回顾：' + rt.replace('上一讲：', ''),
                    readlines(os.path.join(ROOT, rf)))
    ri = 1
    for i, pg in enumerate(body):
        if '复习' in pg.split('\n', 1)[0]:
            ri = i + 1
            break
    body[ri:ri] = ['第 _ 页 · ' + tt + '\n```\n' + cc + '\n```\n' for tt, cc in rb]

    # 2) 按锚点插入
    added = 0
    shown = []          # 本讲已出现的脚本（用于“与上一步基本相同”判断）
    for anchor, scripts in M[(course, num)]:
        idx = None
        for i, pg in enumerate(body):
            if anchor in pg.split('\n', 1)[0]:
                idx = i
        if idx is None:
            print('  !! 锚点未找到:', course, num, anchor)
            continue
        atitle = re.sub(r'^第\s*\d+\s*页\s*·\s*', '', body[idx].split('\n', 1)[0]).strip()
        pages = []      # (标题, 正文, 页脚)
        for rel in scripts:
            fp = os.path.join(ROOT, course, 'source_codes', DIRS[(course, num)], rel)
            lines = readlines(fp)
            ttl = '代码：' + script_title(fp, rel, atitle)
            foot = '页脚：%s ｜ %s' % (atitle, rel)
            dup = None
            for prel, plines in shown:
                sm = difflib.SequenceMatcher(None, plines, lines)
                r = sm.ratio()
                add = sum(b2 - b1 for tag, a1, a2, b1, b2 in sm.get_opcodes()
                          if tag in ('insert', 'replace'))
                if r >= SIM and add <= ADD_MAX:
                    dup = (prel, add); break
            if dup:
                pages.append((ttl, '- 答：本步代码与《%s》**基本相同**'
                                   '（仅新增/修改 %d 行），不再重复展示。' % (dup[0], dup[1]), foot))
            else:
                for cc in split_lines(lines):
                    pages.append((ttl, '```\n%s\n```' % '\n'.join(cc), foot))
            shown.append((rel, lines))
        tot = len(pages)
        ins = []
        for i, (ttl, bd, ft) in enumerate(pages, 1):
            suffix = '' if tot <= 1 else '（%d/%d）' % (i, tot)
            ins.append('第 _ 页 · %s%s\n%s\n%s\n' % (ttl, suffix, bd, ft))
            added += 1
        body[idx + 1:idx + 1] = ins

    out = [head.rstrip('\n')]
    for i, pg in enumerate(body, 1):
        first, _, rest = pg.partition('\n')
        first = re.sub(r'^第\s*[_\d]+\s*页', '第 %d 页' % i, first.strip())
        out.append('### ' + first)
        if rest.strip():
            out.append(rest.strip('\n'))
    io.open(path, 'w', encoding='utf-8').write('\n\n'.join(out).rstrip('\n') + '\n')
    return added, len(body)


def source_files(course, num):
    d = os.path.join(ROOT, course, 'source_codes', DIRS[(course, num)])
    res = []
    for root, _, fs in os.walk(d):
        for fn in sorted(fs):
            if not fn.endswith(('.py', '.html', '.js', '.css')):
                continue
            if any(v in fn for v in VENDOR):
                continue
            rel = os.path.relpath(os.path.join(root, fn), d)
            res.append('/'.join(rel.split(os.sep)))
    return sorted(res)


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else None
    for (c, n) in sorted(DIRS):
        if which and c != which:
            continue
        mapped = set()
        for _, ss in M[(c, n)]:
            mapped |= set(ss)
        real = set(source_files(c, n))
        missing = real - mapped
        if missing:
            print('  ~~ 未安排位置的脚本:', c, n, sorted(missing))
        add, tot = place(c, n)
        print('%s-%s  插入 %d 个代码页  (现 %d 页)' % (c, n, add, tot))
