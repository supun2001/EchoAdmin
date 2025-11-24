import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def generate_reply(body, custom_instruction=None):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = "gemini-2.5-pro"

    base_prompt = (
        "You are an administrative assistant. "
        "Write a single, direct email reply to the message. "
        "Be polite, professional, and helpful. "
        "Be concise, clear, and respectful. "
        "Do not provide multiple options or examples - just write one email response."
    )

    if custom_instruction:
        base_prompt += f"\n\nAdditional instruction: {custom_instruction}"

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part(text=f"{base_prompt}\n\nMessage:\n{body}")
            ],
        )
    ]

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
    )

    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model, contents=contents, config=config
    ):
        if chunk.text:
            print(chunk.text, end="")
            response_text += chunk.text

    print()
    return response_text
