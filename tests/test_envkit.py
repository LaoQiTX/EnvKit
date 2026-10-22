import os
import sys
import json
import pytest
from pathlib import Path

# Add EnvKit to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'EnvKit'))

from utils.path_check import normalize_path, analyze_paths, rebuild_path, clean_path_entries
from utils.path_helper import get_base_dir, get_bundle_dir, get_model_config_path, get_backup_dir
from utils.win_utils import is_admin, notify_environment_change
from core.env_manager import EnvManager
from core.reg_manager import RegManager, PRESET_KEYS
from core.backup import backup, restore
from core.analyzer import Analyzer
from models.model_client import ModelClient

def test_normalize_path():
    # Quotes stripping
    assert normalize_path('"C:\\Windows"') == 'C:\\Windows'
    assert normalize_path("'C:\\Windows'") == 'C:\\Windows'
    assert normalize_path('   "C:\\Windows"   ') == 'C:\\Windows'
    assert normalize_path('') == ''
    assert normalize_path('   ') == ''
    
    # Environment variable expansion
    system_root = os.environ.get('SystemRoot', 'C:\\Windows')
    assert normalize_path('%SystemRoot%') == system_root

def test_analyze_paths():
    test_str = 'C:\\Windows;"C:\\Program Files";;c:\\windows;C:\\NonExistentDirectory_12345;'
    entries = analyze_paths(test_str)
    
    assert len(entries) == 6
    # Index 0: C:\Windows
    assert entries[0]['exists'] is True
    assert entries[0]['is_empty'] is False
    assert entries[0]['duplicate'] is False
    
    # Index 1: "C:\Program Files" (Quotes handled properly)
    assert entries[1]['exists'] is True
    assert entries[1]['is_empty'] is False
    assert entries[1]['duplicate'] is False
    
    # Index 2: Empty path
    assert entries[2]['is_empty'] is True
    assert entries[2]['exists'] is False
    
    # Index 3: c:\windows (Case-insensitive duplicate of C:\Windows)
    assert entries[3]['duplicate'] is True
    assert entries[3]['shadowed'] is True
    assert entries[3]['first_seen_index'] == 0
    
    # Index 4: Nonexistent directory
    assert entries[4]['exists'] is False
    assert entries[4]['is_empty'] is False
    assert entries[4]['duplicate'] is False
    
    # Index 5: Trailing empty path
    assert entries[5]['is_empty'] is True
    assert entries[5]['exists'] is False

def test_clean_path_entries():
    raw_list = ['C:\\Windows', '"C:\\Program Files"', '', 'c:\\windows', 'C:\\NonExistentDirectory_12345', '']
    cleaned, stats = clean_path_entries(raw_list, remove_invalid=True, remove_duplicates=True, remove_empty=True)
    
    assert stats['removed_empty'] == 2
    assert stats['removed_duplicate'] == 1
    assert stats['removed_invalid'] == 1
    assert stats['total_removed'] == 4
    assert cleaned == ['C:\\Windows', '"C:\\Program Files"']

def test_rebuild_path():
    assert rebuild_path(['C:\\Windows', '  ', 'C:\\Program Files']) == 'C:\\Windows;C:\\Program Files'
    assert rebuild_path([]) == ''

def test_path_helper():
    base = get_base_dir()
    assert base.exists()
    
    bundle = get_bundle_dir()
    assert bundle.exists()
    
    cfg_path = get_model_config_path()
    assert cfg_path.exists()
    assert cfg_path.parent.exists()
    
    backup_dir = get_backup_dir()
    assert backup_dir.exists()

def test_backup_and_restore(tmp_path):
    env_sample = {'TEST_ENV_VAR': 'HelloEnvKit'}
    reg_sample = {'HKCU\\Environment\\TEST_REG_VAR': 'Val'}
    meta = {'scope': 'user'}
    
    out_file = backup(env_sample, reg_sample, out_dir=str(tmp_path), category='env', meta=meta)
    assert os.path.exists(out_file)
    
    restored = restore(out_file)
    assert restored['category'] == 'env'
    assert restored['env']['TEST_ENV_VAR'] == 'HelloEnvKit'
    assert restored['meta']['scope'] == 'user'

def test_env_manager_read():
    mgr = EnvManager('user')
    vars_map = mgr.list()
    assert isinstance(vars_map, dict)
    # PATH or TEMP should typically exist in User or System
    path_entries = mgr.list_path('PATH')
    assert isinstance(path_entries, list)

def test_reg_manager_read():
    reg = RegManager('HKCU')
    values = reg.list_values('Environment')
    assert isinstance(values, list)

def test_analyzer_and_model_client(tmp_path):
    cfg_file = tmp_path / 'models' / 'model_config.json'
    analyzer = Analyzer(str(cfg_file))
    
    models = analyzer.models()
    assert len(models) >= 1
    assert any(m['name'] == 'local-rules' for m in models)
    
    # Test rule analysis
    items = [
        {'kind': 'env', 'key': 'PATH', 'value': 'C:\\Windows;;c:\\windows;C:\\NotExist;'},
        {'kind': 'env', 'key': 'EMPTY_VAR', 'value': ''},
        {'kind': 'env', 'key': 'DANGLING', 'value': '%A_VERY_STRANGE_NONEXISTENT_VAR%\\bin'}
    ]
    res = analyzer.analyze(items, model_name='local-rules')
    assert 'suggestions' in res
    assert 'summary' in res
    assert len(res['suggestions']) > 0

def test_win_utils():
    # is_admin returns a boolean
    admin_state = is_admin()
    assert isinstance(admin_state, bool)
    
    # notify_environment_change should not crash
    notify_environment_change()
