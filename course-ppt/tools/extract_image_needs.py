# -*- coding: utf-8 -*-
"""汇总教案与 PPT 里的配图需求 -> 每讲一份 MD（描述 / 画面细节 / 关键词 / 功能 / 出处）
   并在根目录生成 README.md（给"图片生成 AI"的完整课程背景）。
"""
import io, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.environ.get('COURSE_PROJ') or HERE
OUT = os.environ.get('COURSE_IMG_OUT') or os.path.join(os.path.dirname(PROJ), 'images')
os.makedirs(OUT, exist_ok=True)

import jieba.posseg as pseg

SPLIT = re.compile(r'[，。、；：（）()【】“”"\'/→+\-—\s]+')
KEEP_FLAG = ('n', 'nr', 'ns', 'nt', 'nz', 'ng', 'vn', 'eng', 'an')
BAD = set(('的 了 着 是 在 与 和 把 被 让 从 到 旁边 中间 上面 下面 里面 外边 一个 一张 一块 '
           '一组 一下 变化 画面 情况 内容 东西 地方 时候 样子 过程 方式 办法 结果 问题 部分 '
           '类似 其余 其中 封面 课程 知识点 应用 练习 实验 编程任务 小结 步骤 标签 环节 页 第').split())
COMPOUND = ['扫地机器人', '人形机器人', '电动窗帘', '智能门锁', '玩具车', '机械臂', '智能音箱',
            '开发板', '传感器', '蜂鸣器', '旋钮', '按键', '按钮', '点阵', '像素', '倒计时',
            '柱状图', '接线图', '示意图', '占空比', '减速电机', '减速箱', '光敏电阻', '土壤湿度',
            '智能花盆', '遥控器', '面包板', '杜邦线', '显示器', '浏览器', '服务器', '局域网']
EN = {'电机': 'motor', '减速箱': 'gearbox', '减速电机': 'geared motor', 'H 桥': 'H-bridge',
      'PWM': 'PWM', '占空比': 'duty cycle', 'OLED': 'OLED', 'WiFi': 'WiFi', 'ESP-NOW': 'ESP-NOW',
      'MAC 地址': 'MAC address', 'LED': 'LED', '按钮': 'button', '旋钮': 'knob', '传感器': 'sensor',
      '土壤': 'soil', '水泵': 'water pump', '蜂鸣器': 'buzzer', '麦克风': 'microphone',
      '扬声器': 'speaker', '光敏电阻': 'photoresistor', '点阵': 'LED matrix', '像素': 'pixel',
      '网页': 'webpage', '服务器': 'server', '浏览器': 'browser', '手机': 'phone',
      '开发板': 'dev board', '无线': 'wireless', '串口': 'UART serial', '屏幕': 'screen',
      '时钟': 'clock', '倒计时': 'countdown', '柱状图': 'bar chart', '花盆': 'flower pot',
      '机器人': 'robot', '小车': 'robot car', '遥控器': 'remote controller', '太阳': 'sun',
      '心形': 'heart', '字节': 'byte', '二进制': 'binary', '开关': 'switch', '电源': 'power',
      '接线': 'wiring', '杜邦线': 'jumper wire', '面包板': 'breadboard'}

