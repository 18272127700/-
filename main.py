import os
import logging
import asyncio

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

from aiohttp import web


# ==============================
# Telegram Bot Token (从环境变量安全读取)
# ==============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# ==============================
# 日志
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ==============================
# 接收 Telegram 消息
# ==============================
async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.info("========== 收到 UPDATE ==========")
    logger.info(str(update))

    # 普通消息
    if update.message:

        user_text = update.message.text or ""
        chat_id = update.effective_chat.id if update.effective_chat else "未知"

        logger.info("📩 收到普通消息")
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

        logger.info("📢 收到频道消息")
        logger.info(f"消息内容: {user_text}")

    # 其他类型
    else:

        logger.info("⚠️ 收到其他类型的 Update")

    logger.info("================================")


# ==============================
# Render 健康检查
# ==============================
async def handle_web(request):

    return web.Response(
        text="Bot is running!"
    )


async def start_web_server():

    app = web.Application()

    app.add_routes([
        web.get("/", handle_web)
    ])

    runner = web.AppRunner(app)

    await runner.setup()

    port = int(
        os.getenv("PORT", "10000")
    )

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()


# ==============================
# 主程序
# ==============================
def main():

    if not TELEGRAM_TOKEN:

        logger.error(
            "❌ 没有找到 TELEGRAM_TOKEN，请检查 Render 环境变量配置"
        )

        return

    tg_app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    # 接收所有类型的消息
    tg_app.add_handler(
        MessageHandler(
            filters.ALL,
            handle_message
        )
    )

    # 启动 Render Web 服务
    try:

        loop = asyncio.get_event_loop()

    except RuntimeError:

        loop = asyncio.new_event_loop()

        asyncio.set_event_loop(loop)

    loop.run_until_complete(
        start_web_server()
    )

    logger.info(
        "🤖 机器人启动成功，开始监听..."
    )

    # Telegram 轮询
    tg_app.run_polling()


# ==============================
# 启动
# ==============================
if __name__ == "__main__":

    main()
