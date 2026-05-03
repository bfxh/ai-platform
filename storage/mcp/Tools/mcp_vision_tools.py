#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 视觉工具集成 - 支持有视觉和无视觉调用

功能：
1. 无视觉模式：直接调用工具，无需屏幕感知
2. 有视觉模式：通过屏幕截图+AI分析，智能调用工具
3. 视觉引导自动化：看到什么就操作什么
4. 工具链组合：多个工具串联执行

用法：
    python mcp_vision_tools.py <mode> <action> [params]

模式：
    --no-vision    无视觉模式（直接调用）
    --vision       有视觉模式（屏幕感知）
    --hybrid       混合模式（优先无视觉，需要时启用视觉）

示例：
    # 无视觉调用
    python mcp_vision_tools.py --no-vision call blender open file=model.blend
    
    # 有视觉调用（自动截屏分析）
    python mcp_vision_tools.py --vision click "保存按钮"
    
    # 混合模式
    python mcp_vision_tools.py --hybrid workflow import_3d_asset
    
    # 视觉引导自动化
    python mcp_vision_tools.py --vision auto "打开Blender并导入模型"

MCP调用：
    {"tool": "mcp_vision_tools", "mode": "vision", "action": "click", "target": "保存按钮"}
"""

import json
import sys
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
VISION_PRO = MCP_PATH / "vision_pro.py"
DA = MCP_PATH / "da.py"
MCP_WORKFLOW = MCP_PATH / "mcp_workflow.py"

# ============================================================
# 视觉感知模块
# ============================================================
class VisionPerception:
    """视觉感知模块 - 屏幕理解和分析"""
    
    def __init__(self):
        self.last_screenshot = None
        self.last_analysis = None
    
    def capture_screen(self, region: Tuple[int, int, int, int] = None) -> str:
        """截取屏幕"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = MCP_PATH / "temp" / f"vision_{timestamp}.bmp"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            result = subprocess.run(
                ["python", str(VISION_PRO), "capture", str(screenshot_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.last_screenshot = str(screenshot_path)
                return self.last_screenshot
            else:
                return None
        except Exception as e:
            print(f"截图失败: {e}")
            return None
    
    def analyze_screen(self, screenshot_path: str = None) -> Dict:
        """分析屏幕内容"""
        path = screenshot_path or self.last_screenshot
        
        if not path or not Path(path).exists():
            return {"error": "没有可用的截图"}
        
        try:
            result = subprocess.run(
                ["python", str(VISION_PRO), "screen_analyze", path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    analysis = json.loads(result.stdout)
                    self.last_analysis = analysis
                    return analysis
                except:
                    return {"raw": result.stdout}
            else:
                return {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}
    
    def find_element(self, element_type: str, name: str = None) -> Dict:
        """查找界面元素"""
        # 先截图
        screenshot = self.capture_screen()
        if not screenshot:
            return {"error": "截图失败"}
        
        try:
            if element_type == "text":
                # OCR识别文字
                result = subprocess.run(
                    ["python", str(VISION_PRO), "ocr", screenshot],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            elif element_type == "button":
                # UI元素检测
                result = subprocess.run(
                    ["python", str(VISION_PRO), "ui_detect", screenshot],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            elif element_type == "image":
                # 模板匹配
                result = subprocess.run(
                    ["python", str(VISION_PRO), "find_image", name, screenshot],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            elif element_type == "color":
                # 颜色检测
                result = subprocess.run(
                    ["python", str(VISION_PRO), "find_color", name, screenshot],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                return {"error": f"不支持的元素类型: {element_type}"}
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except:
                    return {"result": result.stdout}
            else:
                return {"error": result.stderr}
        
        except Exception as e:
            return {"error": str(e)}
    
    def get_click_position(self, target: str) -> Tuple[int, int]:
        """获取点击位置"""
        # 尝试多种方式定位
        
        # 1. 尝试作为文字查找
        result = self.find_element("text", target)
        if "position" in result:
            return result["position"]
        
        # 2. 尝试作为按钮查找
        result = self.find_element("button", target)
        if "position" in result:
            return result["position"]
        
        # 3. 尝试作为图像查找
        result = self.find_element("image", target)
        if "position" in result:
            return result["position"]
        
        return None

# ============================================================
# 工具调用器
# ============================================================
class ToolInvoker:
    """工具调用器 - 执行各种工具"""
    
    def __init__(self):
        self.vision = VisionPerception()
    
    def invoke_no_vision(self, tool: str, action: str, params: Dict = None) -> Dict:
        """无视觉调用工具"""
        params = params or {}
        
        # 直接调用 mcp_workflow
        try:
            cmd = ["python", str(MCP_WORKFLOW), "call", tool, action]
            
            # 添加参数
            for k, v in params.items():
                cmd.append(f"{k}={v}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except:
                    return {"success": True, "result": result.stdout}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def invoke_with_vision(self, action: str, target: str = None, params: Dict = None) -> Dict:
        """有视觉调用工具"""
        params = params or {}
        
        # 根据动作类型选择视觉策略
        if action in ["click", "double_click", "right_click"]:
            return self._vision_click(target, params)
        
        elif action in ["type", "input"]:
            return self._vision_type(target, params.get("text", ""), params)
        
        elif action == "find":
            return self.vision.find_element("text", target)
        
        elif action == "wait_for":
            return self._vision_wait_for(target, params.get("timeout", 30))
        
        elif action == "drag":
            return self._vision_drag(target, params.get("to"), params)
        
        elif action == "scroll":
            return self._vision_scroll(params.get("direction", "down"), params.get("amount", 3))
        
        elif action == "screenshot":
            path = self.vision.capture_screen()
            return {"success": True, "screenshot": path}
        
        elif action == "analyze":
            analysis = self.vision.analyze_screen()
            return {"success": True, "analysis": analysis}
        
        elif action == "auto":
            return self._vision_auto(target, params)
        
        else:
            return {"error": f"不支持的有视觉操作: {action}"}
    
    def _vision_click(self, target: str, params: Dict) -> Dict:
        """视觉引导点击"""
        print(f"[视觉] 查找点击目标: {target}")
        
        # 获取点击位置
        position = self.vision.get_click_position(target)
        
        if not position:
            return {"success": False, "error": f"未找到目标: {target}"}
        
        x, y = position
        print(f"[视觉] 找到目标位置: ({x}, {y})")
        
        # 执行点击
        try:
            click_type = params.get("click_type", "click")
            
            if click_type == "double":
                result = subprocess.run(
                    ["python", str(DA), "double_click", str(x), str(y)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            elif click_type == "right":
                result = subprocess.run(
                    ["python", str(DA), "right_click", str(x), str(y)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                result = subprocess.run(
                    ["python", str(DA), "click", str(x), str(y)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            if result.returncode == 0:
                return {"success": True, "action": "click", "target": target, "position": [x, y]}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _vision_type(self, target: str, text: str, params: Dict) -> Dict:
        """视觉引导输入"""
        print(f"[视觉] 查找输入目标: {target}")
        
        # 先点击输入框
        if target:
            click_result = self._vision_click(target, {})
            if not click_result.get("success"):
                return click_result
            
            time.sleep(0.5)  # 等待输入框激活
        
        # 输入文字
        try:
            result = subprocess.run(
                ["python", str(DA), "type", text],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {"success": True, "action": "type", "text": text}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _vision_wait_for(self, target: str, timeout: int) -> Dict:
        """视觉等待目标出现"""
        print(f"[视觉] 等待目标出现: {target} (超时: {timeout}s)")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            position = self.vision.get_click_position(target)
            
            if position:
                return {"success": True, "target": target, "position": position, "wait_time": time.time() - start_time}
            
            time.sleep(1)
        
        return {"success": False, "error": f"等待超时: {target}"}
    
    def _vision_drag(self, from_target: str, to_target: str, params: Dict) -> Dict:
        """视觉引导拖拽"""
        print(f"[视觉] 拖拽: {from_target} -> {to_target}")
        
        # 获取起点和终点
        from_pos = self.vision.get_click_position(from_target)
        to_pos = self.vision.get_click_position(to_target)
        
        if not from_pos:
            return {"success": False, "error": f"未找到起点: {from_target}"}
        
        if not to_pos:
            return {"success": False, "error": f"未找到终点: {to_target}"}
        
        try:
            result = subprocess.run(
                ["python", str(DA), "drag", str(from_pos[0]), str(from_pos[1]), str(to_pos[0]), str(to_pos[1])],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {"success": True, "action": "drag", "from": from_target, "to": to_target}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _vision_scroll(self, direction: str, amount: int) -> Dict:
        """视觉引导滚动"""
        print(f"[视觉] 滚动: {direction} x {amount}")
        
        try:
            result = subprocess.run(
                ["python", str(DA), "scroll", str(amount), direction],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {"success": True, "action": "scroll", "direction": direction, "amount": amount}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _vision_auto(self, instruction: str, params: Dict) -> Dict:
        """视觉引导自动化（自然语言指令）"""
        print(f"[视觉] 执行自动化指令: {instruction}")
        
        # 解析指令
        steps = self._parse_instruction(instruction)
        
        results = []
        for step in steps:
            print(f"  执行: {step['action']} - {step.get('target', '')}")
            
            if step['action'] == 'click':
                result = self._vision_click(step['target'], step.get('params', {}))
            elif step['action'] == 'type':
                result = self._vision_type(step.get('target'), step.get('text', ''), step.get('params', {}))
            elif step['action'] == 'wait':
                time.sleep(step.get('seconds', 1))
                result = {"success": True, "action": "wait"}
            elif step['action'] == 'screenshot':
                path = self.vision.capture_screen()
                result = {"success": True, "screenshot": path}
            else:
                result = {"success": False, "error": f"未知操作: {step['action']}"}
            
            results.append(result)
            
            if not result.get("success"):
                print(f"  ✗ 失败: {result.get('error')}")
                break
            
            print(f"  ✓ 成功")
            time.sleep(0.5)  # 步骤间等待
        
        return {
            "success": all(r.get("success") for r in results),
            "instruction": instruction,
            "steps": len(steps),
            "results": results
        }
    
    def _parse_instruction(self, instruction: str) -> List[Dict]:
        """解析自然语言指令为操作步骤"""
        steps = []
        
        instruction_lower = instruction.lower()
        
        # 简单规则匹配
        if "打开" in instruction or "启动" in instruction:
            # 提取软件名
            software = self._extract_software_name(instruction)
            if software:
                steps.append({
                    "action": "click",
                    "target": software,
                    "params": {}
                })
                steps.append({
                    "action": "wait",
                    "seconds": 3
                })
        
        if "点击" in instruction or "按" in instruction:
            # 提取按钮名
            button = self._extract_button_name(instruction)
            if button:
                steps.append({
                    "action": "click",
                    "target": button,
                    "params": {}
                })
        
        if "输入" in instruction or "填写" in instruction:
            # 提取输入内容
            text = self._extract_input_text(instruction)
            field = self._extract_field_name(instruction)
            if text:
                steps.append({
                    "action": "type",
                    "target": field,
                    "text": text,
                    "params": {}
                })
        
        if "保存" in instruction:
            steps.append({
                "action": "click",
                "target": "保存",
                "params": {}
            })
        
        if "确定" in instruction or "确认" in instruction:
            steps.append({
                "action": "click",
                "target": "确定",
                "params": {}
            })
        
        # 如果没有匹配到任何步骤，默认截图分析
        if not steps:
            steps.append({
                "action": "screenshot"
            })
        
        return steps
    
    def _extract_software_name(self, instruction: str) -> str:
        """提取软件名"""
        # 简单提取"打开"后面的词
        if "打开" in instruction:
            parts = instruction.split("打开")
            if len(parts) > 1:
                return parts[1].split()[0].strip()
        return None
    
    def _extract_button_name(self, instruction: str) -> str:
        """提取按钮名"""
        if "点击" in instruction:
            parts = instruction.split("点击")
            if len(parts) > 1:
                return parts[1].split()[0].strip()
        return None
    
    def _extract_input_text(self, instruction: str) -> str:
        """提取输入文本"""
        # 简单实现，实际应该用NLP
        return ""
    
    def _extract_field_name(self, instruction: str) -> str:
        """提取字段名"""
        return None

# ============================================================
# MCP 接口
# ============================================================
class MCPVisionTools:
    """MCP 视觉工具接口"""
    
    def __init__(self):
        self.invoker = ToolInvoker()
    
    def handle(self, request: Dict) -> Dict:
        """处理MCP请求"""
        mode = request.get("mode", "no-vision")
        action = request.get("action")
        params = request.get("params", {})
        
        if mode == "no-vision":
            # 无视觉模式
            tool = request.get("tool")
            return self.invoker.invoke_no_vision(tool, action, params)
        
        elif mode == "vision":
            # 有视觉模式
            target = request.get("target")
            return self.invoker.invoke_with_vision(action, target, params)
        
        elif mode == "hybrid":
            # 混合模式
            return self._handle_hybrid(request)
        
        else:
            return {"success": False, "error": f"未知模式: {mode}"}
    
    def _handle_hybrid(self, request: Dict) -> Dict:
        """处理混合模式请求"""
        # 先尝试无视觉模式
        tool = request.get("tool")
        action = request.get("action")
        params = request.get("params", {})
        
        result = self.invoker.invoke_no_vision(tool, action, params)
        
        # 如果失败，尝试视觉模式
        if not result.get("success"):
            target = request.get("target") or action
            result = self.invoker.invoke_with_vision(action, target, params)
        
        return result

# ============================================================
# 命令行接口
# ============================================================
def main():
    """主函数"""
    if len(sys.argv) < 3:
        print(__doc__)
        return
    
    mode = sys.argv[1]
    action = sys.argv[2]
    
    invoker = ToolInvoker()
    
    if mode == "--no-vision":
        # 无视觉模式
        if action == "call":
            if len(sys.argv) < 5:
                print("用法: --no-vision call <tool> <action> [params...]")
                return
            
            tool = sys.argv[3]
            tool_action = sys.argv[4]
            params = {}
            
            for arg in sys.argv[5:]:
                if '=' in arg:
                    k, v = arg.split('=', 1)
                    params[k] = v
            
            result = invoker.invoke_no_vision(tool, tool_action, params)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        elif action == "workflow":
            if len(sys.argv) < 4:
                print("用法: --no-vision workflow <workflow_name>")
                return
            
            workflow_name = sys.argv[3]
            result = invoker.invoke_no_vision("mcp_workflow", "workflow", {"name": workflow_name})
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        else:
            print(f"未知操作: {action}")
    
    elif mode == "--vision":
        # 有视觉模式
        target = sys.argv[3] if len(sys.argv) > 3 else None
        params = {}
        
        for arg in sys.argv[4:]:
            if '=' in arg:
                k, v = arg.split('=', 1)
                params[k] = v
        
        result = invoker.invoke_with_vision(action, target, params)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif mode == "--hybrid":
        # 混合模式
        tool = sys.argv[3] if len(sys.argv) > 3 else None
        tool_action = sys.argv[4] if len(sys.argv) > 4 else action
        params = {}
        
        for arg in sys.argv[5:]:
            if '=' in arg:
                k, v = arg.split('=', 1)
                params[k] = v
        
        result = invoker.invoke_no_vision(tool, tool_action, params)
        
        if not result.get("success"):
            result = invoker.invoke_with_vision(tool_action, tool, params)
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif mode == "--mcp":
        # MCP服务器模式
        print("MCP 视觉工具服务器已启动")
        print("支持模式: no-vision, vision, hybrid")
        
        mcp = MCPVisionTools()
        
        import select
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    response = mcp.handle(request)
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print(json.dumps({"success": False, "error": "无效的JSON"}))
                    sys.stdout.flush()
    
    else:
        print(f"未知模式: {mode}")
        print(__doc__)

if __name__ == "__main__":
    main()
