import os
import json
import openai
from config import OPTIONS

def analyze_rfq(text):
    """
    Analyzes RFQ text using OpenAI API to extract materials and forms.
    Returns a dictionary with 'materials' and 'forms' lists.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    client = openai.OpenAI(api_key=api_key)

    material_opts = ", ".join(OPTIONS["material_types"])
    form_opts = ", ".join(OPTIONS["form_types"])

    system_prompt = (
        "You are an expert procurement assistant. Your task is to extract required materials and forms "
        "from an unstructured Request for Quotation (RFQ) text."
    )

    user_prompt = (
        f"Extract materials and forms from the following text.\n"
        f"Valid materials: {material_opts}\n"
        f"Valid forms: {form_opts}\n\n"
        f"Return ONLY a JSON object with keys 'materials' and 'forms'. "
        f"Do not include any other text or markdown formatting. "
        f"Only include values that strictly match the provided valid lists.\n\n"
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

        # Ensure keys exist
        return {
            "materials": result.get("materials", []),
            "forms": result.get("forms", [])
        }

    except Exception as e:
        print(f"Error analyzing RFQ: {e}")
        return {"materials": [], "forms": []}
