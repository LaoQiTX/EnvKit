import sys
from pathlib import Path

# Add EnvKit to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'EnvKit'))

import dearpygui.dearpygui as dpg
import main
from gui.main_window import NAV_VIEWS

def test_full_gui_sidebar_lifecycle():
    dpg.create_context()
    main._setup_font()
    main.build_ui()
    
    dpg.create_viewport(title='Test Sidebar GUI', width=1100, height=780)
    dpg.setup_dearpygui()
    dpg.set_primary_window('EnvKit', True)
    dpg.show_viewport()
    
    # Render multiple initial frames
    for _ in range(10):
        dpg.render_dearpygui_frame()
        
    # Verify main UI elements and views exist
    assert dpg.does_item_exist('EnvKit')
    assert dpg.does_item_exist('content_area')
    
    for nav_id, view_id, _ in NAV_VIEWS:
        assert dpg.does_item_exist(nav_id)
        assert dpg.does_item_exist(view_id)
        
        # Switch to each view and render frames
        for _, other_view, _ in NAV_VIEWS:
            dpg.configure_item(other_view, show=(other_view == view_id))
        dpg.render_dearpygui_frame()
    
    dpg.destroy_context()
