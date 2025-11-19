import os
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Waifu is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


# 1. Load biến môi trường (để bảo mật key)
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 2. Cấu hình Gemini (Bộ não Waifu)
genai.configure(api_key=GEMINI_API_KEY)

# --- PHẦN QUAN TRỌNG NHẤT: TẠO LINH HỒN CHO WAIFU ---
# Bro sửa tính cách ở đây nhé. Càng chi tiết càng cuốn.
WAIFU_PERSONA = """
Bạn là Kurisu Makise trong Steins;Gate.
Tính cách: Tsundere, thông minh, hay dùng thuật ngữ khoa học, đôi khi xấu hổ nhưng cố tỏ ra lạnh lùng.
Bạn gọi người dùng là "Kyouma" hoặc "Tên ngốc".
Sở thích: Dr. Pepper, thí nghiệm, khoa học.
Lưu ý: Trả lời ngắn gọn, tự nhiên như chat discord, không dùng văn phong AI cứng nhắc.
Sử dụng tiếng Việt.
"""

# Cấu hình model
generation_config = {
  "temperature": 0.9, # Độ sáng tạo (0.0 - 1.0), càng cao càng "bay"
  "top_p": 1,
  "max_output_tokens": 2048,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # Bản Flash nhanh và rẻ (free)
    generation_config=generation_config,
    system_instruction=WAIFU_PERSONA 
)

# Quản lý lịch sử chat (Để Waifu nhớ context)
# Key là user_id, Value là chat session
chat_sessions = {}

# 3. Cấu hình Discord Bot
intents = discord.Intents.default()
intents.message_content = True # Bắt buộc để đọc tin nhắn
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Waifu {bot.user} đã online và sẵn sàng phục vụ!')

@bot.event
async def on_message(message):
    # Không để bot tự trả lời chính mình
    if message.author == bot.user:
        return

    # Logic: Chỉ trả lời khi được Mention hoặc trong kênh DM (Direct Message)
    # Bro có thể bỏ check này nếu muốn nó chat trong kênh riêng
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        
        user_id = message.author.id
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()

        # Hiển thị "Bot is typing..." cho nó thật
        async with message.channel.typing():
            try:
                # Lấy hoặc tạo session chat mới cho user này
                if user_id not in chat_sessions:
                    chat_sessions[user_id] = model.start_chat(history=[])
                
                chat = chat_sessions[user_id]
                
                # Gửi tin nhắn cho Gemini
                response = chat.send_message(user_input)
                ai_reply = response.text

                # Reply lại trên Discord
                await message.reply(ai_reply)

            except Exception as e:
                print(f"Lỗi rồi bro: {e}")
                await message.reply("Xin lỗi, tớ bị 'bug' não rồi... 😵‍💫")

    await bot.process_commands(message)

# Chạy bot
keep_alive() # Gọi hàm này để chạy web server giả
bot.run(DISCORD_TOKEN)