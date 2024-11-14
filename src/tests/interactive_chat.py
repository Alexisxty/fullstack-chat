import asyncio
import sys
import os
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.worker import Worker
from src.core.state import DialogueState

class InteractiveChatTester:
    def __init__(self):
        self.worker = Worker()
        self.session_id = None
        self.current_model = "qwen"  # 默认模型
        
    async def initialize(self):
        """初始化会话"""
        self.session_id = self.worker.session_manager.create_session()
        await self.worker.switch_model(self.session_id, self.current_model)
        print(f"Session initialized: {self.session_id}")
        print(f"Using model: {self.current_model}")
        
    async def handle_command(self, command: str) -> bool:
        """处理特殊命令"""
        if command.startswith("/"):
            cmd_parts = command[1:].split()
            cmd = cmd_parts[0].lower()
            
            if cmd == "quit":
                return False
            elif cmd == "model":
                if len(cmd_parts) > 1:
                    new_model = cmd_parts[1]
                    if await self.worker.switch_model(self.session_id, new_model):
                        self.current_model = new_model
                        print(f"Switched to model: {new_model}")
                    else:
                        print(f"Error: Model {new_model} not available")
                else:
                    print(f"Current model: {self.current_model}")
            elif cmd == "help":
                print("""
Available commands:
/quit - Exit the program
/model <name> - Switch to specified model
/model - Show current model
/help - Show this help message
                """)
            else:
                print(f"Unknown command: {cmd}")
            return True
        return True
        
    async def chat_loop(self):
        """主对话循环"""
        await self.initialize()
        
        print("\nChat started! Type /help for commands or just start chatting.")
        print("Type /quit to exit.\n")
        
        while True:
            try:
                user_input = input("User: ").strip()
                
                if not user_input:
                    continue
                    
                # 处理命令
                should_continue = await self.handle_command(user_input)
                if not should_continue:
                    break
                    
                if not user_input.startswith("/"):
                    # 处理普通对话
                    result = await self.worker.process_input(
                        session_id=self.session_id,
                        text_input=user_input
                    )
                    
                    if result:
                        print(f"Assistant: {result['response']}")
                    else:
                        print("Error: No response")
                        
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")

async def main():
    tester = InteractiveChatTester()
    await tester.chat_loop()

if __name__ == "__main__":
    asyncio.run(main())


# Available commands:
# /quit - Exit the program
# /model <name> - Switch to specified model
# /model - Show current model
# /help - Show this help message