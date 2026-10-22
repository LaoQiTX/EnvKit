import os
import re
import sys
import importlib.util
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from core.env_manager import EnvManager
from core.reg_manager import RegManager
from core.backup import backup
from utils.path_check import normalize_path, analyze_paths, clean_path_entries
from utils.path_helper import get_base_dir
from utils.logger import get_logger

LOGGER = get_logger('EnvKit')

@dataclass
class SkillContext:
    user_env: EnvManager
    sys_env: EnvManager
    hkcu_reg: RegManager
    hklm_reg: RegManager
    dry_run: bool = True

@dataclass
class SkillResult:
    skill_id: str
    skill_name: str
    success: bool
    issues_found: int = 0
    fixes_applied: int = 0
    summary: str = ""
    details: List[str] = field(default_factory=list)
    backup_file: Optional[str] = None

class BaseSkill:
    id: str = "base_skill"
    name: str = "基础技能"
    category: str = "通用"
    icon: str = "[技能]"
    description: str = "技能基类"
    author: str = "EnvKit Core"
    version: str = "1.0"

    def execute(self, context: SkillContext) -> SkillResult:
        raise NotImplementedError

# ==========================================
# 1. 幽灵路径清理技能 (Ghost Paths Cleaner)
# ==========================================
class GhostPathCleanerSkill(BaseSkill):
    id = "ghost_path_cleaner"
    name = "幽灵无效路径清理技能"
    category = "PATH 治理"
    icon = "[清理]"
    description = "深度扫描用户与系统 PATH 中已被删除或卸载软件残留的失效目录，支持安全备份并一键清理"

    def execute(self, context: SkillContext) -> SkillResult:
        details = []
        issues = 0
        fixed = 0
        backup_path = None

        # 检查 User PATH
        u_mgr = context.user_env
        u_raw = u_mgr.get('PATH') or ''
        u_entries = analyze_paths(u_raw)
        u_invalids = [e['raw'] for e in u_entries if (not e['exists'] and not e['is_empty'])]
        u_empties = [e['raw'] for e in u_entries if e['is_empty']]
        
        # 检查 System PATH
        s_mgr = context.sys_env
        s_raw = s_mgr.get('PATH') or ''
        s_entries = analyze_paths(s_raw)
        s_invalids = [e['raw'] for e in s_entries if (not e['exists'] and not e['is_empty'])]
        s_empties = [e['raw'] for e in s_entries if e['is_empty']]

        issues = len(u_invalids) + len(u_empties) + len(s_invalids) + len(s_empties)

        if issues == 0:
            return SkillResult(
                skill_id=self.id,
                skill_name=self.name,
                success=True,
                issues_found=0,
                fixes_applied=0,
                summary="恭喜！用户与系统 PATH 中未发现任何失效或空路径，状态极佳。"
            )

        details.append(f"扫描发现用户 PATH 中有 {len(u_invalids)} 处失效路径，{len(u_empties)} 处多余空分号。")
        for inv in u_invalids:
            details.append(f"  - [用户失效] {inv}")

        details.append(f"扫描发现系统 PATH 中有 {len(s_invalids)} 处失效路径，{len(s_empties)} 处多余空分号。")
        for inv in s_invalids:
            details.append(f"  - [系统失效] {inv}")

        if not context.dry_run:
            # 自动预先备份
            backup_path = backup(
                {'user_PATH': u_raw, 'sys_PATH': s_raw},
                {},
                category='env',
                meta={'trigger': 'GhostPathCleanerSkill'}
            )
            # 执行清理
            u_clean_stat = u_mgr.clean_path(remove_invalid=True, remove_duplicates=False, remove_empty=True)
            fixed += u_clean_stat['total_removed']
            
            try:
                s_clean_stat = s_mgr.clean_path(remove_invalid=True, remove_duplicates=False, remove_empty=True)
                fixed += s_clean_stat['total_removed']
            except Exception as e:
                details.append(f"注意：清理系统 PATH 需要管理员权限 ({e})")

            summary = f"清理完成！已移除 {fixed} 个无效与空路径条目，已自动生成备份快照。"
        else:
            summary = f"体检完成：共发现 {issues} 个失效幽灵路径或多余空分号。建议执行一键清理。"

        return SkillResult(
            skill_id=self.id,
            skill_name=self.name,
            success=True,
            issues_found=issues,
            fixes_applied=fixed,
            summary=summary,
            details=details,
            backup_file=backup_path
        )

