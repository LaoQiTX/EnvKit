import dearpygui.dearpygui as dpg
from core.analyzer import Analyzer
from gui.env_table import EnvUI
from gui.reg_table import RegUI
from gui.config_panel import ConfigUI
from pathlib import Path
import sys

def build_ui():
    if getattr(sys, 'frozen', False):
        base = Path(sys.argv[0]).resolve().parent
    else:
        base = Path(__file__).resolve().parents[1]
    analyzer = Analyzer(str(base / 'models' / 'model_config.json'))
    with dpg.window(tag='EnvKit', width=1024, height=768, no_move=True, no_resize=True, no_close=True):
        with dpg.tab_bar():
            with dpg.tab(label='环境变量'):
                EnvUI(analyzer).build()
                dpg.add_input_text(tag='analysis_output_env', label='分析结果', multiline=True, readonly=True)
            with dpg.tab(label='注册表'):
                RegUI(analyzer).build()
            with dpg.tab(label='模型配置'):
                ConfigUI(analyzer).build()
