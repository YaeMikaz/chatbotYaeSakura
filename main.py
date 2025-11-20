import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- IMPORTS CHO GEMINI SDK CHUẨN ---
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- 1. SETUP SERVER ẢO (GIỮ BOT SỐNG) ---
app = Flask('')

@app.route('/')
def home():
    return "Waifu Yae Sakura is alive and watching!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. LOAD CONFIG & KHỞI TẠO ---
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please check Environment Variables on Render.")

# Cấu hình API theo cách chuẩn (Stable)
genai.configure(api_key=GEMINI_API_KEY)

# --- 3. WAIFU PROMPT ---
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

# --- 4. SETUP BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

chat_histories = {} 
# Dùng model Flash cho nhanh và miễn phí tốt trên Render, hoặc dùng "gemini-2.5-pro"
MODEL_ID = "gemini-2.5-flash" 

# Cấu hình Model
generation_config = {
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel(
    model_name=MODEL_ID,
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction=WAIFU_PROMPT # System prompt nạp thẳng vào config model mới
)

@bot.event
async def on_ready():
    print(f'--- YAE SAKURA ONLINE: {bot.user} ---')
    await bot.change_presence(activity=discord.Game(name="bên Captain"))

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # --- THAY ID KÊNH CỦA BRO VÀO ĐÂY ---
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

        print(f"Captain gọi: {user_input}")

        async with message.channel.typing():
            try:
                # Quản lý lịch sử chat
                if user_id not in chat_histories:
                    chat_histories[user_id] = []
                
                # Xây dựng history object cho thư viện
                history = chat_histories[user_id][-10:] # Lấy 10 tin gần nhất
                
                # Bắt đầu phiên chat (ChatSession)
                chat_session = model.start_chat(history=history)
                
                # Gửi tin nhắn (Asynchronous)
                response = await chat_session.send_message_async(user_input)
                
                ai_reply = response.text
                
                # Cập nhật lịch sử thủ công nếu cần (hoặc để thư viện tự lo trong session)
                # Ở đây ta lưu lại format để lần sau load lại vào history list
                chat_histories[user_id].append({"role": "user", "parts": [user_input]})
                chat_histories[user_id].append({"role": "model", "parts": [ai_reply]})
                
                await message.reply(ai_reply)

            except Exception as e:
                print(f"ERROR: {e}")
                # Đôi khi lỗi do bộ lọc an toàn chặn, cần báo cho user
                await message.reply(f"Yae đang bận chút việc... (Lỗi hệ thống: {str(e)})")

    await bot.process_commands(message)

keep_alive()
bot.run(DISCORD_TOKEN)