# ── 硬件外观知识库：命中词 → 画面补充（供 AI 生成写实图时参考） ──
KB = [
 ('NovaStar', '深色 PCB 的 ESP32 开发板：Type-C 供电口、XH 电池接口、一排黑色 GPIO 排针（丝印白色 GPIO 编号）、板载双路 H 桥芯片、两颗板载 LED'),
 ('开发板', '约名片大小的深色 PCB 开发板，四角圆形安装孔，边缘一排排针'),
 ('N20', 'N20 减速电机：银色长条金属减速箱 + 黄白色塑料电机本体，侧出 D 形轴，两根引线（红黑），整体约 12×10×20mm'),
 ('减速箱', '银色金属齿轮箱，外壳上有齿轮与轴，与电机本体相连'),
 ('H 桥', '四个开关 S1~S4 围成字母 H 形，中间横向接直流电机，上下两端分别接正负电源，箭头标出电流方向'),
 ('双路 H 桥', '黑色贴片功率芯片，带散热焊盘，周围有电容与走线'),
 ('拨码开关', '板上红色小拨码开关，并排四个，白色小拨杆'),
 ('PWM', '方波示意图：高电平与低电平交替，标注占空比百分比，横轴为时间'),
 ('SSD1306', '0.96 寸 OLED：黑色小方屏，白/蓝自发光文字，下方 4 个针脚 VCC/GND/SCL/SDA，蓝色小板'),
 ('OLED', '0.96 寸黑色小方屏，自发光白/蓝文字，四周蓝色 PCB 边框'),
 ('I2C', '两条总线 SDA（数据）与 SCL（时钟）并行，一条线上挂多个从设备，每个标一个地址'),
 ('SU03T', '蓝色小号语音识别模块：板上有麦克风拾音孔、喇叭接口、排针，丝印 SU03T'),
 ('VTX316', '语音合成小板（蓝色 PCB），接一个 3W 黑色小喇叭'),
 ('DHT11', '蓝色栅格外壳的温湿度传感器，四个针脚，旁边一个 10k 上拉电阻'),
 ('土壤', '电容式土壤湿度探头：黑色细长条，两根平行电极，尾部接线端子，插在土里'),
 ('光敏电阻', '小圆片光敏电阻（表面蛇形纹路），装在小块比较器 PCB 上，3 个针脚'),
 ('水泵', '微型潜水泵：蓝色小圆柱泵体 + 透明硅胶软管，两根引线'),
 ('蜂鸣器', '黑色圆柱形蜂鸣器模块，顶部一个小出音孔'),
 ('按键', '方形轻触按键模块，带黑色/白色按键帽，3 个针脚'),
 ('按钮', '方形轻触按键模块，带按键帽，3 个针脚'),
 ('旋钮', '蓝黑色电位器模块，带可旋的旋钮帽，3 个针脚'),
 ('WS2812', '8×8 黑色方形灯板，64 颗贴片 RGB LED 均匀排布，3 根排针标着 DIN / VCC / GND'),
 ('RGB 灯', '单个 RGB LED 模块，透明灯珠，3 或 4 个针脚'),
 ('锂电池', '9V 方块充电锂电池 + 电池扣，接 XH 插头'),
 ('Type-C', '开发板上的 USB Type-C 供电口'),
 ('杜邦线', '彩色杜邦线（红黑黄），一端插针一端插孔'),
 ('面包板', '白色面包板，孔位整齐，插入彩色跳线'),
 ('WiFi', '无线信号波纹图标，从开发板连向无线路由器'),
 ('ESP-NOW', '两块开发板之间一条无线信号线，不经过路由器，标注双向箭头'),
 ('ESP32', 'ESP32 开发板主板，带金属屏蔽罩的无线模块'),
 ('机器人', 'NovaBot 桌面机器人：球形或方形 3D 打印外壳，一只 OLED 眼睛（可显示表情），底部两个 N20 主动轮 + 一个万向轮'),
 ('小车', '双轮差速小车底盘：两个 N20 主动轮 + 一个万向轮，上方一块开发板'),
 ('遥控器', '定制遥控器：外壳上两个大按键 + 一块开发板 + 电池仓'),
 ('服务器', '一台一直开着的机器（可用开发板或机柜表示），持续响应请求'),
 ('浏览器', '手机/电脑浏览器窗口，地址栏 + 网页内容'),
 ('柱状图', '柱状图：横轴日期、纵轴番茄个数，柱子由矮到高'),
 ('心形', '由像素点拼成的红色心形图案'),
 ('时钟', '指针时钟表盘：圆形表盘 + 时针/分针/秒针 + 刻度'),
]

