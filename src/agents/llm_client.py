import json
from pydantic import BaseModel
from groq import Groq

client = Groq()

def generate_structured_analysis(system_prompt: str, user_prompt: str, response_model: type[BaseModel]):
    schema = response_model.model_json_schema()
    
    dummy_dict = {}
    for key, details in schema.get('properties', {}).items():
        field_type = details.get('type', 'string')
        if field_type in ['number', 'integer']:
            dummy_dict[key] = 0.99
        elif field_type == 'array':
            dummy_dict[key] = ["item1"]
        else:
            dummy_dict[key] = "your_text_here"
            
    template_json = json.dumps(dummy_dict, indent=2)

    enforced_prompt = (
        f"{system_prompt}\n\n"
        "CRITICAL INSTRUCTION: You must return ONLY a raw, valid JSON object. "
        "Keep your reasoning concise (under 100 words) so you do not get cut off. "
        "Do not wrap it in markdown code blocks (```json). Do not add trailing commas. "
        f"Your output must exactly match this JSON structure and respect data types:\n{template_json}"
    )
    
    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": enforced_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=400 
    )
    
    raw_json = response.choices[0].message.content
    return response_model.model_validate_json(raw_json)