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
    try: return json.loads(json_str)
    except: return []

# --- 供應商管理組件 ---
class SupplierManager(ft.Column):
    def __init__(self, page: ft.Page, lang="zh"):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
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
                    self.input_name, self.input_contact, self.input_email, self.input_phone, self.input_address,
                    ft.Text(self.t["materials"], weight=ft.FontWeight.BOLD), self.check_materials,
                    ft.Text(self.t["forms"], weight=ft.FontWeight.BOLD), self.check_forms,
                    ft.Text(self.t["qualifications"], weight=ft.FontWeight.BOLD), self.check_qualifications,
                ], scroll=ft.ScrollMode.AUTO), width=500, height=600
            ),
            actions=[ft.TextButton(self.t["cancel"], on_click=self.close_dialog), ft.TextButton(self.t["save"], on_click=self.save_supplier)],
        )
        self.main_page.overlay.append(self.dialog)
        self.data_table = ft.DataTable(columns=[ft.DataColumn(ft.Text(self.t[k])) for k in ["name", "contact", "phone", "materials", "forms", "qualifications", "actions"]], rows=[])
        self.add_btn = ft.Button(self.t["add_supplier"], icon=ft.Icons.ADD, on_click=self.open_add_dialog)
        self.controls = [ft.Row([ft.Text(self.t["supplier_management"], size=30), self.add_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Divider(), ft.Row([self.data_table], scroll=ft.ScrollMode.AUTO)]

    def _create_checkbox_group(self, options): return ft.Column([ft.Checkbox(label=self.opt_trans.get(opt, opt), value=False, data=opt) for opt in options])
    def _get_checked_values(self, cb_group): return [cb.data for cb in cb_group.controls if cb.value]
    def _set_checked_values(self, cb_group, values):
        for cb in cb_group.controls: cb.value = cb.data in values
    def _clear_inputs(self):
        for f in [self.input_name, self.input_contact, self.input_email, self.input_phone, self.input_address]: f.value = ""
        self._set_checked_values(self.check_materials, []); self._set_checked_values(self.check_forms, []); self._set_checked_values(self.check_qualifications, [])
        self.editing_id = None
    def load_data(self):
        self.suppliers = database.get_suppliers(); self.data_table.rows = []
        for s in self.suppliers:
            mats_disp = ", ".join([self.opt_trans.get(m, m) for m in from_json_str(s[6])])
            forms_disp = ", ".join([self.opt_trans.get(f, f) for f in from_json_str(s[7])])
            quals_disp = ", ".join([self.opt_trans.get(q, q) for q in from_json_str(s[8])])
            self.data_table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(s[1])), ft.DataCell(ft.Text(s[2])), ft.DataCell(ft.Text(s[4])), ft.DataCell(ft.Text(mats_disp)), ft.DataCell(ft.Text(forms_disp)), ft.DataCell(ft.Text(quals_disp)), ft.DataCell(ft.Row([ft.IconButton(ft.Icons.EDIT, on_click=lambda e, sid=s[0]: self.open_edit_dialog(sid)), ft.IconButton(ft.Icons.DELETE, on_click=lambda e, sid=s[0]: self.delete_supplier(sid))]))]))
        self.update()
    def open_add_dialog(self, e): self._clear_inputs(); self.dialog.title.value = ft.Text(self.t["add_supplier"]); self.dialog.open = True; self.main_page.update()
    def open_edit_dialog(self, s_id):
        s = next((s for s in self.suppliers if s[0] == s_id), None)
        if not s: return
        self.editing_id = s_id; self.input_name.value = s[1]; self.input_contact.value = s[2]; self.input_email.value = s[3]; self.input_phone.value = s[4]; self.input_address.value = s[5]
        self._set_checked_values(self.check_materials, from_json_str(s[6])); self._set_checked_values(self.check_forms, from_json_str(s[7])); self._set_checked_values(self.check_qualifications, from_json_str(s[8]))
        self.dialog.title.value = ft.Text(self.t["edit_supplier"]); self.dialog.open = True; self.main_page.update()
    def close_dialog(self, e): self.dialog.open = False; self.main_page.update()
    def save_supplier(self, e):
        data = (self.input_name.value, self.input_contact.value, self.input_email.value, self.input_phone.value, self.input_address.value, to_json_str(self._get_checked_values(self.check_materials)), to_json_str(self._get_checked_values(self.check_forms)), to_json_str(self._get_checked_values(self.check_qualifications)))
        if self.editing_id: database.update_supplier(self.editing_id, *data)
        else: database.add_supplier(*data)
        self.close_dialog(None); self.load_data()
    def delete_supplier(self, s_id): database.delete_supplier(s_id); self.load_data()

