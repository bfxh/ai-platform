from core.plugin_system.plugin_interface import PluginInterface

class Plugin(PluginInterface):
    def __init__(self):
        self.config = {
            "name": "Basic Workflow",
            "steps": [
                "text_generation"
            ]
        }
    
    def initialize(self):
        """初始化插件"""
        print("Initializing Basic Workflow")
    
    def execute(self, data):
        """执行工作流"""
        print("Executing Basic Workflow")
        
        # 这里应该执行工作流的各个步骤
        # 示例返回值
        return {
            "status": "completed",
            "result": f"Workflow executed with data: {data}"
        }
    
    def cleanup(self):
        """清理插件资源"""
        print("Cleaning up Basic Workflow")
    
    def get_config(self):
        """获取插件配置"""
        return self.config
    
    def set_config(self, config):
        """设置插件配置"""
        self.config.update(config)