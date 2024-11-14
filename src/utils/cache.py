from typing import Dict, Any, Optional
import time
import hashlib
import json

class ResponseCache:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl
        
    def _generate_key(self, text: str, images: Optional[list] = None) -> str:
        """生成缓存键"""
        key_data = {
            "text": text,
            "images": images if images else None
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
        
    def get(self, text: str, images: Optional[list] = None) -> Optional[str]:
        """获取缓存的响应"""
        key = self._generate_key(text, images)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["response"]
            else:
                del self.cache[key]
        return None
        
    def set(self, text: str, images: Optional[list], response: str):
        """设置缓存"""
        key = self._generate_key(text, images)
        self.cache[key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        # 如果缓存超出大小限制，删除最旧的条目
        if len(self.cache) > self.max_size:
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k]["timestamp"]
            )
            del self.cache[oldest_key]