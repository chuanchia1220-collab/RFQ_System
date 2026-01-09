# main.py 的 RFQAnalyzer 類別與結尾修正部分

class RFQAnalyzer(ft.Column):
    # ... (前面的 __init__ 與 run_analysis 保持不變)

    def reset_btn(self):
        self.analyze_btn.disabled = False
        self.analyze_btn.text = "開始解析"

    # --- 關鍵修正：確保此函式在類別內 ---
    def generate_draft(self, supplier_dropdown, item):
        print("\n[Draft] 開始生成流程...")
        supplier_id = supplier_dropdown.value
        if not supplier_id:
            self.main_page.snack_bar = ft.SnackBar(ft.Text("請先選擇供應商"))
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return
        
        suppliers = database.get_suppliers()
        supplier = next((s for s in suppliers if str(s[0]) == str(supplier_id)), None)
        templates = database.get_templates()
        template = templates[0] if templates else (0, "Default", "Inquiry {date}", "<p>Hi,</p>", "<p>Thanks</p>")

        from datetime import datetime
        subject = template[2].format(date=datetime.now().strftime("%Y%m%d")) + f"_{supplier[1]}"
        
        # 表格生成邏輯 ... (此處保留您之前的 HTML Table 代碼)
        # ...
        try:
            if os.name == 'nt':
                import win32com.client
                outlook = win32com.client.Dispatch('Outlook.Application')
                mail = outlook.CreateItem(0)
                mail.Subject = subject
                mail.HTMLBody = f"{template[3]}<br><br>...表格內容...<br><br>{template[4]}"
                mail.To = supplier[3]
                mail.Save()
                msg = "Outlook 草稿已建立"
            else:
                msg = "非 Windows 環境，模擬建立草稿"
            
            self.main_page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.main_page.snack_bar.open = True
        except Exception as ex:
            self.main_page.snack_bar = ft.SnackBar(ft.Text(f"出錯: {str(ex)}"))
            self.main_page.snack_bar.open = True
        self.main_page.update()

# --- 結尾啟動方式修正 ---
if __name__ == "__main__":
    ft.run(main) # 修正 app() 的棄用警告