STYLE = {
 '封面主图': '深色科技感背景（深灰/深蓝），主体居中偏右，左侧留出标题空间；写实渲染或精致 3D 风格；16:9。',
 '引入场景图': '生活化真实场景照片风，暖色调，景深虚化背景；16:9。',
 '原理 / 结构示意图': '纯白或浅灰底，扁平化矢量风格，部件分解清晰，中文引线标注，粗细统一的线条；16:9。',
 '实物 / 应用图': '写实产品图，浅灰或白色无缝背景，柔和阴影，45° 俯视；16:9。',
 '实验操作图': '桌面俯拍（top-down），开发板 + 连线 + 模块摆放整齐，可带人手；16:9。',
 '动手练习图': '桌面俯拍，突出学生正在操作的开发板与模块；16:9。',
 '任务效果 / 界面图': '设备实拍或网页界面截图，界面简洁、留出数据区，中文文案；16:9。',
 '步骤示意图': '白底扁平矢量，分 3~4 步从左到右排列，每步一个中文小标签；16:9。',
 '原因解释图': '白底矢量，用箭头/对比表现因果；16:9。',
 '对比图': '左右分屏对比，两侧配中文小标题；16:9。',
 '总结图': '白底，几个圆形图标横向排列，配中文短标签；16:9。',
 '配图': '白底扁平矢量或实拍，主体清晰、留白充足；16:9。',
}
FUNC = [('封面', '封面主图'), ('认识', '实物 / 结构图'), ('什么是', '原理 / 结构示意图'),
        ('为什么', '原因解释图'), ('对比', '对比图'), ('怎么', '步骤示意图'),
        ('应用', '实物 / 应用图'), ('知识点', '原理 / 结构示意图'), ('实验', '实验操作图'),
        ('练习', '动手练习图'), ('编程任务', '任务效果 / 界面图'), ('第一步', '步骤示意图'),
        ('第二步', '步骤示意图'), ('第三步', '步骤示意图'), ('小结', '总结图')]


def func_of(title):
    for k, v in FUNC:
        if k in title:
            return v
    return '配图'


def _extract(text):
    keep = []
    for w, flag in pseg.cut(text):
        w = w.strip()
        if not w or w in BAD:
            continue
        if flag in KEEP_FLAG and len(w) >= 2:
            keep.append(w)
        elif re.fullmatch(r'[A-Za-z0-9×xX./+\-]+', w) and len(w) >= 2:
            keep.append(w)
    return keep


def keywords(desc, topic, title=''):
    keep = _extract(desc)
    for c in COMPOUND:
        if c in desc:
            keep.insert(0, c)
    keep += _extract(re.sub(r'^第\s*\d+\s*页\s*·\s*', '', title))
    ens = [v for k, v in EN.items() if k in desc or k in topic]
    out = [topic] + keep[:10] + ens[:6]
    r = []
    for x in out:
        if x and x not in r:
            r.append(x)
    return '、'.join(r)


def detail(desc, func):
    """在描述基础上补足画面细节（供 AI 生图）。"""
    parts = [desc.rstrip('。') + '。']
    hits = []
    for k, v in KB:
        if k in desc and v not in hits:
            hits.append(v)
    # 命中过多时，只保留前两条最相关的
    hits = hits[:2]
    if hits:
        parts.append('关键外观：' + '；'.join(hits) + '。')
    parts.append(STYLE.get(func, STYLE['配图']))
    parts.append('中文标注（如需文字）；画面干净、无 logo、无英文乱码、无水印。')
    return ''.join(parts)


