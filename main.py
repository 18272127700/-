import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import asyncio
from aiohttp import web

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 从环境变量中获取 Telegram Bot Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"收到来自 {chat_id} 的消息: {user_text}")
    # 这里是消息转发逻辑，目前先原样回复测试
    await update.message.reply_text(f"收到你的消息: {user_text}")

# 搭建一个极简的 web 服务应对 Render 的健康检查，防止被判死刑
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

    # 用事件循环同时跑 Web 服务和 Telegram 轮询（兼容新版 Python）
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(start_web_server())

    logger.info("机器人启动成功，开始监听...")
    tg_app.run_polling()

if __name__ == "__main__":
    main()
