import flet as ft
import json
import os
from datetime import datetime
from config import TRANSLATIONS, OPTIONS, OPTION_TRANSLATIONS
import database
import analyzer

# --- 工具函數 ---
def to_json_str(data_list):
    return json.dumps(data_list) if data_list else "[]"

def from_json_str(json_str):
    try:
        return json.loads(json_str)
    except:
        return []

# --- 供應商管理組件 ---
class SupplierManager(ft.Column):
    def __init__(self, page: ft.Page, lang="zh"):
        super().__init__(expand=True)
        self.main_page = page
        self.lang = lang
        self.t = TRANSLATIONS[lang]
        self.opt_trans = OPTION_TRANSLATIONS.get(lang, {})
        
        self.suppliers = []
        self.editing_id = None
        
        # 1. 初始化輸入欄位
        self.input_name = ft.TextField(label=self.t["name"])
        self.input_contact = ft.TextField(label=self.t["contact"])
        self.input_email = ft.TextField(label=self.t["email"])
        self.input_phone = ft.TextField(label=self.t["phone"])
        self.input_address = ft.TextField(label=self.t["address"])
        self.check_materials = self._create_checkbox_group(OPTIONS["material_types"])
        self.check_forms = self._create_checkbox_group(OPTIONS["form_types"])
        self.check_qualifications = self._create_checkbox_group(OPTIONS["qualifications"])

        # 2. 建立對話框
        self.dialog = ft.AlertDialog(
            title=ft.Text(self.t["add_supplier"]),
            content=ft.Container(
                content=ft.Column([
                    self.input_name, self.input_contact, self.input_email,
                    self.input_phone, self.input_address,
                    ft.Text(self.t["materials"], weight=ft.FontWeight.BOLD), self.check_materials,
                    ft.Text(self.t["forms"], weight=ft.FontWeight.BOLD), self.check_forms,
                    ft.Text(self.t["qualifications"], weight=ft.FontWeight.BOLD), self.check_qualifications,
                ], scroll=ft.ScrollMode.AUTO),
                width=500, height=600
            ),
            actions=[
                ft.TextButton(self.t["cancel"], on_click=self.close_dialog),
                ft.TextButton(self.t["save"], on_click=self.save_supplier),
            ],
        )
        self.main_page.overlay.append(self.dialog)

        # 3. UI 佈局
        self.data_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(self.t[k])) for k in ["name", "contact", "phone", "materials", "forms", "qualifications", "actions"]],
            rows=[]
        )
        
        self.add_btn = ft.Button(
            self.t["add_supplier"],
            icon=ft.Icons.ADD,
            on_click=self.open_add_dialog
        )
        
        self.controls = [
            ft.Row([ft.Text(self.t["supplier_management"], size=30), self.add_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Row([self.data_table], scroll=ft.ScrollMode.AUTO, expand=True)
        ]

    def _create_checkbox_group(self, options):
        return ft.Column([
            ft.Checkbox(label=self.opt_trans.get(opt, opt), value=False, data=opt)
            for opt in options
        ])

    def _get_checked_values(self, checkbox_group):
        return [cb.data for cb in checkbox_group.controls if cb.value]

    def _set_checked_values(self, checkbox_group, values):
        for cb in checkbox_group.controls:
            cb.value = cb.data in values
    
    def _clear_inputs(self):
        for f in [self.input_name, self.input_contact, self.input_email, self.input_phone, self.input_address]:
            f.value = ""
        self._set_checked_values(self.check_materials, [])
        self._set_checked_values(self.check_forms, [])
        self._set_checked_values(self.check_qualifications, [])
        self.editing_id = None

    def load_data(self):
        self.suppliers = database.get_suppliers()
        self.data_table.rows = []
        for s in self.suppliers:
            s_id = s[0]
            mats = from_json_str(s[6])
            forms = from_json_str(s[7])
            quals = from_json_str(s[8])
            
            mats_disp = ", ".join([self.opt_trans.get(m, m) for m in mats])
            forms_disp = ", ".join([self.opt_trans.get(f, f) for f in forms])
            quals_disp = ", ".join([self.opt_trans.get(q, q) for q in quals])

            self.data_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(s[1])),
                    ft.DataCell(ft.Text(s[2])),
                    ft.DataCell(ft.Text(s[4])),
                    ft.DataCell(ft.Text(mats_disp)),
                    ft.DataCell(ft.Text(forms_disp)),
                    ft.DataCell(ft.Text(quals_disp)),
                    ft.DataCell(ft.Row([
                        ft.IconButton(ft.Icons.EDIT, on_click=lambda e, sid=s_id: self.open_edit_dialog(sid)),
                        ft.IconButton(ft.Icons.DELETE, on_click=lambda e, sid=s_id: self.delete_supplier(sid))
                    ])),
                ])
            )
        try:
            self.update()
        except Exception:
            pass

    def open_add_dialog(self, e):
        self._clear_inputs()
        self.dialog.title.value = ft.Text(self.t["add_supplier"])
        self.dialog.open = True
        self.main_page.update()

    def open_edit_dialog(self, s_id):
        supplier = next((s for s in self.suppliers if s[0] == s_id), None)
        if not supplier: return
        self.editing_id = s_id
        self.input_name.value = supplier[1]
        self.input_contact.value = supplier[2]
        self.input_email.value = supplier[3]
        self.input_phone.value = supplier[4]
        self.input_address.value = supplier[5]
        self._set_checked_values(self.check_materials, from_json_str(supplier[6]))
        self._set_checked_values(self.check_forms, from_json_str(supplier[7]))
        self._set_checked_values(self.check_qualifications, from_json_str(supplier[8]))
        self.dialog.title.value = ft.Text(self.t["edit_supplier"])
        self.dialog.open = True
        self.main_page.update()

    def close_dialog(self, e):
        self.dialog.open = False
        self.main_page.update()

    def save_supplier(self, e):
        data = (
            self.input_name.value, self.input_contact.value, self.input_email.value,
            self.input_phone.value, self.input_address.value,
            to_json_str(self._get_checked_values(self.check_materials)),
            to_json_str(self._get_checked_values(self.check_forms)),
            to_json_str(self._get_checked_values(self.check_qualifications))
        )
        if self.editing_id:
            database.update_supplier(self.editing_id, *data)
        else:
            database.add_supplier(*data)
        self.close_dialog(None)
        self.load_data()

    def delete_supplier(self, s_id):
        database.delete_supplier(s_id)
        self.load_data()

