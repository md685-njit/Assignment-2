"""Send a prompt to Anthropic or OpenAI and save the reply.

GIVEN CODE. Do not change it.

Which provider is used:
  Paste one key into .env and that provider is used. If you paste both keys, set
  AI_PROVIDER to anthropic or openai.

Every reply is saved in ai_replies/ under a name made from the provider, the model and
the exact prompt. Asking the same prompt again reads the saved reply, so a rerun costs
nothing. Commit ai_replies/ with your results: it is how the grader checks them.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone

from askcode import ENV_FILE, REPLIES_DIR
from askcode.core import Prompt

DEFAULT_MODELS = {
    "anthropic": "claude-haiku-4-5-20251001",
    "openai": "gpt-5.6-luna",
}

# Reply length cap. Answers are one short JSON object.
ANTHROPIC_MAX_TOKENS = 1024
# OpenAI reasoning models count their hidden reasoning toward this cap, so it is larger.
OPENAI_MAX_COMPLETION_TOKENS = 4096
# Sent only to the default OpenAI model, which supports it. Other models may not.
OPENAI_DEFAULT_REASONING_EFFORT = "low"


class SetupError(RuntimeError):
    """Something in .env needs fixing."""


class AIError(RuntimeError):
    """The provider refused or failed the request."""


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    api_key: str | None
    price_input_per_mtok: float | None
    price_output_per_mtok: float | None


@dataclass(frozen=True)
class Reply:
    text: str
    input_tokens: int
    output_tokens: int
    provider: str
    model: str
    cached: bool


def _price(name: str) -> float | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise SetupError(f"{name} in .env must be a number such as 1.00, not {raw!r}.") from exc
    if value < 0:
        raise SetupError(f"{name} in .env cannot be negative.")
    return value


def load_settings() -> Settings:
    """Read .env and work out the provider, model, key and prices."""
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise SetupError("python-dotenv is not installed. Run: pip install -r requirements.txt") from exc
    load_dotenv(ENV_FILE, override=False)

    provider = os.getenv("AI_PROVIDER", "").strip().lower()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if provider == "":
        if anthropic_key and not openai_key:
            provider = "anthropic"
        elif openai_key and not anthropic_key:
            provider = "openai"
        elif anthropic_key and openai_key:
            raise SetupError(
                "Both ANTHROPIC_API_KEY and OPENAI_API_KEY are set. "
                "Set AI_PROVIDER in .env to anthropic or openai to choose one."
            )
        else:
            raise SetupError(
                "No API key found. Copy .env.example to .env and paste your Anthropic "
                "or OpenAI key into it."
            )
    elif provider not in DEFAULT_MODELS:
        raise SetupError(f"AI_PROVIDER in .env must be anthropic or openai, not {provider!r}.")

    key = anthropic_key if provider == "anthropic" else openai_key
    model = os.getenv("AI_MODEL", "").strip() or DEFAULT_MODELS[provider]
    return Settings(
        provider=provider,
        model=model,
        api_key=key or None,
        price_input_per_mtok=_price("PRICE_INPUT_PER_MTOK"),
        price_output_per_mtok=_price("PRICE_OUTPUT_PER_MTOK"),
    )


def estimate_tokens(text: str) -> int:
    """A rough count: characters divided by four (slide 24).

    Code usually costs more than this, so use it only to plan. The real counts come
    back from the provider with every reply and are written to your results.
    """
    return (len(text) + 3) // 4


def cost_usd(input_tokens: int, output_tokens: int, price_in: float | None, price_out: float | None) -> float | None:
    """Dollars for a number of tokens at per-million prices, or None if a price is missing."""
    if price_in is None or price_out is None:
        return None
    return input_tokens / 1_000_000 * price_in + output_tokens / 1_000_000 * price_out


def prompt_key(provider: str, model: str, prompt: Prompt) -> str:
    """The saved-reply name for this exact provider, model and prompt."""
    blob = json.dumps(
        {"provider": provider, "model": model, "system": prompt.system, "user": prompt.user},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


def ask_model(prompt: Prompt, settings: Settings, fresh: bool = False) -> Reply:
    """Return the model's reply to the prompt, from ai_replies/ if it was asked before.

    fresh=True ignores the saved reply, asks again, and replaces the saved one.
    """
    key = prompt_key(settings.provider, settings.model, prompt)
    path = REPLIES_DIR / f"{key}.json"
    if path.exists() and not fresh:
        saved = json.loads(path.read_text(encoding="utf-8"))
        return Reply(
            text=saved["text"],
            input_tokens=int(saved["input_tokens"]),
            output_tokens=int(saved["output_tokens"]),
            provider=saved["provider"],
            model=saved["model"],
            cached=True,
        )

    text, input_tokens, output_tokens = call_model(prompt, settings)
    REPLIES_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "provider": settings.provider,
        "model": settings.model,
        "prompt_key": key,
        "asked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "text": text,
    }
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return Reply(text, input_tokens, output_tokens, settings.provider, settings.model, cached=False)


def call_model(prompt: Prompt, settings: Settings) -> tuple[str, int, int]:
    """Make one real API call. Returns (reply text, input tokens, output tokens)."""
    if not settings.api_key:
        raise SetupError(
            f"This needs a real call to {settings.provider}, but no API key is set in .env."
        )
    if settings.provider == "anthropic":
        return _call_anthropic(prompt, settings)
    return _call_openai(prompt, settings)


def _call_anthropic(prompt: Prompt, settings: Settings) -> tuple[str, int, int]:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.api_key, max_retries=4)
    kwargs = {
        "model": settings.model,
        "max_tokens": ANTHROPIC_MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt.user}],
    }
    if prompt.system:
        kwargs["system"] = prompt.system
    try:
        response = client.messages.create(**kwargs)
    except anthropic.AuthenticationError as exc:
        raise AIError("Anthropic rejected your API key. Check ANTHROPIC_API_KEY in .env.") from exc
    except anthropic.PermissionDeniedError as exc:
        raise AIError(f"Anthropic refused the request (permission): {exc}") from exc
    except anthropic.NotFoundError as exc:
        raise AIError(f"Anthropic does not know the model {settings.model!r}. Check AI_MODEL in .env.") from exc
    except anthropic.RateLimitError as exc:
        raise AIError(
            "Anthropic rate limit or spend limit reached. Wait a minute and run the same "
            "command again; answers already received are saved and will not be paid for twice."
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise AIError("Could not reach Anthropic. Check your internet connection.") from exc
    except anthropic.APIStatusError as exc:
        raise AIError(f"Anthropic returned an error ({exc.status_code}): {exc}") from exc
    text = "".join(block.text for block in response.content if block.type == "text")
    return text, int(response.usage.input_tokens), int(response.usage.output_tokens)


def _call_openai(prompt: Prompt, settings: Settings) -> tuple[str, int, int]:
    import openai

    client = openai.OpenAI(api_key=settings.api_key, max_retries=4)
    messages = []
    if prompt.system:
        messages.append({"role": "system", "content": prompt.system})
    messages.append({"role": "user", "content": prompt.user})
    kwargs = {
        "model": settings.model,
        "messages": messages,
        "max_completion_tokens": OPENAI_MAX_COMPLETION_TOKENS,
    }
    if settings.model == DEFAULT_MODELS["openai"]:
        kwargs["reasoning_effort"] = OPENAI_DEFAULT_REASONING_EFFORT
    try:
        response = client.chat.completions.create(**kwargs)
    except openai.AuthenticationError as exc:
        raise AIError("OpenAI rejected your API key. Check OPENAI_API_KEY in .env.") from exc
    except openai.PermissionDeniedError as exc:
        raise AIError(f"OpenAI refused the request (permission): {exc}") from exc
    except openai.NotFoundError as exc:
        raise AIError(f"OpenAI does not know the model {settings.model!r}. Check AI_MODEL in .env.") from exc
    except openai.RateLimitError as exc:
        raise AIError(
            "OpenAI rate limit or quota reached. Wait a minute and run the same command "
            "again; answers already received are saved and will not be paid for twice. "
            "If it keeps failing, check that your OpenAI account has credit."
        ) from exc
    except openai.APIConnectionError as exc:
        raise AIError("Could not reach OpenAI. Check your internet connection.") from exc
    except openai.APIStatusError as exc:
        raise AIError(f"OpenAI returned an error ({exc.status_code}): {exc}") from exc
    text = response.choices[0].message.content or ""
    usage = response.usage
    return text, int(usage.prompt_tokens), int(usage.completion_tokens)
