import json
from anthropic import AsyncAnthropic
from app.config import settings

client = AsyncAnthropic(api_key=settings.anthropic_api_key)


async def generate_flashcards_from_chunks(chunks: list[str]) -> list[dict]:
    # Join chunks into one block of text separated by double newlines
    combined_text = "\n\n".join(chunks)

    prompt = f"""You are an expert educator creating flashcards from study material.

Given the following text from a student's notes or textbook, generate high quality flashcards.

Rules:
- Each flashcard must have a clear, specific question and a concise answer
- Focus on key concepts, definitions, formulas, and important relationships
- Questions should test understanding, not just memorization
- Aim for 1 flashcard per major concept
- Return ONLY a JSON array, no other text

Text to process:
{combined_text}

Return a JSON array in exactly this format:
[
  {{"question": "What is X?", "answer": "X is..."}},
  {{"question": "How does Y work?", "answer": "Y works by..."}}
]"""

    message = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text

    try:
        flashcards = json.loads(response_text)
    # Handle cases where the model returns additional text around the JSON array
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            flashcards = json.loads(json_match.group())
        else:
            raise ValueError(f"Could not parse flashcards from response: {response_text}")

    return flashcards