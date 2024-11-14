import numpy as np
import cv2
from typing import Optional, Dict, Any
import time
from src.config.settings import VIDEO_CONFIG

class CameraManager:
    def __init__(self):
        self.frame_buffer = []
        self.is_streaming = False
        self.config = VIDEO_CONFIG
        
    async def process_frame(self, frame_data: np.ndarray) -> Optional[Dict[str, Any]]:
        """处理摄像头帧"""
        if frame_data is None:
            return None
            
        try:
            # 确保图像格式正确
            if len(frame_data.shape) == 2:
                frame_data = cv2.cvtColor(frame_data, cv2.COLOR_GRAY2RGB)
            elif len(frame_data.shape) == 3 and frame_data.shape[2] == 4:
                frame_data = cv2.cvtColor(frame_data, cv2.COLOR_RGBA2RGB)
                
            # 调整大小
            frame_data = cv2.resize(
                frame_data,
                (self.config['frame_width'], self.config['frame_height'])
            )
            
            processed_frame = {
                'frame': frame_data,
                'timestamp': time.time()
            }
            
            self.frame_buffer.append(processed_frame)
            
            # 保持固定大小的缓冲区
            if len(self.frame_buffer) > 30:  # 保持1秒的帧数据
                self.frame_buffer.pop(0)
                
            return processed_frame
            
        except Exception as e:
            print(f"Frame processing error: {e}")
            return None
            
    def get_recent_frames(self, num_frames: int = 5) -> list:
        """获取最近的几帧"""
        return self.frame_buffer[-num_frames:] if self.frame_buffer else []