# --- 樣板管理組件 ---
class TemplateManager(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self.main_page = page; self.templates = []; self.editing_id = None
        self.input_name = ft.TextField(label="Template Name")
        self.chk_default_subject = ft.Checkbox(label="使用預設主旨 (RFQYYMMDDHH_材質_供應商)", on_change=self.toggle_subject_input)
        self.input_subject = ft.TextField(label="Subject Format")
        self.input_cc = ft.TextField(label="副本 (CC)")
        self.input_preamble = ft.TextField(label="Preamble (HTML)", multiline=True, min_lines=3)
        self.input_closing = ft.TextField(label="Closing (HTML)", multiline=True, min_lines=3)
        self.dialog = ft.AlertDialog(title=ft.Text("Template"), content=ft.Container(content=ft.Column([self.input_name, self.chk_default_subject, self.input_subject, self.input_cc, self.input_preamble, self.input_closing], scroll=ft.ScrollMode.AUTO), width=600, height=600), actions=[ft.TextButton("Cancel", on_click=self.close_dialog), ft.TextButton("Save", on_click=self.save_template)])
        self.main_page.overlay.append(self.dialog)
        self.data_table = ft.DataTable(columns=[ft.DataColumn(ft.Text("Name")), ft.DataColumn(ft.Text("Type")), ft.DataColumn(ft.Text("Actions"))], rows=[])
        self.add_btn = ft.Button("Add Template", icon=ft.Icons.ADD, on_click=self.open_add_dialog)
        self.controls = [ft.Row([ft.Text("Template Settings", size=30), self.add_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Divider(), ft.Row([self.data_table], scroll=ft.ScrollMode.AUTO)]
    def toggle_subject_input(self, e): self.input_subject.disabled = self.chk_default_subject.value; self.input_subject.update()
    def load_data(self):
        self.templates = database.get_templates(); self.data_table.rows = []
        for t in self.templates:
            type_disp = "Auto" if (t[12] if len(t)>12 else 0) else (t[2] or "")
            self.data_table.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(t[1])), ft.DataCell(ft.Text(type_disp)), ft.DataCell(ft.Row([ft.IconButton(ft.Icons.EDIT, on_click=lambda e, tid=t[0]: self.open_edit_dialog(tid)), ft.IconButton(ft.Icons.DELETE, on_click=lambda e, tid=t[0]: self.delete_template(tid))]))]))
        self.update()
    def open_add_dialog(self, e): self.editing_id = None; self.input_name.value = ""; self.chk_default_subject.value = False; self.input_subject.disabled = False; self.input_cc.value = ""; self.input_preamble.value = ""; self.input_closing.value = ""; self.dialog.open = True; self.main_page.update()
    def open_edit_dialog(self, t_id):
        t = next((t for t in self.templates if t[0] == t_id), None)
        if not t: return
        self.editing_id = t_id; self.input_name.value = t[1]; self.input_subject.value = t[2] or ""; self.input_preamble.value = t[3] or ""; self.input_closing.value = t[4] or ""; self.input_cc.value = t[11] if len(t)>11 else ""; self.chk_default_subject.value = bool(t[12] if len(t)>12 else 0); self.input_subject.disabled = self.chk_default_subject.value; self.dialog.open = True; self.main_page.update()
    def close_dialog(self, e): self.dialog.open = False; self.main_page.update()
    def save_template(self, e):
        use_def = 1 if self.chk_default_subject.value else 0
        if self.editing_id: database.update_template(self.editing_id, self.input_name.value, self.input_subject.value, self.input_preamble.value, self.input_closing.value, self.input_cc.value, use_def)
        else: database.add_template(self.input_name.value, self.input_subject.value, self.input_preamble.value, self.input_closing.value, self.input_cc.value, use_def)
        self.close_dialog(None); self.load_data()
    def delete_template(self, t_id): database.delete_template(t_id); self.load_data()

