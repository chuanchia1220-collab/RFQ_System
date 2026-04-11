import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

class TGBotHandler:
    def __init__(self, token: str, allowed_chat_id: str):
        self.token = token
        self.allowed_chat_id = str(allowed_chat_id)
        self.application = Application.builder().token(self.token).build()

        # 註冊路由
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.REPLY & filters.TEXT, self.handle_text_reply))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """啟動測試"""
        if str(update.effective_chat.id) != self.allowed_chat_id:
            return
        await update.message.reply_text("🟢 SMMC RFQ 數位採購助理已上線。")

    async def send_draft_for_approval(self, rfq_id: str, summary: str, draft_text: str):
        """發送解析結果與草稿，附帶操作按鈕"""
        keyboard = [
            [
                InlineKeyboardButton("✅ 確認發送", callback_data=f"send_{rfq_id}"),
                InlineKeyboardButton("💾 存為草稿", callback_data=f"draft_{rfq_id}")
            ],
            [
                InlineKeyboardButton("❌ 捨棄", callback_data=f"discard_{rfq_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = (
            f"📥 **[RFQ 審核] {rfq_id}**\n\n"
            f"**解析摘要**:\n{summary}\n\n"
            f"**預計發送草稿**:\n```\n{draft_text}\n```\n\n"
            f"*(若需修改，請直接「回覆」此訊息並輸入指令)*"
        )

        await self.application.bot.send_message(
            chat_id=self.allowed_chat_id,
            text=message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理按鈕點擊"""
        query = update.callback_query
        await query.answer()

        # 解析 callback_data (例如: "send_RFQ001")
        action, rfq_id = query.data.split("_", 1)

        if action == "send":
            await query.edit_message_text(text=f"✅ **RFQ {rfq_id}** 已進入發送排程。(系統將自動更新資料庫與匯出表單)", parse_mode="Markdown")
            # TODO: 透過事件機制通知 agent_main 執行發送
        elif action == "draft":
            await query.edit_message_text(text=f"💾 **RFQ {rfq_id}** 已標記為草稿。", parse_mode="Markdown")
            # TODO: 通知 agent_main 存檔
        elif action == "discard":
            await query.edit_message_text(text=f"❌ **RFQ {rfq_id}** 已捨棄。", parse_mode="Markdown")

    async def handle_text_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理用戶的修正指令"""
        if str(update.effective_chat.id) != self.allowed_chat_id:
            return

        reply_msg = update.message.reply_to_message
        if not reply_msg or "[RFQ 審核]" not in reply_msg.text:
            return

        user_instruction = update.message.text

        # 提取 RFQ_ID (依賴訊息格式)
        try:
            rfq_id = reply_msg.text.split("\n")[0].split("] ")[1].replace("**", "").strip()
        except IndexError:
            rfq_id = "UNKNOWN"

        await update.message.reply_text(f"🔄 收到修改指令：『{user_instruction}』\n正在為 {rfq_id} 重新擬稿中...")
        # TODO: 通知 agent_main 呼叫 RFQSkill 重新生成並再次發送草稿

    def start_polling(self):
        """啟動監聽"""
        self.application.run_polling()
