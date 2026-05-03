#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边界情况和异常处理测试
测试各种极端情况和异常场景
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from skills.base import Skill, handle_errors
from skills.ai_toolkit_ecosystem.skill import AIToolkitEcosystem
from skills.network_transfer.skill import NetworkTransferSkill
from skills.download_manager.skill import DownloadManagerSkill


class TestEdgeCases:
    """边界情况测试类"""

    def test_skill_with_none_config(self):
        """测试技能初始化 - None 配置"""
        skill = AIToolkitEcosystem(config=None)
        assert skill is not None
        assert skill.name == "ai_toolkit_ecosystem"

    def test_skill_with_empty_config(self):
        """测试技能初始化 - 空配置"""
        skill = AIToolkitEcosystem(config={})
        assert skill is not None

    def test_skill_with_invalid_config_type(self):
        """测试技能初始化 - 无效配置类型"""
        # 测试传入字符串而不是字典
        skill = AIToolkitEcosystem(config="invalid")
        assert skill is not None

    def test_execute_with_very_long_params(self):
        """测试执行 - 超长参数"""
        skill = AIToolkitEcosystem()
        long_string = "a" * 10000
        result = skill.execute({"action": "list", "extra": long_string})
        assert isinstance(result, dict)

    def test_execute_with_special_characters(self):
        """测试执行 - 特殊字符参数"""
        skill = AIToolkitEcosystem()
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = skill.execute({"action": "list", "special": special_chars})
        assert isinstance(result, dict)

    def test_execute_with_unicode(self):
        """测试执行 - Unicode 字符"""
        skill = AIToolkitEcosystem()
        unicode_text = "你好世界 🌍 émojis ñoño"
        result = skill.execute({"action": "list", "text": unicode_text})
        assert isinstance(result, dict)

    def test_execute_with_nested_dict(self):
        """测试执行 - 嵌套字典参数"""
        skill = AIToolkitEcosystem()
        nested = {"level1": {"level2": {"level3": "value"}}}
        result = skill.execute({"action": "list", "nested": nested})
        assert isinstance(result, dict)

    def test_execute_with_list_params(self):
        """测试执行 - 列表参数"""
        skill = AIToolkitEcosystem()
        result = skill.execute({"action": "list", "items": [1, 2, 3, "a", "b", "c"]})
        assert isinstance(result, dict)

    def test_execute_with_boolean_params(self):
        """测试执行 - 布尔参数"""
        skill = AIToolkitEcosystem()
        result = skill.execute({"action": "list", "flag": True, "other": False})
        assert isinstance(result, dict)

    def test_execute_with_numeric_params(self):
        """测试执行 - 数值参数"""
        skill = AIToolkitEcosystem()
        result = skill.execute({"action": "list", "int": 42, "float": 3.14})
        assert isinstance(result, dict)

    def test_execute_with_none_values(self):
        """测试执行 - None 值参数"""
        skill = AIToolkitEcosystem()
        result = skill.execute({"action": "list", "null_value": None})
        assert isinstance(result, dict)

    def test_multiple_skills_concurrent_access(self):
        """测试多个技能并发访问"""
        skill1 = AIToolkitEcosystem()
        skill2 = NetworkTransferSkill()
        skill3 = DownloadManagerSkill()

        result1 = skill1.execute({"action": "list"})
        result2 = skill2.execute({"action": "status"})
        result3 = skill3.execute({"action": "queue_status"})

        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert isinstance(result3, dict)


