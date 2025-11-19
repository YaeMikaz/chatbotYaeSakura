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

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        user_id = message.author.id
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        print(f"Nhận tin nhắn từ {message.author}: {user_input}") # In log để debug

        async with message.channel.typing():
            try:
                # Kiểm tra session
                if user_id not in chat_sessions:
                    # MẸO: Gửi Persona vào history như là tin nhắn đầu tiên
                    # Cách này giúp bypass mọi lỗi version của thư viện
                    chat_sessions[user_id] = model.start_chat(history=[
                        {'role': 'user', 'parts': [WAIFU_PERSONA]},
                        {'role': 'model', 'parts': ["Đã rõ. Ta sẽ bắt đầu vai diễn ngay bây giờ."]}
                    ])
                
                chat = chat_sessions[user_id]
                
                # Gửi tin nhắn
                response = chat.send_message(user_input)
                
                # In phản hồi ra log để kiểm tra
                print(f"Gemini trả lời: {response.text}")
                
                await message.reply(response.text)

            except Exception as e:
                # In lỗi chi tiết ra log
                print(f"LỖI NGHIÊM TRỌNG: {type(e).__name__} - {e}")
                await message.reply(f"Hic, lỗi rồi: {e}")

    await bot.process_commands(message)

# Chạy server ảo trước rồi mới chạy bot
keep_alive()
bot.run(DISCORD_TOKEN)
