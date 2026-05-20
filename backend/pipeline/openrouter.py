import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel
from backend.config import settings

# Pricing per 1M tokens: (input_price_usd, output_price_usd)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "mistralai/mistral-7b-instruct": (0.07, 0.07),
    "anthropic/claude-3-haiku-20240307": (0.25, 1.25),
    "anthropic/claude-3-haiku-20240307:beta": (0.25, 1.25),
    "google/gemini-flash-1.5": (0.075, 0.30),
}


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in MODEL_PRICING:
        return 0.0
    input_price, output_price = MODEL_PRICING[model]
    cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000
    return round(cost, 8)


def get_client() -> instructor.AsyncInstructor:
    raw_client = AsyncOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        default_headers={
            "HTTP-Referer": settings.site_url,
            "X-Title": "Ticket Triage MVP",
        }
    )
    return instructor.from_openai(raw_client, mode=instructor.Mode.JSON)


async def llm_call(
    model: str,
    messages: list[dict],
    response_model: type[BaseModel],
    max_retries: int = 2,
) -> tuple[BaseModel, int, int, float]:
    """
    Makes a structured LLM call via OpenRouter.
    Returns (result, input_tokens, output_tokens, cost_usd).
    On failure after retries, returns a zero-confidence sentinel.
    """
    client = get_client()
    try:
        result, completion = await client.chat.completions.create_with_completion(
            model=model,
            messages=messages,
            response_model=response_model,
            max_retries=max_retries,
        )
        usage = completion.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        cost = compute_cost(model, input_tokens, output_tokens)
        return result, input_tokens, output_tokens, cost
    except Exception:
        # Exhausted retries or API error — return zero-confidence sentinel
        sentinel = response_model.model_construct(confidence=0.0)
        return sentinel, 0, 0, 0.0
