import asyncio
import logging
import os
from core.config import Config
from core.db_manager import db
from core.file_manager import file_manager
from connectors.gmail_client import GmailClient
from connectors.tg_bot import TGBotHandler
from skills.rfq_parser import RFQSkill

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def mail_polling_task(gmail_client, rfq_skill, tg_bot):
    """背景巡邏 Gmail 並驅動 Agent 流程"""
    temp_dir = "temp_rfq_attachments"
    while True:
        logging.info("掃描新 RFQ 郵件...")
        emails = gmail_client.fetch_unprocessed_rfqs(base_save_dir=temp_dir)

        for mail in emails:
            rfq_id = f"RFQ-{mail['uid']}"
            logging.info(f"處理 {rfq_id}")

            # 1. 呼叫大腦解析
            pdf_paths = mail.get('attachments', [])
            parsed_result = rfq_skill.parse_and_draft(mail['text'], pdf_paths)

            # 2. 建立本地枝狀目錄
            items = parsed_result.get('items', [])
            item_name = items[0].get('item_name', 'UnknownItem') if items else 'UnknownItem'
            paths = file_manager.create_rfq_tree(rfq_id, item_name)

            # 搬移附件至「1_原始需求」
            if '1_原始需求' in paths:
                for att in pdf_paths:
                    if os.path.exists(att):
                        os.rename(att, os.path.join(paths['1_原始需求'], os.path.basename(att)))

            # 3. 寫入資料庫
            db.save_rfq_record(rfq_id, mail['text'], parsed_result, status="PENDING")

            # 4. 推播至 Telegram 等待指令
            summary = f"料號: {item_name}\n數量: {items[0].get('quantity', 'N/A') if items else 'N/A'}"
            await tg_bot.send_draft_for_approval(rfq_id, summary, parsed_result.get('draft', '草稿生成失敗'))

            # 5. 更新 Gmail 狀態
            gmail_client.mark_as_read(mail['uid'])
            gmail_client.update_label(mail['uid'], "RFQ-進行中")

        await asyncio.sleep(60)

async def main():
    Config.validate()
    gmail_client = GmailClient(Config.GMAIL_USER, Config.GMAIL_PWD)
    tg_bot = TGBotHandler(Config.TG_TOKEN, Config.TG_CHAT_ID)
    rfq_skill = RFQSkill(Config.GEMINI_API_KEY)

    # 啟動背景任務
    asyncio.create_task(mail_polling_task(gmail_client, rfq_skill, tg_bot))

    # 啟動 Telegram Bot (將阻塞主執行緒保持運行)
    logging.info("Agent 系統已啟動，開始監聽 Telegram...")
    await tg_bot.application.initialize()
    await tg_bot.application.start()
    await tg_bot.application.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
