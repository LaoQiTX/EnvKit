# EnvKit — Windows 环境变量与注册表管理工具

EnvKit 是一款基于 Python 与 DearPyGui 的桌面工具，专注于在 Windows 平台上安全、直观地管理环境变量与注册表，提供路径检测、启用/禁用、备份与文件恢复、双击选中、删除前确认，以及可自定义的大模型分析能力。

## 功能特性

- 环境变量管理：列出/新增/删除变量，支持 `user/system` 作用域切换
- PATH 管理：
  - 路径状态标识：不存在（红）、重复（橙）、两者兼有（洋红）
  - 复选启用/禁用并一键应用
  - 折叠区内滚动列表，避免一次性占满界面
  - 双击索引快速切换启用状态并设置删除索引
- 注册表管理：
  - 根选择 `HKCU/HKLM`，默认子键自动填充常用环境变量路径
  - 列出/设置/删除值，双击名称快速编辑
  - 值为路径或重复内容时颜色标识
- 删除前确认：
  - 变量/PATH 项/注册表值删除均弹窗确认
  - 关键名、存在路径、变量引用、系统目录、靠前优先级等命中时提示“谨慎删除”
- 备份与恢复：
  - 环境变量备份文件：`EnvKit/.backup/backup-env-YYYYMMDD-HHMMSS.json`
  - 注册表子键备份文件：`EnvKit/.backup/backup-reg-YYYYMMDD-HHMMSS.json`，含 `meta.root/subkey`
  - 备份后界面显示完整保存路径；恢复通过文件选择器选择 `.json` 文件
- 大模型分析：
  - 本地规则分析与自定义 HTTP 模型 API
  - 前端支持添加/删除模型、设置默认模型、刷新列表
  - HTTP 模型以 `POST` 接收 `{"items": [...], "model": "可选"}` 并返回 `{"suggestions": [...]}`

## 运行环境

- 操作系统：Windows 10/11
- Python：3.12（或兼容版本）
- 依赖：`dearpygui>=2.1.0`（已验证 2.1.1）

## 安装与启动

1. 安装依赖：

   ```bash
   python -m pip install -r EnvKit/requirements.txt
   ```

2. 运行程序：

   ```bash
   python EnvKit/main.py
   ```

程序启动时会自动绑定系统常见中文字体（如 `Microsoft YaHei`），确保中文显示正常。

## 打包为 EXE

1. 安装 PyInstaller：

   ```bash
   python -m pip install pyinstaller
   ```

2. 打包命令（包含模型配置文件）：

   ```bash
   pyinstaller -F -w --name EnvKit --add-data "EnvKit/models/model_config.json;models" EnvKit\main.py
   ```

3. 可执行文件位置：`dist/EnvKit.exe`

说明：程序在打包环境中自动使用 `sys._MEIPASS` 定位 `models/model_config.json`。

## 使用指南

- 环境变量页：
  - 切换作用域（`user/system`）后，点击“刷新变量”获取列表
  - 新增/删除变量；删除会根据谨慎条件弹窗确认
  - 多选分析：输入逗号分隔变量名，结果显示在“分析结果”框；双击变量名可快速填充并加入分析列表
  - PATH 检测：在折叠区滚动列表，支持新增、按索引删除、启用/禁用应用
  - 备份/恢复：点击“备份全部环境变量”后提示备份路径；点击“选择备份文件恢复环境变量”并在文件选择器中选择 `.json`

- 注册表页：
  - 选择根（`HKCU/HKLM`），默认子键自动填充常用路径（可修改）
  - 列出值并双击名称快速编辑；设置/删除值前后分别提示或确认
  - 备份当前子键后提示备份路径；恢复通过文件选择器选择 `.json` 文件

- 模型配置页：
  - 模型列表：选择并设置默认模型、删除模型、刷新列表
  - 添加模型：填写名称、类型（`rule/http`）、HTTP 端点、模型名（可选）、API Key（可选），点击“添加模型”即可生效

## 备份文件说明

- 环境变量：`EnvKit/.backup/backup-env-YYYYMMDD-HHMMSS.json`
- 注册表子键：`EnvKit/.backup/backup-reg-YYYYMMDD-HHMMSS.json`，`meta.root` 和 `meta.subkey` 记录上下文
- 恢复操作均通过文件选择器执行，避免误恢复不匹配内容

## 安全与权限

- 修改 `system` 作用域环境变量与 `HKLM` 注册表可能需要管理员权限
- PATH 更新会影响后续新进程；当前进程需重启以读取新值
- 模型 API 的 `API Key` 仅用于请求头，不会在界面或日志中暴露

## 常见问题

- 中文无法显示：检查系统字体是否存在；程序会自动绑定常见中文字体
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

- 本项目依赖开源组件 DearPyGui、PyInstaller 等，感谢其社区支持。

