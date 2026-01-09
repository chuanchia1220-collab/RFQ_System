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

# --- 供應商管理組件 (維持您手動修復後的版本) ---
class SupplierManager(ft.Column):
    def __init__(self, page: ft.Page, lang="zh"):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self.main_page = page
        self.lang = lang
        self.t = TRANSLATIONS[lang]
        self.opt_trans = OPTION_TRANSLATIONS.get(lang, {})
        
        self.suppliers = []
        self.editing_id = None
        
        # 初始化輸入欄位
        self.input_name = ft.TextField(label=self.t["name"])
        self.input_contact = ft.TextField(label=self.t["contact"])
        self.input_email = ft.TextField(label=self.t["email"])
        self.input_phone = ft.TextField(label=self.t["phone"])
        self.input_address = ft.TextField(label=self.t["address"])
        self.check_materials = self._create_checkbox_group(OPTIONS["material_types"])
        self.check_forms = self._create_checkbox_group(OPTIONS["form_types"])
        self.check_qualifications = self._create_checkbox_group(OPTIONS["qualifications"])

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
            ft.Row([self.data_table], scroll=ft.ScrollMode.AUTO)
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

# --- 樣板管理組件 (維持您手動修復後的版本) ---
class TemplateManager(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self.main_page = page
        self.templates = []
        self.editing_id = None

        self.input_name = ft.TextField(label="Template Name")
        self.chk_default_subject = ft.Checkbox(label="使用預設主旨 (格式: RFQYYMMDDHH_材質_供應商)", value=False, on_change=self.toggle_subject_input)
        self.input_subject = ft.TextField(label="Subject Format")
        self.input_cc = ft.TextField(label="副本 (CC) - 多筆請用分號隔開")
        self.input_preamble = ft.TextField(label="Preamble (HTML)", multiline=True, min_lines=3)
        self.input_closing = ft.TextField(label="Closing (HTML)", multiline=True, min_lines=3)

        self.dialog = ft.AlertDialog(
            title=ft.Text("Add Template"),
            content=ft.Container(
                content=ft.Column([
                    self.input_name, self.chk_default_subject, self.input_subject, self.input_cc, self.input_preamble, self.input_closing
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
            columns=[ft.DataColumn(ft.Text("Name")), ft.DataColumn(ft.Text("Subject/Type")), ft.DataColumn(ft.Text("Actions"))],
            rows=[]
        )

        self.add_btn = ft.Button("Add Template", icon=ft.Icons.ADD, on_click=self.open_add_dialog)

        self.controls = [
            ft.Row([ft.Text("Template Settings", size=30), self.add_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Row([self.data_table], scroll=ft.ScrollMode.AUTO)
        ]

    def toggle_subject_input(self, e):
        self.input_subject.disabled = self.chk_default_subject.value
        self.input_subject.update()

    def load_data(self):
        self.templates = database.get_templates()
        self.data_table.rows = []
        for t in self.templates:
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
        try: self.update()
        except: pass

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
            database.update_template(self.editing_id, self.input_name.value, self.input_subject.value, self.input_preamble.value, self.input_closing.value, self.input_cc.value, use_def)
        else:
            database.add_template(self.input_name.value, self.input_subject.value, self.input_preamble.value, self.input_closing.value, self.input_cc.value, use_def)
        self.close_dialog(None)
        self.load_data()

    def delete_template(self, t_id):
        database.delete_template(t_id)
        self.load_data()

# --- 詢價解析組件 (應用修改：輸入框放大 + 認證過濾 + UI版面調整) ---
class RFQAnalyzer(ft.Column):
    def __init__(self, page: ft.Page, lang="zh"):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self.main_page = page
        self.lang = lang
        self.t = TRANSLATIONS[lang]
        self.opt_trans = OPTION_TRANSLATIONS.get(lang, {})
        self.analyzed_items = []

        # 修改: 橫向滿版 (width=float("inf"))
        self.input_text = ft.TextField(
            multiline=True, 
            min_lines=12,     
            text_size=15,     
            label="貼上詢價 Email 內容",
            width=float("inf") # 強制水平滿版
        )
        self.analyze_btn = ft.Button("開始解析", icon=ft.Icons.ANALYTICS, on_click=self.run_analysis)
        self.results_container = ft.Column()

        self.controls = [
            # 修改: 標題縮小，分隔線高度縮小 (Header最小化)
            ft.Text(self.t["rfq_analysis"], size=20, weight=ft.FontWeight.BOLD), 
            ft.Divider(height=10, thickness=1),
            self.input_text,
            ft.Row([self.analyze_btn], alignment=ft.MainAxisAlignment.END),
            ft.Divider(),
            ft.Text("解析結果與匹配 (材質分組)", size=20, weight=ft.FontWeight.BOLD),
            self.results_container
        ]

    def run_analysis(self, e):
        self.analyze_btn.disabled = True
        self.analyze_btn.text = "解析中..."
        self.main_page.update()
        try:
            analysis_result = analyzer.analyze_rfq(self.input_text.value)
            all_items = analysis_result.get("items", [])
            req_id = database.save_rfq_request(self.input_text.value, json.dumps(all_items))
            self.results_container.controls = []
            
            grouped_items = {}
            for item in all_items:
                mat_type = item.get("material_type", "Other")
                if mat_type not in grouped_items: grouped_items[mat_type] = []
                grouped_items[mat_type].append(item)
            
            if not grouped_items:
                 self.main_page.snack_bar = ft.SnackBar(ft.Text("未能解析出項目"))
                 self.main_page.snack_bar.open = True
                 return
            
            for mat_type, group_items_list in grouped_items.items():
                # 認證類別篩選邏輯
                req_qual = "ISO"
                for it in group_items_list:
                    q = it.get("qualification", "ISO")
                    if q == "Aerospace": 
                        req_qual = "Aerospace"
                    elif q == "Automotive" and req_qual == "ISO": 
                        req_qual = "Automotive"

                initial_suppliers = database.search_suppliers([mat_type], [])
                
                matched_suppliers = []
                for s in initial_suppliers:
                    s_quals = from_json_str(s[8])
                    if req_qual in s_quals:
                        matched_suppliers.append(s)

                supplier_options = [ft.dropdown.Option(str(s[0]), f"{s[1]} ({s[2]})") for s in matched_suppliers]
                
                ui_rows_data = [] 
                data_rows = []
                for idx, item in enumerate(group_items_list):
                    database.save_rfq_item(req_id, idx, mat_type, item.get("form", "Other"), json.dumps(item), [s[0] for s in matched_suppliers])
                    
                    txt_spec = ft.TextField(value=item.get("material_spec", "-"), border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, expand=True)
                    txt_form = ft.TextField(value=item.get("form", "-"), border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, width=80)
                    txt_dims = ft.TextField(value=item.get("dimensions", "-"), border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, expand=True)
                    txt_qty = ft.TextField(value=item.get("quantity", "-"), border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, width=80)
                    txt_notes = ft.TextField(value=item.get("notes", "-"), border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, expand=True)
                    txt_moq = ft.TextField(value="", border=ft.InputBorder.UNDERLINE, dense=True, text_size=13, width=80, hint_text="if need")
                    
                    ui_rows_data.append({
                        "mat_type": mat_type, 
                        "spec": txt_spec, 
                        "form": txt_form, 
                        "dimensions": txt_dims, 
                        "quantity": txt_qty, 
                        "moq": txt_moq, 
                        "notes": txt_notes,
                        "qual": item.get("qualification", "ISO")
                    })
                    
                    qual_display = item.get("qualification", "ISO")
                    mat_display = ft.Column([
                        ft.Text(str(idx + 1)),
                        ft.Container(
                            content=ft.Text(qual_display, size=10, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.BLUE_GREY if qual_display=="ISO" else (ft.Colors.ORANGE if qual_display=="Automotive" else ft.Colors.RED),
                            padding=2, border_radius=3
                        )
                    ], spacing=2)

                    data_rows.append(ft.DataRow(cells=[
                        ft.DataCell(mat_display),
                        ft.DataCell(txt_spec), 
                        ft.DataCell(txt_form), 
                        ft.DataCell(txt_dims), 
                        ft.DataCell(txt_qty), 
                        ft.DataCell(ft.Text("(Vendor)")), 
                        ft.DataCell(txt_moq), 
                        ft.DataCell(txt_notes)
                    ]))
                
                items_table = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("#/Qual")), 
                        ft.DataColumn(ft.Text("Spec")), 
                        ft.DataColumn(ft.Text("Form")), 
                        ft.DataColumn(ft.Text("Dimensions")), 
                        ft.DataColumn(ft.Text("Qty")), 
                        ft.DataColumn(ft.Text("Price")), 
                        ft.DataColumn(ft.Text("MOQ")), 
                        ft.DataColumn(ft.Text("Notes"))
                    ], 
                    rows=data_rows, 
                    border=ft.border.all(1, ft.Colors.GREY_300)
                )
                
                supp_dds = [ft.Dropdown(label=f"供應商 {i+1} ({req_qual})", options=supplier_options, width=200, dense=True) for i in range(4)]
                batch_draft_btn = ft.Button("生成草稿 (批次)", icon=ft.Icons.EMAIL, on_click=lambda e, rows=ui_rows_data, mt=mat_type, dds=supp_dds: self.generate_batch_drafts(rows, dds, mt))
                
                card = ft.Card(content=ft.Container(padding=20, content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.CATEGORY, color=ft.Colors.BLUE), 
                        ft.Text(f"材質群組: {mat_type}", size=20, weight=ft.FontWeight.BOLD),
                        ft.Container(content=ft.Text(f"需求認證: {req_qual}", color=ft.Colors.WHITE), bgcolor=ft.Colors.BLUE, padding=5, border_radius=5)
                    ]), 
                    ft.Divider(), 
                    ft.Row([items_table], expand=True, scroll=ft.ScrollMode.AUTO), 
                    ft.Divider(), 
                    ft.Text(f"選擇詢價對象 (已篩選 {req_qual} 認證, 最多 4 家):", weight=ft.FontWeight.BOLD), 
                    ft.Row(supp_dds, wrap=True), 
                    ft.Row([batch_draft_btn], alignment=ft.MainAxisAlignment.END)
                ])))
                self.results_container.controls.append(card)
        except Exception as ex:
            self.main_page.snack_bar = ft.SnackBar(ft.Text(f"發生錯誤: {str(ex)}"))
            self.main_page.snack_bar.open = True
        finally:
            self.reset_btn()
            self.main_page.update()

    def reset_btn(self):
        self.analyze_btn.disabled = False
        self.analyze_btn.text = "開始解析"

    def generate_batch_drafts(self, ui_rows, dropdowns, material_type_group):
        selected_ids = [dd.value for dd in dropdowns if dd.value]
        if not selected_ids:
            self.main_page.snack_bar = ft.SnackBar(ft.Text("請至少選擇 1 家供應商"))
            self.main_page.snack_bar.open = True
            return
        suppliers_db = database.get_suppliers()
        templates = database.get_templates()
        template = templates[0] if templates else (0, "Default", "Inquiry {date}", "<p>Hi,</p>", "<p>Thanks</p>", "", "", "", "", "", "", "", 0)
        tmpl_cc = template[11] if len(template) > 11 else ""
        use_default_subj = template[12] if len(template) > 12 else 0
        
        current_items_data = [{"material_type": r["mat_type"], "material_spec": r["spec"].value, "form": r["form"].value, "dimensions": r["dimensions"].value, "quantity": r["quantity"].value, "moq": r["moq"].value, "notes": r["notes"].value, "qual": r["qual"]} for r in ui_rows]
        
        table_rows_html = "".join([f"<tr><td style='border: 1px solid #333; padding: 10px;'>{item['material_type']}<br>({item['qual']})</td><td style='border: 1px solid #333; padding: 10px;'>{item['material_spec']}</td><td style='border: 1px solid #333; padding: 10px;'>{item['form']}</td><td style='border: 1px solid #333; padding: 10px;'>{item['dimensions']}</td><td style='border: 1px solid #333; padding: 10px;'>{item['quantity']}</td><td style='border: 1px solid #333; padding: 10px;'></td><td style='border: 1px solid #333; padding: 10px;'>{item['moq']}</td><td style='border: 1px solid #333; padding: 10px;'>{item['notes']}</td></tr>" for item in current_items_data])
        full_table_html = f"<table style='border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 13px;'><thead><tr><th style='border: 1px solid #333; padding: 10px; background-color: #eee;'>Material</th><th style='border: 1px solid #333; padding: 10px; background-color: #eee;'>Spec</th><th style='border: 1px solid #333; padding: 10px; background-color: #eee;'>Form</th><th style='border: 1px solid #333; padding: 10px; background-color: #eee;'>Dimensions</th><th style='border: 1px solid #333; padding: 10px; background-color: #eee;'>Quantity</th><th style='border: 1px solid #333; padding: 10px; background-color: #eee;'>Price</th><th style='border: 1px solid #333; padding: 10px; background-color: #eee;'>MOQ</th><th style='border: 1px solid #333; padding: 10px; background-color: #eee;'>Notes</th></tr></thead><tbody>{table_rows_html}</tbody></table>"
        try:
            if os.name == 'nt':
                import win32com.client
                outlook = win32com.client.Dispatch('Outlook.Application')
                for supp_id in list(set(selected_ids)):
                    supplier = next((s for s in suppliers_db if str(s[0]) == str(supp_id)), None)
                    if not supplier: continue
                    if use_default_subj: subject = f"RFQ{datetime.now().strftime('%y%m%d%H')}_{material_type_group}_{supplier[1]}"
                    else: subject = (template[2] or "Inquiry").format(date=datetime.now().strftime("%Y%m%d")) + f"_{supplier[1]}"
                    mail = outlook.CreateItem(0)
                    mail.Subject, mail.To, mail.CC = subject, supplier[3], tmpl_cc
                    mail.HTMLBody = f"<div>{template[3]}</div><br>{full_table_html}<br><div>{template[4]}</div>"
                    mail.Save()
                self.main_page.snack_bar = ft.SnackBar(ft.Text(f"成功建立 {len(selected_ids)} 封草稿"))
            else: self.main_page.snack_bar = ft.SnackBar(ft.Text("非 Windows 環境: 模擬成功"))
            self.main_page.snack_bar.open = True
        except Exception as ex:
            self.main_page.snack_bar = ft.SnackBar(ft.Text(f"錯誤: {str(ex)}"))
            self.main_page.snack_bar.open = True
        self.main_page.update()

# --- 主程式 ---
def main(page: ft.Page):
    database.init_db()
    page.title = "RFQ System v1.8 (UI Fixes)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width, page.window_height = 1400, 950 

    current_lang = "zh"
    supplier_manager = SupplierManager(page, current_lang)
    rfq_analyzer = RFQAnalyzer(page, current_lang)
    template_manager = TemplateManager(page)
    
    # 修改: 減少 Top Padding (從 20 改為 10)，讓 Header 區域更緊湊
    content_area = ft.Container(content=supplier_manager, expand=True, padding=ft.padding.only(left=20, top=10, right=20, bottom=20))

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
        selected_index=0, label_type=ft.NavigationRailLabelType.ALL, min_width=100, min_extended_width=200, group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.PERSON_OUTLINE, selected_icon=ft.Icons.PERSON, label="供應商管理"),
            ft.NavigationRailDestination(icon=ft.Icons.ANALYTICS_OUTLINED, selected_icon=ft.Icons.ANALYTICS, label="詢價解析"),
            ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="樣板設定"),
        ],
        on_change=on_nav_change,
    )
    page.add(ft.Row([rail, ft.VerticalDivider(width=1), content_area], expand=True))
    supplier_manager.load_data()

if __name__ == "__main__":
    ft.run(main)
