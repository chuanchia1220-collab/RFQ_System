import os
import smtplib
from email.message import EmailMessage
import ssl
from imap_tools import MailBox, AND

class GmailClient:
    def __init__(self, user, pwd):
        self.user = user
        self.pwd = pwd
        self.imap_server = "imap.gmail.com"
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465

    def fetch_unprocessed_rfqs(self, base_save_dir):
        """
        抓取未讀且標題含 RFQ 的信件。
        附件將依據 UID 建立獨立資料夾或命名。
        """
        rfq_emails = []
        os.makedirs(base_save_dir, exist_ok=True)

        try:
            with MailBox(self.imap_server).login(self.user, self.pwd) as mailbox:
                # mark_seen=False: 確保系統處理完畢前，信件保持未讀，避免漏單
                for msg in mailbox.fetch(AND(seen=False, subject="RFQ"), mark_seen=False):
                    attachments_info = []

                    for att in msg.attachments:
                        if att.filename.lower().endswith((".pdf", ".eml")):
                            # 強制加入 uid 避免不同信件的同名附件覆蓋
                            safe_filename = f"{msg.uid}_{att.filename}"
                            file_path = os.path.join(base_save_dir, safe_filename)

                            with open(file_path, "wb") as f:
                                f.write(att.payload)
                            attachments_info.append(file_path)

                    # 優先使用純文字，避免 HTML 標籤消耗 Token
                    clean_text = msg.text if msg.text else msg.html

                    rfq_emails.append({
                        "uid": msg.uid,
                        "subject": msg.subject,
                        "from": msg.from_,
                        "text": clean_text,
                        "attachments": attachments_info,
                        "date": msg.date
                    })
        except Exception as e:
            print(f"[Gmail Error] Fetching emails failed: {e}")

        return rfq_emails

    def send_mail(self, to_addr, subject, body, bcc_self=True):
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = self.user
        msg['To'] = to_addr

        if bcc_self:
            msg['Bcc'] = self.user

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
                server.login(self.user, self.pwd)
                server.send_message(msg)
                print(f"[Gmail Info] Successfully sent email to {to_addr}")
        except Exception as e:
            print(f"[Gmail Error] Failed to send email: {e}")

    def update_label(self, msg_uid, new_label):
        """
        注意：使用此功能前，必須先在 Gmail 網頁端手動建立對應名稱的標籤
        """
        try:
            with MailBox(self.imap_server).login(self.user, self.pwd) as mailbox:
                mailbox.client.uid('STORE', str(msg_uid), '+X-GM-LABELS', f'"{new_label}"')
                print(f"[Gmail Info] Label '{new_label}' added to message UID {msg_uid}")
        except Exception as e:
            print(f"[Gmail Error] Error updating label: {e}")

    def mark_as_read(self, msg_uid):
        """將信件標記為已讀，於生成草稿後呼叫"""
        try:
            with MailBox(self.imap_server).login(self.user, self.pwd) as mailbox:
                mailbox.flag(str(msg_uid), '\\Seen', True)
        except Exception as e:
            print(f"[Gmail Error] Failed to mark as read: {e}")
