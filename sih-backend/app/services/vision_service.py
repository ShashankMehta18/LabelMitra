import base64
import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


# ============================================================
# INSPECTOR AI
# ============================================================

FIELDS = [
    "product_name",
    "manufacturer_packer_importer",
    "net_quantity",
    "mrp",
    "mfg_date",
    "expiry_or_best_before",
    "consumer_care",
]


PROMPT = """
You are a product-label extraction AI for Nexora.

Analyze the product label image and extract ONLY information that is
actually visible.

Map different label terms correctly:

Net Wt / Net Qty / Net Weight
-> net_quantity

M.R.P / MRP / Maximum Retail Price
-> mrp

Date of Pkg / Packed On / Mfg Date / Manufacturing Date
-> mfg_date

Used By / Best Before / Expiry / Expiry Date
-> expiry_or_best_before

Marketed & Packed By / Manufactured By / Packed By
-> manufacturer_packer_importer

Customer Care No / Consumer Care / Helpline
-> consumer_care

Important:
- Do not invent information.
- Do not guess missing values.
- Preserve the value exactly as visible.
- Return null when a field is not visible.
- Carefully inspect the entire image.
- Read text even if it is slightly distorted or rotated.
- For product_name, identify the actual product name printed on the package,
  not labels such as "Pkg", "Batch", "Date", or "By".

Return ONLY valid JSON.

Your response MUST be a JSON object with exactly these fields:

{
  "product_name": null,
  "manufacturer_packer_importer": null,
  "net_quantity": null,
  "mrp": null,
  "mfg_date": null,
  "expiry_or_best_before": null,
  "consumer_care": null
}
"""


def analyze_image(file_path: str) -> Dict[str, Any]:

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured"
        )

    client = Groq(
        api_key=api_key
    )

    # Read image
    with open(file_path, "rb") as image_file:
        image_bytes = image_file.read()

    # Convert image to base64
    base64_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    # Detect image type
    extension = os.path.splitext(file_path)[1].lower()

    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(extension)

    if mime_type is None:
        raise RuntimeError(
            f"Unsupported image format for Groq Vision: {extension}"
        )

    response = client.chat.completions.create(
        model=os.getenv(
            "GROQ_MODEL",
            "qwen/qwen3.8-27b"
        ),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{mime_type};base64,"
                                f"{base64_image}"
                            )
                        },
                    },
                ],
            }
        ],
        response_format={
            "type": "json_object"
        },
        temperature=0,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Groq Vision AI returned an empty response"
        )

    try:
        data = json.loads(content)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Groq returned invalid JSON: {content}"
        ) from exc

    return {
        field: data.get(field)
        for field in FIELDS
    }


# ============================================================
# CONSUMER / LABELMITRA FOOD INTELLIGENCE AI
# ============================================================

def analyze_consumer_image(file_path: str) -> Dict[str, Any]:

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured"
        )

    client = Groq(
        api_key=api_key
    )

    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    with open(file_path, "rb") as image_file:
        image_bytes = image_file.read()

    # --------------------------------------------------------
    # Convert image to base64
    # --------------------------------------------------------

    base64_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    # --------------------------------------------------------
    # Detect image type
    # --------------------------------------------------------

    extension = os.path.splitext(
        file_path
    )[1].lower()

    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(extension)

    if mime_type is None:
        raise RuntimeError(
            f"Unsupported image format for Groq Vision: {extension}"
        )

    # --------------------------------------------------------
    # Consumer AI Prompt
    # --------------------------------------------------------

    consumer_prompt = """
You are LabelMitra Consumer AI.

Analyze the uploaded packaged food label.

Read ONLY information that is actually visible.

Do NOT guess missing information.

Return ONLY valid JSON.

Requirements:

1. Identify product name.
2. Extract visible ingredients.
3. Extract visible nutrition values.
4. Mention up to 3 ingredients or nutrition factors
   consumers may want to pay attention to.
5. Give a simple label-based assessment.
6. Give up to 3 general alternative choices.

Important rules:

- Never invent values.
- Use null when information is not visible.
- Do not provide medical diagnosis.
- Do not claim the product causes disease.
- Keep the assessment general and label-based.
- Keep explanations short.
- Keep reasons short.
- Keep alternatives short.

Allowed assessment labels:

GENERALLY_BETTER
MIXED
LIMIT
INSUFFICIENT_DATA

Return exactly this JSON structure:

{
  "product_name": null,

  "ingredients": [],

  "nutrition": {
    "serving_size": null,
    "calories": null,
    "protein": null,
    "carbohydrates": null,
    "sugars": null,
    "fat": null,
    "saturated_fat": null,
    "fiber": null,
    "sodium": null
  },

  "ingredients_to_watch": [],

  "health_assessment": {
    "label": "INSUFFICIENT_DATA",
    "score": null,
    "summary": "",
    "reasons": []
  },

  "alternatives": [],

  "disclaimer": "General label-based information, not medical advice."
}
"""

    # --------------------------------------------------------
    # Groq Vision Request
    # --------------------------------------------------------

    response = client.chat.completions.create(

        model=os.getenv(
            "GROQ_MODEL",
            "qwen/qwen3.8-27b"
        ),

        messages=[
            {
                "role": "user",

                "content": [

                    {
                        "type": "text",
                        "text": consumer_prompt,
                    },

                    {
                        "type": "image_url",

                        "image_url": {
                            "url": (
                                f"data:{mime_type};base64,"
                                f"{base64_image}"
                            )
                        },
                    },

                ],
            }
        ],

        response_format={
            "type": "json_object"
        },

        temperature=0,

        # Keep output below Groq's 1000-token limit
        max_completion_tokens=850,
    )

    # --------------------------------------------------------
    # Get AI response
    # --------------------------------------------------------

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Groq Consumer AI returned an empty response"
        )

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        data = json.loads(
            content
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            f"Groq returned invalid consumer JSON: {content}"
        ) from exc

    # --------------------------------------------------------
    # Ensure required structure exists
    # --------------------------------------------------------

    if "product_name" not in data:
        data["product_name"] = None

    if "ingredients" not in data:
        data["ingredients"] = []

    if "nutrition" not in data:
        data["nutrition"] = {}

    if "ingredients_to_watch" not in data:
        data["ingredients_to_watch"] = []

    if "health_assessment" not in data:
        data["health_assessment"] = {}

    if "alternatives" not in data:
        data["alternatives"] = []

    if "disclaimer" not in data:
        data["disclaimer"] = (
            "General label-based information, not medical advice."
        )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return data