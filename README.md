# EnvKit — Windows 环境变量与注册表管理工具

EnvKit 是一款基于 Python + DearPyGui 的桌面工具，专注在 Windows 平台上安全、直观地管理环境变量与注册表，提供路径检测、高亮标识、启用/禁用、备份与文件恢复、双击选中、删除前确认，以及可自定义的大模型分析能力。

## 注意 目前的打包后的文件会无法正确读取目录 暂时需要部署项目后运行main.py

## 功能特性



- 环境变量管理：列出/新增/删除，支持 `user/system` 作用域切换
- PATH 管理：
- 路径状态高亮：不存在（红）、重复（橙）、同时命中（洋红）
- 复选启用/禁用并一键应用；折叠区+滚动容器显示大量路径
- 双击索引快速切换启用状态并写入删除索引
- 注册表管理：
- 根选择 `HKCU/HKLM`；默认子键自动填充常用环境变量路径
- 列出/设置/删除值；双击名称快速编辑；路径/重复值高亮
- 删除前确认：变量、PATH 项、注册表值均弹窗确认；对关键名、存在路径、变量引用、系统目录、靠前优先级等给出“谨慎删除”提示
- 备份与恢复：
- 环境变量备份：`EnvKit/.backup/backup-env-YYYYMMDD-HHMMSS.json`
- 注册表子键备份：`EnvKit/.backup/backup-reg-YYYYMMDD-HHMMSS.json`（含 `meta.root/subkey`）
- 备份后界面提示完整路径；恢复通过文件选择器选择 `.json`
- 大模型分析：本地规则与自定义 HTTP 模型 API；前端支持添加/删除模型、设置默认、刷新列表

## 运行环境

- Windows 10/11
- Python 3.12（或兼容版本）
- 依赖：`dearpygui>=2.1.0`（已验证 2.1.1）

## 安装与运行

- 安装依赖：
  - `python -m pip install -r EnvKit/requirements.txt`
- 启动：
  - `python EnvKit/main.py`
- 中文字体：程序会自动绑定系统常见中文字体（如 `Microsoft YaHei`）。

## 打包与分发

- PyInstaller（传统方式）：
  - 安装：`python -m pip install pyinstaller`
  - 单文件、窗口模式、输出到自定义目录：
    - `pyinstaller -F -w --name EnvKit --add-data "EnvKit/models/model_config.json;models" --distpath dist_py EnvKit\main.py`
  - 结果路径：`dist_py\EnvKit.exe`

- Nuitka（更稳定的替代方式）：
  - 安装：`python -m pip install nuitka ordered_set zstandard`
  - 单文件、窗口模式、输出到自定义目录：
    - `python -m nuitka --standalone --onefile --windows-console-mode=disable --include-data-files=EnvKit/models/model_config.json=models --output-dir=dist_nuitka --output-filename=EnvKit.exe EnvKit\main.py`
  - 结果路径：`dist_nuitka\EnvKit.exe`
  - 说明：若 PyInstaller 版在你的环境崩溃（例如返回 `0xC0000005`），建议使用 Nuitka 方案。

## 使用指南

- 环境变量页：
  - 切换作用域、刷新变量、增删变量（删除有确认与谨慎提示）
  - 多选分析：输入逗号分隔变量名；双击变量名可快速填充并加入分析列表
  - PATH 检测：折叠区滚动列表；新增/按索引删除；启用/禁用一键应用
  - 备份/恢复：备份后展示完整路径；点击按钮选择 `.json` 文件恢复

- 注册表页：
  - 根选择（`HKCU/HKLM`），默认子键自动填充（可修改）
  - 列出值并双击名称快速编辑；设置/删除值均有提示与确认
  - 备份当前子键后提示完整路径；点击按钮选择 `.json` 文件恢复

- 模型配置页：
  - 列表操作：设置默认、删除、刷新
  - 添加模型：名称、类型（`rule/http`）、HTTP 端点、模型名（可选）、API Key（可选）
  - HTTP 模型协议：`POST` 发送 `{"items": [...], "model": "可选"}`；返回 `{"suggestions": [...]}` 生效

## 备份文件说明

- 环境变量：`EnvKit/.backup/backup-env-YYYYMMDD-HHMMSS.json`
- 注册表子键：`EnvKit/.backup/backup-reg-YYYYMMDD-HHMMSS.json`（`meta.root/subkey` 记录上下文）
- 恢复通过文件选择器执行，避免误恢复不匹配内容。

## 安全与权限

- 修改 `system` 作用域环境变量与 `HKLM` 注册表可能需要管理员权限
- PATH 更新影响后续新进程；当前进程需重启才能读取新值
- 打包版默认关闭文件日志；开发版可在控制台查看信息

## 常见问题与排查

- 打包后无法启动/立即退出：
  - 更新显卡驱动与安装 VC++ 2015–2022 运行时（x64）
  - 优先使用 Nuitka 打包方案（兼容性通常更好）
  - 如需诊断，请使用带控制台的构建方式运行并查看输出

- 中文无法显示：检查系统中文字体是否存在；程序会自动绑定常见中文字体
- 注册表写入失败：检查管理员权限、根选择与子键路径是否正确
- 模型分析无效：确认 HTTP 端点可访问且返回包含 `suggestions` 字段的 JSON

## 项目结构

```
EnvKit/
├─ gui/
│   ├─ main_window.py
│   ├─ env_table.py
│   ├─ reg_table.py
│   └─ config_panel.py
├─ core/
│   ├─ env_manager.py
│   ├─ reg_manager.py
│   ├─ backup.py
│   └─ analyzer.py
├─ models/
│   ├─ model_config.json
│   └─ model_client.py
├─ utils/
│   ├─ path_check.py
│   └─ logger.py
├─ main.py
└─ requirements.txt
```

## 许可与鸣谢

- 本项目依赖开源组件 DearPyGui、PyInstaller、Nuitka 等，感谢其社区支持。
- 感谢TRAE SOLO辅助开发
