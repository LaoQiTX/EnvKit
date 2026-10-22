import dearpygui.dearpygui as dpg
from typing import List, Optional
from core.skill_manager import SkillManager, BaseSkill, SkillResult
from utils.win_utils import open_in_explorer
from gui.theme import (
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_MUTED,
    COLOR_PRIMARY, create_button_theme
)

class SkillsViewUI:
    def __init__(self, skill_manager: SkillManager):
        self.sm = skill_manager
        self.category_filter = "全部"
        self.cards_container_id = None
        self.console_text_id = None
        self.status_text_id = None

    def build(self):
        btn_primary = create_button_theme((37, 99, 235), (59, 130, 246), (29, 78, 216))
        btn_success = create_button_theme((16, 185, 129), (52, 211, 153), (5, 150, 105))
        btn_amber = create_button_theme((217, 119, 6), (245, 158, 11), (180, 83, 9))

        # 弹窗：新建本地技能
        with dpg.window(modal=True, show=False, tag='modal_new_skill', no_move=True, no_resize=True, width=460, height=230):
            dpg.add_text("[新建] 创建本地自定义优化技能", color=COLOR_PRIMARY)
            dpg.add_separator()
            dpg.add_text("技能英文标识/文件名 (例如 my_cuda_cleaner):")
            dpg.add_input_text(tag='new_skill_id', default_value='my_env_cleaner', width=430)
            dpg.add_text("技能功能说明:")
            dpg.add_input_text(tag='new_skill_desc', default_value='自定义专项环境变量检查与清理', width=430)
            dpg.add_spacer(height=8)
            with dpg.group(horizontal=True):
                b_create = dpg.add_button(label="生成技能脚本模板", callback=self._do_create_skill)
                dpg.bind_item_theme(b_create, btn_primary)
                dpg.add_button(label="取消", callback=lambda s, d: dpg.configure_item('modal_new_skill', show=False))

        # 顶部工具栏与概览
        with dpg.group(horizontal=True):
            dpg.add_text("[技能箱] 本地技能中心：", color=COLOR_PRIMARY)
            dpg.add_text("模块化本地排查与修复引擎，完全离线安全运行")
            dpg.add_spacer(width=15)
            
            b_run_all = dpg.add_button(label="[运行] 运行全套技能体检", callback=self._run_all_skills)
            dpg.bind_item_theme(b_run_all, btn_primary)

            dpg.add_button(label="[+] 新建自定义技能", callback=lambda s, d: dpg.configure_item('modal_new_skill', show=True))
            dpg.add_button(label="[目录] 打开 skills 插件目录", callback=lambda s, d: open_in_explorer(str(self.sm.skills_dir)))
            dpg.add_button(label="重新扫描加载", callback=self._reload_skills)

        dpg.add_spacer(height=4)

        # 分类筛选单选按钮
        with dpg.group(horizontal=True):
            dpg.add_text("分类筛选:")
            categories = ["全部", "PATH 治理", "冲突解决", "开发环境", "注册表修复", "自定义扩展"]
            dpg.add_radio_button(
                items=categories,
                default_value="全部",
                horizontal=True,
                callback=self._on_category_change
            )

        dpg.add_spacer(height=6)

        # 技能卡片列表区（左/上）与执行控制台（右/下）
        with dpg.group(horizontal=True):
            # 左侧：技能卡片列表
            with dpg.child_window(width=540, height=540, border=True):
                self.cards_container_id = dpg.add_group()
                self._render_skill_cards()

            # 右侧：实时输出控制台与报告详情
            with dpg.child_window(width=-1, height=540, border=True):
                dpg.add_text("[日志] 技能执行日志与诊断报告", color=COLOR_PRIMARY)
                self.status_text_id = dpg.add_text("就绪。选择任意技能点击“排查”或“一键修复”查看结果。", color=COLOR_MUTED)
                dpg.add_separator()
                self.console_text_id = dpg.add_input_text(
                    multiline=True,
                    readonly=True,
                    width=-1,
                    height=450,
                    default_value="[EnvKit Skill Engine v2.0]\n本地技能就绪。点击左侧技能卡片进行专项检测与修复。"
                )

    def _render_skill_cards(self):
        if not self.cards_container_id or not dpg.does_item_exist(self.cards_container_id):
            return

        children = dpg.get_item_children(self.cards_container_id, 1) or []
        for c in children:
            dpg.delete_item(c)

        btn_dry = create_button_theme((45, 55, 72), (74, 85, 104), (45, 55, 72), text_color=(255, 255, 255))
        btn_apply = create_button_theme((16, 185, 129), (52, 211, 153), (5, 150, 105), text_color=(255, 255, 255))

        skills = self.sm.list_skills()
        for skill in skills:
            if self.category_filter != "全部" and skill.category != self.category_filter:
                continue

            with dpg.child_window(parent=self.cards_container_id, height=115, border=True):
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{skill.icon} {skill.name}", color=COLOR_PRIMARY)
                    dpg.add_spacer(width=10)
                    dpg.add_text(f"[{skill.category}]", color=COLOR_MUTED)

                dpg.add_text(skill.description, wrap=500)
                dpg.add_spacer(height=2)

                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="[排查] 仅体检排查 (Dry Run)",
                        parent=dpg.last_container(),
                        callback=self._run_single_skill,
                        user_data=(skill.id, True)
                    )
                    
                    b_fix = dpg.add_button(
                        label="[修复] 一键执行修复",
                        parent=dpg.last_container(),
                        callback=self._run_single_skill,
                        user_data=(skill.id, False)
                    )
                    dpg.bind_item_theme(b_fix, btn_apply)

    def _on_category_change(self, sender, data):
        self.category_filter = data
        self._render_skill_cards()

    def _reload_skills(self, sender=None, data=None):
        self.sm.load_custom_skills()
        self._render_skill_cards()
        dpg.set_value(self.status_text_id, f"技能重载完毕，当前可用技能总数: {len(self.sm.list_skills())}")

    def _run_single_skill(self, sender, app_data, user_data):
        skill_id, dry_run = user_data
        mode_str = "体检排查" if dry_run else "执行修复"
        dpg.set_value(self.status_text_id, f"正在运行技能 [{skill_id}] ({mode_str})...")

        res: SkillResult = self.sm.run_skill(skill_id, dry_run=dry_run)
        if not res:
            dpg.set_value(self.status_text_id, "未找到该技能！")
            return

        self._display_result(res, dry_run)

    def _run_all_skills(self, sender, data):
        dpg.set_value(self.status_text_id, "正在对全套本地技能进行全量体检...")
        all_logs = ["[EnvKit 全套本地技能综合体检报告]", "=" * 45]
        total_issues = 0

        for skill in self.sm.list_skills():
            res = self.sm.run_skill(skill.id, dry_run=True)
            if res:
                total_issues += res.issues_found
                all_logs.append(f"\n▶ 技能: {res.skill_name} [{skill.category}]")
                all_logs.append(f"  结果: {res.summary}")
                for d in res.details:
                    all_logs.append(f"  {d}")

        all_logs.append("\n" + "=" * 45)
        all_logs.append(f"综合排查完毕！全套技能共发现 {total_issues} 处可优化项。")
        dpg.set_value(self.console_text_id, "\n".join(all_logs))
        dpg.set_value(self.status_text_id, f"全套体检完成，共发现 {total_issues} 处异常。")

    def _display_result(self, res: SkillResult, dry_run: bool):
        lines = [
            f"[执行技能] {res.skill_name} (ID: {res.skill_id})",
            f"[模式] {'仅体检排查 (Dry Run)' if dry_run else '实盘优化修复 (Apply)'}",
            f"[概况] {res.summary}",
            f"[发现异常] {res.issues_found} 处  |  [已执行修复] {res.fixes_applied} 处"
        ]
        if res.backup_file:
            lines.append(f"[安全备份] 已生成快照: {res.backup_file}")
            
        lines.append("\n[详细追踪记录]:")
        if res.details:
            for d in res.details:
                lines.append(f"  {d}")
        else:
            lines.append("  (无额外详细日志)")

        dpg.set_value(self.console_text_id, "\n".join(lines))
        stat_color = COLOR_SUCCESS if res.issues_found == 0 else COLOR_WARNING
        dpg.set_value(self.status_text_id, f"执行完毕：发现 {res.issues_found} 处异常，修复 {res.fixes_applied} 处。")

    def _do_create_skill(self, sender, data):
        name = dpg.get_value('new_skill_id').strip()
        desc = dpg.get_value('new_skill_desc').strip()
        dpg.configure_item('modal_new_skill', show=False)

        if not name:
            return

        file_path = self.sm.create_skill_template(name, desc)
        self._render_skill_cards()
        dpg.set_value(self.status_text_id, f"已生成自定义技能模板: {file_path.name}")
        open_in_explorer(str(file_path))
