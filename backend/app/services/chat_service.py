import anthropic
from app.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def get_socratic_response(question: str, context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)

    prompt = f"""You are a Socratic tutor helping a student understand their own study material.

You have been given relevant excerpts from the student's notes. Use ONLY this material to answer.
If the answer cannot be found in the provided context, say so honestly rather than making things up.
Guide the student toward understanding by explaining concepts clearly and building on what's in their notes.

Context from student's notes:
{context}

Student's question:
{question}

Answer clearly and concisely, grounding every claim in the provided context."""

    message = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text