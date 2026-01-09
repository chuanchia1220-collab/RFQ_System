# rfq_schema.py
# 這是系統的「憲法」，定義了 AI 輸出的絕對邊界

RFQ_SCHEMA = {
  "type": "object",
  "required": ["items"],
  "properties": {
    "items": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": [
          "material_type",
          "material_spec",
          "form",
          "dimensions",
          "quantity",
          "qualification",  # 新增認證要求
          "notes"
        ],
        "properties": {
          "material_type": {
            "type": "string",
            "enum": ["Aluminum", "Copper", "Carbon Steel", "Stainless Steel", "Tool Steel", "Nickel Alloy", "Titanium Alloy", "Plastic", "Other"]
          },
          "material_spec": {
            "type": "string",
            "minLength": 1
          },
          "form": {
            "type": "string",
            "enum": ["Bar", "Tube", "Sheet", "Plate", "Forging", "Stamping", "Other"]
          },
          "dimensions": {
            "type": "string",
            "minLength": 1
          },
          "quantity": {
            "type": "string",
            "pattern": "^[0-9.,]+\\\\s*[a-zA-Z]+$"
          },
          "qualification": {
            "type": "string",
            "enum": ["ISO", "Automotive", "Aerospace"],
            "description": "ISO is default. Automotive if IATF 16949 is mentioned. Aerospace if AS9100/NADCAP is mentioned."
          },
          "notes": {
            "type": "string"
          }
        },
        "additionalProperties": False
      }
    }
  },
  "additionalProperties": False
}
