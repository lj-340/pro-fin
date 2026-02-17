# Copilot / AI agent instructions for this repository

目的：帮助 AI 编码代理快速理解并在本仓库中高效工作。下面聚焦可被代码直接验证的事实与可操作的例子。

1) 大体架构（Big picture）
- 项目是一个 Django 网站：主工程为 `webFinPro`（见 `webFinPro/settings.py`）。Django 版本注释为 2.2.5。
- 主要前端/后台 app：`pageIndex`（视图和表单在 `pageIndex/views.py` 与 `pageIndex/forms.py`）。
- 大量金融/回测/数据处理脚本放在 `fu_t1/`，以独立脚本/模块形式存在（例如 `fu_t1/BackTrade_*.py`）。这些脚本并不是 Django app，但被 `pageIndex.views` 直接 import 并调用。

2) 关键文件与入口
- 启动（开发）：`manage.py runserver`。常见部署配置文件：`uwsgi.ini`（可用于生产通过 uWSGI + nginx）。
- 配置：`webFinPro/settings.py`（注意：`BASE_DIR` 被硬编码为 `D:/charm/Django/webFinPro`，且数据库为 MySQL，配置在文件中可见）。
- 视图/业务逻辑集中：`pageIndex/views.py`（大量业务逻辑、全局状态 `serverparams`、会话依赖、tushare 调用在此）。

3) 可观测约定与实现细节（务必遵守）
- 全局状态：`pageIndex/views.py` 使用大量模块级全局变量（例：`serverparams`, `userparams`），并通过 `updateServerstate` 管理。修改这类代码需谨慎考虑并发与状态恢复。
- 第三方服务 token：`pageIndex/views.py` 中直接调用 `ts.set_token(...)`（tushare token 明文出现在代码），搜索并避免把新秘钥放硬编码处，优先使用环境变量或 `settings`。
- CSV 编码与路径：代码中读取上传/下载文件时常用 `encoding='GBK'` 和路径 `settings.BASE_DIR + '/static/download/<username>/'`。处理 I/O 时注意 GBK 与 UTF-8 的差异。
- 数据源选择：`sel_havedatasourcetype` 标志表示是否使用本地数据或 tushare（0/1）。

4) 常见开发任务与示例命令
- 本地运行（开发调试）：
  - `python manage.py runserver 0.0.0.0:8000`
- 迁移/模型（如果需要）：
  - `python manage.py makemigrations`
  - `python manage.py migrate`
- 生产（线索）：查看 `uwsgi.ini` 并使用 uWSGI 启动。日志与 pid 在项目根 `uwsgi.pid` / `log/` 目录下。

## Copilot / AI agent instructions (condensed)

目的：让 AI 编码代理在本仓库立即上手，指出可验证的约定、关键入口与易错点。

**项目与启动**
- Django 项目根：[webFinPro/settings.py](webFinPro/settings.py)。开发启动：`python manage.py runserver 0.0.0.0:8000`。

**主要位置**
- 视图与表单：`pageIndex` — 见 [pageIndex/views.py](pageIndex/views.py) 和 [pageIndex/forms.py](pageIndex/forms.py)。
- 策略/数据脚本：`fu_t1/`（许多命令式脚本如 `fu_t1/BackTrade_*.py`，由视图直接 import 并调用）。

**关键约定（必须注意）**
- 全局状态：模块级全局变量 `serverparams`, `userparams` 在 `pageIndex/views.py` 被频繁使用与更新；修改须考虑并发与恢复。
- 配置与路径：项目普遍使用 `settings.BASE_DIR` 作为路径根（当前为 Windows 硬编码），下载路径形如 `settings.BASE_DIR + '/static/download/<username>/'`。
- 编码：CSV/文件读取多用 `encoding='GBK'`，处理时注意编码转换。
- 数据源切换：查看 `sel_havedatasourcetype`（本地数据 vs tushare）。

**安全提醒**
- `webFinPro/settings.py` 包含 `SECRET_KEY` 与数据库凭据；`pageIndex/views.py` 可能含 tushare token（明文）。切勿再硬编码新密钥，优先使用环境变量并在 `settings.py` 中读取。

**调试 & 变更要点**
- 视图中有大量业务逻辑（例如 `accessvalue`），优先在开发服务器观察 traceback；提取可测试的纯函数到 `fu_t1/` 或 `pageIndex/services.py`。
- 并发控制点：`serverparams['connectparams']['connectnums']`（示例 6），更改并发逻辑时同时调整此限制。

**快速查找技巧**
- 搜索 `serverparams`、`updateServerstate`、`sel_havedatasourcetype`。
- 查找 tushare token：在 [pageIndex/views.py](pageIndex/views.py) 搜 `ts.set_token`。

我已从原文保留所有可验证事实并压缩为便于 AI 消耗的要点。如需我：
- 将敏感配置改为环境变量并提交示例修改（修改 [webFinPro/settings.py](webFinPro/settings.py)），或
- 把大型视图重构为 `pageIndex/services.py` 并提交 PR。
请指示下一步优先项。
