from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import time

class DialogueState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"

@dataclass
class MessageHistory:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    
@dataclass
class SessionState:
    session_id: str
    dialogue_state: DialogueState = DialogueState.IDLE
    messages: List[MessageHistory] = field(default_factory=list)
    current_speaker: Optional[str] = None
    interrupt_flag: bool = False
    audio_buffer: List[bytes] = field(default_factory=list)
    video_buffer: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    
    def update_activity(self):
        self.last_activity = time.time()