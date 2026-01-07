# config.py
# Section 3: Fixed Options & Translations

# Fixed Options
OPTIONS = {
    "rfq_status": ["New", "Sent", "Received", "Analyzed", "Approved", "Rejected"],
    "currencies": ["USD", "EUR", "CNY", "TWD", "JPY"],
    "payment_terms": ["Net 30", "Net 60", "COD", "Advance Payment"],
    "languages": {
        "en": "English",
        "zh": "Chinese"
    },
    "material_types": [
        "Aluminum", "Copper", "Carbon Steel", "Stainless Steel", "Tool Steel",
        "Nickel Alloy", "Titanium Alloy", "Plastic", "Other"
    ],
    "form_types": [
        "Bar", "Tube", "Sheet", "Plate", "Forging", "Stamping", "Other"
    ],
    "qualifications": [
        "ISO", "Automotive", "Aerospace"
    ]
}

# Option Translations (Value -> Display)
OPTION_TRANSLATIONS = {
    "zh": {
        "Aluminum": "鋁材",
        "Copper": "銅材",
        "Carbon Steel": "碳鋼",
        "Stainless Steel": "不鏽鋼",
        "Tool Steel": "工具鋼",
        "Nickel Alloy": "鎳合金",
        "Titanium Alloy": "鈦合金",
        "Plastic": "塑膠",
        "Other": "其他",
        "Bar": "棒材",
        "Tube": "管材",
        "Sheet": "板材 (薄)",
        "Plate": "板材 (厚)",
        "Forging": "鍛造件",
        "Stamping": "沖壓件",
        "ISO": "ISO 認證",
        "Automotive": "車規",
        "Aerospace": "航太"
    }
}

# Translations
TRANSLATIONS = {
    "en": {
        "app_title": "RFQ System",
        "supplier_management": "Supplier Management",
        "rfq_analysis": "RFQ Analysis",
        "template_settings": "Template Settings",
        "welcome": "Welcome",
        # Supplier Management
        "add_supplier": "Add Supplier",
        "edit_supplier": "Edit Supplier",
        "delete_supplier": "Delete Supplier",
        "name": "Name",
        "contact": "Contact Person",
        "email": "Email",
        "phone": "Phone",
        "address": "Address",
        "materials": "Material Types",
        "forms": "Form Types",
        "qualifications": "Qualifications",
        "save": "Save",
        "cancel": "Cancel",
        "actions": "Actions",
        "confirm_delete": "Confirm Delete",
        "delete_message": "Are you sure you want to delete this supplier?",
        "select_options": "Select Options"
    },
    "zh": {
        "app_title": "詢價系統",
        "supplier_management": "供應商管理",
        "rfq_analysis": "詢價解析",
        "template_settings": "樣板設定",
        "welcome": "歡迎",
        # Supplier Management
        "add_supplier": "新增供應商",
        "edit_supplier": "編輯供應商",
        "delete_supplier": "刪除供應商",
        "name": "名稱",
        "contact": "聯絡人",
        "email": "電子郵件",
        "phone": "電話",
        "address": "地址",
        "materials": "金屬種類",
        "forms": "形狀",
        "qualifications": "認證等級",
        "save": "儲存",
        "cancel": "取消",
        "actions": "操作",
        "confirm_delete": "確認刪除",
        "delete_message": "確定要刪除此供應商嗎？",
        "select_options": "選擇選項"
    }
}
