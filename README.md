# 天青·中国象棋

一个基于 **Python + pygame** 的中国象棋双人对弈程序（人机对战），电脑方采用 **Alpha-Beta 剪枝搜索 + 局面评估**的智能算法。

原项目为平铺式脚本（`chinachess.py` / `botton.py` 等），本版本重构为标准 Python 包结构，修复走法规则与胜负判定 bug，并重写了电脑 AI。

![](https://i.imgs.ovh/2026/08/15/1bd64e0aae4781823e7934f7ba0ba018.jpg)

## 功能特性

- 🎮 玩家执红（下方），电脑执黑（上方），鼠标点击走棋
- 🧠 电脑 AI：Alpha-Beta 剪枝 + 置换表 + 历史启发（迭代加深 + 时间预算，默认 2 秒，界面不冻结）
- ⏪ 悔棋（按钮 / U 键）：撤销最近一个完整回合，支持吃子恢复
- ✅ 完整中国象棋规则：车马炮兵士象将走法、蹩马腿、塞象眼、炮架、过河兵、九宫、飞将、不送将
- 🏁 将军 / 将死 / 困毙判定（显式状态机 PLAYING/AI_THINKING/GAME_OVER）
- 🔬 棋局分析面板（chessai 集成）：按 **H** 或 **F1** 查看 FEN、chessai 将军/将死/飞将状态、AI 推荐走法（自研 AI 计算 + chessai 交叉校验）
- 🎨 木纹棋盘 UI：棋子缩放适配、最近一步标记、将军警报（将子红环 + 红底徽章）、按钮三态交互（悬停/按下/禁用）
- 🔄 重新开始按钮、选中棋子高亮、可走位置提示
- 🔌 引擎接口抽象：`Engine.get_best_move()`，可替换自研 AI 或接外部引擎

### 可选依赖：chessai-python（分析面板增强）

```bash
# 方式一：独立清单安装
pip install -r requirements-optional.txt
# 方式二：与主项目一起（editable 安装）
pip install -e ".[analysis]"
```

已安装时：分析面板显示 FEN、将军/将死/飞将状态（`chessai.game` 规则引擎交叉校验）、AI 推荐走法合法性标记。未安装时游戏正常运行，分析面板显示"chessai 未安装"。集成代码见 `chinese_chess/chessai_bridge.py`。

> 注意：`chessai-python` 是完整应用包，会引入 opencv / fastapi / pywebview 等大量重依赖；仅玩游戏、不需要分析面板时可跳过，游戏功能不受影响。

## 环境要求

- Python 3.8+
- pygame 2.x

## 安装与运行

```bash
pip install -r requirements.txt
python main.py
```

## 操作说明

1. 点击自己的棋子选中（金色高亮），可走位置显示绿色圆点
2. 点击可走位置落子；点击己方其他棋子可改选
3. 电脑思考时状态栏会提示；被将军时显示"将军！"
4. 按 **U** 或点"悔棋"按钮撤销最近一个完整回合（吃子也会恢复）
5. 按 **H** / **F1** 打开/关闭棋局分析面板（FEN、chessai 状态、AI 推荐走法）
6. 右下角"重新开始"按钮随时可重开一局

## 目录结构

```
Python_chinese_chess/
├── main.py                 # 程序入口：python main.py（或 pip 安装后运行 chinese-chess）
├── pyproject.toml          # 项目元数据 / 命令入口 / 可选依赖（pip install -e .）
├── requirements.txt        # 核心依赖（pygame）
├── requirements-optional.txt  # 可选依赖（chessai，分析面板增强）
├── README.md
├── .gitignore
├── chinese_chess/          # 主包
│   ├── __init__.py
│   ├── constants.py        # 常量与图片资源管理
│   ├── fonts.py            # 中文字体管理（候选字体名 + 文件兜底）
│   ├── pieces.py           # 棋子走法规则 + Board 局面（纯逻辑，可单测）
│   ├── board.py            # 棋盘 / 棋子渲染
│   ├── button.py           # 按钮控件
│   ├── ai.py               # Alpha-Beta AI（negamax + 置换表 + 历史启发）
│   ├── zobrist.py          # Zobrist 哈希（置换表局面键）
│   ├── engine.py           # 引擎接口抽象（Engine 协议 + AlphaBetaEngine）
│   ├── chessai_bridge.py   # chessai 集成（FEN / 局面状态 / 走法校验，优雅降级）
│   └── game.py             # 游戏主循环（状态机 + AI 线程 + 渲染）
├── assets/s2/              # 棋子图片（统一小写文件名，跨平台）
├── docs/
│   └── DEVELOPMENT.md      # 架构现状 / 性能优化 / 开发建议
└── tests/                  # 单元测试（不依赖 pygame）
```

## 测试

```bash
python -m unittest discover -s tests -v
```

覆盖：七种棋子走法、吃子、绊脚/塞眼/炮架、过河兵、九宫、飞将、不送将过滤、将死/困毙、AI 吃子与将军。

## AI 设计

- **搜索**：negamax + Alpha-Beta 剪枝 + 迭代加深，走法排序（吃子优先 / MVV-LVA）提升剪枝效率
- **时间控制**：默认 2 秒思考预算，节点级超时检查，保证响应（可调 `DEFAULT_TIME_BUDGET`）
- **评估**：子力价值（车 9、炮 4.5、马 4、士象 2、兵 1）+ 兵过河位置加成 + 马炮中心位置加成 + 被将军罚分
- **合法性**：所有走法生成后模拟执行，过滤"走后己方被将军（含飞将）"的走法
- **终局**：将死判负、困毙判和；无合法走法时对局结束
- **体验**：AI 在后台线程思考，界面不冻结；选中走法与将军状态缓存，渲染无重复搜索

## 性能优化与开发建议

详见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)：架构现状、卡顿优化记录（AI 搜索 4 倍加速、时间预算、线程化）、功能/架构/AI/工程/测试的后续开发建议。

## 变更记录

| 版本 | 说明 |
| --- | --- |
| 2.5.0 | P2 信息与动效：俘虏区（双方被吃棋子小图，自动折行）；回合数显示；AI 思考动态省略号；终局居中半透明横幅 + 大字 |
| 2.4.0 | UI 优化：信息栏布局分区（消除分析面板/按钮重叠）；窗口 900x720；木纹棋盘 + 河界描边艺术字；棋子缩放适配 + 描边；最近一步标记；将军红环 + 红底徽章；按钮三态（悬停/按下/禁用）；悔棋无历史时禁用；修复 GIF 8-bit 缩放崩溃 |
| 2.3.1 | 规范化：新增 pyproject.toml（`pip install -e .` + `chinese-chess` 命令 + 可选依赖声明）；拆分 requirements-optional.txt；统一版本号；更新 README 目录结构；清理废弃常量 |
| 2.3.0 | 状态机化；悔棋（按钮/U 键）；引擎接口抽象；AI 置换表+历史启发（depth4 快 2x）；将帅位置缓存；git 版本管理 |
| 2.2.0 | 集成 chessai-python：分析面板（H/F1）、FEN/将军/将死交叉校验、桥接层优雅降级 |
| 2.1.0 | AI 搜索 4x 加速（快速将军检测、make/unmake）、迭代加深+时间预算、AI 线程化不冻结、渲染缓存；开发建议文档 |
| 2.0.0 | 重构为标准包结构；修复走法/胜负 bug；AI 重写为 Alpha-Beta；新增将军/将死/困毙与单元测试 |
| 1.0.0 | 原平铺版（见 `backup/`），可运行但电脑无智能 |
