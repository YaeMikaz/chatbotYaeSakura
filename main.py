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
async def on_message(message):
    if message.author == bot.user:
        return

    # --- CHECK KÊNH HOẶC TAG ---
    # Nhớ thay ID kênh của bro vào chỗ số 000000 này nhé
    ALLOWED_CHANNEL_ID = 112233445566778899 
    
    should_reply = (
        bot.user.mentioned_in(message) or 
        message.channel.id == ALLOWED_CHANNEL_ID or 
        isinstance(message.channel, discord.DMChannel)
    )

    if should_reply:
        user_id = message.author.id
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not user_input:
            return

        print(f"Đang xử lý cho {message.author}: {user_input}")

        async with message.channel.typing():
            try:
                if user_id not in chat_histories:
                    chat_histories[user_id] = []
                
                history = chat_histories[user_id][-10:]
                
                contents_payload = [
                    {"role": "user", "parts": [{"text": WAIFU_PROMPT + "\n\nBắt đầu hội thoại."}]},
                    {"role": "model", "parts": [{"text": "Đã rõ."}]}
                ]
                contents_payload.extend(history)
                contents_payload.append({"role": "user", "parts": [{"text": user_input}]})

                # --- CẤU HÌNH MỚI: TẮT BỘ LỌC AN TOÀN ---
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
                # -----------------------------------------

                async with aiohttp.ClientSession() as session:
                    async with session.post(API_URL, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Kiểm tra kỹ xem có câu trả lời không (Phòng hờ vẫn bị chặn)
                            if 'candidates' in data and data['candidates'] and 'content' in data['candidates'][0]:
                                ai_reply = data['candidates'][0]['content']['parts'][0]['text']
                                
                                chat_histories[user_id].append({"role": "user", "parts": [{"text": user_input}]})
                                chat_histories[user_id].append({"role": "model", "parts": [{"text": ai_reply}]})
                                
                                await message.reply(ai_reply)
                            else:
                                # Nếu Google trả về 200 OK nhưng không có nội dung (Bị chặn hoàn toàn)
                                print(f"Dữ liệu trả về lạ: {data}")
                                await message.reply("Ah... Ta không biết phải nói sao (Google chặn câu trả lời này rồi).")
                        else:
                            error_text = await response.text()
                            print(f"API Error: {error_text}")
                            await message.reply(f"Google đang lỗi (Code {response.status}).")

            except Exception as e:
                # QUAN TRỌNG: In lỗi ra Discord để bro biết đường sửa
                print(f"CRITICAL ERROR: {e}")
                await message.reply(f"Code bị lỗi rồi bro ơi: {str(e)}")

    await bot.process_commands(message)
# Chạy server ảo trước rồi mới chạy bot
keep_alive()
bot.run(DISCORD_TOKEN)
