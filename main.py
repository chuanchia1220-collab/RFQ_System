import flet as ft
import json
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

        # 2. 建立對話框 (修正 TextButton 語法)
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

        # 3. 掛載對話框至 Overlay
        self.main_page.overlay.append(self.dialog)

        # 4. UI 佈局 (修正 ElevatedButton 語法)
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

    # --- 邏輯函數 ---
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
        self.update()

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

# --- 詢價解析組件 ---
class RFQAnalyzer(ft.Column):
    def __init__(self, page: ft.Page, lang="zh"):
        super().__init__(expand=True)
        self.main_page = page
        self.lang = lang
        self.t = TRANSLATIONS[lang]
        self.opt_trans = OPTION_TRANSLATIONS.get(lang, {})

        # 1. UI Components
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

        self.result_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("供應商名稱")),
                ft.DataColumn(ft.Text("匹配原因")),
                ft.DataColumn(ft.Text("聯繫方式")),
            ],
            rows=[]
        )

        self.controls = [
            ft.Text(self.t["rfq_analysis"], size=30),
            ft.Divider(),
            ft.Row([self.input_text], expand=False),
            ft.Row([self.analyze_btn], alignment=ft.MainAxisAlignment.END),
            ft.Divider(),
            ft.Text("推薦廠商", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([self.result_table], scroll=ft.ScrollMode.AUTO, expand=True)
        ]

    def run_analysis(self, e):
        # 1. Show loading (optional, but good UX)
        self.analyze_btn.disabled = True
        self.analyze_btn.text = "解析中..."
        self.main_page.update()

        try:
            # 2. Call Analyzer
            text = self.input_text.value
            if not text:
                self.reset_btn()
                return

            analysis_result = analyzer.analyze_rfq(text)
            materials = analysis_result.get("materials", [])
            forms = analysis_result.get("forms", [])

            # 3. Search Database
            matched_suppliers = database.search_suppliers(materials, forms)

            # 4. Update UI
            self.result_table.rows = []

            target_materials = set(materials)
            target_forms = set(forms)

            for s in matched_suppliers:
                # s: id, name, contact, email, phone, address, materials, forms, ...
                s_materials = set(json.loads(s[6])) if s[6] else set()
                s_forms = set(json.loads(s[7])) if s[7] else set()

                matched_mats = s_materials.intersection(target_materials)
                matched_forms = s_forms.intersection(target_forms)

                reasons = []
                if matched_mats:
                    translated_mats = [self.opt_trans.get(m, m) for m in matched_mats]
                    reasons.append(f"材料: {', '.join(translated_mats)}")
                if matched_forms:
                    translated_forms = [self.opt_trans.get(f, f) for f in matched_forms]
                    reasons.append(f"形狀: {', '.join(translated_forms)}")

                contact_info = f"{s[2]} ({s[3]})"

                self.result_table.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(s[1])),
                        ft.DataCell(ft.Text("; ".join(reasons))),
                        ft.DataCell(ft.Text(contact_info)),
                    ])
                )

            if not matched_suppliers:
                 self.main_page.snack_bar = ft.SnackBar(ft.Text("未找到匹配的供應商"))
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
    content_area = ft.Container(content=supplier_manager, expand=True, padding=20)

    def on_nav_change(e):
        index = e.control.selected_index
        content_area.content = None
        if index == 0:
            supplier_manager.load_data()
            content_area.content = supplier_manager
        elif index == 1:
            content_area.content = rfq_analyzer
        elif index == 2:
            content_area.content = ft.Text(t["template_settings"], size=30)
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
