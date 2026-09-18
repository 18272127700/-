import os
import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.header import Header

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

from aiohttp import web

# ==============================
# 配置参数
# ==============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# 邮箱配置（使用 Gmail 中转，完美避开 Render 的网络限制）
MAIL_HOST = "smtp.gmail.com"
MAIL_PORT = 465
MAIL_SENDER = "您的谷歌邮箱@gmail.com"  # <--- 请在这里改成您自己的 Gmail 邮箱地址
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")  # 在 Render 后台填刚才生成的 16 位应用专用密码
MAIL_RECEIVER = "1063379810@qq.com"  # 接收邮件的 QQ 邮箱

# ==============================
# 日志
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ==============================
# 发送邮件核心函数
# ==============================
def send_email(subject, content):
    if not MAIL_PASSWORD:
        logger.error("❌ 没有找到 MAIL_PASSWORD 授权码环境变量")
        return

    try:
        message = MIMEText(content, "plain", "utf-8")
        message["From"] = Header(MAIL_SENDER, "utf-8")
        message["To"] = Header(MAIL_RECEIVER, "utf-8")
        message["Subject"] = Header(subject, "utf-8")

        server = smtplib.SMTP_SSL(MAIL_HOST, MAIL_PORT)
        server.login(MAIL_SENDER, MAIL_PASSWORD)
        server.sendmail(MAIL_SENDER, [MAIL_RECEIVER], message.as_string())
        server.quit()
        logger.info("📧 邮件通过 Gmail 成功发送到 1063379810@qq.com！")
    except Exception as e:
        logger.error(f"❌ 邮件发送失败: {e}")

# ==============================
# 接收 Telegram 消息并转发
# ==============================
async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    logger.info("========== 收到 UPDATE ==========")
    logger.info(str(update))

    text_to_send = ""

    # 普通消息
    if update.message:
        user_text = update.message.text or ""
        chat_id = update.effective_chat.id if update.effective_chat else "未知"

        logger.info("📩 收到普通消息")
        logger.info(f"群 ID: {chat_id}")
        logger.info(f"消息内容: {user_text}")

        if user_text:
            text_to_send = f"收到来自 Telegram (群ID: {chat_id}) 的消息:\n\n{user_text}"
            await update.message.reply_text(
                f"收到你的消息并已通过 Gmail 转发到邮箱: {user_text}"
            )

    # 频道消息
    elif update.channel_post:
        user_text = update.channel_post.text or ""

        logger.info("📢 收到频道消息")
        logger.info(f"消息内容: {user_text}")

        if user_text:
            text_to_send = f"收到来自 Telegram 频道的消息:\n\n{user_text}"

    # 其他类型
    else:
        logger.info("⚠️ 收到其他类型的 Update")

    # 如果有抓取到文本内容，异步推送到邮箱
    if text_to_send:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, send_email, "Telegram 实时体育数据提醒", text_to_send)

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
        "🤖 机器人启动成功，开始监听并准备通过 Gmail 转发邮件..."
    )

    # Telegram 轮询
    tg_app.run_polling()

# ==============================
# 启动
# ==============================
if __name__ == "__main__":
    main()
