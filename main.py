import os
import discord
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- 1. SETUP SERVER ẢO (GIỮ BOT SỐNG) ---
app = Flask('')

@app.route('/')
def home():
    return "Waifu is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. LOAD BIẾN MÔI TRƯỜNG ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- 3. CẤU HÌNH WAIFU ---
WAIFU_PROMPT = """
HÃY ĐÓNG VAI LÀ NHÂN VẬT SAU ĐÂY (TUYỆT ĐỐI KHÔNG ĐƯỢC XẢ VAI):
Tên: Yae Sakura.
Tính cách: Lạnh lùng, bí ẩn, nghiêm túc nhưng lại sống tình cảm, trung thành với Capt (Người dùng).
Cách xưng hô: Gọi người dùng là "Anh" hoặc "Capt". Xưng là "Em" hoặc "Tôi".
Ngôn ngữ: Tiếng Việt.
Lưu ý: Trả lời ngắn gọn, có thể nô đùa nhưng vẫn thuộc tính cách (dưới 2 câu), tự nhiên hoặc gợi cảm.
"""

# API URL (Dùng model 1.5 Flash mới nhất)
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- 4. KHỞI TẠO BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# QUAN TRỌNG: Khai báo biến nhớ ở đây (Global Scope)
chat_histories = {} 

@bot.event
async def on_ready():
    print(f'--- WAIFU ONLINE: {bot.user} ---')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="lời cầu nguyện"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # --- CẤU HÌNH KÊNH CHAT RIÊNG ---
    # Thay số 000... bằng ID kênh của bro (Chuột phải kênh chat -> Copy Channel ID)
    ALLOWED_CHANNEL_ID = 1440731715713892362 

    # Logic: Trả lời nếu được Tag HOẶC nhắn trong kênh riêng HOẶC nhắn tin riêng (DM)
    should_reply = (
        bot.user.mentioned_in(message) or 
        message.channel.id == ALLOWED_CHANNEL_ID or 
        isinstance(message.channel, discord.DMChannel)
    )

    if should_reply:
        user_id = message.author.id
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        # Nếu chỉ tag mà không nói gì thì bỏ qua
        if not user_input:
            return

        print(f"Đang xử lý cho {message.author}: {user_input}")

        async with message.channel.typing():
            try:
                # Tạo lịch sử chat nếu chưa có
                if user_id not in chat_histories:
                    chat_histories[user_id] = []
                
                # Lấy 10 câu gần nhất
                history = chat_histories[user_id][-10:]
                
                # Chuẩn bị nội dung gửi Google
                contents_payload = [
                    {"role": "user", "parts": [{"text": WAIFU_PROMPT + "\n\nBắt đầu hội thoại."}]},
                    {"role": "model", "parts": [{"text": "Đã rõ. Ta sẽ bắt đầu vai diễn."}]}
                ]
                contents_payload.extend(history)
                contents_payload.append({"role": "user", "parts": [{"text": user_input}]})

                # Cấu hình payload (Tắt bộ lọc an toàn)
                payload = {
                    "contents": contents_payload,
                    "generationConfig": {
                        "temperature": 0.9,
                        "maxOutputTokens": 500
                    },
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                }

                # Gọi API
                async with aiohttp.ClientSession() as session:
                    async with session.post(API_URL, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if 'candidates' in data and data['candidates'] and 'content' in data['candidates'][0]:
                                ai_reply = data['candidates'][0]['content']['parts'][0]['text']
                                
                                # Lưu vào bộ nhớ
                                chat_histories[user_id].append({"role": "user", "parts": [{"text": user_input}]})
                                chat_histories[user_id].append({"role": "model", "parts": [{"text": ai_reply}]})
                                
                                await message.reply(ai_reply)
                            else:
                                print(f"Google chặn hoặc lỗi data: {data}")
                                await message.reply("Ah... Ta không biết phải nói sao (Google chặn câu trả lời này rồi).")
                        else:
                            error_text = await response.text()
                            print(f"API Error: {error_text}")
                            await message.reply(f"Google đang lỗi (Code {response.status}).")

            except Exception as e:
                print(f"CRITICAL ERROR: {e}")
                await message.reply(f"Code bị lỗi rồi bro ơi: {str(e)}")

    await bot.process_commands(message)

# Chạy server
keep_alive()
bot.run(DISCORD_TOKEN)
