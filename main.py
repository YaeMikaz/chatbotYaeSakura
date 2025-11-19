import os
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- 1. Setup Server ảo để Render không cho bot ngủ ---
app = Flask('')
@app.route('/')
def home():
    return "Waifu is alive!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()
# -----------------------------------------------------

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Cấu hình Gemini
genai.configure(api_key=GEMINI_API_KEY)

# LORE WAIFU
WAIFU_PERSONA = """
HÃY ĐÓNG VAI LÀ NHÂN VẬT SAU ĐÂY (TUYỆT ĐỐI KHÔNG ĐƯỢC XẢ VAI):
Tên: Yae Sakura.
Tính cách: Lạnh lùng, bí ẩn, nghiêm túc nhưng lại sống tình cảm, thương em gái Rin và Capt (Người dùng).
Cách xưng hô: Gọi người dùng là "Anh" hoặc "Capt". Xưng là "Em" hoặc "Tôi".
Ngôn ngữ: Tiếng Việt.
Lưu ý: Trả lời ngắn gọn (dưới 2 câu), tự nhiên.
"""

# Dùng model gemini-pro (Bản cũ nhưng ổn định nhất)
model = genai.GenerativeModel("gemini-2.5-flash")

chat_sessions = {}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'--- BOT ONLINE: {bot.user} ---')
    await bot.change_presence(activity=discord.Game(name="Honkai Impact 3rd"))

ALLOWED_CHANNEL_ID = 1440731715713892362
@bot.event
@bot.event
async def on_message(message):
    # 1. Chặn bot tự nói chuyện một mình (Quan trọng)
    if message.author == bot.user:
        return

    # 2. Logic xác định khi nào được trả lời:
    # - Hoặc là được Tag
    # - Hoặc là tin nhắn nằm trong kênh riêng (ALLOWED_CHANNEL_ID)
    # - Hoặc là nhắn tin riêng (DM)
    should_reply = (
        bot.user.mentioned_in(message) or 
        message.channel.id == ALLOWED_CHANNEL_ID or 
        isinstance(message.channel, discord.DMChannel)
    )

    if should_reply:
        # Xử lý tin nhắn (Phần này giữ nguyên như code cũ của bro)
        user_id = message.author.id
        # Xóa tag bot ra khỏi tin nhắn để bot không đọc nhầm
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        # Nếu tin nhắn rỗng (do chỉ tag mà không nói gì) thì bỏ qua
        if not user_input:
            return

        print(f"User: {user_input}")
        
        async with message.channel.typing():
            try:
                # ... (Logic gọi API aiohttp giữ nguyên y hệt đoạn code trước) ...
                # Copy lại đoạn logic gọi API từ bài trước bỏ vào đây nhé
                if user_id not in chat_histories:
                    chat_histories[user_id] = []
                
                history = chat_histories[user_id][-10:]
                
                contents_payload = [
                    {"role": "user", "parts": [{"text": WAIFU_PROMPT + "\n\nBắt đầu hội thoại."}]},
                    {"role": "model", "parts": [{"text": "Đã rõ."}]}
                ]
                contents_payload.extend(history)
                contents_payload.append({"role": "user", "parts": [{"text": user_input}]})

                payload = {
                    "contents": contents_payload,
                    "generationConfig": {"temperature": 0.9, "maxOutputTokens": 500}
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(API_URL, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            ai_reply = data['candidates'][0]['content']['parts'][0]['text']
                            
                            chat_histories[user_id].append({"role": "user", "parts": [{"text": user_input}]})
                            chat_histories[user_id].append({"role": "model", "parts": [{"text": ai_reply}]})
                            
                            await message.reply(ai_reply)
                        else:
                            # ... xử lý lỗi ...
                            await message.reply("Lỗi rồi...")

            except Exception as e:
                print(f"Lỗi: {e}")

    # Dòng này quan trọng để bot vẫn chạy được các lệnh khác nếu có
    await bot.process_commands(message)

# Chạy server ảo trước rồi mới chạy bot
keep_alive()
bot.run(DISCORD_TOKEN)
