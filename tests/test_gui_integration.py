import sys
from pathlib import Path

# Add EnvKit to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'EnvKit'))

import dearpygui.dearpygui as dpg
import main
from gui.main_window import ALL_NAV
from gui.theme import get_current_theme_mode, toggle_global_theme, load_theme_preference

def test_full_gui_sidebar_lifecycle():
    dpg.create_context()
    main._setup_font()
    main.build_ui()
    
    dpg.create_viewport(title='Test Sidebar GUI', width=1420, height=890)
    dpg.setup_dearpygui()
    dpg.set_primary_window('EnvKit', True)
    dpg.show_viewport()
    
    # Render multiple initial frames
    for _ in range(5):
        dpg.render_dearpygui_frame()
        
    # Verify main UI elements and views exist
    assert dpg.does_item_exist('EnvKit')
    assert dpg.does_item_exist('content_area')
    assert dpg.does_item_exist('btn_theme_toggle')
    
    for nav_id, view_id, label in ALL_NAV:
        assert dpg.does_item_exist(nav_id)
        assert dpg.does_item_exist(view_id)
        # Ensure label has no question mark or broken emoji prefix
        assert not label.startswith('?')
        
        # Switch to each view and render frames
        for _, other_view, _ in ALL_NAV:
            dpg.configure_item(other_view, show=(other_view == view_id))
        dpg.render_dearpygui_frame()
    
    # Test Theme Toggle
    init_mode = get_current_theme_mode()
    new_mode = toggle_global_theme()
    assert new_mode != init_mode
    dpg.render_dearpygui_frame()
    
    # Revert theme
    reverted_mode = toggle_global_theme()
    assert reverted_mode == init_mode
    dpg.render_dearpygui_frame()

    # Test Path View Inputs
    assert dpg.does_item_exist('path_add_input')
    dpg.set_value('path_add_input', r'C:\MyTest\Bin')
    assert dpg.get_value('path_add_input') == r'C:\MyTest\Bin'

    # Test Reg Address Input
    assert dpg.does_item_exist('reg_address_input')
    dpg.set_value('reg_address_input', 'Environment')
    assert dpg.get_value('reg_address_input') == 'Environment'

    dpg.destroy_context()

def test_theme_persistence():
    mode = load_theme_preference()
    assert mode in ('dark', 'light')