def ppt_entries(path):
    t = io.open(path, encoding='utf-8').read()
    res = []
    for p in re.split(r'(?m)^### (?=第\s*\d+\s*页)', t)[1:]:
        title = p.split('\n', 1)[0].strip()
        m = re.search(r'第\s*(\d+)\s*页', title)
        ttl = re.sub(r'^第\s*\d+\s*页\s*·\s*', '', title)
        for l in p.split('\n'):
            s = l.strip()
            if s.startswith('- 图：') or s.startswith('图：'):
                res.append((int(m.group(1)) if m else 0, ttl, s.split('图：', 1)[1].strip()))
    return res


def plan_entries(path):
    t = io.open(path, encoding='utf-8').read()
    res = []
    sec = ''
    for l in t.split('\n'):
        s = l.strip()
        if s.startswith('#'):
            sec = re.sub(r'^#+\s*', '', s)
        m = re.search(r'(?:建议配|图片占位|建议画)(.*?)(?:\*|\]|$)', s)
        if ('📝' in s or '🖼' in s) and m:
            d = m.group(1).strip().lstrip('一张').lstrip('：:').strip()
            res.append((sec, d))
    return res


def md_for(course, num):
    g = [x for x in glob.glob(os.path.join(PROJ, course, 'PPTs', course + '_' + num + '*')) if x.endswith('.md')]
    ppt = g[0]
    title = io.open(ppt, encoding='utf-8').readline().lstrip('# ').strip()
    topic = title.split('·')[-1].strip()
    pe = ppt_entries(ppt)
    lp = glob.glob(os.path.join(PROJ, course, 'lesson_plans', course + '_' + num + '*'))
    le = plan_entries(lp[0]) if lp else []

    L = ['# %s —— 图片素材需求' % title, '',
         '> 本讲共 **%d** 张（PPT %d + 教案补充 %d）。' % (len(pe) + len(le), len(pe), len(le)),
         '> **描述**＝画面内容；**画面细节**＝可直接作为生图提示；**关键词**＝检索用；'
         '**功能**＝该页作用；**出处**＝课件位置。',
         '> 全局背景见同目录 [README.md](README.md)。', '', '---', '']
    n = 0
    for pg, ttl, d in pe:
        n += 1
        f = func_of(ttl)
        L += ['## %d. %s' % (n, d[:44]), '',
              '- **描述**：%s' % d,
              '- **画面细节**：%s' % detail(d, f),
              '- **关键词**：%s' % keywords(d, topic, ttl),
              '- **功能**：%s（%s）' % (f, ttl),
              '- **出处**：PPT 第 %d 页 · %s' % (pg, ttl), '']
    if le:
        L += ['---', '', '## 教案补充建议', '']
        for sec, d in le:
            n += 1
            f = func_of(sec)
            L += ['### %d. %s' % (n, d[:44]), '',
                  '- **描述**：%s' % d,
                  '- **画面细节**：%s' % detail(d, f),
                  '- **关键词**：%s' % keywords(d, topic, sec),
                  '- **功能**：教案标注的配图建议（%s）' % sec,
                  '- **出处**：教案 · %s' % sec, '']
    return '\n'.join(L).rstrip() + '\n', topic, len(pe) + len(le)


