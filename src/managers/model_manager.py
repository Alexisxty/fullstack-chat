from typing import Dict, Optional, List, Any
import asyncio
import numpy as np
from .model_interfaces import (
    BaseModelInterface,
    OpenAIInterface,
    QwenInterface
)
from src.config.settings import MODEL_CONFIG

class ModelManager:
    def __init__(self):
        self.interfaces: Dict[str, BaseModelInterface] = {}
        self.current_model = MODEL_CONFIG["default_model"]
        self.load_models()
        
    def load_models(self):
        """加载配置的模型接口"""
        if "openai" in MODEL_CONFIG:
            self.interfaces["openai"] = OpenAIInterface(MODEL_CONFIG["openai"])
            
        if "qwen" in MODEL_CONFIG:
            self.interfaces["qwen"] = QwenInterface(MODEL_CONFIG["qwen"])
    
    def switch_model(self, model_name: str) -> bool:
        """切换当前使用的模型"""
        if model_name in self.interfaces:
            self.current_model = model_name
            return True
        return False
        
    async def generate_response(self,
                              text: str,
                              images: Optional[List[np.ndarray]] = None,
                              model_name: Optional[str] = None,
                              **kwargs) -> str:
        """生成响应"""
        model_interface = self.interfaces.get(
            model_name or self.current_model,
            self.interfaces[MODEL_CONFIG["default_model"]]
        )
        
        try:
            response = await model_interface.generate_response(
                text=text,
                images=images,
                **kwargs
            )
            return response
        except Exception as e:
            print(f"Model generation error: {e}")
            return "[S.SPEAK] 抱歉，模型处理过程中出现错误。"