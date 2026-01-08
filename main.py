import flet as ft
import json
import os
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
        
        self.add_btn = ft.ElevatedButton(
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

# --- 樣板管理組件 ---
class TemplateManager(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.main_page = page
        self.templates = []
        self.editing_id = None

        self.input_name = ft.TextField(label="Template Name")
        self.input_subject = ft.TextField(label="Subject Format")
        self.input_preamble = ft.TextField(label="Preamble (HTML)", multiline=True, min_lines=3)
        self.input_closing = ft.TextField(label="Closing (HTML)", multiline=True, min_lines=3)

        self.dialog = ft.AlertDialog(
            title=ft.Text("Add Template"),
            content=ft.Container(
                content=ft.Column([
                    self.input_name, self.input_subject, self.input_preamble, self.input_closing
                ], scroll=ft.ScrollMode.AUTO),
                width=600, height=500
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
                ft.DataColumn(ft.Text("Subject")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[]
        )

        self.add_btn = ft.ElevatedButton(
            "Add Template",
            icon=ft.Icons.ADD,
            on_click=self.open_add_dialog
        )

        self.controls = [
            ft.Row([ft.Text("Template Settings", size=30), self.add_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            ft.Row([self.data_table], scroll=ft.ScrollMode.AUTO, expand=True)
        ]

    def load_data(self):
        self.templates = database.get_templates()
        self.data_table.rows = []
        for t in self.templates:
            t_id = t[0]
            self.data_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(t[1])),
                    ft.DataCell(ft.Text(t[2] or "")),
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
        self.input_subject.value = ""
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
        self.dialog.title.value = ft.Text("Edit Template")
        self.dialog.open = True
        self.main_page.update()

    def close_dialog(self, e):
        self.dialog.open = False
        self.main_page.update()

    def save_template(self, e):
        if self.editing_id:
            database.update_template(self.editing_id, self.input_name.value, self.input_subject.value, self.input_preamble.value, self.input_closing.value)
        else:
            database.add_template(self.input_name.value, self.input_subject.value, self.input_preamble.value, self.input_closing.value)
        self.close_dialog(None)
        self.load_data()

    def delete_template(self, t_id):
        database.delete_template(t_id)
        self.load_data()

# --- 詢價解析組件 ---
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

        self.analyze_btn = ft.ElevatedButton(
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
            ft.Text("解析結果與匹配", size=20, weight=ft.FontWeight.BOLD),
            self.results_container
        ]

    def run_analysis(self, e):
        self.analyze_btn.disabled = True
        self.analyze_btn.text = "解析中..."
        self.main_page.update()

        try:
            text = self.input_text.value
            if not text:
                self.reset_btn()
                return

            analysis_result = analyzer.analyze_rfq(text)
            self.analyzed_items = analysis_result.get("items", [])
            req_id = database.save_rfq_request(text, json.dumps(self.analyzed_items))

            self.results_container.controls = []

            for item in self.analyzed_items:
                mat_type = item.get("material_type", "Other")
                form_type = item.get("form", "Other")
                spec = item.get("spec", {})
                dims = spec.get("dimensions", {})

                matched_suppliers = database.search_suppliers([mat_type], [form_type])
                matched_ids = [s[0] for s in matched_suppliers]
                database.save_rfq_item(req_id, item.get("item_index"), mat_type, form_type, json.dumps(spec), matched_ids)

                supplier_options = [ft.dropdown.Option(str(s[0]), f"{s[1]} ({s[2]})") for s in matched_suppliers]
                supplier_dropdown = ft.Dropdown(label="選擇供應商", options=supplier_options, width=300)
                spec_text = f"Dims: {dims} | Qty: {spec.get('annual_qty')} {spec.get('unit')}"

                draft_btn = ft.ElevatedButton(
                    "生成草稿",
                    icon=ft.Icons.EMAIL,
                    on_click=lambda e, sp=supplier_dropdown, it=item: self.generate_draft(sp, it)
                )

                card = ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.CIRCLE, color=ft.colors.GREEN if item.get("confidence", 0) > 0.6 else ft.colors.RED),
                                title=ft.Text(f"{mat_type} - {form_type}"),
                                subtitle=ft.Text(spec_text),
                            ),
                            ft.Row([supplier_dropdown, draft_btn], alignment=ft.MainAxisAlignment.END)
                        ])
                    )
                )
                self.results_container.controls.append(card)

            if not self.analyzed_items:
                 self.main_page.snack_bar = ft.SnackBar(ft.Text("未能解析出項目"))
                 self.main_page.snack_bar.open = True

        except Exception as ex:
            self.main_page.snack_bar = ft.SnackBar(ft.Text(f"發生錯誤: {str(ex)}"))
            self.main_page.snack_bar.open = True
        finally:
            self.reset_btn()
            self.main_page.update()

    def reset_btn(self):
        self.analyze_btn.disabled = False
        self.analyze_btn.text = "開始解析"

    def generate_draft(self, supplier_dropdown, item):
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
            if os.name == 'nt':
                import win32com.client
                outlook = win32com.client.Dispatch('Outlook.Application')
                mail = outlook.CreateItem(0)
                mail.Subject = subject
                mail.HTMLBody = f"{template[3]}<br>Item: {item['material_type']} {item['form']}<br>Spec: {item['spec']}<br>{template[4]}"
                mail.To = supplier[3]
                mail.Save()
                msg = "Outlook 草稿已建立"
            else:
                msg = f"已模擬建立草稿給 {supplier[1]}"
            self.main_page.snack_bar = ft.SnackBar(ft.Text(msg))
            self.main_page.snack_bar.open = True
        except Exception as ex:
            self.main_page.snack_bar = ft.SnackBar(ft.Text(f"草稿建立失敗: {str(ex)}"))
            self.main_page.snack_bar.open = True
        self.main_page.update()

# --- 主程式 ---
def main(page: ft.Page):
    database.init_db()
    page.title = "RFQ System"
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
            content_area.content = supplier_manager # 先加入頁面
            supplier_manager.load_data()           # 後讀取資料
        elif index == 1:
            content_area.content = rfq_analyzer
        elif index == 2:
            content_area.content = template_manager # 先加入頁面
            template_manager.load_data()            # 後讀取資料
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
    ft.app(target=main)