# ==========================================
# 2. 用户与系统作用域冲突解决技能
# ==========================================
class ScopeConflictSkill(BaseSkill):
    id = "scope_conflict_resolver"
    name = "跨作用域 PATH 重复冲突分析技能"
    category = "冲突解决"
    icon = "[冲突]"
    description = "对比用户 PATH 与系统 PATH 的重叠项，解决因优先级覆盖导致的工具版本错乱问题"

    def execute(self, context: SkillContext) -> SkillResult:
        u_raw = context.user_env.get('PATH') or ''
        s_raw = context.sys_env.get('PATH') or ''

        u_parts = [p.strip().strip('"') for p in u_raw.split(';') if p.strip()]
        s_parts = [p.strip().strip('"') for p in s_raw.split(';') if p.strip()]

        u_norm_map = {normalize_path(p).lower(): p for p in u_parts}
        s_norm_map = {normalize_path(p).lower(): p for p in s_parts}

        overlap = set(u_norm_map.keys()) & set(s_norm_map.keys())
        details = []

        if not overlap:
            return SkillResult(
                skill_id=self.id,
                skill_name=self.name,
                success=True,
                issues_found=0,
                fixes_applied=0,
                summary="用户 PATH 与系统 PATH 互相独立，不存在重叠冲突条目。"
            )

        details.append(f"检测到 {len(overlap)} 个路径在【用户 PATH】与【系统 PATH】中同时存在：")
        for key in overlap:
            details.append(f"  - 重复项: {u_norm_map[key]}")
            details.append("    说明: Windows 执行时系统 PATH 优先，用户 PATH 中的该条目会被静默覆盖。")

        fixed = 0
        backup_path = None
        if not context.dry_run:
            backup_path = backup({'user_PATH': u_raw}, {}, category='env', meta={'trigger': 'ScopeConflictSkill'})
            # 从用户 PATH 中移除与系统 PATH 重复的冗余条目
            new_u_parts = [p for p in u_parts if normalize_path(p).lower() not in overlap]
            context.user_env.update_path_entries(new_u_parts)
            fixed = len(overlap)
            summary = f"优化完成！已从用户 PATH 中安全剔除 {fixed} 个与系统 PATH 重复的冗余项。"
        else:
            summary = f"共发现 {len(overlap)} 处跨作用域冗余重复项，建议从用户 PATH 中清理以加快命令行检索速度。"

        return SkillResult(
            skill_id=self.id,
            skill_name=self.name,
            success=True,
            issues_found=len(overlap),
            fixes_applied=fixed,
            summary=summary,
            details=details,
            backup_file=backup_path
        )

