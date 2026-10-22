# EnvKit — Windows 环境变量与注册表管理工具

EnvKit 是一款基于 Python + DearPyGui 的现代桌面工具，专注在 Windows 平台上安全、直观、高效地管理环境变量与注册表。提供深度路径检测、空路径与重复项排查、一键清理优化、安全备份与恢复、以及内置专家规则与大模型（DeepSeek / OpenAI / Ollama 等）智能诊断分析能力。

---

## ✨ 核心功能特性

### 1. 📌 环境变量管理
- **作用域切换**：支持自由切换 `用户变量 (User)` 与 `系统变量 (System)`。
- **实时搜索过滤**：支持按变量名或变量值进行毫秒级实时过滤筛选。
- **直观列表展示**：清晰标识系统关键变量、单路径、路径集合及空值项，双击快速填入编辑区。
- **增删改与防误删提示**：修改即时广播 Windows 系统消息（`WM_SETTINGCHANGE`），删除前自动针对核心变量、有效路径及变量引用给出“谨慎删除”安全告警。

### 2. 🛣️ PATH 专属高级管理
- **全方位健康状态体检**：自动统计有效路径、失效/不存在路径、大小写不敏感重复项、以及多余分号导致的空条目。
- **一键智能清理**：
  - **一键清理无效与空路径**：自动剔除已失效不存在的目录和多余空分号。
  - **一键去除重复项**：自动保留首个有效条目，剔除冗余重复条目。
- **条目精细调整**：支持单项启用/禁用复选、上移（▲）、下移（▼）、一键置顶、在 Windows 资源管理器直接定位打开。
- **原生目录选择**：支持调用 Windows 原生文件夹选择器快速添加新目录到 PATH 首部或末尾。

### 3. 🗃️ 注册表便捷管理
- **根键与快捷子键**：支持 `HKCU` / `HKLM` 切换，内置常用快捷子键（用户环境变量、系统环境变量、当前用户/系统开机自启 Run/RunOnce、应用别名 App Paths 等）。
- **类型感知与路径检测**：支持 `REG_SZ`、`REG_EXPAND_SZ`、`REG_DWORD` 等类型自动转换，对指向本地文件/目录的键值进行有效性检测与高亮。
- **子键级备份与恢复**：支持针对当前子键一键备份为 JSON，并支持通过原生文件选择器进行无损恢复。

### 4. 🤖 智能诊断与 AI 专家分析
- **一键全系统体检**：全量扫描用户变量、系统变量及 PATH 路径，定位潜在性能隐患、空路径及悬挂引用。
- **PATH 专项诊断**：深入评估 PATH 长度、条目数量与依赖健康度。
- **大模型深度解读**：
  - **内置专家规则**：无网络依赖，毫秒级输出诊断报告。
  - **标准大模型接入**：全面支持 DeepSeek、OpenAI、本地 Ollama 等（兼容 OpenAI Chat Completions 协议），深度解读变量归属、作用及安全清理指导。
- **一键复制报告**：支持将分析报告一键拷贝至系统剪贴板。

### 5. 🛡️ 权限感知与即时生效
- **管理员权限检测**：界面实时展示当前运行权限；非管理员状态下提供一键 UAC 提权重启。
- **全局环境即时生效**：变量与 PATH 更改后自动广播系统设置变更通知，新启动的命令行和软件立即生效，无需注销或重启电脑。

---

## 🖥️ 运行环境

- **操作系统**：Windows 10 / 11 (x64)
- **Python 版本**：Python 3.12（或兼容版本）
- **核心依赖**：`dearpygui>=2.1.0`

---

## 🚀 安装与启动

1. **安装依赖**：
   ```bash
   python -m pip install -r EnvKit/requirements.txt
   ```

2. **启动程序**：
   ```bash
   python EnvKit/main.py
   ```

> **中文字体与高清屏适配**：程序已内置 Windows 常见中文字体自动绑定，并启用了 Windows 高 DPI 缩放感知，高分屏下界面与字体锐利清晰。

---

## 📦 打包与分发（已完全修复打包读取目录问题）

项目已彻底修复此前打包环境下无法正确读取或创建数据目录的问题。打包后的单一可执行文件支持便携式运行，能够自动初始化配置并定位备份目录。

### 方案 A：PyInstaller 打包（推荐）

使用项目内置的优化配置文件 `EnvKit.spec` 直接打包：
```bash
python -m PyInstaller --noconfirm EnvKit.spec
```
生成文件位于：`dist\EnvKit.exe`。

如需手动单命令打包（单文件、无控制台黑框、包含模型默认配置）：
```bash
python -m PyInstaller -F -w --name EnvKit --add-data "EnvKit/models/model_config.json;models" EnvKit\main.py
```