# ───────────────────────── README（给生图 AI 的完整背景） ─────────────────────────
README = '''# 课件配图素材需求 · 总览（MP2 / MP3）

> **给"图片生成 AI"的说明**：本目录是「斯坦星球 MicroPython 中级课程（MP2）」与
> 「MicroPython Web 应用课程（MP3）」两门课全部课件配图的需求清单。
> 请先读完本文件建立背景，再逐个读取 `MP2_XX_*.md` / `MP3_XX_*.md`：
> 每个文件里按条目给出 **描述 / 画面细节 / 关键词 / 功能 / 出处**，
> 其中「**画面细节**」可直接当作生成提示词使用。

---

## 一、这是什么课

- **产品线**：斯坦星球（Stemstar）少儿编程课程体系中的硬件 + 编程阶段。
- **三个阶段**：
  - **MP1**：硬件基础（LED、按键、蜂鸣器、电位器、光敏、温湿度等单个模块的认知）。
  - **MP2**：**机器人进阶**。用一块 **NovaStar ESP32 开发板**把电机、屏幕、语音、网络、AI 串起来，最终做出桌面机器人 **NovaBot**。
  - **MP3**：**物联网全栈**。把同一块开发板变成一台 **Web 服务器**，用网页去控制与查看硬件，完成番茄时钟、智能花盆、像素矩阵三个作品。
- **教学理念**：「**先原理认知，后工程抽象**」——先手写底层（H 桥、PWM、位图），再引入封装好的类（`Motor`、`DiffDriveCar`、`SSD1306`）。配图要能支撑"从原理到应用"的递进。
- **主角硬件**：`NovaStar` 开发板（ESP32 + 板载双 H 桥），出厂烧录 `NovaMP` 固件（16 个预置驱动模块）。
- **主角机器人**：`NovaBot` —— 由两块板组成：
  - **device1（大脑）**：负责「听（SU03T 语音识别）→ 想（大模型 ChatBot）→ 说（VTX316 语音合成）」；
  - **device2（小脑）**：负责「动（两个 N20 电机）→ 表情（OLED + NovaEyes 眼睛）」；
  - 两块板之间用 **ESP-NOW** 无线通信，靠一张"命令暗号表"对齐。

---

## 二、硬件外观（生成写实图时的重要参考）

| 物料 | 外观描述 | 用途 |
| --- | --- | --- |
| NovaStar 开发板 | 深色 PCB 的 ESP32 板：Type-C 口、XH 电池接口、一排 GPIO 排针（丝印 GPIO 编号）、板载双路 H 桥、两颗板载 LED | 所有课程的主控 |
| N20 减速电机 | 银色金属减速箱 + 黄白色塑料电机本体，**侧出 D 形轴**，两根引线（红黑），约 12×10×20mm | 驱动小车 / 机器人 |
| H 桥模块 | 四个开关 S1~S4 围成字母 H，中间接直流电机，两端接电源 | 让电机能正反转 |
| 0.96 寸 OLED（SSD1306） | 黑色小方屏，自发光白/蓝文字，下方 4 针（VCC/GND/SCL/SDA） | 显示表情 / 数据 / 时钟 |
| SU03T | 蓝色小号语音识别模块，带麦克风孔、喇叭接口、排针 | 听人说话（离线命令词） |
| VTX316 | 语音合成小板 + 一个 3W 黑色小喇叭 | 让机器人说话（TTS） |
| DHT11 | 蓝色栅格外壳的温湿度传感器，四针 | 读环境温湿度 |
| 电容式土壤湿度探头 | 黑色细长条，两根平行电极，尾部接线端子 | 判土壤干湿 |
| 光敏电阻模块 | 小圆片光敏电阻 + 比较器小板，3 针 | 测光照 |
| 有源蜂鸣器 | 黑色圆柱形，顶部一个小出音孔 | 到点"响一声" |
| 轻触按键模块 | 方形小按键（带按键帽），3 针 | 开始/暂停/重置 |
| 旋钮（电位器）模块 | 蓝黑色电位器 + 可旋旋钮帽，3 针 | 调速度 |
| 微型潜水泵 | 蓝色小圆柱泵体 + 透明硅胶软管 | 自动浇水 |
| 8×8 WS2812B 矩阵 | 黑色方形灯板，64 颗贴片 RGB LED，3 针（DIN/VCC/GND） | 像素图案 / 文字 / 动画 |
| 9V 锂电池 + 电池扣 | 方块充电电池，接 XH 插头 | 给电机/机器人独立供电 |
| 3D 打印件 | 电池仓、夜灯壳、气象站支架、机器人外壳 | 作品外观 |

---

## 三、MP2 十二讲（机器人进阶）

| 讲 | 主题 | 关键知识点 | 单元产出 |
| --- | --- | --- | --- |
| 01 | 电机转动 | N20 减速原理、H 桥正反转、PWM 调速、`Motor` 类 | — |
| 02 | NovaBot | 双轮差速（v_L/v_R）、六种基本动作、`DiffDriveCar` 封装 | — |
| 03 | 无线遥控小车 | ESP-NOW 广播/点对点、MAC 地址、信道 | **无线遥控车** |
| 04 | 网络连接 | WiFi(STA/AP)、NTP 对时、boot.py、requests、WeatherStation | — |
| 05 | Function Call | 大语言模型、API Key、JSON、函数调用两轮流程 | — |
| 06 | 语音识别 | 串口 UART、SU03T 命令词、指令码 | **语音夜灯** |
| 07 | OLED 屏幕 | I2C、SSD1306、坐标系与缓冲区、指针时钟 | — |
| 08 | 位图与动画 | 矢量图/位图、二进制与十六进制、framebuf、NAF 动画 | — |
| 09 | 桌面气象站 | TTS 同步/异步、VTX316、天气图标、同屏刷新 | **桌面气象站** |
| 10 | NovaBot 制作 1 | 引脚冲突、两块板分工、大脑/小脑、device1 助手 | — |
| 11 | NovaBot 制作 2 | 表情系统、NovaEyes（11 种表情）、动作+表情合一 | — |
| 12 | NovaBot 制作 3 | ESP-NOW 联调、状态机（busy/idle）、表演编排 | **NovaBot 机器人** |

---

## 四、MP3 十二讲（Web / IoT 全栈）

| 讲 | 主题 | 关键知识点 | 单元产出 |
| --- | --- | --- | --- |
| 01 | NovaServer 基础 | 服务器概念、HTTP 请求/响应、状态码、路由、RESTful 四方法 | — |
| 02 | 网页入门 | HTML 骨架与标签、CSS、nova-style、send_file、static_dir | — |
| 03 | 前端调 API | `<a>`/`<form>` 发请求、JavaScript、fetch、nova-js、响应式 | **全栈基础（LED 小灯）** |
| 04 | 番茄时钟基础 | 常量/状态分层、ticks_ms 非阻塞计时、render、主循环 | — |
| 05 | 番茄时钟配置页 | `@app.task` 周期任务、CRUD/REST、nova.api、PUT 热更新 | — |
| 06 | 番茄时钟统计 | NTP 对时 + boot.py、nova-db 持久化、nova-chart 图表 | **番茄时钟** |
| 07 | 智能花盆基础 | 模拟信号与 ADC、DHT11 单总线、传感器融合、水泵冷却 | — |
| 08 | 智能花盆 Web 监控 | 面向对象建模、RESTful 资源化、nova.poll 轮询 | — |
| 09 | 智能浇水策略 | 常量→配置、参数热更新、浇水记录、仪表盘 | **智能花盆** |
| 10 | 像素矩阵基础 | WS2812 级联、一维↔二维坐标映射（Z/S 排布）、扫描动画 | — |
| 11 | 像素矩阵数字与文字 | RGBMatrix 驱动、show_number/show_text/scroll_text、同步与异步 | — |
| 12 | 像素矩阵图标与综合 | 内置图标、网页画板、nova-db 存图、三合一控制台 | **像素矩阵屏** |

---

## 五、视觉风格规范（所有配图统一遵守）

- **画风**：写实产品图 / 扁平化矢量示意图 / 真实场景照片 / UI 截图，四类各司其职；**不要**卡通化到失真。
- **比例**：统一 **16:9**（PPT 为 16:9 版面）；图标类可为 **1:1**。
- **底色**：示意图用**纯白或浅灰**；封面用**深灰/深蓝**科技感底；场景图用真实环境。
- **颜色**：主色偏科技感（蓝 `#1D4ED8`、青、深灰 `#222A35`）；强调色用橙色/红色；避免高饱和刺眼配色。
- **文字**：需要标注时**一律中文**，字号大、可读；**不要**英文乱码、不要水印、不要无关 logo。
- **主体**：单主体、居中或按构图三分法；背景干净、留白充足。
- **禁止**：真实品牌 logo、人脸特写、恐怖/血腥元素、错误接线（正负极、TX/RX 交叉等要正确）。

---

## 六、图片类型 → 生成要点

| 功能 | 生成要点 |
| --- | --- |
| 封面主图 | 深色科技底，主体居中偏右，左侧留标题空间 |
| 引入场景图 | 生活化真实照片，暖色，景深虚化 |
| 原理 / 结构示意图 | 白底扁平矢量，部件分解、中文引线标注 |
| 实物 / 应用图 | 写实产品图，浅灰无缝底，柔和阴影，45° 俯视 |
| 实验 / 练习图 | 桌面俯拍，开发板+模块摆放整齐，可带人手 |
| 任务效果 / 界面图 | 设备实拍或网页界面，界面简洁、中文文案 |
| 步骤示意图 | 白底矢量，3~4 步从左到右，每步小标签 |
| 对比图 | 左右分屏，两侧中文小标题 |
| 数据图 | 柱状/折线图，横轴日期、纵轴数量，配色克制 |
| 总结图 | 白底 + 几个圆形图标横向排列 + 中文短标签 |

---

## 七、图片清单索引

| 讲 | 主题 | 张数 | 文档 |
| --- | --- | --- | --- |
%ROWS%

> 合计 **%TOTAL%** 张。

---

## 八、术语表（中 → 英，供检索图库）

| 中文 | 英文 |
| --- | --- |
| 开发板 | development board |
| 减速电机 | geared motor |
| H 桥 | H-bridge |
| 脉宽调制 / 占空比 | PWM / duty cycle |
| 差速转向 | differential steering |
| 无线通信 | wireless communication |
| 语音识别 / 语音合成 | speech recognition / text-to-speech (TTS) |
| 屏幕 / 点阵 | OLED screen / LED matrix |
| 位图 / 像素 | bitmap / pixel |
| 传感器 | sensor |
| 土壤湿度 | soil moisture |
| 水泵 | water pump |
| 蜂鸣器 | buzzer |
| 按键 / 旋钮 | button / knob |
| 网页 / 浏览器 / 服务器 | webpage / browser / server |
| 请求 / 响应 | request / response |
| 持久化存储 | persistent storage |
| 柱状图 / 折线图 | bar chart / line chart |

---

## 九、产出要求（建议）

- **格式**：PNG（透明背景优先）或 JPG；单张长边 ≥ 1920px。
- **命名**：`MPx_XX_<序号>_<短名>.png`，例如 `MP2_01_01_novabot-chassis.png`。
- **目录**：按讲分文件夹（`MP2_01/`、`MP2_02/` …）便于回填。
- **回填**：课件里每张图都标了"**出处**"（PPT 第 N 页 · 页面标题），拿到图后可按此自动插回对应幻灯片。
'''


def main():
    index = []
    for course in ['MP2', 'MP3']:
        for num in ['%02d' % i for i in range(1, 13)]:
            md, topic, n = md_for(course, num)
            name = '%s_%s_%s.md' % (course, num, topic.replace('/', '_'))
            io.open(os.path.join(OUT, name), 'w', encoding='utf-8').write(md)
            index.append((course, num, topic, n, name))
            print('%s  %2d 张 -> %s' % (course + '-' + num, n, name))
    rows = '\n'.join('| %s-%s | %s | %d | `%s` |' % r for r in index)
    io.open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8').write(
        README.replace('%ROWS%', rows).replace('%TOTAL%', str(sum(x[3] for x in index))))
    print('README.md 已生成，合计', sum(x[3] for x in index), '张')


if __name__ == '__main__':
    main()