# --- 樣板管理組件 (TemplateManager) ---
class TemplateManager(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page
        self.templates = []
        self.editing_id = None

        self.input_name = ft.TextField(label="Template Name")
        
        # 新增欄位：預設主旨勾選 與 副本
        self.chk_default_subject = ft.Checkbox(
            label="使用預設主旨 (格式: RFQYYMMDDHH_材質_供應商)", 
            value=False,
            on_change=self.toggle_subject_input
        )
        self.input_subject = ft.TextField(label="Subject Format")
        self.input_cc = ft.TextField(label="副本 (CC) - 多筆請用分號隔開")
        
        self.input_preamble = ft.TextField(label="Preamble (HTML)", multiline=True, min_lines=3)
        self.input_closing = ft.TextField(label="Closing (HTML)", multiline=True, min_lines=3)

        self.dialog = ft.AlertDialog(
            title=ft.Text("Add Template"),
            content=ft.Container(
                content=ft.Column([
                    self.input_name, 
                    self.chk_default_subject,
                    self.input_subject, 
                    self.input_cc,
                    self.input_preamble, 
                    self.input_closing
                ], scroll=ft.ScrollMode.AUTO),
                width=600, height=600
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self.close_dialog),
                ft.TextButton("Save", on_click=self.save_template),
            ],
        )
        self.main_page.overlay.append(self.dialog)

        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Subject/Type")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[]
        )

        self.add_btn = ft.Button(
            "Add Template",
            icon=ft.Icons.ADD,
            on_click=self.open_add_dialog
        )

        self.controls = [
            ft.Row([ft.Text("Template Settings", size=30), self.add_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Row([self.data_table], scroll=ft.ScrollMode.AUTO, expand=True)
        ]

    def toggle_subject_input(self, e):
        self.input_subject.disabled = self.chk_default_subject.value
        self.input_subject.update()

    def load_data(self):
        self.templates = database.get_templates()
        self.data_table.rows = []
        for t in self.templates:
            # t: (id, name, subject, preamble, closing, fields, font, size, styles, by, at, cc, use_default)
            t_id = t[0]
            try:
                use_default = t[12] if len(t) > 12 else 0
            except:
                use_default = 0

            subject_display = "預設格式 (Auto)" if use_default else (t[2] or "")

            self.data_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(t[1])),
                    ft.DataCell(ft.Text(subject_display)),
                    ft.DataCell(ft.Row([
                        ft.IconButton(ft.Icons.EDIT, on_click=lambda e, tid=t_id: self.open_edit_dialog(tid)),
                        ft.IconButton(ft.Icons.DELETE, on_click=lambda e, tid=t_id: self.delete_template(tid))
                    ])),
                ])
            )
        try:
            self.update()
        except Exception:
            pass

    def open_add_dialog(self, e):
        self.editing_id = None
        self.input_name.value = ""
        self.chk_default_subject.value = False
        self.input_subject.value = ""
        self.input_subject.disabled = False
        self.input_cc.value = ""
        self.input_preamble.value = ""
        self.input_closing.value = ""
        self.dialog.title.value = ft.Text("Add Template")
        self.dialog.open = True
        self.main_page.update()

    def open_edit_dialog(self, t_id):
        tmpl = next((t for t in self.templates if t[0] == t_id), None)
        if not tmpl: return
        self.editing_id = t_id
        self.input_name.value = tmpl[1]
        self.input_subject.value = tmpl[2] or ""
        self.input_preamble.value = tmpl[3] or ""
        self.input_closing.value = tmpl[4] or ""
        
        cc_val = tmpl[11] if len(tmpl) > 11 else ""
        use_default_val = tmpl[12] if len(tmpl) > 12 else 0

        self.input_cc.value = cc_val or ""
        self.chk_default_subject.value = bool(use_default_val)
        self.input_subject.disabled = bool(use_default_val)

        self.dialog.title.value = ft.Text("Edit Template")
        self.dialog.open = True
        self.main_page.update()

    def close_dialog(self, e):
        self.dialog.open = False
        self.main_page.update()

    def save_template(self, e):
        use_def = 1 if self.chk_default_subject.value else 0
        if self.editing_id:
            database.update_template(
                self.editing_id, 
                self.input_name.value, 
                self.input_subject.value, 
                self.input_preamble.value, 
                self.input_closing.value,
                self.input_cc.value, 
                use_def
            )
        else:
            database.add_template(
                self.input_name.value, 
                self.input_subject.value, 
                self.input_preamble.value, 
                self.input_closing.value,
                self.input_cc.value,
                use_def
            )
        self.close_dialog(None)
        self.load_data()

    def delete_template(self, t_id):
        database.delete_template(t_id)
        self.load_data()

