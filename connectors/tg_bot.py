from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

class TGBotHandler:
    def __init__(self, token):
        self.token = token

    async def send_draft_for_approval(self, chat_id, rfq_id, draft_content, bot=None):
        """
        傳送 Inline Keyboard
        包含 [✅ 確認發送] [💾 存為草稿] [❌ 捨棄]
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ 確認發送", callback_data=f"send_{rfq_id}"),
                InlineKeyboardButton("💾 存為草稿", callback_data=f"draft_{rfq_id}"),
            ],
            [
                InlineKeyboardButton("❌ 捨棄", callback_data=f"discard_{rfq_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = f"【RFQ #{rfq_id} 草稿審核】\n\n{draft_content}\n\n*如需修改，請直接回覆您想修改的內容指示。*"

        # In a real app we'd use application.bot.send_message
        if bot:
            await bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            print(f"Would send to {chat_id}: {message_text}")

        return reply_markup

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        處理按鈕點擊事件，推進狀態機
        """
        query = update.callback_query
        await query.answer()

        data = query.data
        if data.startswith("send_"):
            rfq_id = data.split("_")[1]
            # TODO: 推進狀態為 SENT
            await query.edit_message_text(text=f"RFQ #{rfq_id} 已確認發送！")

        elif data.startswith("draft_"):
            rfq_id = data.split("_")[1]
            # TODO: 推進狀態為 DRAFTED
            await query.edit_message_text(text=f"RFQ #{rfq_id} 已存為草稿！")

        elif data.startswith("discard_"):
            rfq_id = data.split("_")[1]
            # TODO: 捨棄流程
            await query.edit_message_text(text=f"RFQ #{rfq_id} 已捨棄。")

    async def handle_text_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        處理用戶直接回覆文字的「修正指令」，觸發 AI 重新擬稿
        """
        user_text = update.message.text
        chat_id = update.effective_chat.id

        # 在實際整合中，需要從 context.user_data 中取出對應的 RFQ ID 和前次草稿
        # rfq_id = context.user_data.get('current_rfq')
        # previous_draft = context.user_data.get('current_draft')

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"收到修正指示：「{user_text}」\nAI 正在重新擬稿中，請稍候..."
        )

        # TODO: Trigger RFQSkill.parse_and_draft with user_text as user_instruction