class TestExceptionHandling:
    """异常处理测试类"""

    def test_handle_errors_decorator_with_exception(self):
        """测试错误处理装饰器 - 捕获异常"""

        class TestSkill(Skill):
            name = "test_skill"
            description = "测试技能"
            version = "1.0.0"

            @handle_errors
            def execute(self, params):
                raise ValueError("测试异常")

        skill = TestSkill()
        result = skill.execute({"action": "test"})

        assert result["success"] is False
        assert "error" in result
        assert "测试异常" in result["error"]

    def test_handle_errors_decorator_with_key_error(self):
        """测试错误处理装饰器 - KeyError"""

        class TestSkill(Skill):
            name = "test_skill"
            description = "测试技能"
            version = "1.0.0"

            @handle_errors
            def execute(self, params):
                data = {}
                return {"success": True, "value": data["missing_key"]}

        skill = TestSkill()
        result = skill.execute({"action": "test"})

        assert result["success"] is False
        assert "error" in result

    def test_handle_errors_decorator_with_type_error(self):
        """测试错误处理装饰器 - TypeError"""

        class TestSkill(Skill):
            name = "test_skill"
            description = "测试技能"
            version = "1.0.0"

            @handle_errors
            def execute(self, params):
                return "string" + 123  # 类型错误

        skill = TestSkill()
        result = skill.execute({"action": "test"})

        assert result["success"] is False
        assert "error" in result

    def test_handle_errors_decorator_with_attribute_error(self):
        """测试错误处理装饰器 - AttributeError"""

        class TestSkill(Skill):
            name = "test_skill"
            description = "测试技能"
            version = "1.0.0"

            @handle_errors
            def execute(self, params):
                obj = None
                return obj.some_method()  # AttributeError

        skill = TestSkill()
        result = skill.execute({"action": "test"})

        assert result["success"] is False
        assert "error" in result

    def test_skill_with_missing_required_method(self):
        """测试技能 - 缺少必需方法"""

        class IncompleteSkill(Skill):
            name = "incomplete"
            description = "不完整的技能"
            version = "1.0.0"

            # 没有实现 execute 方法

        # 应该抛出 TypeError，因为 execute 是抽象方法
        with pytest.raises(TypeError):
            IncompleteSkill()

    def test_skill_with_invalid_return_type(self):
        """测试技能 - 无效返回类型"""

        class BadReturnSkill(Skill):
            name = "bad_return"
            description = "返回类型错误的技能"
            version = "1.0.0"

            def execute(self, params):
                return "not a dict"  # 应该返回字典

        skill = BadReturnSkill()
        result = skill.execute({"action": "test"})

        # 即使返回类型错误，也不应该抛出异常
        assert result is not None

    def test_validate_params_with_none(self):
        """测试参数验证 - None 参数"""
        skill = AIToolkitEcosystem()
        is_valid, error = skill.validate_params(None)
        assert is_valid is False
        assert error is not None

    def test_validate_params_with_non_dict(self):
        """测试参数验证 - 非字典参数"""
        skill = AIToolkitEcosystem()
        is_valid, error = skill.validate_params("string")
        assert is_valid is False
        assert error is not None

    def test_validate_params_with_list(self):
        """测试参数验证 - 列表参数"""
        skill = AIToolkitEcosystem()
        is_valid, error = skill.validate_params([1, 2, 3])
        assert is_valid is False
        assert error is not None

    def test_get_config_with_invalid_key(self):
        """测试配置获取 - 无效键"""
        skill = AIToolkitEcosystem()
        # 测试获取不存在的配置键
        result = skill.get_config("non_existent_key", default="default_value")
        assert result == "default_value"

    def test_get_config_with_none_key(self):
        """测试配置获取 - None 键"""
        skill = AIToolkitEcosystem()
        result = skill.get_config(None, default="default")
        assert result == "default"


class TestPerformanceEdgeCases:
    """性能边界情况测试"""

    def test_execute_multiple_times(self):
        """测试多次执行技能"""
        skill = AIToolkitEcosystem()

        for i in range(10):
            result = skill.execute({"action": "list"})
            assert isinstance(result, dict)
            assert "success" in result

    def test_execute_with_large_data(self):
        """测试执行 - 大数据量"""
        skill = AIToolkitEcosystem()
        large_data = {"items": list(range(1000))}
        result = skill.execute({"action": "list", "data": large_data})
        assert isinstance(result, dict)


class TestSecurityEdgeCases:
    """安全边界情况测试"""

    def test_execute_with_sql_injection_attempt(self):
        """测试执行 - SQL 注入尝试"""
        skill = AIToolkitEcosystem()
        sql_injection = "'; DROP TABLE users; --"
        result = skill.execute({"action": "list", "input": sql_injection})
        assert isinstance(result, dict)

    def test_execute_with_path_traversal(self):
        """测试执行 - 路径遍历尝试"""
        skill = AIToolkitEcosystem()
        path_traversal = "../../../etc/passwd"
        result = skill.execute({"action": "list", "path": path_traversal})
        assert isinstance(result, dict)

    def test_execute_with_script_injection(self):
        """测试执行 - 脚本注入尝试"""
        skill = AIToolkitEcosystem()
        script = "<script>alert('xss')</script>"
        result = skill.execute({"action": "list", "input": script})
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