# --- 詢價解析組件 (恢復大卡片樣式) ---
class RFQAnalyzer(ft.Column):
    def __init__(self, page: ft.Page, lang="zh"):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self.main_page = page; self.lang = lang; self.t = TRANSLATIONS[lang]
        self.input_text = ft.TextField(multiline=True, min_lines=10, label="貼上詢價 Email 內容")
        self.analyze_btn = ft.Button("開始解析", icon=ft.Icons.ANALYTICS, on_click=self.run_analysis)
        self.results_container = ft.Column()
        self.controls = [ft.Text(self.t["rfq_analysis"], size=30), ft.Divider(), self.input_text, ft.Row([self.analyze_btn], alignment=ft.MainAxisAlignment.END), ft.Divider(), ft.Text("解析結果與匹配 (材質分組)", size=20, weight=ft.FontWeight.BOLD), self.results_container]

    def run_analysis(self, e):
        self.analyze_btn.disabled = True; self.analyze_btn.text = "解析中..."; self.main_page.update()
        try:
            analysis_result = analyzer.analyze_rfq(self.input_text.value)
            all_items = analysis_result.get("items", [])
            req_id = database.save_rfq_request(self.input_text.value, json.dumps(all_items))
            self.results_container.controls = []
            
            grouped_items = {}
            for item in all_items:
                mat = item.get("material_type", "Other")
                if mat not in grouped_items: grouped_items[mat] = []
                grouped_items[mat].append(item)

            for mat_type, items in grouped_items.items():
                matched_suppliers = database.search_suppliers([mat_type], [])
                supp_opts = [ft.dropdown.Option(str(s[0]), f"{s[1]} ({s[2]})") for s in matched_suppliers]
                ui_rows = []; cards_col = ft.Column()
                
                for idx, item in enumerate(items):
                    txt_spec = ft.TextField(label="Spec", value=item.get("material_spec", "-"), expand=True)
                    txt_form = ft.TextField(label="Form", value=item.get("form", "-"), width=120)
                    txt_dims = ft.TextField(label="Dimensions", value=item.get("dimensions", "-"), expand=True)
                    txt_qty = ft.TextField(label="Quantity", value=item.get("quantity", "-"), width=100)
                    txt_moq = ft.TextField(label="MOQ (Vendor)", value="", width=100, hint_text="if need")
                    txt_notes = ft.TextField(label="Notes", value=item.get("notes", "-"), multiline=True, expand=True)
                    qual = item.get("qualification", "ISO")
                    
                    ui_rows.append({"mat": mat_type, "spec": txt_spec, "form": txt_form, "dims": txt_dims, "qty": txt_qty, "moq": txt_moq, "notes": txt_notes, "qual": qual})
                    cards_col.controls.append(ft.Card(content=ft.Container(padding=15, content=ft.Column([
                        ft.Row([ft.Text(f"項目 #{idx + 1}", weight="bold"), ft.Text(f"判定認證: {qual}", color=ft.Colors.BLUE_GREY)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([txt_spec, txt_form]), ft.Row([txt_dims, txt_qty, txt_moq]), txt_notes,
                    ]))))

                dds = [ft.Dropdown(label=f"詢價供應商 {i+1}", options=supp_opts, width=220, dense=True) for i in range(4)]
                btn = ft.Button("生成草稿 (批次)", icon=ft.Icons.EMAIL, on_click=lambda e, r=ui_rows, mt=mat_type, d=dds: self.generate_batch(r, d, mt))
                self.results_container.controls.append(ft.Card(color=ft.Colors.BLUE_50, content=ft.Container(padding=20, content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.CATEGORY, color=ft.Colors.BLUE), ft.Text(f"材質群組: {mat_type}", size=22, weight=ft.FontWeight.BOLD)]),
                    ft.Divider(), cards_col, ft.Divider(), ft.Text("選擇詢價對象 (最多 4 家):", weight=ft.FontWeight.BOLD),
                    ft.Row(dds, wrap=True), ft.Row([btn], alignment=ft.MainAxisAlignment.END)
                ]))))
        except Exception as ex: self.main_page.snack_bar = ft.SnackBar(ft.Text(f"錯誤: {str(ex)}")); self.main_page.snack_bar.open = True
        finally: self.analyze_btn.disabled = False; self.analyze_btn.text = "開始解析"; self.main_page.update()

    def generate_batch(self, rows, dds, mat_group):
        s_ids = list(set([d.value for d in dds if d.value]))
        if not s_ids: self.main_page.snack_bar = ft.SnackBar(ft.Text("請選擇供應商")); self.main_page.snack_bar.open = True; self.main_page.update(); return
        suppliers = database.get_suppliers(); templates = database.get_templates()
        tmpl = templates[0] if templates else (0, "Default", "Inquiry {date}", "<p>Hi,</p>", "<p>Thanks</p>", "", "", "", "", "", "", "", 0)
        
        table_rows = "".join([f"<tr><td style='border:1px solid #333;padding:10px;'>{r['mat']}<br>({r['qual']})</td><td style='border:1px solid #333;padding:10px;'>{r['spec'].value}</td><td style='border:1px solid #333;padding:10px;'>{r['form'].value}</td><td style='border:1px solid #333;padding:10px;'>{r['dims'].value}</td><td style='border:1px solid #333;padding:10px;'>{r['qty'].value}</td><td style='border:1px solid #333;padding:10px;'></td><td style='border:1px solid #333;padding:10px;'>{r['moq'].value}</td><td style='border:1px solid #333;padding:10px;'>{r['notes'].value}</td></tr>" for r in rows])
        html_table = f"<table style='border-collapse:collapse;width:100%;font-size:13px;'><thead><tr style='background:#eee;'><th style='border:1px solid #333;padding:10px;'>Material</th><th style='border:1px solid #333;padding:10px;'>Spec</th><th style='border:1px solid #333;padding:10px;'>Form</th><th style='border:1px solid #333;padding:10px;'>Dimensions</th><th style='border:1px solid #333;padding:10px;'>Quantity</th><th style='border:1px solid #333;padding:10px;'>Price</th><th style='border:1px solid #333;padding:10px;'>MOQ</th><th style='border:1px solid #333;padding:10px;'>Notes</th></tr></thead><tbody>{table_rows}</tbody></table>"
        
        try:
            if os.name == 'nt':
                import win32com.client; outlook = win32com.client.Dispatch('Outlook.Application')
                for sid in s_ids:
                    s = next((s for s in suppliers if str(s[0])==str(sid)), None); if not s: continue
                    subj = f"RFQ{datetime.now().strftime('%y%m%d%H')}_{mat_group}_{s[1]}" if (tmpl[12] if len(tmpl)>12 else 0) else (tmpl[2] or "Inquiry").format(date=datetime.now().strftime("%Y%m%d")) + f"_{s[1]}"
                    mail = outlook.CreateItem(0); mail.Subject, mail.To, mail.CC = subj, s[3], (tmpl[11] if len(tmpl)>11 else ""); mail.HTMLBody = f"<div>{tmpl[3]}</div><br>{html_table}<br><div>{tmpl[4]}</div>"; mail.Save()
                self.main_page.snack_bar = ft.SnackBar(ft.Text(f"成功建立 {len(s_ids)} 封草稿"))
            else: self.main_page.snack_bar = ft.SnackBar(ft.Text("非 Windows 環境: 模擬成功"))
        except Exception as ex: self.main_page.snack_bar = ft.SnackBar(ft.Text(f"錯誤: {str(ex)}"))
        self.main_page.snack_bar.open = True; self.main_page.update()

