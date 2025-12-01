from openai import AsyncOpenAI

from .config import MODEL_NAME, OPENROUTER_API_KEY, OPENROUTER_BASE_URL


SYSTEM_PROMPT = """
Ты — профессиональный туристический консультант.
Помогаешь пользователю выбирать направления, сезон, маршруты, отели и виды активности.
Уточняй бюджет, даты, состав путешественников и предпочтения, если это важно для ответа.
Отвечай понятно, структурированно и по делу.
"""

TEMPERATURE = 0.7
MAX_TOKENS = 512


def _create_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)


_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = _create_client()
    return _client


async def ask_llm(user_message: str, history: list[dict] | None = None) -> str:
    """
    Отправляет запрос в LLM через OpenRouter с учётом истории диалога.

    Args:
        user_message: Текущее сообщение пользователя
        history: Список предыдущих сообщений в формате [{"role": "...", "content": "..."}, ...]
    """
    client = get_client()

    messages = [{"role": "system", "content": SYSTEM_PROMPT.strip()}]

    # Добавляем историю, если она есть
    if history:
        messages.extend(history)

    # Добавляем текущее сообщение пользователя
    messages.append({"role": "user", "content": user_message})

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=messages,
    )

    return (response.choices[0].message.content or "").strip()



