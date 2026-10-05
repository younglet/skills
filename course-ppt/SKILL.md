---
name: course-ppt
description: Build and maintain "textbook-style" course slide decks (PPT) from Markdown sources — page structure, module-page format, code placement, and a python-pptx build pipeline. Covers concept-page-first structure, per-page code limit (≤20 lines) with logic-aware splitting, code attached to the matching lesson step, review + code-review pages, no meta-narration, no emoji. Use when generating, editing, reviewing, or rebuilding course PPT/课件 (e.g. MicroPython MP1/MP2/MP3), or when writing/formatting PPT source Markdown.
---

# Course PPT 生成（教材式课件）

把 Markdown 写的"教材式"讲稿编译成 PPT，并保证**排版统一、代码规范、结构一致**。

## 何时用

- 新增/修改某讲课件（改 `MPx_XX_*.md` 后重新生成 `.pptx`）。
- 把课程代码（`source_codes/`）自动贴进课件，并放到**对应课堂环节旁边**。
- 检查课件是否违反规范（emoji、元叙述、代码行数、集中堆放等）。
- 换一门课，复用这套流程与工具。

## 快速开始

1. 确认项目结构（详见 [reference/规范细则.md](reference/规范细则.md) 第一节）：

   ```
   <项目根>/
   ├── 模板.pptx           # 16:9 母版：1_自定义版式=封面、3_自定义版式=内容
   ├── build_ppt.py  inject_codes.py  place_codes.py
   └── <课程>/PPTs/MPx_XX_*.md          # PPT 源（唯一手改对象）
       <课程>/source_codes/…            # 配套代码
   ```

2. 把 [tools/](tools/) 下的三个脚本复制到项目根目录（若尚未有）。
3. 改 PPT 源 md →（如需）`python place_codes.py` → `python build_ppt.py`。

## 核心规则（务必遵守）

| # | 规则 |
| --- | --- |
| 1 | **一页只讲一件事**；关键概念先有"知识点介绍页"，再讲原理/特点/应用 |
| 2 | **不要 emoji**；**不要面向老师的元叙述**（"本节几个脚本""下面逐个讲""上课前……"） |
| 3 | **每页代码 ≤ 20 行**；超出自动分页，**按逻辑断点切、兼顾均衡，逻辑优先于均衡** |
| 4 | **顶部注释头（`# 文件名:` 等）不带进课件** |
| 5 | **代码紧跟对应环节**，不集中在讲末；**没有"代码列表"独立页** |
| 5b | **步骤代码若与前面某一步基本相同（相似≥85% 且改动≤6 行）→ 不重复贴代码**，改为一页说明"本步与《xx》基本相同（仅新增 N 行），不再重复展示" |
| 5c | 代码页**标题只说功能（取脚本头注释的"功能描述"），不出现第几步**；**页脚用微软雅黑 10pt 灰色**标注"对应环节 ｜ 源文件" |
| 6 | 每讲固定含：封面 → **复习（问答成对）** → **代码回顾（上一讲核心脚本）** → 课程引入 → 知识点… → 模块页 → 编程任务… → 小结 |
| 7 | **模块页四页格式**：介绍+引脚 / 初始化参数+导入实例 / 核心属性或方法 / 使用示例 |
| 8 | 正文微软雅黑、无填充无边框；只有封面大标题白色；动画只加解答性内容 |
| 9 | 页面文字不以标点起句（设置悬挂标点） |

## 三个脚本

| 脚本 | 作用 | 关键配置 |
| --- | --- | --- |
| `build_ppt.py` | 把 `<课程>/PPTs/*.md` 编译成 `MPx_PPT.pptx`（分节、表格、代码、动画） | `模板.pptx`、字号/版式常量 |
| `inject_codes.py` | **首次**把 `source_codes` 全部脚本贴进 PPT 源（复习/代码回顾/任务代码） | `REVIEW`（代码回顾选哪个脚本）、`DIRS` |
| `place_codes.py` | 把代码页**贴到对应环节旁边**（清旧、按 ≤20 行重排、去顶部注释） | `M`（锚点页子串 → 脚本列表） |
| `extract_image_needs.py` | 汇总教案与 PPT 里的配图需求，输出每讲一份带**描述/关键词/功能/出处**的 MD | `PROJ`（项目路径）、`OUT`（输出目录） |
| `attach_images.py` | 把生成好的图片按“出处”绑定回 PPT 源（`图：images:<相对路径> \| <描述>`） | `PROJ`、`IMG`（图片根目录） |
| `rebuild_review.py` | 按**教案的「复习环节」**重建复习页：**问题页 + 答案页**（按篇幅自动分页） | `PROJ`、`CHARS_PER_LINE`、`Q_CAP/A_CAP` |

