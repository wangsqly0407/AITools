#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
函数调用指标评估工具模块

该模块提供了评估函数调用预测结果与参考结果匹配度的功能。
"""

import json
from typing import List, Dict, Any


def evaluate_function_calls_metrics(
        predictions: List[Dict[str, Any]], 
        references: List[Dict[str, Any]], 
        number: int = 1
) -> Dict[str, Any]:
    """
    评估函数调用指标，计算预测结果与参考结果的交集及相关指标
    
    该函数接收预测结果和参考结果两个列表，根据函数名称（function.name）作为唯一标识符，
    找出两个列表中的交集元素，返回匹配的函数调用记录以及工具识别率和调用准确率。
    
    Args:
        predictions (List[Dict[str, Any]]): 预测结果列表，每个元素包含函数调用信息
            格式: [{
                "id": str,
                "type": "function", 
                "function": {
                    "name": str,
                    "arguments": str (JSON格式字符串)
                }
            }, ...]
            
        references (List[Dict[str, Any]]): 参考结果列表，格式与predictions相同
        
        number (int, optional): 判断工作流选择正确性的阈值，默认为1
            必须为非负数（>= 0），交集个数 >= number 时认为选择了正确的工作流
    
    Returns:
        Dict[str, Any]: 返回包含以下字段的字典:
            - "fcm": List[Dict[str, Any]] - 匹配的函数调用记录列表
            - "tool_recognition_rate": bool - 工具识别率，predictions非空为True
            - "correct_workflow_selection": bool - 是否选择了正确的工作流
            - "hallucination_rate": float - 幻觉率，
              (predictions独有数量)/references数量
    
    Raises:
        ValueError: 当输入参数格式不正确时抛出
        TypeError: 当输入参数类型不正确时抛出
    
    Examples:
        >>> predictions = [{
        ...     "id": "test-1",
        ...     "type": "function",
        ...     "function": {"name": "智能体-A", "arguments": "{}"}
        ... }]
        >>> references = [{
        ...     "id": "ref-1", 
        ...     "type": "function",
        ...     "function": {"name": "智能体-A", "arguments": "{}"}
        ... }]
        >>> result = evaluate_function_calls_metrics(predictions, references)
        >>> len(result["fcm"]) == 1
        True
        >>> result["tool_recognition_rate"]
        True
    """
    
    # 1. 基本类型校验
    if not isinstance(predictions, list):
        raise TypeError(
            f"predictions 必须是 list 类型，当前类型: "
            f"{type(predictions).__name__}"
        )
    
    if not isinstance(references, list):
        raise TypeError(
            f"references 必须是 list 类型，当前类型: "
            f"{type(references).__name__}"
        )
    
    # 2. 新增参数类型校验
    if not isinstance(number, int):
        raise TypeError(
            f"number 必须是 int 类型，当前类型: "
            f"{type(number).__name__}"
        )
    
    # 3. 校验number参数必须为非负数
    if number < 0:
        raise ValueError(f"number 必须是非负数，当前值: {number}")
    
    # 4. 计算工具识别率
    tool_recognition_rate = len(predictions) > 0
    
    # 5. 处理空列表情况
    if not predictions or not references:
        # 计算幻觉率：(predictions独有数量) / references数量
        if len(predictions) == 0:
            # predictions为空，没有预测就没有幻觉
            hallucination_rate = 0.0
        else:
            # predictions不为空但references为空，所有predictions都是幻觉
            hallucination_rate = float('inf')
        
        return {
            "fcm": [],
            "tool_recognition_rate": tool_recognition_rate,
            # 空列表时无法选择正确的工作流
            "correct_workflow_selection": False,
            "hallucination_rate": hallucination_rate
        }
    
    # 6. 验证列表元素格式
    def validate_function_call_format(item: Any, item_type: str, index: int) -> None:
        """验证单个函数调用记录的格式"""
        if not isinstance(item, dict):
            raise ValueError(
                f"{item_type}[{index}] 必须是 dict 类型，"
                f"当前类型: {type(item).__name__}"
            )
        
        # 检查必需字段
        required_fields = ["id", "type", "function"]
        for field in required_fields:
            if field not in item:
                raise ValueError(
                    f"{item_type}[{index}] 缺少必需字段: {field}"
                )
        
        # 检查 type 字段值
        if item["type"] != "function":
            raise ValueError(
                f"{item_type}[{index}] 的 type 字段必须为 'function'，"
                f"当前值: {item['type']}"
            )
        
        # 检查 function 字段格式
        function_obj = item["function"]
        if not isinstance(function_obj, dict):
            raise ValueError(
                f"{item_type}[{index}] 的 function 字段必须是 dict 类型"
            )
        
        function_required_fields = ["name", "arguments"]
        for field in function_required_fields:
            if field not in function_obj:
                raise ValueError(
                    f"{item_type}[{index}] 的 function 缺少必需字段: {field}"
                )
        
        # 验证 arguments 是否为有效 JSON 字符串
        try:
            json.loads(function_obj["arguments"])
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(
                f"{item_type}[{index}] 的 function.arguments "
                f"不是有效的 JSON 字符串: {e}"
            )
    
    # 7. 验证所有元素格式
    for i, pred in enumerate(predictions):
        validate_function_call_format(pred, "predictions", i)
    
    for i, ref in enumerate(references):
        validate_function_call_format(ref, "references", i)
    
    # 8. 创建参考结果的函数名称集合，便于快速查找
    reference_function_names = {ref["function"]["name"] for ref in references}
    
    # 9. 找出交集：predictions 中的函数名称在 references 中存在的记录
    matched_calls = []
    for pred in predictions:
        function_name = pred["function"]["name"]
        if function_name in reference_function_names:
            matched_calls.append(pred)
    
    # 10. 计算各种指标
    intersection_count = len(matched_calls)  # 交集数量
    predictions_count = len(predictions)     # 预测数量
    references_count = len(references)       # 参考数量
    
    # 计算工作流选择正确性
    correct_workflow_selection = intersection_count >= number
    
    # 计算幻觉率：(predictions独有数量) / references数量
    # predictions独有的数量
    predictions_only_count = predictions_count - intersection_count
    if references_count == 0:
        if predictions_only_count > 0:
            hallucination_rate = float('inf')
        else:
            hallucination_rate = 0.0
    else:
        hallucination_rate = predictions_only_count / references_count
    
    return {
        "fcm": matched_calls,
        "tool_recognition_rate": tool_recognition_rate,
        "correct_workflow_selection": correct_workflow_selection,
        "hallucination_rate": hallucination_rate
    }


def run_tests():
    """运行单元测试和功能测试"""
    import traceback
    
    print("=" * 60)
    print("开始运行 evaluate_function_calls_metrics 函数测试")
    print("=" * 60)
    
    passed_count = 0
    
    # 测试用例1：正常情况 - 有交集
    def test_normal_intersection():
        predictions = [
            {
                "id": "chatcmpl-tool-1f7c0ca26c8240d98a54db95c9a3b369",
                "type": "function",
                "function": {
                    "name": "企业金融行为智能体-V3",
                    "arguments": "{\"reason\": \"用户询问北京源码资本投资有限公司自2023年以来退出的风险投资事件\"}"
                }
            },
            {
                "id": "chatcmpl-tool-51300ca26c8240018a54db95c9a3cdef",
                "type": "function", 
                "function": {
                    "name": "智能体-1",
                    "arguments": "{\"reason\": \"用户询问xx公司自2020年以来退出的风险投资事件\"}"
                }
            }
        ]
        
        references = [
            {
                "id": "chatcmpl-tool-1f7c0ca26c8240d98a54db95c9a3b369",
                "type": "function",
                "function": {
                    "name": "企业金融行为智能体-V3",
                    "arguments": "{\"reason\": \"用户询问北京源码资本投资有限公司自2023年以来退出的风险投资事件\"}"
                }
            },
            {
                "id": "chatcmpl-tool-2a3b0ca26c8240018a54db95c9a3a9b6",
                "type": "function",
                "function": {
                    "name": "智能体-5", 
                    "arguments": "{\"reason\": \"用户询问xx公司自2020年以来退出的风险投资事件\"}"
                }
            }
        ]
        
        result = evaluate_function_calls_metrics(predictions, references)
        
        # 验证结果
        assert "fcm" in result, "结果必须包含 fcm 字段"
        assert len(result["fcm"]) == 1, f"预期交集长度为1，实际为{len(result['fcm'])}"
        assert result["fcm"][0]["function"]["name"] == "企业金融行为智能体-V3", "交集元素函数名不匹配"
        
        # 验证新增指标
        assert result["tool_recognition_rate"] == True, "工具识别率应为True"
        # 交集数量为1，默认number=1，1 >= 1 为True
        assert result["correct_workflow_selection"] == True, "工作流选择应为正确（交集数量1等于阈值1）"
        # 幻觉率：predictions=2，交集=1，references=2，(2-1)/2=0.5
        assert result["hallucination_rate"] == 0.5, f"幻觉率应为0.5，实际为{result['hallucination_rate']}"
        
        return True, "正常情况测试通过"
    
    # 测试用例2：空列表情况
    def test_empty_lists():
        # predictions 为空，references 不为空
        test_ref = [{"id": "1", "type": "function", 
                     "function": {"name": "test", "arguments": "{}"}}]
        result1 = evaluate_function_calls_metrics([], test_ref)
        expected1 = {
            "fcm": [],
            "tool_recognition_rate": False,
            "correct_workflow_selection": False,
            "hallucination_rate": 0.0  # predictions为空，没有预测就没有幻觉
        }
        assert result1 == expected1, (
            f"predictions 为空时结果不正确，期望: {expected1}，实际: {result1}"
        )
        
        # predictions 不为空，references 为空  
        test_pred = [{"id": "1", "type": "function", 
                      "function": {"name": "test", "arguments": "{}"}}]
        result2 = evaluate_function_calls_metrics(test_pred, [])
        expected2 = {
            "fcm": [],
            "tool_recognition_rate": True,
            "correct_workflow_selection": False,
            "hallucination_rate": float('inf')  # references为空，所有predictions都是幻觉
        }
        assert result2 == expected2, (
            f"references 为空时结果不正确，期望: {expected2}，实际: {result2}"
        )
        
        # 都为空
        result3 = evaluate_function_calls_metrics([], [])
        expected3 = {
            "fcm": [],
            "tool_recognition_rate": False,
            "correct_workflow_selection": False,
            "hallucination_rate": 0.0  # predictions为空，没有预测就没有幻觉
        }
        assert result3 == expected3, (
            f"都为空时结果不正确，期望: {expected3}，实际: {result3}"
        )
        
        return True, "空列表情况测试通过"
    
    # 测试用例3：无交集情况
    def test_no_intersection():
        predictions = [{"id": "1", "type": "function", 
                        "function": {"name": "智能体-A", "arguments": "{}"}}]
        references = [{"id": "2", "type": "function", 
                       "function": {"name": "智能体-B", "arguments": "{}"}}]
        
        result = evaluate_function_calls_metrics(predictions, references)
        expected = {
            "fcm": [],
            "tool_recognition_rate": True,
            "correct_workflow_selection": False,
            "hallucination_rate": 1.0  # 1个predictions，0个交集，1个references：1/1=1.0
        }
        assert result == expected, (
            f"无交集时结果不正确，期望: {expected}，实际: {result}"
        )
        
        return True, "无交集情况测试通过"
    
    # 测试用例4：参数类型错误
    def test_type_errors():
        try:
            evaluate_function_calls_metrics("not_a_list", [])
            assert False, "应该抛出 TypeError"
        except TypeError as e:
            assert "predictions 必须是 list 类型" in str(e)
        
        try:
            evaluate_function_calls_metrics([], "not_a_list")
            assert False, "应该抛出 TypeError"
        except TypeError as e:
            assert "references 必须是 list 类型" in str(e)
        
        try:
            evaluate_function_calls_metrics([], [], "not_an_int")
            assert False, "应该抛出 TypeError"
        except TypeError as e:
            assert "number 必须是 int 类型" in str(e)
        
        # 测试负数number参数
        try:
            evaluate_function_calls_metrics([], [], -5)
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            assert "number 必须是非负数" in str(e)
        
        return True, "类型错误测试通过"
    
    # 测试用例5：格式校验错误
    def test_format_validation():
        # 缺少必需字段
        try:
            invalid_pred = [{"id": "1"}]
            valid_ref = [{"id": "2", "type": "function", 
                          "function": {"name": "test", "arguments": "{}"}}]
            evaluate_function_calls_metrics(invalid_pred, valid_ref)
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            assert "缺少必需字段" in str(e)
        
        # type 字段值错误
        try:
            invalid_type_pred = [{"id": "1", "type": "invalid", 
                                  "function": {"name": "test", "arguments": "{}"}}]
            valid_ref = [{"id": "2", "type": "function", 
                          "function": {"name": "test", "arguments": "{}"}}]
            evaluate_function_calls_metrics(invalid_type_pred, valid_ref)
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            assert "type 字段必须为 'function'" in str(e)
        
        # arguments 不是有效 JSON
        try:
            invalid_json_pred = [{"id": "1", "type": "function", 
                                  "function": {"name": "test", 
                                              "arguments": "invalid_json"}}]
            valid_ref = [{"id": "2", "type": "function", 
                          "function": {"name": "test", "arguments": "{}"}}]
            evaluate_function_calls_metrics(invalid_json_pred, valid_ref)
            assert False, "应该抛出 ValueError"  
        except ValueError as e:
            assert "不是有效的 JSON 字符串" in str(e)
        
        return True, "格式校验测试通过"
    
    # 测试用例6：完全匹配情况
    def test_full_match():
        data = [
            {"id": "1", "type": "function", 
             "function": {"name": "智能体-A", "arguments": "{}"}},
            {"id": "2", "type": "function", 
             "function": {"name": "智能体-B", "arguments": "{}"}}
        ]
        
        result = evaluate_function_calls_metrics(data, data)
        assert len(result["fcm"]) == 2, "完全匹配时应返回所有元素"
        assert result["tool_recognition_rate"] is True, "工具识别率应为True"
        assert result["correct_workflow_selection"] is True, "工作流选择应为正确"
        assert result["hallucination_rate"] == 0.0, "幻觉率应为0.0"
        
        return True, "完全匹配测试通过"
    
    # 测试用例7：新指标专项测试
    def test_new_metrics():
        # 测试 number 参数的影响
        predictions = [
            {"id": "1", "type": "function", 
             "function": {"name": "智能体-A", "arguments": "{}"}},
            {"id": "2", "type": "function", 
             "function": {"name": "智能体-B", "arguments": "{}"}}
        ]
        references = [
            {"id": "3", "type": "function", 
             "function": {"name": "智能体-A", "arguments": "{}"}},
            {"id": "4", "type": "function", 
             "function": {"name": "智能体-C", "arguments": "{}"}}
        ]
        
        # number=1 时，交集数量1 >= 1 为True
        result1 = evaluate_function_calls_metrics(
            predictions, references, number=1
        )
        assert result1["correct_workflow_selection"] is True, (
            "number=1时工作流选择应为True"
        )
        
        # number=0 时，交集数量1 >= 0 为True
        result2 = evaluate_function_calls_metrics(
            predictions, references, number=0
        )
        assert result2["correct_workflow_selection"] is True, (
            "number=0时工作流选择应为True"
        )
        
        # number=2 时，交集数量1 >= 2 为False
        result3 = evaluate_function_calls_metrics(
            predictions, references, number=2
        )
        assert result3["correct_workflow_selection"] is False, (
            "number=2时工作流选择应为False"
        )
        
        # 测试幻觉率计算：predictions=2，交集=1，references=2，幻觉率=(2-1)/2=0.5
        assert result1["hallucination_rate"] == 0.5, (
            f"幻觉率应为0.5，实际为{result1['hallucination_rate']}"
        )
        
        return True, "新指标专项测试通过"
    
    # 测试用例8：边界情况测试
    def test_edge_cases():
        # 测试references为0的幻觉率计算
        predictions = [{"id": "1", "type": "function", 
                        "function": {"name": "智能体-A", "arguments": "{}"}}]
        references = []
        
        result = evaluate_function_calls_metrics(predictions, references)
        assert result["hallucination_rate"] == float('inf'), (
            "references为0且有predictions时幻觉率应为inf"
        )
        assert result["tool_recognition_rate"] is True, (
            "有predictions时工具识别率应为True"
        )
        assert result["correct_workflow_selection"] is False, (
            "空references时工作流选择应为False"
        )
        
        # 测试多个相同名称函数的情况
        predictions_multi = [
            {"id": "1", "type": "function", 
             "function": {"name": "智能体-A", "arguments": "{}"}},
            {"id": "2", "type": "function",  # 重复名称
             "function": {"name": "智能体-A", "arguments": "{}"}},
            {"id": "3", "type": "function", 
             "function": {"name": "智能体-B", "arguments": "{}"}}
        ]
        references_multi = [
            {"id": "4", "type": "function", 
             "function": {"name": "智能体-A", "arguments": "{}"}},
            {"id": "5", "type": "function", 
             "function": {"name": "智能体-C", "arguments": "{}"}}
        ]
        
        result_multi = evaluate_function_calls_metrics(
            predictions_multi, references_multi
        )
        # 应该有2个智能体-A匹配（都匹配到references中的智能体-A）
        assert len(result_multi["fcm"]) == 2, "重复名称应该都被匹配"
        assert result_multi["fcm"][0]["function"]["name"] == "智能体-A"
        assert result_multi["fcm"][1]["function"]["name"] == "智能体-A"
        
        # 幻觉率计算：predictions=3，交集=2，references=2，幻觉率=(3-2)/2=0.5
        assert result_multi["hallucination_rate"] == 0.5, (
            f"多重匹配时幻觉率应为0.5，实际为{result_multi['hallucination_rate']}"
        )
        
        return True, "边界情况测试通过"
    
    # 测试用例9：负数和极值number参数测试
    def test_extreme_number_values():
        predictions = [
            {"id": "1", "type": "function", 
             "function": {"name": "智能体-A", "arguments": "{}"}},
            {"id": "2", "type": "function", 
             "function": {"name": "智能体-B", "arguments": "{}"}}
        ]
        references = [
            {"id": "3", "type": "function", 
             "function": {"name": "智能体-A", "arguments": "{}"}}
        ]
        
        # 测试负数number参数应该抛出异常
        try:
            evaluate_function_calls_metrics(
                predictions, references, number=-1
            )
            assert False, "负数number参数应该抛出异常"
        except ValueError as e:
            assert "number 必须是非负数" in str(e), f"异常信息不正确: {e}"
        
        # 测试极大number值
        result_large = evaluate_function_calls_metrics(
            predictions, references, number=1000
        )
        assert result_large["correct_workflow_selection"] is False, (
            "极大阈值时应该为False（1 >= 1000为False）"
        )
        
        # 测试number为0的边界情况
        result_zero = evaluate_function_calls_metrics(
            predictions, references, number=0
        )
        assert result_zero["correct_workflow_selection"] is True, (
            "阈值为0时应该为True（1 >= 0）"
        )
        
        return True, "极值number参数测试通过"
    
    # 测试用例10：函数名边界情况测试
    def test_function_name_boundaries():
        # 测试空字符串函数名
        predictions_empty_name = [
            {"id": "1", "type": "function", 
             "function": {"name": "", "arguments": "{}"}}
        ]
        references_empty_name = [
            {"id": "2", "type": "function", 
             "function": {"name": "", "arguments": "{}"}}
        ]
        
        result_empty = evaluate_function_calls_metrics(
            predictions_empty_name, references_empty_name
        )
        assert len(result_empty["fcm"]) == 1, "空字符串函数名应该能够匹配"
        assert result_empty["hallucination_rate"] == 0.0, "完全匹配时幻觉率应为0"
        
        # 测试包含特殊字符的函数名
        special_chars_name = "函数@#$%^&*()_+-=[]{}|;':\",./<>?"
        predictions_special = [
            {"id": "1", "type": "function", 
             "function": {"name": special_chars_name, "arguments": "{}"}}
        ]
        references_special = [
            {"id": "2", "type": "function", 
             "function": {"name": special_chars_name, "arguments": "{}"}}
        ]
        
        result_special = evaluate_function_calls_metrics(
            predictions_special, references_special
        )
        assert len(result_special["fcm"]) == 1, "特殊字符函数名应该能够匹配"
        
        # 测试Unicode字符（emoji等）
        unicode_name = "智能体🤖AI助手✨"
        predictions_unicode = [
            {"id": "1", "type": "function", 
             "function": {"name": unicode_name, "arguments": "{}"}}
        ]
        references_unicode = [
            {"id": "2", "type": "function", 
             "function": {"name": unicode_name, "arguments": "{}"}}
        ]
        
        result_unicode = evaluate_function_calls_metrics(
            predictions_unicode, references_unicode
        )
        assert len(result_unicode["fcm"]) == 1, "Unicode字符函数名应该能够匹配"
        
        return True, "函数名边界情况测试通过"
    
    # 测试用例11：大小写敏感性测试
    def test_case_sensitivity():
        predictions_lower = [
            {"id": "1", "type": "function", 
             "function": {"name": "aiagent", "arguments": "{}"}}
        ]
        references_upper = [
            {"id": "2", "type": "function", 
             "function": {"name": "AIAGENT", "arguments": "{}"}}
        ]
        
        result = evaluate_function_calls_metrics(
            predictions_lower, references_upper
        )
        # 函数名匹配应该是大小写敏感的
        assert len(result["fcm"]) == 0, "大小写不同的函数名不应该匹配"
        assert result["hallucination_rate"] == 1.0, (
            "无匹配时幻觉率应为 1.0 (1/1)"
        )
        
        # 测试完全相同的大小写
        predictions_same = [
            {"id": "1", "type": "function", 
             "function": {"name": "AIAgent", "arguments": "{}"}}
        ]
        references_same = [
            {"id": "2", "type": "function", 
             "function": {"name": "AIAgent", "arguments": "{}"}}
        ]
        
        result_same = evaluate_function_calls_metrics(
            predictions_same, references_same
        )
        assert len(result_same["fcm"]) == 1, "相同大小写的函数名应该匹配"
        
        return True, "大小写敏感性测试通过"
    
    # 测试用例12：复杂JSON arguments测试
    def test_complex_json_arguments():
        # 测试复杂嵌套JSON
        complex_json = json.dumps({
            "reason": "测试复杂参数",
            "parameters": {
                "nested": {
                    "array": [1, 2, 3, {"key": "value"}],
                    "unicode": "测试中文🎉",
                    "special_chars": "@#$%^&*()"
                },
                "numbers": [1.23, -456, 0],
                "boolean": True,
                "null_value": None
            }
        }, ensure_ascii=False)
        
        predictions_complex = [
            {"id": "1", "type": "function", 
             "function": {"name": "complex-agent", "arguments": complex_json}}
        ]
        references_complex = [
            {"id": "2", "type": "function", 
             "function": {"name": "complex-agent", "arguments": "{}"}}
        ]
        
        # 应该能正常处理复杂JSON（只看函数名匹配）
        result = evaluate_function_calls_metrics(
            predictions_complex, references_complex
        )
        assert len(result["fcm"]) == 1, "复杂JSON参数应该能正常处理"
        
        # 测试空JSON对象
        predictions_empty_json = [
            {"id": "1", "type": "function", 
             "function": {"name": "test-agent", "arguments": "{}"}}
        ]
        references_empty_json = [
            {"id": "2", "type": "function", 
             "function": {"name": "test-agent", "arguments": "{}"}}
        ]
        
        result_empty_json = evaluate_function_calls_metrics(
            predictions_empty_json, references_empty_json
        )
        assert len(result_empty_json["fcm"]) == 1, "空JSON对象应该能正常处理"
        
        return True, "复杂JSON arguments测试通过"
    
    # 测试用例13：数据类型边界测试
    def test_data_type_boundaries():
        # 测试function.name不是字符串的情况（应该抛异常）
        try:
            invalid_name_type = [
                {"id": "1", "type": "function", 
                 "function": {"name": 123, "arguments": "{}"}}
            ]
            references = [
                {"id": "2", "type": "function", 
                 "function": {"name": "test", "arguments": "{}"}}
            ]
            # 这里不会抛异常，因为验证逻辑只检查字段存在，不检查类型
            result = evaluate_function_calls_metrics(invalid_name_type, references)
            # 但数字和字符串不会匹配
            assert len(result["fcm"]) == 0, "数字类型函数名不应该匹配字符串"
        except Exception as e:
            # 如果抛异常也是合理的
            pass
        
        # 测试function.arguments不是字符串但能被json.loads处理的情况
        try:
            invalid_args_type = [
                {"id": "1", "type": "function", 
                 "function": {"name": "test", "arguments": 123}}  # 数字
            ]
            references = [
                {"id": "2", "type": "function", 
                 "function": {"name": "test", "arguments": "{}"}}
            ]
            evaluate_function_calls_metrics(invalid_args_type, references)
            assert False, "非字符串arguments应该抛出异常"
        except (ValueError, TypeError):
            pass  # 预期的异常
        
        return True, "数据类型边界测试通过"
    
    # 测试用例14：大数据量性能测试
    def test_large_dataset_performance():
        import time
        
        # 创建大量数据进行性能测试
        large_predictions = []
        large_references = []
        
        # 创建1000个预测和800个参考，其中500个匹配
        for i in range(1000):
            large_predictions.append({
                "id": f"pred-{i}",
                "type": "function",
                "function": {
                    "name": f"agent-{i % 500}" if i < 500 else f"unique-pred-{i}",
                    "arguments": f"{{\"index\": {i}}}"
                }
            })
        
        for i in range(800):
            large_references.append({
                "id": f"ref-{i}",
                "type": "function",
                "function": {
                    "name": f"agent-{i}" if i < 500 else f"unique-ref-{i}",
                    "arguments": f"{{\"index\": {i}}}"
                }
            })
        
        start_time = time.time()
        result = evaluate_function_calls_metrics(large_predictions, large_references)
        end_time = time.time()
        
        # 验证结果正确性
        assert len(result["fcm"]) == 500, f"应该有500个匹配，实际有{len(result['fcm'])}"
        assert result["tool_recognition_rate"] is True, "大量数据时工具识别率应为True"
        
        # 验证性能（应该在合理时间内完成，比如1秒）
        execution_time = end_time - start_time
        assert execution_time < 2.0, f"大数据量处理时间过长: {execution_time:.3f}秒"
        
        # 验证幻觉率计算：predictions=1000，matched=500，references=800
        # hallucination_rate = (1000-500)/800 = 0.625
        expected_hallucination_rate = 0.625
        assert abs(result["hallucination_rate"] - expected_hallucination_rate) < 1e-10, (
            f"大数据量幻觉率计算错误，期望{expected_hallucination_rate}，"
            f"实际{result['hallucination_rate']}"
        )
        
        return True, "大数据量性能测试通过"
    
    # 测试用例15：异常恢复和鲁棒性测试
    def test_robustness():
        # 测试包含None值的情况
        try:
            predictions_with_none = [
                {"id": "1", "type": "function", 
                 "function": {"name": "test", "arguments": None}}
            ]
            references = [
                {"id": "2", "type": "function", 
                 "function": {"name": "test", "arguments": "{}"}}
            ]
            evaluate_function_calls_metrics(predictions_with_none, references)
            assert False, "None类型的arguments应该抛出异常"
        except (ValueError, TypeError):
            pass  # 预期的异常
        
        # 测试混合有效和无效数据（部分数据有效的情况）
        # 这种情况下，无效数据应该在验证阶段被捕获，不应该进行部分处理
        try:
            mixed_predictions = [
                {"id": "1", "type": "function", 
                 "function": {"name": "valid-agent", "arguments": "{}"}},
                {"id": "2", "type": "function", 
                 "function": {"name": "invalid-agent"}}  # 缺少arguments字段
            ]
            references = [
                {"id": "3", "type": "function", 
                 "function": {"name": "valid-agent", "arguments": "{}"}}
            ]
            evaluate_function_calls_metrics(mixed_predictions, references)
            assert False, "混合有效无效数据应该抛出异常"
        except ValueError:
            pass  # 预期的异常
        
        return True, "异常恢复和鲁棒性测试通过"
    
    # 执行所有测试
    test_functions = [
        ("正常情况测试", test_normal_intersection),
        ("空列表测试", test_empty_lists), 
        ("无交集测试", test_no_intersection),
        ("类型错误测试", test_type_errors),
        ("格式校验测试", test_format_validation),
        ("完全匹配测试", test_full_match),
        ("新指标专项测试", test_new_metrics),
        ("边界情况测试", test_edge_cases),
        ("极值number参数测试", test_extreme_number_values),
        ("函数名边界情况测试", test_function_name_boundaries),
        ("大小写敏感性测试", test_case_sensitivity),
        ("复杂JSON arguments测试", test_complex_json_arguments),
        ("数据类型边界测试", test_data_type_boundaries),
        ("大数据量性能测试", test_large_dataset_performance),
        ("异常恢复和鲁棒性测试", test_robustness)
    ]
    
    for test_name, test_func in test_functions:
        try:
            success, message = test_func()
            if success:
                print(f"✅ {test_name}: {message}")
                passed_count += 1
            else:
                print(f"❌ {test_name}: {message}")
        except Exception as e:
            print(f"❌ {test_name}: 异常 - {str(e)}")
            traceback.print_exc()
    
    print(f"\n测试总结: {passed_count}/{len(test_functions)} 个测试用例通过")
    
    # 功能演示
    print("\n" + "=" * 60)
    print("功能演示")
    print("=" * 60)
    
    demo_predictions = [
        {
            "id": "chatcmpl-tool-demo1",
            "type": "function",
            "function": {
                "name": "企业金融行为智能体-V3",
                "arguments": "{\"reason\": \"演示查询功能\"}"
            }
        },
        {
            "id": "chatcmpl-tool-demo2", 
            "type": "function",
            "function": {
                "name": "智能体-演示",
                "arguments": "{\"query\": \"演示参数\"}"
            }
        }
    ]
    
    demo_references = [
        {
            "id": "chatcmpl-tool-ref1",
            "type": "function", 
            "function": {
                "name": "企业金融行为智能体-V3",
                "arguments": "{\"reason\": \"参考查询功能\"}"
            }
        },
        {
            "id": "chatcmpl-tool-ref2",
            "type": "function",
            "function": {
                "name": "其他智能体",
                "arguments": "{\"param\": \"其他参数\"}"
            }
        }
    ]
    
    demo_result = evaluate_function_calls_metrics(demo_predictions, demo_references)
    
    print("演示输入:")
    print(f"predictions: {len(demo_predictions)} 个函数调用")
    print(f"references: {len(demo_references)} 个函数调用") 
    print(f"\n演示输出:")
    print(f"匹配结果: {len(demo_result['fcm'])} 个函数调用匹配")
    if demo_result['fcm']:
        for i, match in enumerate(demo_result['fcm']):
            print(f"  匹配 {i+1}: {match['function']['name']}")
    
    print(f"\n指标评估:")
    print(f"工具识别率: {demo_result['tool_recognition_rate']}")
    print(f"正确工作流选择: {demo_result['correct_workflow_selection']}")
    print(f"幻觉率: {demo_result['hallucination_rate']}")
    
    # 额外演示不同number参数的影响  
    print(f"\n不同阈值下的工作流选择结果（交集数量为1）:")
    for threshold in [0, 1, 2]:
        result_with_threshold = evaluate_function_calls_metrics(
            demo_predictions, demo_references, number=threshold
        )
        print(
            f"  阈值 {threshold}: "
            f"{result_with_threshold['correct_workflow_selection']} "
            f"(1 >= {threshold})"
        )


if __name__ == "__main__":
    # 运行测试
    run_tests()