# ==========================================
# 3. 开发者环境全景诊断技能 (Dev Stack Audit)
# ==========================================
class DevStackAuditSkill(BaseSkill):
    id = "dev_stack_audit"
    name = "开发工具链环境全景诊断技能"
    category = "开发环境"
    icon = "[开发]"
    description = "全面检测 Python、Java、Node.js、Go、Rust、Git 等开发工具链环境变量配置与版本绑定"

    def execute(self, context: SkillContext) -> SkillResult:
        details = []
        issues = 0
        user_vars = context.user_env.list()
        sys_vars = context.sys_env.list()
        all_vars = {**sys_vars, **user_vars} # 用户变量优先级更高

        u_path = context.user_env.get('PATH') or ''
        s_path = context.sys_env.get('PATH') or ''
        full_path = f"{s_path};{u_path}"

        # 1. Java 检查
        java_home = all_vars.get('JAVA_HOME')
        if java_home:
            if not os.path.exists(java_home):
                issues += 1
                details.append(f"[×] [Java] JAVA_HOME 指向的目录不存在: {java_home}")
            else:
                bin_dir = os.path.join(java_home, 'bin')
                if os.path.exists(bin_dir) and bin_dir.lower() not in full_path.lower():
                    issues += 1
                    details.append(f"[!] [Java] JAVA_HOME 存在，但 %JAVA_HOME%\\bin 未加入 PATH 环境变量")
                else:
                    details.append(f"[√] [Java] JAVA_HOME 配置正常: {java_home}")
        else:
            details.append("[i] [Java] 未配置 JAVA_HOME 环境变量")

        # 2. Python 检查
        py_scripts = [p for p in full_path.split(';') if 'python' in p.lower() and 'scripts' in p.lower()]
        py_homes = [p for p in full_path.split(';') if 'python' in p.lower() and os.path.exists(os.path.join(p, 'python.exe'))]
        if py_homes:
            details.append(f"[√] [Python] 检测到当前 PATH 中包含 {len(py_homes)} 个 Python 环境: {py_homes[0]}")
            if len(py_homes) > 1:
                details.append(f"[!] [Python] 存在多个不同 Python 版本在 PATH 中，靠前的将优先执行: {py_homes}")
            if not py_scripts:
                issues += 1
                details.append("[!] [Python] PATH 中未检测到 Python\\Scripts 目录，可能导致 pip 安装的命令行工具无法直接运行")
        else:
            details.append("[i] [Python] PATH 中未直接检测到 python.exe 目录")

        # 3. Node.js 检查
        node_paths = [p for p in full_path.split(';') if os.path.exists(os.path.join(p, 'node.exe'))]
        if node_paths:
            details.append(f"[√] [Node.js] 检测到 Node.js 运行时路径: {node_paths[0]}")
        else:
            details.append("[i] [Node.js] 未检测到 node.exe 路径")

        # 4. Git 检查
        git_paths = [p for p in full_path.split(';') if 'git' in p.lower() and ('cmd' in p.lower() or 'bin' in p.lower())]
        if git_paths:
            details.append(f"[√] [Git] Git 命令路径已正确配置: {git_paths[0]}")
        else:
            details.append("[i] [Git] 未在 PATH 中找到 Git 路径")

        # 5. Rust & Go
        if 'CARGO_HOME' in all_vars:
            details.append(f"[√] [Rust] CARGO_HOME: {all_vars['CARGO_HOME']}")
        if 'GOPATH' in all_vars:
            details.append(f"[√] [Go] GOPATH: {all_vars['GOPATH']}")

        summary = f"开发工具链体检完成：共评估 6 种主流语言与运行时，发现 {issues} 处待优化配置。"
        return SkillResult(
            skill_id=self.id,
            skill_name=self.name,
            success=True,
            issues_found=issues,
            fixes_applied=0,
            summary=summary,
            details=details
        )

