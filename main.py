import os
import sys
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    JoinEvent
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Get channel secret and access token from environment variables
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

if CHANNEL_SECRET is None:
    print('Warning: LINE_CHANNEL_SECRET is not set.')
if CHANNEL_ACCESS_TOKEN is None:
    print('Warning: LINE_CHANNEL_ACCESS_TOKEN is not set.')

# Initialize Line Bot configuration
if CHANNEL_ACCESS_TOKEN:
    configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
else:
    configuration = None

if CHANNEL_SECRET:
    line_handler = WebhookHandler(CHANNEL_SECRET)
else:
    line_handler = None


@app.get("/")
async def root():
    return {"message": "Line Bot Translator is running!"}


@app.post("/callback")
async def callback(request: Request):
    # get X-Line-Signature header value
    signature = request.headers.get('X-Line-Signature')

    # get request body as text
    body = await request.body()
    body_text = body.decode('utf-8')

    # handle webhook body
    try:
        if line_handler:
            line_handler.handle(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return 'OK'


@line_handler.add(FollowEvent)
def handle_follow(event):
    """
    Handle FollowEvent (Welcome message)
    """
    welcome_text = '歡迎使用真心話翻譯機！\n請先設定你的角色，輸入 "設定：我是男友" 或 "設定：我是女友"。'
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=welcome_text)]
            )
        )


@line_handler.add(JoinEvent)
def handle_join(event):
    """
    Handle JoinEvent (Group/Room restrictions)
    """
    # Bot only supports 1:1, so leave if joined a group or room
    if event.source.type in ['group', 'room']:
        try:
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="抱歉，本 Bot 只支援一對一情侶對話。再見！")]
                    )
                )
                if event.source.type == 'group':
                    line_bot_api.leave_group(event.source.group_id)
                elif event.source.type == 'room':
                    line_bot_api.leave_room(event.source.room_id)
        except Exception as e:
            print(f"Error leaving group/room: {e}")


@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """
    Handle TextMessageEvent
    """
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # Check if it's a group or room (Double check, though JoinEvent should handle it)
    if event.source.type != 'user':
        # Logic to leave is handled in JoinEvent, but if we receive a message in a group
        # before leaving, we might want to ignore or leave again.
        # For now, just return to avoid processing group messages.
        return

    # 1. Role Setting Detection
    # Normalize text: remove spaces and colons for easier matching
    clean_text = text.replace("：", "").replace(":", "").replace(" ", "")
    
    # Check for keywords
    is_role_setting = False
    new_role = None
    
    if any(keyword in clean_text for keyword in ["設定", "我是"]):
        if "男友" in clean_text:
            new_role = "男友"
            is_role_setting = True
        elif "女友" in clean_text:
            new_role = "女友"
            is_role_setting = True
    
    # Also allow exact matches for "男友" or "女友"
    if clean_text in ["男友", "女友"]:
        new_role = clean_text
        is_role_setting = True

    if is_role_setting and new_role:
        from store import store
        success = store.set_role(user_id, new_role)
        
        # Get Process ID to hint about Serverless state
        import os
        pid = os.getpid()
        
        if success:
            reply_text = f"設定成功！你的角色是：{new_role}\n(Server PID: {pid})\n\n注意：在 Vercel 上，若一段時間未對話，記憶體可能會被重置，導致角色遺失。"
        else:
            reply_text = "設定失敗，系統錯誤。"
            
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
        return

    # 2. Context Storage (for non-setting messages)
    # Relaxed translation command detection
    is_translation_command = "翻譯" in text or text in ["譯", "1"]
    
    if not is_translation_command:
        from store import store
        store.add_message_to_context(
            user_id=user_id, 
            partner_id=None, 
            message_text=text, 
            is_user_speaker=False # Treat as partner's message per MVP assumption
        )

    # 3. Translation Trigger Detection
    if is_translation_command:
        print(f"Translation triggered by text: {text}") # Debug log
        from store import store
        role = store.get_role(user_id)
        
        if not role:
            reply_text = "請先設定你的角色。例如輸入：設定：我是女友"
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )
            return

        # 4. Execute Translation
        last_message = store.get_last_partner_message(user_id)
        if not last_message:
            reply_text = "沒有可翻譯的訊息。請先傳送或轉傳一句話給我。"
        else:
            # Get context for better translation
            context = store.get_recent_context(user_id)
            
            # Call LLM
            from llm_client import llm_client
            translation = llm_client.call_llm_api(context, last_message, role)
            reply_text = f"真心話：{translation}"

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