# --- 詢價解析組件 (RFQAnalyzer) ---
class RFQAnalyzer(ft.Column):
    def __init__(self, page: ft.Page, lang="zh"):
        super().__init__(expand=True)
        self.main_page = page
        self.lang = lang
        self.t = TRANSLATIONS[lang]
        self.opt_trans = OPTION_TRANSLATIONS.get(lang, {})
        self.analyzed_items = []

        self.input_text = ft.TextField(
            multiline=True,
            min_lines=10,
            label="貼上詢價 Email 內容",
            expand=True
        )

        self.analyze_btn = ft.Button(
            "開始解析",
            icon=ft.Icons.ANALYTICS,
            on_click=self.run_analysis
        )

        self.results_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

        self.controls = [
            ft.Text(self.t["rfq_analysis"], size=30),
            ft.Divider(),
            ft.Row([self.input_text], expand=False),
            ft.Row([self.analyze_btn], alignment=ft.MainAxisAlignment.END),
            ft.Divider(),
            ft.Text("解析結果與匹配 (材質分組)", size=20, weight=ft.FontWeight.BOLD),
            self.results_container
        ]

    def run_analysis(self, e):
        print("\n[UI 階段 1] 點擊解析按鈕")
        self.analyze_btn.disabled = True
        self.analyze_btn.text = "解析中..."
        self.main_page.update()

        try:
            # 1. 解析
            analysis_result = analyzer.analyze_rfq(self.input_text.value)
            all_items = analysis_result.get("items", [])
            
            # 儲存紀錄
            req_id = database.save_rfq_request(self.input_text.value, json.dumps(all_items))

            self.results_container.controls = []

            # 2. 分組
            grouped_items = {}
            for item in all_items:
                mat_type = item.get("material_type", "Other")
                if mat_type not in grouped_items:
                    grouped_items[mat_type] = []
                grouped_items[mat_type].append(item)

            if not grouped_items:
                 self.main_page.snack_bar = ft.SnackBar(ft.Text("未能解析出項目，請檢查 API Key 或輸入內容"))
                 self.main_page.snack_bar.open = True
                 return

            # 3. 渲染
            for mat_type, group_items_list in grouped_items.items():
                print(f"[UI 階段 3] 正在處理分組: {mat_type}, 共 {len(group_items_list)} 個項目")
                
                matched_suppliers = database.search_suppliers([mat_type], [])
                supplier_options = [ft.dropdown.Option(str(s[0]), f"{s[1]} ({s[2]})") for s in matched_suppliers]
                
                ui_rows_data = [] 
                data_rows = []

                for idx, item in enumerate(group_items_list):
                    matched_ids = [s[0] for s in matched_suppliers]
                    database.save_rfq_item(req_id, idx, mat_type, item.get("form", "Other"), json.dumps(item), matched_ids)
                    
                    # 建立輸入框
                    txt_spec = ft.TextField(value=item.get("material_spec", "-"), border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, expand=True)
                    txt_form = ft.TextField(value=item.get("form", "-"), border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, width=80)
                    txt_dims = ft.TextField(value=item.get("dimensions", "-"), border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, expand=True)
                    txt_qty = ft.TextField(value=item.get("quantity", "-"), border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, width=80)
                    txt_notes = ft.TextField(value=item.get("notes", "-"), border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, expand=True)
                    
                    # Price 欄位 (唯讀/Placeholder)
                    txt_price = ft.TextField(value="", disabled=True, border=ft.InputBorder.NONE, dense=True, text_size=13, width=60, hint_text="(Vendor)")

                    # 新增 MOQ 欄位 (可編輯)
                    txt_moq = ft.TextField(value="", border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, width=80, hint_text="if need")

                    ui_rows_data.append({
                        "mat_type": mat_type,
                        "spec": txt_spec,
                        "form": txt_form,
                        "dimensions": txt_dims,
                        "quantity": txt_qty,
                        "moq": txt_moq,  # 加入 moq 參照
                        "notes": txt_notes
                    })

                    data_rows.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(idx + 1))),
                            ft.DataCell(txt_spec),
                            ft.DataCell(txt_form),
                            ft.DataCell(txt_dims),
                            ft.DataCell(txt_qty),
                            ft.DataCell(txt_price), 
                            ft.DataCell(txt_moq),   # UI 顯示 MOQ
                            ft.DataCell(txt_notes),
                        ])
                    )

                items_table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("#")),
                        ft.DataColumn(ft.Text("Spec")),
                        ft.DataColumn(ft.Text("Form")),
                        ft.DataColumn(ft.Text("Dimensions")),
                        ft.DataColumn(ft.Text("Qty")),
                        ft.DataColumn(ft.Text("Price")),
                        ft.DataColumn(ft.Text("MOQ")), # 新增標題
                        ft.DataColumn(ft.Text("Notes")),
                    ],
                    rows=data_rows,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    vertical_lines=ft.border.all(1, ft.Colors.GREY_200),
                    horizontal_lines=ft.border.all(1, ft.Colors.GREY_200),
                    data_row_min_height=40,
                    data_row_max_height=60,
                )

                supp_dd1 = ft.Dropdown(label="供應商 1", options=supplier_options, width=200, dense=True)
                supp_dd2 = ft.Dropdown(label="供應商 2", options=supplier_options, width=200, dense=True)
                supp_dd3 = ft.Dropdown(label="供應商 3", options=supplier_options, width=200, dense=True)
                supp_dd4 = ft.Dropdown(label="供應商 4", options=supplier_options, width=200, dense=True)

                batch_draft_btn = ft.Button(
                    "生成草稿 (批次)",
                    icon=ft.Icons.EMAIL,
                    on_click=lambda e, rows=ui_rows_data, mt=mat_type, dds=[supp_dd1, supp_dd2, supp_dd3, supp_dd4]: self.generate_batch_drafts(rows, dds, mt)
                )

                card = ft.Card(
                    content=ft.Container(
                        padding=20,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.CATEGORY, color=ft.Colors.BLUE),
                                ft.Text(f"材質群組: {mat_type}", size=20, weight=ft.FontWeight.BOLD)
                            ]),
                            ft.Divider(),
                            items_table,
                            ft.Divider(),
                            ft.Text("選擇詢價對象 (最多 4 家):", weight=ft.FontWeight.BOLD),
                            ft.Row([supp_dd1, supp_dd2, supp_dd3, supp_dd4], wrap=True),
                            ft.Row([batch_draft_btn], alignment=ft.MainAxisAlignment.END)
                        ])
                    )
                )
                self.results_container.controls.append(card)

            print("[UI 階段 5] 介面更新完成")

        except Exception as ex:
            print(f"[UI 錯誤] 流程崩潰: {ex}")
            self.main_page.snack_bar = ft.SnackBar(ft.Text(f"發生錯誤: {str(ex)}"))
            self.main_page.snack_bar.open = True
        finally:
            self.reset_btn()
            self.main_page.update()

    def reset_btn(self):
        self.analyze_btn.disabled = False
        self.analyze_btn.text = "開始解析"

    def generate_batch_drafts(self, ui_rows, dropdowns, material_type_group):
        print("\n[Draft] 開始批次生成草稿 (讀取手動修改數據)...")
        
        selected_ids = [dd.value for dd in dropdowns if dd.value]
        
        if not selected_ids:
            self.main_page.snack_bar = ft.SnackBar(ft.Text("請至少選擇 1 家供應商"))
            self.main_page.snack_bar.open = True
            self.main_page.update()
            return
        
        selected_ids = list(set(selected_ids))
        
        suppliers_db = database.get_suppliers()
        templates = database.get_templates()
        template = templates[0] if templates else (0, "Default", "Inquiry {date}", "<p>Hi,</p>", "<p>Thanks</p>", "", "", "", "", "", "", "", 0)
        
        tmpl_cc = template[11] if len(template) > 11 else ""
        use_default_subj = template[12] if len(template) > 12 else 0

        # 1. 從 UI 讀取數據 (含 MOQ)
        current_items_data = []
        for row in ui_rows:
            current_items_data.append({
                "material_type": row["mat_type"],
                "material_spec": row["spec"].value,
                "form": row["form"].value,
                "dimensions": row["dimensions"].value,
                "quantity": row["quantity"].value,
                "moq": row["moq"].value, # 讀取 MOQ
                "notes": row["notes"].value
            })

        # 2. 建立 HTML 表格內容 (加入 MOQ)
        table_style = "border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 13px;"
        th_style = "border: 1px solid #333; padding: 10px; background-color: #eee; text-align: left;"
        td_style = "border: 1px solid #333; padding: 10px;"
        
        table_rows_html = ""
        for item in current_items_data:
            table_rows_html += f"""
            <tr>
                <td style='{td_style}'>{item['material_type']}</td>
                <td style='{td_style}'>{item['material_spec']}</td>
                <td style='{td_style}'>{item['form']}</td>
                <td style='{td_style}'>{item['dimensions']}</td>
                <td style='{td_style}'>{item['quantity']}</td>
                <td style='{td_style}'></td> <td style='{td_style}'>{item['moq']}</td> <td style='{td_style}'>{item['notes']}</td>
            </tr>
            """
        
        full_table_html = f"""
        <table style='{table_style}'>
            <thead>
                <tr>
                    <th style='{th_style}'>Material</th>
                    <th style='{th_style}'>Spec</th>
                    <th style='{th_style}'>Form</th>
                    <th style='{th_style}'>Dimensions</th>
                    <th style='{th_style}'>Quantity</th>
                    <th style='{th_style}'>Price</th>
                    <th style='{th_style}'>MOQ</th>
                    <th style='{th_style}'>Notes</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>
        """

        success_count = 0
        try:
            if os.name == 'nt':
                import win32com.client
                outlook = win32com.client.Dispatch('Outlook.Application')
                
                for supp_id in selected_ids:
                    supplier = next((s for s in suppliers_db if str(s[0]) == str(supp_id)), None)
                    if not supplier: continue
                    
                    if use_default_subj:
                        date_str = datetime.now().strftime("%y%m%d%H")
                        subject = f"RFQ{date_str}_{material_type_group}_{supplier[1]}"
                    else:
                        raw_subj = template[2] or "Inquiry"
                        try:
                            subject = raw_subj.format(date=datetime.now().strftime("%Y%m%d")) + f"_{supplier[1]}"
                        except:
                            subject = raw_subj + f"_{supplier[1]}"
                    
                    mail = outlook.CreateItem(0)
                    mail.Subject = subject
                    mail.HTMLBody = f"<div>{template[3]}</div><br>{full_table_html}<br><div>{template[4]}</div>"
                    mail.To = supplier[3]
                    if tmpl_cc:
                        mail.CC = tmpl_cc
                        
                    mail.Save()
                    success_count += 1
                    print(f"[Draft] 已建立草稿給: {supplier[1]}")
                
                msg = f"成功建立 {success_count} 封草稿 (請至 Outlook 草稿匣查看)"
            else:
                msg = f"非 Windows 環境: 模擬建立 {len(selected_ids)} 封草稿"
            
            self.main_page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.main_page.snack_bar.open = True
            
        except Exception as ex:
            print(f"[Draft 錯誤] Outlook 操作失敗: {ex}")
            self.main_page.snack_bar = ft.SnackBar(ft.Text(f"草稿建立失敗: {str(ex)}"))
            self.main_page.snack_bar.open = True
            
        self.main_page.update()