### 方案 B：Nuitka 编译打包

```bash
python -m nuitka --standalone --onefile --windows-console-mode=disable --include-data-files=EnvKit/models/model_config.json=models/model_config.json --output-dir=dist_nuitka --output-filename=EnvKit.exe EnvKit\main.py
```
生成文件位于：`dist_nuitka\EnvKit.exe`。

---

## 💡 使用指南

1. **环境变量管理**：
   - 顶部单选框切换 `用户变量` 与 `系统变量`；
   - 搜索框即时筛选，双击任意行自动加载到下方编辑表单；
   - 点击“保存/更新”提交修改，系统自动广播生效；
   - 点击“一键备份全部变量”将当前所有变量导出为 JSON 文件。

2. **PATH 专用管理**：
   - 查看顶部状态栏了解失效、重复和空路径总数；
   - 点击“一键清理无效与空路径”或“一键去除重复项”实现快速健康优化；
   - 选中行可通过“▲ / ▼ / 置顶”按钮自由调整优先级；
   - 点击“浏览文件夹...”可直接选取本地目录并追加至 PATH。

3. **注册表管理**：
   - 下拉选择常用快捷子键（如开机自启项、系统环境变量等）；
   - 在列表中查看键值数据及其路径有效性，支持编辑、新建与删除；
   - 点击“备份当前子键”将数据备份至 `.backup` 目录。

4. **AI 与健康诊断**：
   - 在“AI 诊断体检”标签页点击“⚡ 一键全系统体检”查看综合报告；
   - 可在下拉框中选择“local-rules”内置规则或配置的 DeepSeek / OpenAI 大模型；
   - 随时在【环境变量】或【注册表】选中特定项点击“发送到 AI 深入分析”进行定向解读。

5. **模型与设置**：
   - 在模型列表点击预设按钮（如 DeepSeek、OpenAI、Ollama 本地）快速载入模板；
   - 填入对应 API Key 或自定义端口后点击“保存模型配置”；
   - 点击“测试模型连接”即可校验连通性；
   - 点击“在文件资源管理器中打开备份目录”快速查阅历史备份。

---

## 📁 备份数据说明

所有备份文件均自动存储在程序根目录下的 `.backup/` 文件夹中（程序已包含自动创建与权限保障机制）：
- **环境变量备份**：`.backup/backup-env-YYYYMMDD-HHMMSS.json`
- **注册表子键备份**：`.backup/backup-reg-YYYYMMDD-HHMMSS.json`（保留 `meta.root` 与 `meta.subkey` 上下文）
- 恢复操作均调用 Windows 原生文件选择对话框，自动定位至备份目录，安全可靠。

---

## 📂 项目结构

```
EnvKit/
├─ gui/                      # 现代化 UI 模块
│   ├─ main_window.py        # 主窗口与多选项卡容器
│   ├─ env_table.py          # 环境变量管理页面
│   ├─ path_view.py          # PATH 专属高级管理页面
│   ├─ reg_table.py          # 注册表管理页面
│   ├─ diagnosis_panel.py    # AI 与规则诊断中心
│   ├─ config_panel.py       # 模型与设置页面
│   └─ theme.py              # 全局暗黑主题与彩色状态标识
├─ core/                     # 核心业务逻辑
│   ├─ env_manager.py        # 环境变量与 PATH 增删改查及广播
│   ├─ reg_manager.py        # 注册表键值管理与类型映射
│   ├─ backup.py             # 数据备份与恢复引擎
│   └─ analyzer.py           # 诊断与分析调度器
├─ models/                   # 大模型客户端与配置
│   ├─ model_config.json     # 模型预设配置
│   └─ model_client.py       # OpenAI/DeepSeek/Ollama/规则引擎客户端
├─ utils/                    # 工具函数
│   ├─ path_helper.py        # 路径与资源安全定位器（解决打包目录问题）
│   ├─ path_check.py         # 路径规整、空路径检测与去重算法
│   ├─ win_utils.py          # Windows 权限、消息广播与原生对话框
│   └─ logger.py             # 运行日志记录
├─ tests/                    # 自动化单元测试与集成测试
│   ├─ test_envkit.py        # 算法与核心模块单元测试
│   └─ test_gui_integration.py # GUI 生命周期集成测试
├─ EnvKit.spec               # PyInstaller 单文件打包规约
├─ EnvKitFolder.spec         # PyInstaller 目录式打包规约
├─ requirements.txt          # Python 依赖清单
├─ main.py                   # 应用程序入口
└─ README.md                 # 项目文档
```

---

## 📄 许可与鸣谢

- 本项目基于开源许可发布。
- 感谢 DearPyGui、PyInstaller、Nuitka 等优秀的开源项目与社区。
