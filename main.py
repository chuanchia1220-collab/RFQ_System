import flet as ft
import json
from config import TRANSLATIONS, OPTIONS, OPTION_TRANSLATIONS
import database

# Helper Functions
def to_json_str(data_list):
    return json.dumps(data_list) if data_list else "[]"

def from_json_str(json_str):
    try:
        return json.loads(json_str)
    except:
        return []

class SupplierManager(ft.Column):
    def __init__(self, page: ft.Page, lang="zh"):
        super().__init__(expand=True)
        self.main_page = page
        self.lang = lang
        self.t = TRANSLATIONS[lang]
        self.opt_trans = OPTION_TRANSLATIONS.get(lang, {})
        
        # State variables
        self.suppliers = []
        self.editing_id = None
        
        # UI Components
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text(self.t["name"])),
                ft.DataColumn(ft.Text(self.t["contact"])),
                ft.DataColumn(ft.Text(self.t["phone"])),
                ft.DataColumn(ft.Text(self.t["materials"])),
                ft.DataColumn(ft.Text(self.t["forms"])),
                ft.DataColumn(ft.Text(self.t["qualifications"])),
                ft.DataColumn(ft.Text(self.t["actions"])),
            ],
            rows=[]
        )
        
        self.add_btn = ft.ElevatedButton(
            text=self.t["add_supplier"],
            icon=ft.Icons.ADD,
            on_click=self.open_add_dialog
        )
        
        # Dialog Inputs
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
                    self.input_name,
                    self.input_contact,
                    self.input_email,
                    self.input_phone,
                    self.input_address,
                    ft.Text(self.t["materials"], weight=ft.FontWeight.BOLD),
                    self.check_materials,
                    ft.Text(self.t["forms"], weight=ft.FontWeight.BOLD),
                    self.check_forms,
                    ft.Text(self.t["qualifications"], weight=ft.FontWeight.BOLD),
                    self.check_qualifications,
                ], scroll=ft.ScrollMode.AUTO),
                width=500,
                height=600
            ),
            actions=[
                ft.TextButton(self.t["cancel"], on_click=self.close_dialog),
                ft.TextButton(self.t["save"], on_click=self.save_supplier),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
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
        self.input_name.value = ""
        self.input_contact.value = ""
        self.input_email.value = ""
        self.input_phone.value = ""
        self.input_address.value = ""
        self._set_checked_values(self.check_materials, [])
        self._set_checked_values(self.check_forms, [])
        self._set_checked_values(self.check_qualifications, [])
        self.editing_id = None

    def did_mount(self):
        self.load_data()

    def load_data(self):
        self.suppliers = database.get_suppliers()
        self.data_table.rows = []
        for s in self.suppliers:
            # s is tuple: (id, name, contact, email, phone, address, materials, forms, qualifications, created_at)
            # indices: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
            s_id = s[0]
            mats = from_json_str(s[6])
            forms = from_json_str(s[7])
            quals = from_json_str(s[8])
            
            # Translate display values
            mats_disp = ", ".join([self.opt_trans.get(m, m) for m in mats])
            forms_disp = ", ".join([self.opt_trans.get(f, f) for f in forms])
            quals_disp = ", ".join([self.opt_trans.get(q, q) for q in quals])

            self.data_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(s[1])),
                    ft.DataCell(ft.Text(s[2])),
                    ft.DataCell(ft.Text(s[4])), # Phone
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
        self.dialog.title.value = self.t["add_supplier"]
        self.main_page.dialog = self.dialog
        self.dialog.open = True
        self.main_page.update()

    def open_edit_dialog(self, s_id):
        supplier = next((s for s in self.suppliers if s[0] == s_id), None)
        if not supplier:
            return
        
        self.editing_id = s_id
        self.input_name.value = supplier[1]
        self.input_contact.value = supplier[2]
        self.input_email.value = supplier[3]
        self.input_phone.value = supplier[4]
        self.input_address.value = supplier[5]
        
        self._set_checked_values(self.check_materials, from_json_str(supplier[6]))
        self._set_checked_values(self.check_forms, from_json_str(supplier[7]))
        self._set_checked_values(self.check_qualifications, from_json_str(supplier[8]))
        
        self.dialog.title.value = self.t["edit_supplier"]
        self.main_page.dialog = self.dialog
        self.dialog.open = True
        self.main_page.update()

    def close_dialog(self, e):
        self.dialog.open = False
        self.main_page.update()

    def save_supplier(self, e):
        name = self.input_name.value
        contact = self.input_contact.value
        email = self.input_email.value
        phone = self.input_phone.value
        address = self.input_address.value
        
        materials = to_json_str(self._get_checked_values(self.check_materials))
        forms = to_json_str(self._get_checked_values(self.check_forms))
        qualifications = to_json_str(self._get_checked_values(self.check_qualifications))
        
        if self.editing_id:
            database.update_supplier(self.editing_id, name, contact, email, phone, address, materials, forms, qualifications)
        else:
            database.add_supplier(name, contact, email, phone, address, materials, forms, qualifications)
            
        self.close_dialog(None)
        self.load_data()

    def delete_supplier(self, s_id):
        # In a real app, show confirmation dialog. For speed, just delete.
        database.delete_supplier(s_id)
        self.load_data()


def main(page: ft.Page):
    database.init_db()
    page.title = "RFQ System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800

    # 語言與翻譯
    current_lang = "zh"
    t = TRANSLATIONS[current_lang]

    # 初始化 Supplier Manager View
    supplier_manager = SupplierManager(page, current_lang)

    # 右側主內容區域容器
    content_area = ft.Container(content=supplier_manager, expand=True, padding=20)

    # 切換頁面邏輯
    def on_nav_change(e):
        index = e.control.selected_index
        content_area.content = None # Clear first to avoid issues
        if index == 0:
            # Re-instantiate or reuse. Reusing is better if we want to keep state, 
            # but refreshing data on nav is also good. Let's just reuse for now but reload data.
            supplier_manager.load_data()
            content_area.content = supplier_manager
        elif index == 1:
            content_area.content = ft.Text(t["rfq_analysis"], size=30)
        elif index == 2:
            content_area.content = ft.Text(t["template_settings"], size=30)
        page.update()

    # 側邊導覽欄
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.PERSON_OUTLINE,
                selected_icon=ft.Icons.PERSON,
                label=t["supplier_management"]
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ANALYTICS_OUTLINED,
                selected_icon=ft.Icons.ANALYTICS,
                label=t["rfq_analysis"]
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label=t["template_settings"]
            ),
        ],
        on_change=on_nav_change,
    )

    # 核心佈局結構
    layout = ft.Row(
        [
            rail,
            ft.VerticalDivider(width=1),
            content_area,
        ],
        expand=True,
    )

    page.add(layout)

if __name__ == "__main__":
    # 使用 WEB_BROWSER 模式可以先排除是否為在地視窗渲染問題
    # 若成功看到畫面，再改回 ft.AppView.FLET_APP
    ft.app(target=main)
