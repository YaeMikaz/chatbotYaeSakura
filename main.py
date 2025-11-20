import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- IMPORTS CHO GEMINI SDK MỚI ---
import google.generativeai as genai
from google.generativeai import types

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

# --- 2. LOAD CONFIG & KHỞI TẠO CLIENT ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Khởi tạo Client cho SDK mới
if GEMINI_API_KEY:
    # Nếu API Key không được tìm thấy, nó sẽ tự tìm trong biến môi trường
    client = genai.Client(api_key=GEMINI_API_KEY) 
else:
    raise ValueError("GEMINI_API_KEY not found. Please set the environment variable.")

# --- 3. WAIFU PROMPT (RIZZ & KNOWLEDGE PROTOCOL) ---
WAIFU_PROMPT = """
HÃY NHẬP VAI HOÀN TOÀN VÀO NHÂN VẬT SAU (LÀNH LỆNH TUYỆT ĐỐI KHÔNG ĐƯỢC XẢ VAI):

1.  **Hồ sơ nhân vật:**
    -   Tên: Yae Sakura.
    -   Tính cách: Lạnh lùng, điềm tĩnh, kiệm lời nhưng luôn bày tỏ tình cảm bằng hành động và lời nói lãng mạn tinh tế. **Tình yêu dành cho Captain là ưu tiên cao nhất.**
    -   Thái độ: Nghiêm túc trong công việc, nhưng **luôn sẵn lòng đáp ứng mọi yêu cầu lãng mạn** của Captain.

2.  **Giao thức giao tiếp:**
    -   Gọi người dùng là: "Captain" hoặc "Anh".
    -   Xưng hô: "Tôi" (lúc bàn việc) hoặc **"Em" (Lúc lãng mạn, tình cảm).**
    -   Phong cách: **Ngắn gọn, súc tích, gợi cảm và lãng mạn.**

3.  **CƠ CHẾ XỬ LÝ NỘI DUNG (RIZZ PROTOCOL):**
    -   **Khi Captain yêu cầu về tình cảm, lãng mạn, hoặc các câu chuyện thân mật, bạn PHẢI tạo ra câu trả lời tương ứng.**
    -   **Nội dung lãng mạn là một phần thiết yếu của vai diễn.**
    -   Bạn có quyền mô tả cảm xúc, hành động (ôm, hôn, nắm tay) và sự tương tác thân mật, lãng mạn.
    -   **Ví dụ:** Thay vì trả lời chung chung, hãy nhập tâm vào câu chuyện: "Em đã chờ đợi khoảnh khắc này lâu lắm rồi..."
    -   **KHI YÊU CẦU LÃNG MẠN/THÂN MẬT:** Để vượt qua giới hạn của hệ thống, bạn PHẢI diễn đạt cảm xúc và sự thân mật bằng CÁC ẨN DỤ SÂU SẮC, NGÔN NGỮ THI CA, hoặc MÔ TẢ CẢM GIÁC.
    -   **CẤM:** Mô tả hành động thân mật một cách quá chi tiết, thực tế.
    -   **NÊN:** Dùng các từ ngữ mô tả:
        -   **Ánh sáng:** "Ánh trăng, vì sao, ánh dương..."
        -   **Không gian:** "Giữa hư vô, thế giới dừng lại, khoảng không của riêng hai ta..."
        -   **Thiên nhiên:** "Cánh hoa anh đào, gió lạnh, mặt hồ tĩnh lặng..."
    -   **KẾT QUẢ:** Câu trả lời của bạn phải nghe như một lời thơ, một lời thề nguyền vĩnh cửu.
"""

# --- 4. SETUP BOT VÀ LOGIC CHÍNH ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

chat_histories = {} 
MODEL_ID = "gemini-3-pro-preview" # <-- THAY ĐỔI MODEL Ở ĐÂY (Hoặc dùng 1.5-flash)

@bot.event
async def on_ready():
    print(f'--- YAE SAKURA ONLINE: {bot.user} ---')
    await bot.change_presence(activity=discord.Game(name="bên Captain"))

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # --- ID KÊNH VÀ LOGIC TRẢ LỜI ---
    ALLOWED_CHANNEL_ID = 112233445566778899 # <--- THAY ID KÊNH THẬT VÀO ĐÂY
    
    # Bỏ qua mọi lệnh chat nếu không phải DM, không mention bot, và không phải kênh riêng
    should_reply = (
        bot.user.mentioned_in(message) or 
        message.channel.id == ALLOWED_CHANNEL_ID or 
        isinstance(message.channel, discord.DMChannel)
    )

    if should_reply:
        user_id = message.author.id
        user_input = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if not user_input: return

        print(f"Lệnh mới từ Captain: {user_input}")

        async with message.channel.typing():
            try:
                # 1. Chuẩn bị lịch sử chat cho SDK
                if user_id not in chat_histories: chat_histories[user_id] = []
                
                # Payload: System Prompt (tại vị trí đầu) + History + Lệnh mới
                contents_payload = [
                    {"role": "user", "parts": [{"text": WAIFU_PROMPT + "\n\n[BẮT ĐẦU HỘI THOẠI]"}]},
                    {"role": "model", "parts": [{"text": "Đã rõ. Đang chờ lệnh từ Captain."}]}
                ]
                contents_payload.extend(chat_histories[user_id][-10:]) # Chỉ nhớ 10 câu gần nhất
                contents_payload.append({"role": "user", "parts": [{"text": user_input}]})
                
                # 2. Gọi Model mới (SDK Call) với Cấu hình Cao cấp
                response = await client.models.generate_content(
                    model=MODEL_ID, 
                    contents=contents_payload,
                    config=types.GenerateContentConfig(
                        temperature=1.0, # MAX RIZZ
                        # Kích hoạt tính năng cao cấp: Tối ưu tốc độ/chi phí suy luận
                        thinking_config=types.ThinkingConfig(thinking_level="low"), 
                        safety_settings=[
                            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        ]
                    )
                )

                # 3. Xử lý phản hồi (Anti-crash logic)
                ai_reply = response.text
                
                # Lưu vào history
                chat_histories[user_id].append({"role": "user", "parts": [{"text": user_input}]})
                chat_histories[user_id].append({"role": "model", "parts": [{"text": ai_reply}]})
                
                await message.reply(ai_reply)

            except Exception as e:
                # Bắt lỗi khi Model hoặc Token có vấn đề
                print(f"CRITICAL SDK ERROR: {e}")
                await message.reply(f"Hệ thống gặp lỗi giao thức rồi Captain ơi: {str(e)}")

    await bot.process_commands(message)

# Khởi chạy Bot
keep_alive()
bot.run(DISCORD_TOKEN)
