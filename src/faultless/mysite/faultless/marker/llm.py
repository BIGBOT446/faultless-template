"""How to Integrate Langfuse with LangChain Using Google Gemini

This guide demonstrates how to integrate Langfuse with LangChain to perform a grammar and spelling
check on a sample text using Google Gemini. Langfuse provides prompt management and tracing, while
LangChain facilitates the interaction with the LLM.

Disclaimer:
Using LangChain is one way to utilize prompts from Langfuse. Depending on your use case, other
solutions might be more suitable.
"""

import json
import os
from pathlib import Path

from django.core.cache import cache
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

from faultless.config import get

from ..models import Trace

# from upload_file import upload_and_read_docx, upload_docx, read_docx


def ai_output(promptname, text_to_give):
    # Step 1: Load Configuration
    # Load Langfuse and LLM configurations from YAML files.
    config_file = Path("./src/faultless/config")
    langfuse_config = get(value="langfuse", file=config_file / "platforms.yml")
    llm_config = get(value="google", file=config_file / "llm.yml")

    # Step 2: Initialize Langfuse Client
    # Create a Langfuse client using the configuration values.
    # get keys for your project from https://cloud.langfuse.com
    os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_config["public_key"]
    os.environ["LANGFUSE_SECRET_KEY"] = langfuse_config["secret_key"]
    os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"

    # your openai key
    os.environ["GOOGLE_API_KEY"] = llm_config["api_key"]

    langfuse = Langfuse()

    try:
        trace = langfuse.trace(name="connection-test", tags=["connectivity"])
        print("✅ Successfully connected and created test trace.")
        print(f"Trace ID: {trace.id}")
    except Exception as e:
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
    # Set up the Google Gemini model with zero temperature for deterministic output.
    model = langfuse_prompt.config["model"]

    temperature = str(langfuse_prompt.config["temperature"])
    model = ChatGoogleGenerativeAI(model=model, temperature=temperature)

    # Step 6: Create an LLMChain
    # Combine the LangChain prompt template and the LLM into an LLMChain.
    chain = langchain_prompt | model

    # Step 7: Run the Chain
    # Execute the chain with the input text and process the response.

    example_input = {
        "report": text_to_give,
    }
    response = chain.invoke(input=example_input, config={"callbacks": [CallbackHandler]})
    # response = chain.invoke({"report": text_to_give})

    tidy_response = response.content[7:-3]
    a = json.loads(tidy_response)

    trace_id = cache.get("trace_id")
    trace = Trace.objects.get(id=trace_id)

    original_words = []
    for data in a["matches"]:
        if data["original"] not in original_words:
            trace.review_output["matches"].append(data)
            original_words.append(data["original"])

    trace.save()

    return a
