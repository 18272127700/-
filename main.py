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

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 先把完整 Update 打印出来，方便确认 Telegram 到底发来了什么
    logger.info("========== 收到 UPDATE ==========")
    logger.info(str(update))

    # 普通群消息
    if update.message:
        user_text = update.message.text or ""

        chat_id = update.effective_chat.id if update.effective_chat else "未知"

        logger.info(f"📩 收到普通消息")
        logger.info(f"群 ID: {chat_id}")
        logger.info(f"消息内容: {user_text}")

        # 测试回复
        if user_text:
            await update.message.reply_text(
                f"收到你的消息: {user_text}"
            )

    # 频道消息
    elif update.channel_post:
        user_text = update.channel_post.text or ""

        logger.info("📢 收到 Channel Post")
        logger.info(f"消息内容: {user_text}")

    # 其他类型
    else:
        logger.info("⚠️ 收到其他类型的 Update")

    logger.info("================================")


# Render 健康检查
async def handle_web(request):
    return web.Response(text="Bot is running!")


async def start_web_server():
    app = web.Application()
    app.add_routes([
        web.get('/', handle_web)
    ])

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 10000))

    site = web.TCPSite(
        runner,
        '0.0.0.0',
        port
    )

    await site.start()


def main():
    if not TELEGRAM_TOKEN:
        logger.error("❌ 未找到 TELEGRAM_TOKEN 环境变量")
        return

    tg_app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    # 接收所有类型的 Update
    tg_app.add_handler(
        MessageHandler(
            filters.ALL,
            handle_message
        )
    )

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(
        start_web_server()
    )

    logger.info("🤖 机器人启动成功，开始监听...")

    tg_app.run_polling()


if __name__ == "__main__":
    main()()
