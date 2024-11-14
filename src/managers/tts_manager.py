import asyncio
import aiohttp
import os
import time
from typing import Optional
from src.config.settings import TTS_API_URL

class TTSManager:
    def __init__(self, api_url: str = TTS_API_URL):
        self.api_url = api_url
        self.audio_queue = asyncio.Queue()
        self.is_speaking = False
        self.current_audio = None
        
    async def synthesize_speech(self, text: str, session_id: str) -> Optional[str]:
        """调用TTS API生成语音"""
        if not text:
            return None
            
        data = {
            'text': text,
            'speaker': '中文女',
            'stream': False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=data) as response:
                    if response.status == 200:
                        audio_content = await response.read()
                        # 保存音频文件
                        os.makedirs(f"temp/audio/{session_id}", exist_ok=True)
                        audio_path = f"temp/audio/{session_id}/tts_{int(time.time())}.wav"
                        with open(audio_path, 'wb') as f:
                            f.write(audio_content)
                        return audio_path
                        
        except Exception as e:
            print(f"TTS Error: {e}")
            return None
            
    async def queue_audio(self, audio_path: str):
        """将音频加入播放队列"""
        await self.audio_queue.put(audio_path)
        if not self.is_speaking:
            asyncio.create_task(self._process_audio_queue())
            
    async def stop_current_audio(self):
        """停止当前音频播放"""
        self.is_speaking = False
        self.current_audio = None
        # 清空队列
        while not self.audio_queue.empty():
            await self.audio_queue.get()
            
    async def _process_audio_queue(self):
        """处理音频队列"""
        self.is_speaking = True
        while self.is_speaking:
            try:
                audio_path = await self.audio_queue.get()
                self.current_audio = audio_path
                # 这里将返回音频路径给Gradio的Audio组件
                yield audio_path
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Audio processing error: {e}")