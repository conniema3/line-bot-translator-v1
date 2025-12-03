from typing import List, Dict, Optional
from collections import deque

class InMemoryStore:
    def __init__(self):
        # Global dictionary to store conversation state
        # Key: Line User ID
        # Value: Dict with keys 'role', 'partner_id', 'recent_context'
        self.CONVERSATION_STATE = {}

    def get_or_init_state(self, user_id: str) -> Dict:
        """
        獲取或初始化一個新的用戶狀態。
        """
        if user_id not in self.CONVERSATION_STATE:
            self.CONVERSATION_STATE[user_id] = {
                "role": "未設定",
                "partner_id": None,
                "recent_context": deque(maxlen=5)
            }
        return self.CONVERSATION_STATE[user_id]

    def set_role(self, user_id: str, role: str) -> bool:
        """
        更新用戶的角色設定。
        """
        try:
            state = self.get_or_init_state(user_id)
            state["role"] = role
            return True
        except Exception as e:
            print(f"Error setting role: {e}")
            return False

    def add_message_to_context(self, user_id: str, partner_id: Optional[str], message_text: str, is_user_speaker: bool) -> None:
        """
        將新訊息加入上下文，並執行 5 條上限的清理。
        """
        state = self.get_or_init_state(user_id)
        
        # Determine speaker ID and Role
        if is_user_speaker:
            speaker_id = user_id
            speaker_role = state["role"]
        else:
            speaker_id = partner_id if partner_id else "Partner"
            # Simple inference for partner role
            user_role = state["role"]
            if user_role == "男友":
                speaker_role = "女友"
            elif user_role == "女友":
                speaker_role = "男友"
            else:
                speaker_role = "伴侶"

        message_data = {
            "user_id": speaker_id,
            "text": message_text,
            "role": speaker_role
        }
        state["recent_context"].append(message_data)

    def get_last_partner_message(self, user_id: str) -> Optional[str]:
        """
        獲取 recent_context 中伴侶發送的最後一條訊息，用於翻譯。
        """
        state = self.get_or_init_state(user_id)
        # Iterate backwards to find the last message NOT from the user
        for msg in reversed(state["recent_context"]):
            if msg["user_id"] != user_id:
                return msg["text"]
        return None
    
    # Helper for existing logic if needed, or we can remove/update
    def get_role(self, user_id: str) -> Optional[str]:
        state = self.get_or_init_state(user_id)
        role = state.get("role")
        return role if role != "未設定" else None

# Global instance
store = InMemoryStore()
