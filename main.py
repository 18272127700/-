import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from aiohttp import web, ClientSession

# 日志配置
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# 读取环境变量
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QQ_API_URL = os.getenv("QQ_API_URL")
QQ_GROUP_ID = os.getenv("QQ_GROUP_ID")

# 异步转发到 QQ 的函数
async def send_to_qq(text: str):
    if not QQ_API_URL or not QQ_GROUP_ID:
        logger.warning("QQ API URL 或群号未配置")
        return
    
    payload = {
        "group_id": QQ_GROUP_ID,
        "message": text
    }
    async with ClientSession() as session:
        try:
            async with session.post(QQ_API_URL, json=payload) as resp:
                if resp.status != 200:
                    logger.error(f"发送到 QQ 失败，状态码: {resp.status}")
        except Exception as e:
            logger.error(f"请求 QQ 接口异常: {e}")

# 处理 Telegram 消息的主逻辑
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    original_text = update.message.text
    logger.info(f"收到 Telegram 消息: {original_text}")

    # 此处为纯净文本输出，不带任何多余的机器人提示前缀
    clean_text = original_text 

    # 直接将纯文本转发到 QQ
    await send_to_qq(clean_text)

# 搭建一个极简的 Web 服务应对 Render 的健康检查，防止被误判杀死
async def handle_web(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle_web)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

def main():
    if not TELEGRAM_TOKEN:
        logger.error("未找到 TELEGRAM_TOKEN 环境变量")
        return

    # 构建 Telegram 机器人应用
    tg_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    tg_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # 用事件循环同时跑 Web 服务和 Telegram 轮询
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    
    logger.info("机器人启动成功，开始监听...")
    tg_app.run_polling()

if __name__ == "__main__":
    main()
