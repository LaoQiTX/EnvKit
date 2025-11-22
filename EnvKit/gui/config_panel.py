import dearpygui.dearpygui as dpg
from core.analyzer import Analyzer

class ConfigUI:
    def __init__(self, analyzer: Analyzer):
        self.analyzer = analyzer

    def build(self):
        dpg.add_text('模型列表')
        dpg.add_listbox(tag='model_list', items=[m['name'] for m in self.analyzer.models()])
        dpg.add_button(label='设置为默认模型', callback=self._set_default)
        dpg.add_button(label='删除选中模型', callback=self._delete_selected)
        dpg.add_button(label='刷新列表', callback=self._refresh_list)
        dpg.add_separator()
        dpg.add_text('添加模型')
        dpg.add_input_text(tag='new_model_name', label='名称')
        dpg.add_radio_button(tag='new_model_type', items=['rule', 'http'], default_value='http')
        dpg.add_input_text(tag='new_model_endpoint', label='HTTP端点')
        dpg.add_input_text(tag='new_model_model', label='模型名(可选)')
        dpg.add_input_text(tag='new_model_key', label='API Key', password=True)
        dpg.add_button(label='添加模型', callback=self._add_model)

    def _set_default(self, sender, data):
        name = dpg.get_value('model_list')
        if name:
            self.analyzer.set_default(name)

    def _delete_selected(self, sender, data):
        name = dpg.get_value('model_list')
        if name:
            self.analyzer.remove_model(name)
            self._refresh_list(sender, data)

    def _refresh_list(self, sender, data):
        dpg.configure_item('model_list', items=[m['name'] for m in self.analyzer.models()])

    def _add_model(self, sender, data):
        name = dpg.get_value('new_model_name')
        mtype = dpg.get_value('new_model_type')
        endpoint = dpg.get_value('new_model_endpoint')
        model = dpg.get_value('new_model_model')
        key = dpg.get_value('new_model_key')
        if not name:
            return
        mdef = {'name': name, 'type': mtype}
        if mtype == 'http':
            mdef['endpoint'] = endpoint
            if model:
                mdef['model'] = model
            if key:
                mdef['api_key'] = key
        self.analyzer.add_model(mdef)
        self._refresh_list(sender, data)
        dpg.set_value('new_model_name', '')
        dpg.set_value('new_model_endpoint', '')
        dpg.set_value('new_model_model', '')
        dpg.set_value('new_model_key', '')
