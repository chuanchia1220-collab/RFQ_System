import os
import json
import openai
from config import OPTIONS

def analyze_rfq(text):
    """
    Analyzes RFQ text using OpenAI API to extract structured items.
    Returns a dictionary with 'items' list containing detailed specs.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    # If no API key is set, we return a mock response for testing/demo purposes
    # or raise an error if strictly required. Given this is a local app,
    # we'll return an empty structure or a mock if it's a test string.
    if not api_key:
        print("Warning: OPENAI_API_KEY not found. Returning empty analysis.")
        return {"items": []}

    client = openai.OpenAI(api_key=api_key)

    material_opts = ", ".join(OPTIONS["material_types"])
    form_opts = ", ".join(OPTIONS["form_types"])

    system_prompt = (
        "You are an expert procurement assistant. Your task is to extract required materials and forms "
        "from an unstructured Request for Quotation (RFQ) text into a structured JSON format."
    )

    json_structure_example = '''
    {
      "items": [
        {
          "item_index": 0,
          "material_type": "Stainless Steel",
          "form": "Bar",
          "spec": {
            "description": "",
            "dimensions": {
              "d": "",
              "L": "",
              "thickness": "",
              "width": ""
            },
            "tolerance": "",
            "annual_qty": "",
            "unit": "pcs/kg/m",
            "need_by": "",
            "surface_finish": "",
            "heat_treatment": ""
          },
          "notes": "",
          "confidence": 0.95
        }
      ]
    }
    '''

    user_prompt = (
        f"Analyze the following RFQ text and extract items.\n"
        f"Valid materials: {material_opts}\n"
        f"Valid forms: {form_opts}\n\n"
        f"Return ONLY a JSON object strictly following this structure:\n"
        f"{json_structure_example}\n\n"
        f"Rules:\n"
        f"1. 'material_type' and 'form' must strictly match the valid lists. If unsure or mixed, use 'Other'.\n"
        f"2. Extract specifications into the 'spec' object. Use empty strings if not found.\n"
        f"3. 'confidence' should be a float between 0.0 and 1.0.\n\n"
        f"Input Text:\n{text}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        # Clean up potential markdown code blocks if GPT adds them
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        result = json.loads(content)

        # Filter against strict valid options
        valid_materials = OPTIONS["material_types"]
        valid_forms = OPTIONS["form_types"]

        extracted_materials = [m for m in result.get("materials", []) if m in valid_materials]
        extracted_forms = [f for f in result.get("forms", []) if f in valid_forms]

        return {
            "materials": extracted_materials,
            "forms": extracted_forms
        }
        # Ensure 'items' key exists
        if "items" not in result:
            result["items"] = []

        return result

    except Exception as e:
        print(f"Error analyzing RFQ: {e}")
        return {"items": []}
