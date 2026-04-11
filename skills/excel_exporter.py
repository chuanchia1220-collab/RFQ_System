import pandas as pd
import os

class ExcelExporter:
    def generate_srm_report(self, rfq_id: str, item_data: dict, suppliers_quotes: list, save_dir: str):
        """產出單一品項的 SRM 詢比議價表 (對齊附件格式)"""
        item_name = item_data.get('item_name', '未命名')
        file_path = os.path.join(save_dir, f"SRM詢比議價表_{item_name}.xlsx")

        # 垂直欄位架構設定
        data = [
            ["SRM詢比議價表(詢價狀態)", "", "", ""],
            ["採方資料", "", "", ""],
            ["料號", item_name, "", ""],
            ["規格", item_data.get('spec', ''), "", ""],
            ["需求數量/單位", item_data.get('quantity', ''), "", ""],
            ["需求日", item_data.get('delivery_date', ''), "", ""],
            ["參考價", item_data.get('ref_price', ''), "", ""],
            ["供方資料", "", "", ""]
        ]

        # 依據供應商數量橫向擴展 (A, B, C...)
        vendor_row = ["報價廠商"] + [q.get('supplier_name', '') for q in suppliers_quotes]
        first_quote_row = ["首次報價(單價)"] + [q.get('first_quote', '') for q in suppliers_quotes]
        lt_row = ["L/T(工作日)"] + [q.get('lead_time', '') for q in suppliers_quotes]
        final_price_row = ["中價(定價)"] + [q.get('final_price', '') for q in suppliers_quotes]

        data.extend([vendor_row, first_quote_row, lt_row, final_price_row])

        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False, header=False)
        return file_path

excel_exporter = ExcelExporter()
