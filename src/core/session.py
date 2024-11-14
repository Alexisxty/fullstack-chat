from typing import Dict, Optional
import uuid
from .state import SessionState, DialogueState
from src.config.settings import SESSION_CONFIG

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
        
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = SessionState(session_id=session_id)
        return session_id
        
    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self.sessions.get(session_id)
        
    def update_session_state(self, session_id: str, new_state: DialogueState) -> bool:
        session = self.get_session(session_id)
        if session:
            session.dialogue_state = new_state
            session.update_activity()
            return True
        return False
        
    def cleanup_inactive_sessions(self):
        current_time = time.time()
        inactive_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time - session.last_activity > SESSION_CONFIG['timeout']
        ]
        for session_id in inactive_sessions:
            del self.sessions[session_id]