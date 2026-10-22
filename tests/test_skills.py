import sys
from pathlib import Path
import pytest

# Add EnvKit to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'EnvKit'))

from core.skill_manager import (
    SkillManager, SkillContext, SkillResult, BaseSkill,
    GhostPathCleanerSkill, ScopeConflictSkill, DevStackAuditSkill,
    RegistryRunDoctorSkill, DanglingVarSkill
)
from core.env_manager import EnvManager
from core.reg_manager import RegManager

def test_skill_manager_initialization():
    sm = SkillManager()
    skills = sm.list_skills()
    assert len(skills) >= 5
    
    skill_ids = [s.id for s in skills]
    assert 'ghost_path_cleaner' in skill_ids
    assert 'scope_conflict_resolver' in skill_ids
    assert 'dev_stack_audit' in skill_ids
    assert 'reg_run_doctor' in skill_ids
    assert 'dangling_var_resolver' in skill_ids

def test_ghost_path_cleaner_dry_run():
    sm = SkillManager()
    res = sm.run_skill('ghost_path_cleaner', dry_run=True)
    assert res is not None
    assert isinstance(res, SkillResult)
    assert res.success is True
    assert isinstance(res.issues_found, int)
    assert isinstance(res.details, list)

def test_scope_conflict_resolver():
    sm = SkillManager()
    res = sm.run_skill('scope_conflict_resolver', dry_run=True)
    assert res is not None
    assert res.success is True

def test_dev_stack_audit():
    sm = SkillManager()
    res = sm.run_skill('dev_stack_audit', dry_run=True)
    assert res is not None
    assert res.success is True
    assert len(res.details) > 0

def test_dangling_var_resolver():
    sm = SkillManager()
    res = sm.run_skill('dangling_var_resolver', dry_run=True)
    assert res is not None
    assert res.success is True

def test_custom_skill_template_generation(tmp_path, monkeypatch):
    sm = SkillManager()
    monkeypatch.setattr(sm, 'skills_dir', tmp_path)
    
    file_path = sm.create_skill_template('My Test Skill', 'Testing dynamic custom skill creation')
    assert file_path.exists()
    
    # Reload skills from custom dir
    sm.load_custom_skills()
    assert sm.get_skill('my_test_skill') is not None
