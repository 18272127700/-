import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from openai import AsyncOpenAI


# ==================================================
# 1. 读取 Render 环境变量
# ==================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.getenv("PORT", "10000"))


# ==================================================
# 2. 检查必要配置
# ==================================================

if not TELEGRAM_TOKEN:
    raise RuntimeError("错误：没有设置 TELEGRAM_TOKEN")

if not OPENAI_API_KEY:
    raise RuntimeError("错误：没有设置 OPENAI_API_KEY")


# ==================================================
# 3. 连接 OpenAI
# ==================================================

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY
)


# ==================================================
# 4. Render 网站健康检查
# ==================================================

async def health(request):
    return web.Response(
        text="Telegram AI Translator is running."
    )


async def start_web_server():

    app = web.Application()

    app.router.add_get("/", health)

    runner = web.AppRunner(app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    print(f"Render Web服务启动成功，端口：{PORT}")


# ==================================================
# 5. AI 自动翻译
# ==================================================

async def translate_message(text):

    prompt = f"""
你是一个足球实时数据翻译助手。

把下面的足球实时信号完整翻译成中文。

【必须遵守】

1. 保留原始排版。
2. 保留所有 Emoji。
3. 保留所有数字。
4. 保留比分。
5. 保留比赛时间。
6. 保留赔率。
7. 保留百分比。
8. 保留 Radar X。
9. 保留 Strike Rate 数据。
10. MONEYBAG 不翻译。
11. Radar X 不翻译。
12. 不改变任何球队名称中的数字。
13. 不改变任何比赛数据。

【足球术语】

Over 0.5 Goals → 大0.5球
Over 1.5 Goals → 大1.5球
Over 2.5 Goals → 大2.5球
Over 3.5 Goals → 大3.5球

Under → 小

Home → 主队
Away → 客队

Corners → 角球
Shots → 射门
Danger. Att. → 危险进攻
Attacks → 进攻
Pressure → 压力
Last 5' Shots → 最近5分钟射门

Live Stats → 实时数据
Market → 市场
Opening → 初始赔率
Kickoff → 开赛赔率
Live → 即时赔率

Team Profile → 球队资料
Form → 近期状态

【重要】

不要添加投注建议。
不要预测比赛结果。
不要评价比赛。
不要解释。

只返回翻译后的内容。

原文：

{text}
"""

    response = await client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text.strip()


# ==================================================
# 6. Telegram 收到消息
# ==================================================

async def telegram_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text

    if not text:
        return

    print("")
    print("========================================")
    print("Telegram 收到新消息：")
    print(text)
    print("========================================")

    try:

        translated = await translate_message(text)

        print("")
        print("AI 中文翻译结果：")
        print(translated)
        print("========================================")

        # 暂时只显示在 Render 日志
        # 下一步再连接 QQ

    except Exception as e:

        print("AI 翻译失败：")
        print(str(e))


# ==================================================
# 7. 启动 Telegram Bot
# ==================================================

async def start_telegram():

    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            telegram_message
        )
    )

    await application.initialize()

    await application.start()

    await application.updater.start_polling()

    print("Telegram 机器人启动成功")


# ==================================================
# 8. 主程序
# ==================================================

async def main():

    print("")
    print("========================================")
    print("Telegram AI 翻译机器人正在启动...")
    print("========================================")

    await start_web_server()

    await start_telegram()

    while True:

        await asyncio.sleep(3600)


# ==================================================
# 9. 程序入口
# ==================================================

if __name__ == "__main__":

    asyncio.run(main())
