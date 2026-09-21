"""How to Integrate Langfuse with LangChain Using DeepSeek (previously Google Gemini)

This guide demonstrates how to integrate Langfuse with LangChain to perform a grammar and spelling
check on a sample text using DeepSeek. Langfuse provides prompt management and tracing, while
LangChain facilitates the interaction with the LLM.

Disclaimer:
Using LangChain is one way to utilize prompts from Langfuse. Depending on your use case, other
solutions might be more suitable.
"""

import os
from pathlib import Path

from django.core.cache import cache
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

from faultless.config import get
from faultless.llm_factory import get_chat_model
from faultless.models import Trace


def ai_output(promptname: str, text_to_give: str) -> dict:
    """Run the Langfuse-managed prompt for a rule through DeepSeek and return parsed JSON."""
    # Step 1: Load Configuration
    # Load Langfuse and LLM configurations from YAML files.
    config_file = Path("./src/faultless/config")
    langfuse_config = get(value="langfuse", file=config_file / "platforms.yml")

    # Step 2: Initialize Langfuse Client
    # Create a Langfuse client using the configuration values.
    # get keys for your project from https://cloud.langfuse.com
    os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_config["public_key"]
    os.environ["LANGFUSE_SECRET_KEY"] = langfuse_config["secret_key"]
    os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"

    langfuse = Langfuse()

    try:
        trace = langfuse.trace(name="connection-test", tags=["connectivity"])
        print("✅ Successfully connected and created test trace.")
        print(f"Trace ID: {trace.id}")
    except Exception as e:  # noqa: BLE001 - best-effort connectivity check, must not abort the run
        print("❌ Failed to connect to Langfuse API.")
        print("Error:", e)

    # Step 3: Retrieve Prompt from Langfuse
    # Fetch the grammar check prompt from Langfuse using its label.
    langfuse_prompt = langfuse.get_prompt(name=promptname, label="production")

    # Step 4: Create a LangChain Prompt Template
    # Use the Langfuse prompt to create a LangChain prompt template.
    langchain_prompt = ChatPromptTemplate.from_template(
        langfuse_prompt.get_langchain_prompt(),
        metadata={"langfuse_prompt": langfuse_prompt},
    )

    # Step 5: Initialize the LLM
    # The model now comes from config/llm.yml rather than the Langfuse prompt config,
    # which still holds the old "gemini-2.0-flash" name. Temperature is still taken from
    # the prompt config. JSON mode guarantees syntactically valid JSON; JsonOutputParser
    # is kept so fenced output is still handled.
    temperature = langfuse_prompt.config.get("temperature", 0)
    model = get_chat_model(json_mode=True, temperature=temperature)

    # Step 6: Create an LCEL chain
    # Prompt -> model -> JsonOutputParser, so markdown-fenced JSON no longer
    # needs manual slicing (parse_json_markdown handles ```json fences).
    chain = langchain_prompt | model | JsonOutputParser()

    # Step 7: Run the Chain
    # Execute the chain with the input text and process the response.

    example_input = {
        "report": text_to_give,
    }
    a = chain.invoke(input=example_input, config={"callbacks": [CallbackHandler()]})

    trace_id = cache.get("trace_id")
    trace = Trace.objects.get(id=trace_id)

    original_words = []
    for data in a["matches"]:
        if data["original"] not in original_words:
            trace.review_output["matches"].append(data)
            original_words.append(data["original"])

    trace.save()

    return a
