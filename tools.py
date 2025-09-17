#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
函数调用指标评估工具模块

该模块提供了评估函数调用预测结果与参考结果匹配度的功能。
"""

import json
from typing import List, Dict, Any


def evaluate_function_calls_metrics(predictions: List[Dict[str, Any]], references: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    评估函数调用指标，计算预测结果与参考结果的交集
    
    该函数接收预测结果和参考结果两个列表，根据函数名称（function.name）作为唯一标识符，
    找出两个列表中的交集元素，返回匹配的函数调用记录。
    
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
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: 返回格式为 {"fcm": [匹配的函数调用记录列表]}
    
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
    """
    
    # 1. 基本类型校验
    if not isinstance(predictions, list):
        raise TypeError(f"predictions 必须是 list 类型，当前类型: {type(predictions).__name__}")
    
    if not isinstance(references, list):
        raise TypeError(f"references 必须是 list 类型，当前类型: {type(references).__name__}")
    
    # 2. 处理空列表情况
    if not predictions or not references:
        return {"fcm": []}
    
    # 3. 验证列表元素格式
    def validate_function_call_format(item: Any, item_type: str, index: int) -> None:
        """验证单个函数调用记录的格式"""
        if not isinstance(item, dict):
            raise ValueError(f"{item_type}[{index}] 必须是 dict 类型，当前类型: {type(item).__name__}")
        
        # 检查必需字段
        required_fields = ["id", "type", "function"]
        for field in required_fields:
            if field not in item:
                raise ValueError(f"{item_type}[{index}] 缺少必需字段: {field}")
        
        # 检查 type 字段值
        if item["type"] != "function":
            raise ValueError(f"{item_type}[{index}] 的 type 字段必须为 'function'，当前值: {item['type']}")
        
        # 检查 function 字段格式
        function_obj = item["function"]
        if not isinstance(function_obj, dict):
            raise ValueError(f"{item_type}[{index}] 的 function 字段必须是 dict 类型")
        
        function_required_fields = ["name", "arguments"]
        for field in function_required_fields:
            if field not in function_obj:
                raise ValueError(f"{item_type}[{index}] 的 function 缺少必需字段: {field}")
        
        # 验证 arguments 是否为有效 JSON 字符串
        try:
            json.loads(function_obj["arguments"])
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"{item_type}[{index}] 的 function.arguments 不是有效的 JSON 字符串: {e}")
    
    # 4. 验证所有元素格式
    for i, pred in enumerate(predictions):
        validate_function_call_format(pred, "predictions", i)
    
    for i, ref in enumerate(references):
        validate_function_call_format(ref, "references", i)
    
    # 5. 创建参考结果的函数名称集合，便于快速查找
    reference_function_names = {ref["function"]["name"] for ref in references}
    
    # 6. 找出交集：predictions 中的函数名称在 references 中存在的记录
    matched_calls = []
    for pred in predictions:
        function_name = pred["function"]["name"]
        if function_name in reference_function_names:
            matched_calls.append(pred)
    
    return {"fcm": matched_calls}


def run_tests():
    """运行单元测试和功能测试"""
    import traceback
    
    print("=" * 60)
    print("开始运行 evaluate_function_calls_metrics 函数测试")
    print("=" * 60)
    
    test_cases = []
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
        
        return True, "正常情况测试通过"
    
    # 测试用例2：空列表情况
    def test_empty_lists():
        # predictions 为空
        result1 = evaluate_function_calls_metrics([], [{"id": "1", "type": "function", "function": {"name": "test", "arguments": "{}"}}])
        assert result1 == {"fcm": []}, "predictions 为空时应返回空结果"
        
        # references 为空  
        result2 = evaluate_function_calls_metrics([{"id": "1", "type": "function", "function": {"name": "test", "arguments": "{}"}}], [])
        assert result2 == {"fcm": []}, "references 为空时应返回空结果"
        
        # 都为空
        result3 = evaluate_function_calls_metrics([], [])
        assert result3 == {"fcm": []}, "都为空时应返回空结果"
        
        return True, "空列表情况测试通过"
    
    # 测试用例3：无交集情况
    def test_no_intersection():
        predictions = [{"id": "1", "type": "function", "function": {"name": "智能体-A", "arguments": "{}"}}]
        references = [{"id": "2", "type": "function", "function": {"name": "智能体-B", "arguments": "{}"}}]
        
        result = evaluate_function_calls_metrics(predictions, references)
        assert result == {"fcm": []}, "无交集时应返回空结果"
        
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
        
        return True, "类型错误测试通过"
    
    # 测试用例5：格式校验错误
    def test_format_validation():
        # 缺少必需字段
        try:
            evaluate_function_calls_metrics([{"id": "1"}], [{"id": "2", "type": "function", "function": {"name": "test", "arguments": "{}"}}])
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            assert "缺少必需字段" in str(e)
        
        # type 字段值错误
        try:
            evaluate_function_calls_metrics([{"id": "1", "type": "invalid", "function": {"name": "test", "arguments": "{}"}}], [{"id": "2", "type": "function", "function": {"name": "test", "arguments": "{}"}}])
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            assert "type 字段必须为 'function'" in str(e)
        
        # arguments 不是有效 JSON
        try:
            evaluate_function_calls_metrics([{"id": "1", "type": "function", "function": {"name": "test", "arguments": "invalid_json"}}], [{"id": "2", "type": "function", "function": {"name": "test", "arguments": "{}"}}])
            assert False, "应该抛出 ValueError"  
        except ValueError as e:
            assert "不是有效的 JSON 字符串" in str(e)
        
        return True, "格式校验测试通过"
    
    # 测试用例6：完全匹配情况
    def test_full_match():
        data = [
            {"id": "1", "type": "function", "function": {"name": "智能体-A", "arguments": "{}"}},
            {"id": "2", "type": "function", "function": {"name": "智能体-B", "arguments": "{}"}}
        ]
        
        result = evaluate_function_calls_metrics(data, data)
        assert len(result["fcm"]) == 2, "完全匹配时应返回所有元素"
        
        return True, "完全匹配测试通过"
    
    # 执行所有测试
    test_functions = [
        ("正常情况测试", test_normal_intersection),
        ("空列表测试", test_empty_lists), 
        ("无交集测试", test_no_intersection),
        ("类型错误测试", test_type_errors),
        ("格式校验测试", test_format_validation),
        ("完全匹配测试", test_full_match)
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


if __name__ == "__main__":
    # 运行测试
    run_tests()
