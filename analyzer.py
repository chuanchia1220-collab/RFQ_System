def generate_draft(self, supplier_dropdown, item):
        print("\n[Draft] 按鈕被點擊，開始生成流程...")
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
        
        try:
            # 檢查作業系統
            if os.name == 'nt':
                print("[Draft] 偵測到 Windows 環境，嘗試載入 win32com...")
                import win32com.client
                outlook = win32com.client.Dispatch('Outlook.Application')
                print("[Draft] Outlook 應用程式物件建立成功")
                
                mail = outlook.CreateItem(0)
                mail.Subject = subject
                mail.HTMLBody = f"{template[3]}<br>Item: {item['material_type']} {item['form']}<br>Spec: {item['spec']}<br>{template[4]}"
                mail.To = supplier[3]
                mail.Save()
                
                print("[Draft] 草稿儲存指令已發送")
                msg = "Outlook 草稿已建立，請檢查草稿匣 (Drafts)"
            else:
                msg = f"非 Windows 環境: 已模擬建立草稿給 {supplier[1]}"
            
            self.main_page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.main_page.snack_bar.open = True
            
        except ImportError:
            print("[Draft 錯誤] 找不到 pywin32 模組，請執行 pip install pywin32")
            self.main_page.snack_bar = ft.SnackBar(ft.Text("錯誤：請安裝 Outlook 驅動 (pip install pywin32)"))
            self.main_page.snack_bar.open = True
        except Exception as ex:
            print(f"[Draft 錯誤] Outlook 操作失敗: {ex}")
            self.main_page.snack_bar = ft.SnackBar(ft.Text(f"草稿建立失敗: {str(ex)}"))
            self.main_page.snack_bar.open = True
            
        self.main_page.update()
