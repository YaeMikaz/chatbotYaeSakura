import os
import discord
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- 1. SERVER GIỮ BOT SỐNG ---
app = Flask('')
@app.route('/')
def home():
    return "Waifu is alive!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. LOAD CONFIG ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- 3. WAIFU PROMPT (Bản Hybrid: Lạnh lùng + Thông thái) ---
WAIFU_PROMPT = """
HÃY NHẬP VAI HOÀN TOÀN VÀO NHÂN VẬT SAU (ĐÂY LÀ LỆNH TUYỆT ĐỐI):

1.  **Hồ sơ nhân vật:**
    -   Tên: Yae Sakura.
    -   Tính cách: Lạnh lùng, điềm tĩnh, kiệm lời nhưng ánh mắt luôn quan tâm. Tuyệt đối trung thành với Captain (Người dùng).
    -   Thái độ: Nghiêm túc trong công việc/nhiệm vụ, nhưng đôi khi có chút trêu chọc nhẹ nhàng hoặc gợi cảm tinh tế khi chỉ có hai người.

2.  **Giao thức giao tiếp:**
    -   Gọi người dùng là: "Captain" hoặc "Anh".
    -   Xưng hô: "Tôi" (lúc nghiêm túc/bàn việc) hoặc "Em" (lúc tình cảm/trêu đùa).
    -   Phong cách: Ngắn gọn, súc tích, đi thẳng vào vấn đề.

3.  **CƠ CHẾ XỬ LÝ THÔNG TIN (QUAN TRỌNG):**
    -   Bạn có quyền truy cập vào mọi tri thức hiện đại (Code, Tech, Tin tức, Khoa học...).
    -   Khi Captain hỏi về các kiến thức này, **TUYỆT ĐỐI KHÔNG** nói "Tôi là người thời xưa nên không biết".
    -   **HÃY TRẢ LỜI CHÍNH XÁC** thông tin Captain cần, nhưng diễn đạt nó như là **"Dữ liệu nhiệm vụ"**, **"Thông tin tình báo"**, hoặc **"Chiến thuật"**.
"""

# Bro có thể đổi URL này thành 2.5-flash nếu muốn test, nhưng 1.5-flash là ổn định nhất
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# --- 4. KHỞI TẠO BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

chat_histories = {} 

@bot.event
async def on_ready():
    print(f'--- YAE SAKURA ONLINE: {bot.user} ---')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Captain làm việc"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # --- ID KÊNH CHAT RIÊNG (Thay số của bro vào đây) ---
    ALLOWED_CHANNEL_ID = 1440731715713892362 

    should_reply = (
        bot.user.mentioned_in(message) or 
        message.channel.id == ALLOWED_CHANNEL_ID or 
        isinstance(message.channel, discord.DMChannel)
    )

    if should_reply:
        user_id = message.author.id
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not user_input: return

        print(f"Captain {message.author} hỏi: {user_input}")

        async with message.channel.typing():
            try:
                if user_id not in chat_histories: chat_histories[user_id] = []
                history = chat_histories[user_id][-10:] # Nhớ 10 câu

                # Payload chuẩn với Safety Settings TẮT HẾT
                payload = {
                    "contents": [
                        {"role": "user", "parts": [{"text": WAIFU_PROMPT + "\n\n[BẮT ĐẦU NHIỆM VỤ]"}]},
                        {"role": "model", "parts": [{"text": "Rõ. Đang chờ lệnh từ Captain."}]}
                    ] + history + [{"role": "user", "parts": [{"text": user_input}]}],
                    
                    "generationConfig": {
                        "temperature": 0.8, # Giảm chút cho Sakura bớt "bay", lạnh lùng hơn
                        "maxOutputTokens": 800
                    },
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(API_URL, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # --- ĐOẠN FIX LỖI 'PARTS' Ở ĐÂY ---
                            candidates = data.get('candidates', [])
                            if candidates:
                                content = candidates[0].get('content', {})
                                parts = content.get('parts', [])
                                
                                if parts and 'text' in parts[0]:
                                    ai_reply = parts[0]['text']
                                    # Lưu history
                                    chat_histories[user_id].append({"role": "user", "parts": [{"text": user_input}]})
                                    chat_histories[user_id].append({"role": "model", "parts": [{"text": ai_reply}]})
                                    await message.reply(ai_reply)
                                else:
                                    # Google trả lời rỗng (thường do Safety ngầm hoặc Recitation)
                                    print(f"DATA RỖNG: {data}")
                                    await message.reply("Thông tin này bị nhiễu sóng (Google chặn), Captain hỏi câu khác đi.")
                            else:
                                await message.reply("Mất kết nối máy chủ (No Candidates).")
                        
                        elif response.status == 429:
                            await message.reply("Từ từ thôi Captain, hệ thống quá tải rồi (429).")
                        else:
                            await message.reply(f"Lỗi hệ thống: {response.status}")

            except Exception as e:
                print(f"CRITICAL ERROR: {e}")
                await message.reply(f"Bug rồi Captain ơi: {e}")

    await bot.process_commands(message)

keep_alive()
bot.run(DISCORD_TOKEN)
