import os
import json
from core.plugin_system.plugin_manager import PluginManager

class AISystem:
    def __init__(self, config_path):
        # 加载系统配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 初始化插件管理器
        self.plugin_manager = PluginManager("plugins")
        self.plugin_manager.discover_plugins()
        
        print("AI System initialized")
        print(f"Available plugins: {self.plugin_manager.get_available_plugins()}")
    
    def run(self):
        """运行系统"""
        print("Running AI System")
        
        # 示例：加载并执行文本生成插件
        try:
            text_plugin = self.plugin_manager.load_plugin("text_generation")
            result = text_plugin.execute("Hello, AI!")
            print(f"Text generation result: {result}")
        except Exception as e:
            print(f"Error executing text generation plugin: {e}")
        
        # 示例：加载并执行工作流插件
        try:
            workflow_plugin = self.plugin_manager.load_plugin("basic")
            result = workflow_plugin.execute({"prompt": "Hello, Workflow!"})
            print(f"Workflow result: {result}")
        except Exception as e:
            print(f"Error executing workflow plugin: {e}")
    
    def shutdown(self):
        """关闭系统"""
        print("Shutting down AI System")
        
        # 卸载所有加载的插件
        for plugin_name in self.plugin_manager.get_loaded_plugins():
            self.plugin_manager.unload_plugin(plugin_name)

if __name__ == "__main__":
    # 创建并运行 AI 系统
    system = AISystem("config.json")
    system.run()
    system.shutdown()