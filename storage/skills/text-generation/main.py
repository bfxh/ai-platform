from core.plugin_system.plugin_interface import PluginInterface

class Plugin(PluginInterface):
    def __init__(self):
        self.config = {
            "default_model": "gpt-3.5-turbo",
            "max_tokens": 1000
        }
    
    def initialize(self):
        """初始化插件"""
        print("Initializing Text Generation Skill")
    
    def execute(self, prompt, model=None, max_tokens=None):
        """执行文本生成"""
        model = model or self.config["default_model"]
        max_tokens = max_tokens or self.config["max_tokens"]
        
        print(f"Generating text with model {model} and max tokens {max_tokens}")
        print(f"Prompt: {prompt}")
        
        # 这里应该调用实际的模型进行文本生成
        # 示例返回值
        return f"Generated text for prompt: {prompt}"
    
    def cleanup(self):
        """清理插件资源"""
        print("Cleaning up Text Generation Skill")
    
    def get_config(self):
        """获取插件配置"""
        return self.config
    
    def set_config(self, config):
        """设置插件配置"""
        self.config.update(config)