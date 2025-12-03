import os
import google.generativeai as genai
from typing import List, Dict

class LLMClient:
    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("Warning: GOOGLE_API_KEY not found in environment variables.")
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')

    def call_llm_api(self, context: List[Dict], target_message: str, user_role: str) -> str:
        """
        Calls the LLM API to translate the target message based on context and user role.
        
        Args:
            context: List of recent messages (dicts with 'user_id', 'text', 'role').
            target_message: The specific message to translate.
            user_role: The role of the user requesting translation (e.g., "男友", "女友").
            
        Returns:
            Translated text (The "Truth").
        """
        if not hasattr(self, 'model'):
            return "(API Key missing, cannot translate)"

        partner_role = "男友" if user_role == "女友" else "女友" if user_role == "男友" else "伴侶"

        # Format context
        context_str = ""
        if not context:
            context_str = "(無先前對話)"
        else:
            for msg in context:
                # Use the role stored in the message, or infer based on user_id if needed
                # In store.py we already stored 'role' in the message dict
                speaker_role = msg.get('role', '未知')
                text = msg.get('text', '')
                context_str += f"- {speaker_role}: {text}\n"

        prompt = f"""
[System Prompt]
你是一個「Line Bot 真心話翻譯機」。你的任務是將情侶間的對話，翻譯成潛藏的真實心聲。
輸出規則：
1. 嚴格地 **只輸出翻譯內容**，不包含任何開頭詞、總結或解釋。
2. 輸出必須簡潔、有力、有洞察力。
3. 根據上下文判斷語氣（例如，如果對話是負面的，翻譯也應帶有諷刺或負面情緒）。

[Few-Shot Examples]
輸入：目標訊息是：「你在哪裡呀？」
輸出：我好想你，快來陪我！而且最好帶著宵夜。

輸入：目標訊息是：「我還好，沒事啊。」
輸出：我氣炸了，但我希望你主動猜到我生氣的原因。

[User Prompt]
請根據以下情境與對話歷史，翻譯伴侶的這句話的「真心話」：

【我的角色】：{user_role}
【伴侶的角色】：{partner_role}

【對話上下文 (最多 5 條，用於提供情境)】
{context_str}

【需要翻譯的目標訊息 (由伴侶發送)】
「{target_message}」

請輸出伴侶的真心話，不要使用任何額外的標籤或解釋。
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return "（翻譯功能暫時故障，請稍後再試）"

# Global instance
llm_client = LLMClient()