# --- 主程式 ---
def main(page: ft.Page):
    database.init_db()
    page.title = "RFQ System v1.6 (MOQ & Notes Fix)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width, page.window_height = 1200, 800

    current_lang = "zh"
    t = TRANSLATIONS[current_lang]
    supplier_manager = SupplierManager(page, current_lang)
    rfq_analyzer = RFQAnalyzer(page, current_lang)
    template_manager = TemplateManager(page)
    
    content_area = ft.Container(content=supplier_manager, expand=True, padding=20)

    def on_nav_change(e):
        index = e.control.selected_index
        content_area.content = None
        if index == 0:
            content_area.content = supplier_manager
            supplier_manager.load_data()           
        elif index == 1:
            content_area.content = rfq_analyzer
        elif index == 2:
            content_area.content = template_manager
            template_manager.load_data()            
        page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.PERSON_OUTLINE, selected_icon=ft.Icons.PERSON, label=t["supplier_management"]),
            ft.NavigationRailDestination(icon=ft.Icons.ANALYTICS_OUTLINED, selected_icon=ft.Icons.ANALYTICS, label=t["rfq_analysis"]),
            ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label=t["template_settings"]),
        ],
        on_change=on_nav_change,
    )

    page.add(ft.Row([rail, ft.VerticalDivider(width=1), content_area], expand=True))
    
    supplier_manager.load_data()

if __name__ == "__main__":
    ft.run(main)
