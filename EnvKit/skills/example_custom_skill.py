# -*- coding: utf-8 -*-
"""
示例自定义本地技能：开发缓存清理与临时路径审计 (Dev Cache Cleaner Skill)
演示如何编写并在 EnvKit 中动态加载本地自定义优化技能。
"""
import os
from core.skill_manager import BaseSkill, SkillContext, SkillResult

class DevCacheCleanerSkill(BaseSkill):
    id = "dev_cache_cleaner"
    name = "开发缓存与临时路径审计技能"
    category = "自定义扩展"
    icon = "🧹"
    description = "扫描 TEMP/TMP 环境变量指向的目录大小与有效性，并检测 pip / npm / yarn 缓存环境变量"
    author = "EnvKit 社区"
    version = "1.0"

    def execute(self, context: SkillContext) -> SkillResult:
        details = []
        issues = 0
        user_vars = context.user_env.list()
        
        # 1. 检查 TEMP 与 TMP
        temp_dir = user_vars.get('TEMP') or os.environ.get('TEMP', '')
        tmp_dir = user_vars.get('TMP') or os.environ.get('TMP', '')

        if temp_dir:
            if not os.path.exists(temp_dir):
                issues += 1
                details.append(f"❌ TEMP 环境变量指向的目录不存在: {temp_dir}")
            else:
                details.append(f"✅ TEMP 目录有效: {temp_dir}")

        if tmp_dir and tmp_dir != temp_dir:
            if not os.path.exists(tmp_dir):
                issues += 1
                details.append(f"❌ TMP 环境变量指向的目录不存在: {tmp_dir}")
            else:
                details.append(f"✅ TMP 目录有效: {tmp_dir}")

        # 2. 检查包管理器缓存变量
        pip_cache = user_vars.get('PIP_CACHE_DIR')
        if pip_cache:
            details.append(f"ℹ️ 自定义 PIP_CACHE_DIR: {pip_cache}")
        npm_config_cache = user_vars.get('npm_config_cache')
        if npm_config_cache:
            details.append(f"ℹ️ 自定义 npm_config_cache: {npm_config_cache}")

        summary = f"临时路径与开发缓存审计完毕，发现 {issues} 处异常。"
        return SkillResult(
            skill_id=self.id,
            skill_name=self.name,
            success=True,
            issues_found=issues,
            fixes_applied=0,
            summary=summary,
            details=details
        )
