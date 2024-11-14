import asyncio
import sys
import os
import time
from typing import Optional, Dict, Any
import numpy as np
from PIL import Image

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.worker import Worker
from src.core.state import DialogueState
from src.utils.performance import PerformanceMonitor

class ChatTester:
    def __init__(self):
        self.worker = Worker()
        self.performance_monitor = PerformanceMonitor()
        
    def load_test_image(self, image_path: str) -> Optional[np.ndarray]:
        """加载测试图片"""
        try:
            img = Image.open(image_path)
            return np.array(img)
        except Exception as e:
            print(f"Error loading test image: {e}")
            return None
            
    async def test_basic_chat(self, session_id: str, model_name: str):
        """测试基本对话功能"""
        print(f"\n=== Testing basic chat with {model_name.upper()} model ===")
        
        test_cases = [
            {
                "input": "你好，我们开始对话吧",
                "expected_marker": "[S.SPEAK]",
                "description": "基本问候"
            },
            {
                "input": "从前有座山...",
                "expected_marker": "[C.LISTEN]",
                "description": "讲故事检测"
            },
            {
                "input": "等一下，我想问个问题",
                "expected_marker": "[S.LISTEN]",
                "description": "打断检测"
            },
            {
                "input": "这是一个测试问题，请回答",
                "expected_marker": "[S.SPEAK]",
                "description": "普通问答"
            }
        ]
        
        success_count = 0
        for case in test_cases:
            print(f"\nTesting: {case['description']}")
            print(f"User: {case['input']}")
            
            self.performance_monitor.start()
            result = await self.worker.process_input(
                session_id=session_id,
                text_input=case['input']
            )
            self.performance_monitor.end()
            
            if result and 'response' in result:
                response = result['response']
                print(f"Assistant: {response}")
                
                # 验证响应标记
                if case['expected_marker'] in response:
                    print(f"✓ Correct response marker: {case['expected_marker']}")
                    success_count += 1
                else:
                    print(f"✗ Expected {case['expected_marker']}, got different marker")
                    
                # 打印性能指标
                print(f"Response time: {self.performance_monitor.elapsed_time:.2f}s")
            else:
                print("✗ No response received")
                
            await asyncio.sleep(1)
            
        return success_count, len(test_cases)
        
    async def test_multimodal(self, session_id: str, model_name: str):
        """测试多模态功能"""
        print(f"\n=== Testing multimodal with {model_name.upper()} model ===")
        
        # 加载测试图片
        test_image = self.load_test_image("src/tests/test_data/test_image.jpg")
        if test_image is None:
            print("✗ Failed to load test image")
            return 0, 1
            
        test_cases = [
            {
                "input": "请描述这张图片",
                "expected_marker": "[S.SPEAK]",
                "description": "基本图片描述"
            }
        ]
        
        success_count = 0
        for case in test_cases:
            print(f"\nTesting: {case['description']}")
            print(f"User: {case['input']}")
            
            self.performance_monitor.start()
            result = await self.worker.process_input(
                session_id=session_id,
                text_input=case['input'],
                video_frame=test_image
            )
            self.performance_monitor.end()
            
            if result and 'response' in result:
                response = result['response']
                print(f"Assistant: {response}")
                
                if case['expected_marker'] in response:
                    print(f"✓ Correct response marker: {case['expected_marker']}")
                    success_count += 1
                else:
                    print(f"✗ Expected {case['expected_marker']}, got different marker")
                    
                print(f"Response time: {self.performance_monitor.elapsed_time:.2f}s")
            else:
                print("✗ No response received")
                
            await asyncio.sleep(1)
            
        return success_count, len(test_cases)
        
    async def test_interruption(self, session_id: str, model_name: str):
        """测试打断功能"""
        print(f"\n=== Testing interruption with {model_name.upper()} model ===")
        
        # 启动长响应
        long_input = "请详细解释人工智能的发展历史，要尽可能详细"
        print(f"Starting long response...")
        print(f"User: {long_input}")
        
        # 在后台启动长响应
        response_task = asyncio.create_task(
            self.worker.process_input(
                session_id=session_id,
                text_input=long_input
            )
        )
        
        # 等待一小段时间后发送打断
        await asyncio.sleep(2)
        interrupt_text = "等一下，我想问个问题"
        print(f"Interrupting with: {interrupt_text}")
        
        interrupt_result = await self.worker.process_input(
            session_id=session_id,
            text_input=interrupt_text
        )
        
        success = False
        if interrupt_result and 'response' in interrupt_result:
            response = interrupt_result['response']
            print(f"Assistant: {response}")
            if "[S.LISTEN]" in response:
                print("✓ Correct interruption handling")
                success = True
            else:
                print("✗ Unexpected response to interruption")
        else:
            print("✗ No response to interruption")
            
        return int(success), 1

async def run_tests():
    tester = ChatTester()
    
    # 创建会话
    session_id = tester.worker.session_manager.create_session()
    print(f"Created session: {session_id}")
    
    # 测试结果统计
    total_results = {
        "qwen": {"success": 0, "total": 0},
        "openai": {"success": 0, "total": 0}
    }
    
    # 运行测试
    for model in ["qwen"]:#, "openai"
        try:
            # 切换模型
            await tester.worker.switch_model(session_id, model)
            
            # 运行基本对话测试
            basic_success, basic_total = await tester.test_basic_chat(session_id, model)
            total_results[model]["success"] += basic_success
            total_results[model]["total"] += basic_total
            
            # 运行多模态测试
            mm_success, mm_total = await tester.test_multimodal(session_id, model)
            total_results[model]["success"] += mm_success
            total_results[model]["total"] += mm_total
            
            # 运行打断测试
            int_success, int_total = await tester.test_interruption(session_id, model)
            total_results[model]["success"] += int_success
            total_results[model]["total"] += int_total
            
        except Exception as e:
            print(f"Error testing {model} model: {e}")
            
    # 打印总结果
    print("\n=== Test Results ===")
    for model, results in total_results.items():
        success_rate = (results["success"] / results["total"] * 100) if results["total"] > 0 else 0
        print(f"{model.upper()}: {results['success']}/{results['total']} tests passed ({success_rate:.1f}%)")

if __name__ == "__main__":
    asyncio.run(run_tests())