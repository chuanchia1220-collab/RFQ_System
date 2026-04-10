import json
import os
import google.generativeai as genai

OPTIONS = {
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

OPTION_TRANSLATIONS = {
    "zh": {
        "Aluminum": "鋁材", "Copper": "銅材", "Carbon Steel": "碳鋼",
        "Stainless Steel": "不鏽鋼", "Tool Steel": "工具鋼", "Nickel Alloy": "鎳合金",
        "Titanium Alloy": "鈦合金", "Plastic": "塑膠", "Other": "其他",
        "Bar": "棒材", "Tube": "管材", "Sheet": "板材 (薄)", "Plate": "板材 (厚)",
        "Forging": "鍛造件", "Stamping": "沖壓件",
        "ISO": "ISO 認證", "Automotive": "車規", "Aerospace": "航太"
    }
}

class RFQSkill:
    def __init__(self, api_key):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def parse_and_draft(self, email_text, pdf_file_paths=None, previous_draft=None, user_instruction=None):
        """
        1. 支援多模態輸入 (Text + 複數 PDF)
        2. 提取規格、數量、交期
        3. 若有 user_instruction，則依照指令修改 previous_draft
        4. 回傳 JSON 格式的解析結果與草稿
        """
        pure_mat_opts = ", ".join(OPTIONS["material_types"])
        pure_form_opts = ", ".join(OPTIONS["form_types"])
        trans_map = OPTION_TRANSLATIONS.get("zh", {})
        context_hint = "Reference Map (For understanding only): " + ", ".join([f"{m}={trans_map.get(m, m)}" for m in OPTIONS["material_types"]])

        system_instruction = (
            f"You are a senior procurement analyst. Normalize RFQ text and optionally "
            f"modify the draft based on user instructions.\n\n"
            f"*** STRICT RULES ***\n"
            f"1. **ROOT OBJECT**: Output MUST be a JSON object with two keys: 'items' (list) and 'draft' (string).\n"
            f"2. **ITEMS MANDATORY FIELDS**: 'material_type', 'material_spec', 'form', 'dimensions', 'quantity', 'qualification', 'notes'.\n"
            f"3. **QUANTITY**: MUST be a string with unit (e.g. '10 pcs'). NEVER output raw numbers.\n"
            f"4. **FORM LOGIC**:\n"
            f"   - **Bar**: 'Ø', 'dia', 'round', or 'D*L'.\n"
            f"   - **Plate**: 'Block', 'Cuboid' or smallest dim >= 10mm.\n"
            f"   - **Sheet**: smallest dim < 10mm.\n"
            f"   - **Tube**: 'Tube', 'Pipe', 'OD/ID'.\n"
            f"5. **VALID VALUES (Strict Enum)**: \n"
            f"   - Material_type MUST be one of: [{pure_mat_opts}]\n"
            f"   - Form MUST be one of: [{pure_form_opts}]\n"
            f"   - {context_hint}\n"
            f"   - If unsure, use 'Other' and explain in notes.\n"
            f"6. **DIMENSIONS**: Keep original string format exactly.\n"
            f"7. **NOTES**: Extract technical specs or constraints. Do not translate them.\n"
            f"8. **QUALIFICATION**: Extract the required qualification for each item (must be 'ISO', 'Automotive', or 'Aerospace'). Default to 'ISO'.\n"
            f"9. **DRAFT**: Provide a professional email draft based on the RFQ. If a previous_draft and user_instruction are provided, modify the draft accordingly.\n"
        )

        user_prompt = f"System Instruction:\n{system_instruction}\n\n"
        user_prompt += f"Analyze this RFQ text:\n\"\"\"{email_text}\"\"\"\n\n"

        if previous_draft:
            user_prompt += f"Previous Draft:\n\"\"\"{previous_draft}\"\"\"\n\n"

        if user_instruction:
            user_prompt += f"User Instruction for modifying the draft:\n\"\"\"{user_instruction}\"\"\"\n\n"

        contents = [user_prompt]
        uploaded_files = []

        try:
            # 支援多個 PDF 檔案上傳
            if pdf_file_paths:
                for pdf_path in pdf_file_paths:
                    if os.path.exists(pdf_path):
                        file_obj = genai.upload_file(path=pdf_path)
                        uploaded_files.append(file_obj)
                        contents.insert(0, file_obj)

            response = self.model.generate_content(
                contents,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                )
            )

            content = response.text.strip()

            try:
                raw_data = json.loads(content)
                if "items" not in raw_data:
                    raw_data["items"] = []
                if "draft" not in raw_data:
                    raw_data["draft"] = ""
                return raw_data
            except json.JSONDecodeError:
                print("[AI] Response was not valid JSON.")
                return {"items": [], "draft": "", "raw": content}

        except Exception as e:
            print(f"[AI 系統錯誤] {e}")
            return {"items": [], "draft": "", "error": str(e)}
        finally:
            # 清理所有上傳的暫存檔案
            for f_obj in uploaded_files:
                try:
                    genai.delete_file(f_obj.name)
                except:
                    pass
