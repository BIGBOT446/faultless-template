"""Single entry point for constructing the chat model used by Faultless.

Previously ``marker/llm.py`` and ``summary.py`` each instantiated
``ChatGoogleGenerativeAI`` and read the model name from the Langfuse prompt config,
where ``gemini-2.0-flash`` was hard-coded. Switching providers meant editing several
places, and the stale model name stored in Langfuse would be passed to the new
provider verbatim.

All model construction now goes through this module. The model, temperature and
output limit come from the ``deepseek`` section of ``config/llm.yml``.
"""

import os
from pathlib import Path

from langchain_deepseek import ChatDeepSeek

from .config import get

CONFIG_DIR = Path("./src/faultless/config")
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_MAX_TOKENS = 8192


class LLMConfigError(RuntimeError):
    """Raised when the DeepSeek configuration is missing or incomplete."""


def get_llm_config() -> dict:
    """Return the ``deepseek`` section of ``config/llm.yml``."""
    cfg = get(value="deepseek", file=CONFIG_DIR / "llm.yml")
    if not cfg:
        msg = "config/llm.yml is missing the 'deepseek' section"
        raise LLMConfigError(msg)
    return cfg


def model_name() -> str:
    """Return the configured model name."""
    return get_llm_config().get("model", DEFAULT_MODEL)


def get_chat_model(*, json_mode: bool = False, temperature: float | None = None) -> ChatDeepSeek:
    """Build the DeepSeek chat model.

    Args:
        json_mode: Enable DeepSeek JSON Output, which guarantees syntactically valid
            JSON. DeepSeek requires the word "json" to appear in the prompt; the
            rule-review prompts satisfy this.
        temperature: Overrides the configured temperature when given.

    Returns:
        A configured ``ChatDeepSeek`` instance.
    """
    cfg = get_llm_config()
    api_key = cfg.get("api_key")
    if not api_key:
        msg = "DEEPSEEK_API_KEY is not set; add it to your .env file"
        raise LLMConfigError(msg)
    os.environ["DEEPSEEK_API_KEY"] = api_key

    temp = cfg.get("temperature", 0.0) if temperature is None else temperature

    kwargs = {}
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}

    return ChatDeepSeek(
        model=cfg.get("model", DEFAULT_MODEL),
        temperature=float(temp),
        # Grammar-style rules can return many matches on long reports. A low output
        # limit truncates the JSON mid-object.
        max_tokens=int(cfg.get("max_tokens", DEFAULT_MAX_TOKENS)),
        **kwargs,
    )


def strip_json_fence(text: str) -> str:
    """Remove a surrounding ```json ... ``` fence if present.

    The original code sliced ``response.content[7:-3]``, assuming the model always
    wraps its output in a fence. With JSON mode enabled DeepSeek returns bare JSON,
    and a fixed slice would cut off the first seven characters. This strips a fence
    only when one is present.
    """
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()
