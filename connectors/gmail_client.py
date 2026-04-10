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

    def fetch_unprocessed_rfqs(self, save_dir):
        """
        使用 imap_tools 抓取未讀且標題含 RFQ 的信件。
        必須支援下載附檔 PDF，並存入 1_原始需求 資料夾 (save_dir)。
        回傳解析出來的郵件結構清單。
        """
        rfq_emails = []
        os.makedirs(save_dir, exist_ok=True)

        try:
            with MailBox(self.imap_server).login(self.user, self.pwd) as mailbox:
                # 搜尋未讀且標題包含 RFQ 的信件
                for msg in mailbox.fetch(AND(seen=False, subject="RFQ")):
                    attachments_info = []
                    # 處理附件下載
                    for att in msg.attachments:
                        if att.filename.lower().endswith(".pdf") or att.filename.lower().endswith(".eml"):
                            file_path = os.path.join(save_dir, att.filename)
                            # 避免檔名重複可以加上 uid
                            # file_path = os.path.join(save_dir, f"{msg.uid}_{att.filename}")
                            with open(file_path, "wb") as f:
                                f.write(att.payload)
                            attachments_info.append(file_path)

                    rfq_emails.append({
                        "uid": msg.uid,
                        "subject": msg.subject,
                        "from": msg.from_,
                        "text": msg.text or msg.html,
                        "attachments": attachments_info,
                        "date": msg.date
                    })
        except Exception as e:
            print(f"Error fetching emails: {e}")

        return rfq_emails

    def send_mail(self, to_addr, subject, body, bcc_self=True):
        """
        使用 smtplib 發送郵件
        """
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
                print(f"Successfully sent email to {to_addr}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def update_label(self, msg_uid, new_label):
        """
        更新 Gmail 標籤 (RFQ-進行中 / 已詢價 / 已完成)
        IMAP tags 對應到 Gmail labels.
        """
        try:
            with MailBox(self.imap_server).login(self.user, self.pwd) as mailbox:
                # 使用 Gmail 的 X-GM-LABELS 擴充功能來設定自訂標籤
                mailbox.client.uid('STORE', str(msg_uid), '+X-GM-LABELS', f'"{new_label}"')
                print(f"Label {new_label} added to message {msg_uid}")
        except Exception as e:
            print(f"Error updating label: {e}")
