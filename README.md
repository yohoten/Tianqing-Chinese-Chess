# 天青·中国象棋

一个基于 **Python + pygame** 的中国象棋双人对弈程序（人机对战），电脑方采用 **Alpha-Beta 剪枝搜索 + 局面评估**的智能算法。

原项目为平铺式脚本（`chinachess.py` / `botton.py` 等），本版本重构为标准 Python 包结构，修复走法规则与胜负判定 bug，并重写了电脑 AI。

## 功能特性

- 🎮 玩家执红（下方），电脑执黑（上方），鼠标点击走棋
- 🧠 电脑 AI：Alpha-Beta 剪枝 + 置换表 + 历史启发（迭代加深 + 时间预算，默认 2 秒，界面不冻结）
- ⏪ 悔棋（按钮 / U 键）：撤销最近一个完整回合，支持吃子恢复
- ✅ 完整中国象棋规则：车马炮兵士象将走法、蹩马腿、塞象眼、炮架、过河兵、九宫、飞将、不送将
- 🏁 将军 / 将死 / 困毙判定（显式状态机 PLAYING/AI_THINKING/GAME_OVER）
- 🔬 棋局分析面板（chessai 集成）：按 **H** 或 **F1** 查看 FEN、chessai 将军/将死/飞将状态、AI 推荐走法（自研 AI 计算 + chessai 交叉校验）
- 🔄 重新开始按钮、选中棋子高亮、可走位置提示
- 🔌 引擎接口抽象：`Engine.get_best_move()`，可替换自研 AI 或接外部引擎

### 可选依赖：chessai-python（分析面板增强）

```bash
.venv\Scripts\python.exe -m pip install chessai-python
```

已安装时：分析面板显示 FEN、将军/将死/飞将状态（`chessai.game` 规则引擎交叉校验）、AI 推荐走法合法性标记。未安装时游戏正常运行，分析面板显示"chessai 未安装"。集成代码见 `chinese_chess/chessai_bridge.py`。

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
├── main.py                 # 程序入口
├── requirements.txt        # 依赖清单
├── README.md
├── .gitignore
├── backup/                 # 原版代码与资源备份（legacy/ 为重构前的平铺版本）
├── chinese_chess/          # 主包
│   ├── __init__.py
│   ├── constants.py        # 常量与图片资源管理
│   ├── pieces.py           # 棋子走法规则（纯逻辑，可单测）
│   ├── board.py            # 棋盘 / 棋子渲染
│   ├── button.py           # 按钮控件
│   ├── ai.py               # Alpha-Beta AI + 局面评估 + 终局判定
│   └── game.py             # 游戏主循环
├── assets/s2/              # 棋子图片（统一小写文件名，跨平台）
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
| 2.3.0 | 状态机化；悔棋（按钮/U 键）；引擎接口抽象；AI 置换表+历史启发（depth4 快 2x）；将帅位置缓存；git 版本管理 |
| 2.2.0 | 集成 chessai-python：分析面板（H/F1）、FEN/将军/将死交叉校验、桥接层优雅降级 |
| 2.1.0 | AI 搜索 4x 加速（快速将军检测、make/unmake）、迭代加深+时间预算、AI 线程化不冻结、渲染缓存；开发建议文档 |
| 2.0.0 | 重构为标准包结构；修复走法/胜负 bug；AI 重写为 Alpha-Beta；新增将军/将死/困毙与单元测试 |
| 1.0.0 | 原平铺版（见 `backup/`），可运行但电脑无智能 |
