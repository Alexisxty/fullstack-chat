from typing import Optional, Dict, Any
import asyncio
from .session import SessionManager
from .state import DialogueState
from src.managers.asr_manager import ASRManager
from src.managers.tts_manager import TTSManager
from src.managers.camera_manager import CameraManager
from src.managers.model_manager import ModelManager
import numpy as np

class Worker:
    def __init__(self):
        self.session_manager = SessionManager()
        self.asr_manager = ASRManager()
        self.tts_manager = TTSManager()
        self.camera_manager = CameraManager()
        self.model_manager = ModelManager()
        
    async def process_input(self, 
                          session_id: str, 
                          audio_chunk: Optional[bytes] = None,
                          video_frame: Optional[np.ndarray] = None,
                          text_input: Optional[str] = None):
        """处理用户输入"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return None
            
        try:
            # 处理视频帧
            if video_frame is not None:
                processed_frame = await self.camera_manager.process_frame(video_frame)
                if processed_frame:
                    session.video_buffer.append(processed_frame)
                    
            # 处理音频
            transcribed_text = None
            if audio_chunk is not None:
                transcribed_text = await self.asr_manager.process_audio_chunk(audio_chunk)
                
            # 如果有文本输入或语音识别结果
            input_text = text_input or transcribed_text
            if input_text:
                response = await self.model_manager.generate_response(
                    text=input_text,
                    video_frames=self.camera_manager.get_recent_frames(),
                    audio_text=transcribed_text
                )
                
                # 处理模型响应
                if '[S.SPEAK]' in response:
                    # 生成语音
                    audio_path = await self.tts_manager.synthesize_speech(
                        response.replace('[S.SPEAK]', '').strip(),
                        session_id
                    )
                    if audio_path:
                        await self.tts_manager.queue_audio(audio_path)
                        
                elif '[S.LISTEN]' in response or '[C.LISTEN]' in response:
                    self.session_manager.update_session_state(
                        session_id,
                        DialogueState.LISTENING
                    )
                    
                return {
                    'text': input_text,
                    'response': response,
                    'video_frame': processed_frame if video_frame is not None else None
                }
                
        except Exception as e:
            print(f"Input processing error: {e}")
            return None
            
    async def handle_interrupt(self, session_id: str):
        """处理打断"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return
            
        session.interrupt_flag = True
        await self.tts_manager.stop_current_audio()
        self.session_manager.update_session_state(
            session_id,
            DialogueState.INTERRUPTED
        )
    async def switch_model(self, session_id: str, model_name: str) -> bool:
        """切换会话使用的模型"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return False
            
        success = self.model_manager.switch_model(model_name)
        if success:
            # 更新会话状态
            session.model_name = model_name
        return success
        
    async def process_input(self, 
                          session_id: str, 
                          audio_chunk: Optional[bytes] = None,
                          video_frame: Optional[np.ndarray] = None,
                          text_input: Optional[str] = None,
                          model_name: Optional[str] = None):
        """处理输入（更新支持模型选择）"""
        session = self.session_manager.get_session(session_id)
        if not session:
            return None
            
        try:
            # 处理视频帧
            if video_frame is not None:
                processed_frame = await self.camera_manager.process_frame(video_frame)
                if processed_frame:
                    session.video_buffer.append(processed_frame)
                    
            # 处理音频
            transcribed_text = None
            if audio_chunk is not None:
                transcribed_text = await self.asr_manager.process_audio_chunk(audio_chunk)
                
            # 如果有文本输入或语音识别结果
            input_text = text_input or transcribed_text
            if input_text:
                # 使用指定的模型或会话当前的模型
                response = await self.model_manager.generate_response(
                    text=input_text,
                    images=self.camera_manager.get_recent_frames(),
                    model_name=model_name or session.model_name
                )
                
                # 处理模型响应
                if '[S.SPEAK]' in response:
                    audio_path = await self.tts_manager.synthesize_speech(
                        response.replace('[S.SPEAK]', '').strip(),
                        session_id
                    )
                    if audio_path:
                        await self.tts_manager.queue_audio(audio_path)
                        
                return {
                    'text': input_text,
                    'response': response,
                    'video_frame': processed_frame if video_frame is not None else None
                }
                
        except Exception as e:
            print(f"Input processing error: {e}")
            return None