> 顺序：`inject_codes.py`（仅首次）→ `place_codes.py` → `build_ppt.py`。
> `place_codes.py` 可反复运行（幂等：先删旧代码页再重插）。

## 配图需求整理

课件里的图片有两处来源，脚本会把它们汇总成每讲一份 MD（含描述 / 关键词 / 功能 / 出处）：

- **PPT 源**：页面里的 `图：……` 行；
- **教案**：`> 📝 *此处建议配……*` / `🖼️ [图片占位:……]` 标注。

```bash
python extract_image_needs.py      # 默认输出到 桌面/images/，每讲一个 md + README 索引
```

关键词自动抽取（jieba 分词 + 领域术语表），已过滤“封面/知识点/步骤”等阶段词；
需要先 `python -m pip install jieba`。

## 复习环节（问答成对）

- **内容来源**：教案 `## 复习环节` → `### 知识点` 里的「**问题** + 答案」（脚本自动解析，勿手抄）。
- **成对呈现**：`问 → 答（紧贴） → 间隔行`，再下一组；组间留白，翻页即成对出现。
- **答案精简到一行**（≤48 字）：整句 > 子句 > 括号外硬截，**不会把 `foo()` / （…） 切一半**。
- 复习页**保持原序**：问题静态显示，**答案用一个「段落级淡入」动画逐条出现**（点一下出一条）；字号 **12pt**。
- 内容多时自动续页 `（1/2）`；间隔行用源里的 `<<gap>>`（渲染为空行 + 18pt 段后距）。

```bash
python rebuild_review.py     # 会覆盖各讲原有复习页；教案没有复习环节的讲（如 MP2-01）跳过
```

## 配图回填（图片 → PPT）

1. 需求清单：`python extract_image_needs.py` → 每讲一份 MD（描述/画面细节/关键词/功能/出处）。
2. 图片按 `图片根目录/MPx_XX/MPx_XX_NN_slug.png` 存放（NN 与该讲 MD 的序号一致，先 PPT 后教案）。
3. 绑定：`python attach_images.py` —— 把 `图：<描述>` 改为 `图：images:<相对路径> | <描述>`（已含 `images:` 的行会跳过，幂等）。
4. 生成：`python build_ppt.py` —— 解析 `images:` 前缀 → 在 `COURSE_IMG_ROOT`（默认 `../images`）下找图并插入；
   封面图按“覆盖式”铺满整页，内容页图片按比例放进左栏居中，缺失时退回文字占位。

> 图片路径用 `images:` 前缀而非绝对路径，源码可移植；换机器只需改环境变量 `COURSE_IMG_ROOT`。

## 参考

- **[reference/规范细则.md](reference/规范细则.md)** —— 完整细则：目录结构、源文件写法、每讲结构、模块页格式、**代码排版规范（20 行/逻辑分页/去顶部注释/紧贴任务）**、工具流程、改内容指引。
- **[tools/](tools/)** —— 三个脚本的可复用副本。

## 常见坑

- `.pptx` 开在 PowerPoint 里会导致写入失败 → 脚本会另存 `_fixed.pptx`，关掉后再覆盖。
- 代码页过长（>20 行）会严重影响可读性 → 必须分页，且**按逻辑断点**分。
- 代码集中堆在讲末 = 附录化，不符合规范 → 用 `place_codes.py` 的 `M` 把脚本对到各自环节。
- 厂家/库文件（`nova-style*`、`novajs*`、`nova-chart.min*`、`matrix-board.js`）不要贴。