# --- 主程式 ---
def main(page: ft.Page):
    database.init_db(); page.title = "RFQ System v1.7"; page.theme_mode = ft.ThemeMode.LIGHT; page.window_width, page.window_height = 1400, 950
    sm = SupplierManager(page); ra = RFQAnalyzer(page); tm = TemplateManager(page)
    content = ft.Container(content=sm, expand=True, padding=20)
    def nav(e):
        idx = e.control.selected_index; content.content = None
        if idx==0: content.content=sm; sm.load_data()
        elif idx==1: content.content=ra
        elif idx==2: content.content=tm; tm.load_data()
        page.update()
    rail = ft.NavigationRail(selected_index=0, label_type=ft.NavigationRailLabelType.ALL, min_width=100, destinations=[ft.NavigationRailDestination(icon=ft.Icons.PERSON_OUTLINE, label="供應商管理"), ft.NavigationRailDestination(icon=ft.Icons.ANALYTICS_OUTLINED, label="詢價解析"), ft.NavigationRailDestination(icon=ft.Icons.SETTINGS_OUTLINED, label="樣板設定")], on_change=nav)
    page.add(ft.Row([rail, ft.VerticalDivider(width=1), content], expand=True)); sm.load_data()

if __name__ == "__main__": ft.run(main)
