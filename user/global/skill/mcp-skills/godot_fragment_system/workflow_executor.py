import json
import time

class WorkflowExecutor:
    def __init__(self, system):
        self.system = system
    
    def load_workflow(self, workflow_file):
        """加载工作流定义文件"""
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            return workflow_data
        except Exception as e:
            print(f"加载工作流文件失败: {str(e)}")
            return None
    
    def execute_workflow(self, workflow_name, workflow_data):
        """执行工作流"""
        if workflow_name not in workflow_data.get('workflows', {}):
            print(f"工作流 {workflow_name} 不存在")
            return False
        
        workflow = workflow_data['workflows'][workflow_name]
        print(f"开始执行工作流: {workflow['description']}")
        
        for i, step in enumerate(workflow['steps']):
            command = step['command']
            parameters = step.get('parameters', {})
            
            print(f"执行步骤 {i+1}: {command}")
            
            # 执行命令
            if hasattr(self.system, command):
                method = getattr(self.system, command)
                result = method(**parameters)
                
                print(f"  结果: {result['message']}")
                
                if not result.get('success', False):
                    print(f"  步骤执行失败，工作流终止")
                    return False
            else:
                print(f"  命令 {command} 不存在")
                return False
            
            # 等待完成
            if step.get('wait_for_completion', True):
                time.sleep(1)  # 简单的等待
        
        print(f"工作流 {workflow_name} 执行完成")
        return True

if __name__ == "__main__":
    from fragment_weapon_system import FragmentWeaponSystem
    
    # 创建碎片武器系统实例
    system = FragmentWeaponSystem()
    
    # 创建工作流执行器
    executor = WorkflowExecutor(system)
    
    # 加载工作流
    workflow_data = executor.load_workflow('fragment_weapon_workflow.mcp')
    
    if workflow_data:
        # 执行收集和制造工作流
        print("\n=== 执行收集和制造工作流 ===")
        executor.execute_workflow('collect_and_craft', workflow_data)
        
        # 执行完整游戏周期工作流
        print("\n=== 执行完整游戏周期工作流 ===")
        # 注意：这个工作流会启动Godot游戏，需要谨慎执行
        # executor.execute_workflow('full_game_cycle', workflow_data)