# ==========================================
# 4. 注册表开机启动项体检技能 (Registry Run Doctor)
# ==========================================
class RegistryRunDoctorSkill(BaseSkill):
    id = "reg_run_doctor"
    name = "注册表开机启动健康体检技能"
    category = "注册表修复"
    icon = "[自启]"
    description = "排查 HKCU / HKLM 注册表自启动项中的失效残留（已卸载但仍在开机启动中执行的死链接）"

    def execute(self, context: SkillContext) -> SkillResult:
        subkeys = [
            ('HKCU', context.hkcu_reg, r'Software\Microsoft\Windows\CurrentVersion\Run'),
            ('HKLM', context.hklm_reg, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run')
        ]
        details = []
        dead_entries = []

        for root_name, reg_mgr, sub in subkeys:
            items = reg_mgr.list_values(sub)
            for it in items:
                name = it['name']
                cmd = str(it['value'])
                # 解析命令行中的 exe 路径
                match = re.match(r'^\s*"?([^"]+\.exe)"?', cmd, re.IGNORECASE)
                if match:
                    exe_path = match.group(1)
                    norm_exe = normalize_path(exe_path)
                    if not os.path.exists(norm_exe):
                        dead_entries.append((root_name, reg_mgr, sub, name, cmd, norm_exe))
                        details.append(f"[×] [{root_name} 自启动] 键名: {name} | 目标文件不存在: {norm_exe}")
                elif cmd and not os.path.exists(normalize_path(cmd.split(' ')[0])):
                    details.append(f"[!] [{root_name} 自启动] 无法确认程序有效性: {name} -> {cmd[:60]}")

        issues = len(dead_entries)
        if issues == 0:
            return SkillResult(
                skill_id=self.id,
                skill_name=self.name,
                success=True,
                issues_found=0,
                fixes_applied=0,
                summary="开机自启动注册表项健康，未发现失效死链接残留。"
            )

        fixed = 0
        backup_path = None
        if not context.dry_run:
            backup_data = {f"{r}\\{s}\\{n}": c for r, _, s, n, c, _ in dead_entries}
            backup_path = backup({}, backup_data, category='reg', meta={'trigger': 'RegistryRunDoctorSkill'})
            for root_name, reg_mgr, sub, name, _, _ in dead_entries:
                try:
                    reg_mgr.delete_value(sub, name)
                    fixed += 1
                except Exception as e:
                    details.append(f"删除失败 [{name}]: {e}")
            summary = f"修复完成！已安全清除 {fixed} 个无效自启动死链接项。"
        else:
            summary = f"发现 {issues} 个已卸载软件的自启动注册表死链接，建议执行清理以加快开机速度。"

        return SkillResult(
            skill_id=self.id,
            skill_name=self.name,
            success=True,
            issues_found=issues,
            fixes_applied=fixed,
            summary=summary,
            details=details,
            backup_file=backup_path
        )

# ==========================================
# 5. 悬挂变量引用解析技能 (Dangling Var Skill)
# ==========================================
class DanglingVarSkill(BaseSkill):
    id = "dangling_var_resolver"
    name = "未定义环境变量引用修复技能"
    category = "变量修复"
    icon = "[引用]"
    description = "扫描环境变量值中形如 %VAR% 的嵌套引用，排查目标变量不存在导致的路径失效问题"

    def execute(self, context: SkillContext) -> SkillResult:
        user_vars = context.user_env.list()
        sys_vars = context.sys_env.list()
        all_vars = {**sys_vars, **user_vars}
        known_names = set(k.upper() for k in all_vars.keys())

        # 标准系统动态变量
        system_dynamic = {'SYSTEMROOT', 'WINDIR', 'PROGRAMDATA', 'PUBLIC', 'ALLUSERSPROFILE', 'APPDATA', 'LOCALAPPDATA', 'USERPROFILE', 'USERNAME', 'COMPUTERNAME', 'HOMEDRIVE', 'HOMEPATH', 'TEMP', 'TMP', 'SYSTEMDRIVE', 'PROCESSOR_ARCHITECTURE'}
        known_names.update(system_dynamic)

        details = []
        issues = 0

        for scope, vmap in [("用户", user_vars), ("系统", sys_vars)]:
            for k, val in vmap.items():
                if not val or not isinstance(val, str):
                    continue
                refs = re.findall(r'%([^%]+)%', val)
                for ref in refs:
                    if ref.upper() not in known_names:
                        issues += 1
                        details.append(f"[×] [{scope}变量 {k}] 引用了未定义的变量: %{ref}% (完整取值: {val[:80]})")

        if issues == 0:
            summary = "全系统未发现任何悬挂或未定义的环境变量嵌套引用。"
        else:
            summary = f"共发现 {issues} 处引用的环境变量未定义，这通常会导致相关 PATH 或工具无法正确读取。"

        return SkillResult(
            skill_id=self.id,
            skill_name=self.name,
            success=True,
            issues_found=issues,
            fixes_applied=0,
            summary=summary,
            details=details
        )


# ==========================================
# 技能管理器 (SkillManager)
# ==========================================
class SkillManager:
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.skills_dir = get_base_dir() / 'skills'
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.register_builtins()
        self.load_custom_skills()

    def register_builtins(self):
        """注册内置核心优化技能"""
        builtins = [
            GhostPathCleanerSkill(),
            ScopeConflictSkill(),
            DevStackAuditSkill(),
            RegistryRunDoctorSkill(),
            DanglingVarSkill()
        ]
        for skill in builtins:
            self.skills[skill.id] = skill

    def load_custom_skills(self):
        """动态加载 skills/ 目录下的本地自定义 Python 技能插件"""
        if not self.skills_dir.exists():
            return

        for f in self.skills_dir.glob("*.py"):
            if f.name.startswith("__"):
                continue
            try:
                mod_name = f"envkit_skill_{f.stem}"
                spec = importlib.util.spec_from_file_location(mod_name, str(f))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    spec.loader.exec_module(mod)
                    
                    # 查找继承 BaseSkill 的类或导出接口
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name)
                        if isinstance(attr, type) and issubclass(attr, BaseSkill) and attr is not BaseSkill:
                            instance = attr()
                            self.skills[instance.id] = instance
                            LOGGER.info(f"Loaded custom skill: {instance.name} ({instance.id})")
            except Exception as e:
                LOGGER.error(f"Failed to load custom skill {f.name}: {e}")

    def list_skills(self) -> List[BaseSkill]:
        return list(self.skills.values())

    def get_skill(self, skill_id: str) -> Optional[BaseSkill]:
        return self.skills.get(skill_id)

    def run_skill(self, skill_id: str, dry_run: bool = True) -> Optional[SkillResult]:
        skill = self.get_skill(skill_id)
        if not skill:
            return None

        ctx = SkillContext(
            user_env=EnvManager('user'),
            sys_env=EnvManager('system'),
            hkcu_reg=RegManager('HKCU'),
            hklm_reg=RegManager('HKLM'),
            dry_run=dry_run
        )
        return skill.execute(ctx)

    def create_skill_template(self, skill_name: str, desc: str) -> Path:
        """为用户生成自定义本地技能脚本模板"""
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', skill_name).lower() or "my_custom_skill"
        file_path = self.skills_dir / f"{safe_name}.py"
        
        template_code = f'''# -*- coding: utf-8 -*-
"""
自定义 EnvKit 本地技能插件: {skill_name}
"""
from core.skill_manager import BaseSkill, SkillContext, SkillResult

class CustomSkill_{safe_name}(BaseSkill):
    id = "{safe_name}"
    name = "{skill_name}"
    category = "自定义扩展"
    icon = "[自定义]"
    description = "{desc}"
    author = "User"
    version = "1.0"

    def execute(self, context: SkillContext) -> SkillResult:
        details = []
        user_vars = context.user_env.list()
        details.append(f"成功调用自定义技能，当前共读取到 {{len(user_vars)}} 个用户环境变量。")
        
        # 在此处添加您的专属检查或清理逻辑:
        # if not context.dry_run:
        #     context.user_env.set("MY_VAR", "value")

        return SkillResult(
            skill_id=self.id,
            skill_name=self.name,
            success=True,
            issues_found=0,
            fixes_applied=0,
            summary="自定义本地技能执行完毕！",
            details=details
        )
'''
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template_code)
            
        self.load_custom_skills()
        return file_path
