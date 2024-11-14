from abc import ABC, abstractmethod 
from typing import Dict, Any, Optional, List
import asyncio
import torch
import numpy as np
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration, TextIteratorStreamer
from threading import Thread
from src.utils.performance import measure_performance
from src.utils.cache import ResponseCache

class BaseModelInterface(ABC):
    @abstractmethod
    async def generate_response(self, 
                              text: str, 
                              images: Optional[List[np.ndarray]] = None,
                              **kwargs) -> str:
        pass
    
    @abstractmethod
    async def process_response(self, response: Any) -> str:
        pass

class OpenAIInterface(BaseModelInterface):
    def __init__(self, config: Dict[str, Any]):
        import openai
        self.client = openai.Client(
            api_key=config["api_key"],
            base_url=config["api_base"]
        )
        self.model = config["model"]
        self.max_tokens = config["max_tokens"]
        self.temperature = config["temperature"]
        
    def _encode_image(self, image: np.ndarray) -> str:
        img = Image.fromarray(image)
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode()
        
    async def generate_response(self, 
                              text: str, 
                              images: Optional[List[np.ndarray]] = None,
                              **kwargs) -> str:
        try:
            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            content = []
            
            if text:
                content.append({"type": "text", "text": text})
                
            if images:
                for image in images:
                    if image is not None:
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{self._encode_image(image)}"
                            }
                        })
                        
            messages.append({"role": "user", "content": content})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                **kwargs
            )
            return await self.process_response(response)
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "[S.SPEAK] 抱歉，处理过程中出现错误。"
            
    async def process_response(self, response: Any) -> str:
        if not response.choices:
            return "[S.SPEAK] 抱歉，没有得到有效回复。"
        return response.choices[0].message.content

class QwenInterface(BaseModelInterface):
    def __init__(self, config: Dict[str, Any]):
        from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
        
        # 配置模型加载参数
        model_kwargs = {
            "device_map": "auto",
            "torch_dtype": getattr(torch, config.get("torch_dtype", "bfloat16")),  # 默认使用bfloat16
        }
        
        # 如果启用flash attention
        if config.get("use_flash_attention", False):
            model_kwargs["attn_implementation"] = "flash_attention_2"
            
        try:
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                config["checkpoint_path"],
                **model_kwargs
            )
        except Exception as e:
            print(f"Error loading model with flash attention: {e}")
            # 如果flash attention加载失败，回退到普通模式
            model_kwargs.pop("attn_implementation", None)
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                config["checkpoint_path"],
                **model_kwargs
            )
            
        self.processor = AutoProcessor.from_pretrained(config["checkpoint_path"])
        self.tokenizer = self.processor.tokenizer
        self.config = config
        self.response_cache = ResponseCache()
        
        # 设置模型为评估模式
        self.model.eval()
        
        # 启用梯度检查点以节省显存
        if config.get("use_gradient_checkpointing", True):
            self.model.gradient_checkpointing_enable()

    def _prepare_inputs(self, text: str, images: Optional[List[np.ndarray]] = None):
        """准备模型输入"""
        try:
            # 处理文本模版
            if not text.strip():
                text = "请描述这张图片。"
                
            chat_text = self.processor.tokenizer.apply_chat_template(
                [{"role": "user", "content": text}],
                tokenize=False,
                add_generation_prompt=True
            )
            
            # 处理视觉信息
            image_inputs = None
            if images:
                image_inputs = []
                for image in images:
                    if image is not None:
                        image_inputs.append(image)
            
            # 生成模型输入
            inputs = self.processor(
                text=[chat_text],
                images=image_inputs,
                return_tensors="pt",
                padding=True
            )
            
            # 移动到正确的设备
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            return inputs
            
        except Exception as e:
            print(f"Input preparation error: {e}")
            raise

    @measure_performance(name="qwen_generation")
    async def generate_response(self, 
                              text: str, 
                              images: Optional[List[np.ndarray]] = None,
                              **kwargs) -> str:
        # 检查缓存
        cached_response = self.response_cache.get(text, images)
        if cached_response:
            return cached_response
            
        try:
            # 准备输入
            inputs = self._prepare_inputs(text, images)
            
            # 设置生成参数
            generation_kwargs = {
                "max_new_tokens": self.config.get("max_new_tokens", 512),
                "temperature": self.config.get("temperature", 0.7),
                "top_p": self.config.get("top_p", 0.8),
                "repetition_penalty": self.config.get("repetition_penalty", 1.1),
                "do_sample": True,
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
            }
            
            # 设置流式输出
            streamer = TextIteratorStreamer(
                self.tokenizer,
                timeout=20.0,
                skip_prompt=True,
                skip_special_tokens=True
            )
            generation_kwargs["streamer"] = streamer
            
            # 在后台线程中运行生成
            thread = Thread(target=self.model.generate, kwargs={**inputs, **generation_kwargs})
            thread.start()
            
            # 收集生成的文本
            generated_text = ""
            for new_text in streamer:
                generated_text += new_text
                
            # 缓存响应
            self.response_cache.set(text, images, generated_text)
            
            return generated_text
            
        except Exception as e:
            print(f"Qwen model error: {e}")
            return "[S.SPEAK] 抱歉，处理过程中出现错误。"
            
    async def process_response(self, response: str) -> str:
        """处理模型响应"""
        try:
            # 清理响应文本
            response = response.strip()
            
            # 确保响应包含正确的标记
            if not any(marker in response for marker in ['[S.SPEAK]', '[S.LISTEN]', '[C.LISTEN]']):
                response = f"[S.SPEAK] {response}"
                
            return response
            
        except Exception as e:
            print(f"Response processing error: {e}")
            return "[S.SPEAK] 抱歉，响应处理出错。"
            
    @torch.no_grad()
    def _generate_with_streaming(self, **kwargs):
        """使用无梯度上下文的生成函数"""
        return self.model.generate(**kwargs)
        
    def clear_cache(self):
        """清除响应缓存"""
        self.response_cache = ResponseCache()
        
    async def preload(self):
        """预热模型"""
        try:
            # 使用一个简单的测试输入预热模型
            warmup_text = "你好"
            warmup_inputs = self._prepare_inputs(warmup_text)
            
            # 执行一次推理
            with torch.no_grad():
                _ = self.model.generate(
                    **warmup_inputs,
                    max_new_tokens=10,
                    num_beams=1
                )
                
            return True
        except Exception as e:
            print(f"Model preload error: {e}")
            return False