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
    },
    "zh": {
        "app_title": "詢價系統",
        "supplier_management": "供應商管理",
        "rfq_analysis": "詢價解析",
        "template_settings": "樣板設定",
        "welcome": "歡迎",
    }
}
