import asyncio
import sys
import os
from typing import Optional, Dict, Any
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.worker import Worker
from src.core.state import DialogueState

class InterruptionTester:
    def __init__(self):
        self.worker = Worker()
        self.session_id = None
        self.current_model = "qwen"
        self.is_assistant_speaking = False
        self.current_response = ""
        
    async def initialize(self):
        self.session_id = self.worker.session_manager.create_session()
        await self.worker.switch_model(self.session_id, self.current_model)
        print(f"Session initialized: {self.session_id}")
        print(f"Using model: {self.current_model}")

    async def simulate_long_response(self) -> None:
        """模拟助手长回复"""
        self.is_assistant_speaking = True
        long_response = """[S.SPEAK] 让我给你详细解释一下这个问题。
首先，我们需要理解基本概念...
这是一个很长的解释过程...
现在我继续解释第二个要点...
接下来说第三个方面...
让我们进入更深入的讨论..."""

        print("\nAssistant starting long response...")
        for line in long_response.split('\n'):
            if not self.is_assistant_speaking:
                print("\n[INTERRUPTED]")
                break
            self.current_response += line + '\n'
            print(f"Assistant: {line}")
            await asyncio.sleep(1)  # 模拟说话过程

    async def handle_interruption(self, interrupt_text: str) -> None:
        """处理打断"""
        self.is_assistant_speaking = False
        
        # 清空TTS队列
        await self.worker.tts_manager.stop_current_audio()
        
        # 更新会话状态
        session = self.worker.session_manager.get_session(self.session_id)
        if session:
            session.dialogue_state = DialogueState.INTERRUPTED
            session.interrupt_flag = True

        print(f"\nUser interruption: {interrupt_text}")
        
        # 处理打断后的新输入
        result = await self.worker.process_input(
            session_id=self.session_id,
            text_input=interrupt_text
        )
        
        if result:
            print(f"Assistant (after interruption): {result['response']}")

    async def test_interruption_scenarios(self):
        """测试各种打断场景"""
        await self.initialize()
        
        # 测试场景列表
        scenarios = [
            {
                "description": "测试场景1: 基本打断",
                "initial_input": "请给我详细解释一下人工智能的发展历史",
                "interruption": "等一下，我想问个更具体的问题"
            },
            {
                "description": "测试场景2: 多次打断",
                "initial_input": "让我告诉你一个故事",
                "interruption": "抱歉打断一下"
            },
            {
                "description": "测试场景3: 打断后继续",
                "initial_input": "请详细分析一下当前的经济形势",
                "interruption": "等等，我们能先讨论别的吗"
            }
        ]
        
        for scenario in scenarios:
            print(f"\n{'='*50}")
            print(f"\n{scenario['description']}")
            
            # 重置状态
            self.is_assistant_speaking = False
            self.current_response = ""
            
            # 初始输入
            print(f"\nUser: {scenario['initial_input']}")
            
            # 启动长响应
            response_task = asyncio.create_task(self.simulate_long_response())
            
            # 等待一段时间后进行打断
            await asyncio.sleep(2)
            
            # 模拟打断
            await self.handle_interruption(scenario['interruption'])
            
            # 等待响应任务完成
            await response_task
            
            # 检查状态
            session = self.worker.session_manager.get_session(self.session_id)
            print(f"\nFinal dialogue state: {session.dialogue_state}")
            print(f"Interrupt flag: {session.interrupt_flag}")
            
            # 重置会话状态
            await asyncio.sleep(1)
            session.interrupt_flag = False
            session.dialogue_state = DialogueState.IDLE

    async def interactive_test(self):
        """交互式测试打断功能"""
        await self.initialize()
        
        print("\nInteractive interruption test started!")
        print("Commands:")
        print("- Type 'start' to begin a long response")
        print("- Type anything while response is ongoing to interrupt")
        print("- Type 'quit' to exit")
        
        while True:
            try:
                user_input = input("\nUser: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                    
                if user_input.lower() == 'start':
                    # 启动长响应
                    response_task = asyncio.create_task(self.simulate_long_response())
                    print("(Type anything to interrupt the response)")
                    
                    while self.is_assistant_speaking:
                        # 非阻塞地检查用户输入
                        try:
                            interrupt_text = input()
                            if interrupt_text:
                                await self.handle_interruption(interrupt_text)
                                break
                        except EOFError:
                            await asyncio.sleep(0.1)
                            
                    await response_task
                else:
                    # 普通输入处理
                    result = await self.worker.process_input(
                        session_id=self.session_id,
                        text_input=user_input
                    )
                    
                    if result:
                        print(f"Assistant: {result['response']}")
                        
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

async def main():
    tester = InterruptionTester()
    
    # 运行自动化测试场景
    print("\nRunning automated test scenarios...")
    await tester.test_interruption_scenarios()
    
    # 运行交互式测试
    print("\nStarting interactive test...")
    await tester.interactive_test()

if __name__ == "__main__":
    asyncio.run(main())