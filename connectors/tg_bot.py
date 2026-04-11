import re
import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

class TGBotHandler:
    """
    對 Jules 的集成建議實作：
    1. 內建權限過濾器 (auth_filter): 確保只有管理者 ID 能觸發指令，提升安全性。
    2. 穩定提取 ID (Regex): 透過 re.search 抓取「ID:」後方字串，應對 Telegram Text 渲染後的格式。
    3. 就地更新狀態 (query.edit_message_text): 點擊按鈕後直接「覆蓋」原訊息，防止重複操作並保持介面清爽。
    4. 異步對接預留: handle_text_reply 已預留介面供 Agent 重新觸發 RFQ 解析流程。
    """

    def __init__(self, token: str, allowed_chat_id: str):
        self.token = token
        # 轉換為 int 確保比對正確性
        self.allowed_chat_id = int(allowed_chat_id)
        self.application = Application.builder().token(self.token).build()

        # [建議 1] 權限過濾器：防止外部騷擾，僅處理管理者訊息
        self.auth_filter = filters.Chat(chat_id=self.allowed_chat_id)

        # 註冊路由
        self.application.add_handler(CommandHandler("start", self.start, filters=self.auth_filter))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.REPLY & filters.TEXT & self.auth_filter, self.handle_text_reply))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🟢 SMMC RFQ 數位採購助理已上線。")

    async def send_draft_for_approval(self, rfq_id: str, summary: str, draft_text: str):
        """
        發送解析結果與草稿。
        使用 Markdown 區塊 (```) 方便手機端一鍵點擊即可複製內容。
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ 確認發送", callback_data=f"send_{rfq_id}"),
                InlineKeyboardButton("💾 存為草稿", callback_data=f"draft_{rfq_id}")
            ],
            [
                InlineKeyboardButton("❌ 捨棄", callback_data=f"discard_{rfq_id}")
            ]
        ]

        message_text = (
            f"📥 **[RFQ 審核]**\n"
            f"ID: `{rfq_id}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📋 **解析摘要**:\n{summary}\n\n"
            f"📧 **預計發送草稿**:\n```text\n{draft_text}\n```\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 *若需修正，請直接「回覆」此訊息輸入指令*"
        )

        await self.application.bot.send_message(
            chat_id=self.allowed_chat_id,
            text=message_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """[建議 3] 處理按鈕點擊：更新原訊息狀態，節省空間並紀錄結果"""
        query = update.callback_query

        # 權限二次檢查
        if query.message.chat.id != self.allowed_chat_id:
            await query.answer("Access Denied", show_alert=True)
            return

        await query.answer()
        action, rfq_id = query.data.split("_", 1)

        status_msg = {
            "send": f"✅ **RFQ `{rfq_id}`** 已進入發送排程。",
            "draft": f"💾 **RFQ `{rfq_id}`** 已存為草稿。",
            "discard": f"🗑️ **RFQ `{rfq_id}`** 已捨棄處理。"
        }.get(action, "未知操作")

        # 就地修改訊息內容，移除按鈕避免重覆點擊
        await query.edit_message_text(text=status_msg, parse_mode="Markdown")

    async def handle_text_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """[建議 2] 處理用戶修正指令：透過 Regex 穩定抓取 RFQ ID"""
        reply_msg = update.message.reply_to_message

        # 確保回覆的是標有 [RFQ 審核] 的訊息
        if not reply_msg or "[RFQ 審核]" not in reply_msg.text:
            return

        # 透過 Regex 從回覆的文字中提取 ID
        id_match = re.search(r"ID:\s*(\S+)", reply_msg.text)
        rfq_id = id_match.group(1).replace("`", "").strip() if id_match else "UNKNOWN"
        user_instruction = update.message.text

        await update.message.reply_text(
            f"🔄 **重新擬稿中**\n目標: `{rfq_id}`\n指令: `{user_instruction}`"
        )

        # [建議 4] Jules 對接處：此處應調用 Agent 重跑 RFQ 邏輯
        # 範例：await self.main_agent.reprocess_rfq(rfq_id, user_instruction)

    def start_polling(self):
        """啟動監聽"""
        print("Telegram Bot 監聽中...")
        self.application.run_polling()
