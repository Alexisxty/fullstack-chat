import asyncio
import aiohttp
from typing import Optional
import numpy as np
from src.config.settings import ASR_API_URL, AUDIO_CONFIG

class ASRManager:
    def __init__(self, api_url: str = ASR_API_URL):
        self.api_url = api_url
        self.audio_buffer = []
        self.sample_rate = AUDIO_CONFIG['sample_rate']
        
    async def process_audio_chunk(self, audio_chunk: np.ndarray) -> Optional[str]:
        """处理音频块并返回识别文本"""
        self.audio_buffer.append(audio_chunk)
        
        # 累积约1秒的音频
        if len(self.audio_buffer) * len(audio_chunk) / self.sample_rate >= 1.0:
            return await self.transcribe_audio()
        return None
        
    async def transcribe_audio(self) -> Optional[str]:
        """调用ASR API"""
        if not self.audio_buffer:
            return None
            
        try:
            # 准备音频数据
            audio_data = np.concatenate(self.audio_buffer)
            files = {
                'files': ('audio.wav', audio_data.tobytes(), 'audio/wav')
            }
            data = {
                'keys': 'audio1',
                'lang': 'auto'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, data=data, files=files) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['result'][0]['text']
                        
        except Exception as e:
            print(f"ASR Error: {e}")
            return None
        finally:
            self.audio_buffer = []  # 清空缓存