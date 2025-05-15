"""How to Integrate Langfuse with LangChain Using Google Gemini

This guide demonstrates how to integrate Langfuse with LangChain to perform a grammar and spelling
check on a sample text using Google Gemini. Langfuse provides prompt management and tracing, while
LangChain facilitates the interaction with the LLM.

Disclaimer:
Using LangChain is one way to utilize prompts from Langfuse. Depending on your use case, other
solutions might be more suitable.
"""
from pathlib import Path
import importlib.resources

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from langfuse import Langfuse
from django.core.cache import cache

import json
import time
import os

from base.utils.config import get as get_config

#from upload_file import upload_and_read_docx, upload_docx, read_docx
from faultless.marker.scripts.spire.grammar_spelling import grammar_spelling
from faultless.marker.scripts.spire.rules import rules
from faultless.marker.scripts.spire.summary import insert_text_new_page
from faultless.marker.functions.spire.utils import remove_evaluation_warning
from ..models import Trace

def ai_output(promptname, text_to_give):
    # Step 1: Load Configuration
    # Load Langfuse and LLM configurations from YAML files.
    config_file = Path("./src/faultless/config")
    langfuse_config = get_config(value="langfuse", file=config_file / "platforms.yml")
    llm_config = get_config(value="google", file=config_file / "llm.yml")


    # Step 2: Initialize Langfuse Client
    # Create a Langfuse client using the configuration values.
    '''langfuse = Langfuse(
        secret_key=langfuse_config.get("secret_key"),
        public_key=langfuse_config.get("public_key"),
        host=langfuse_config.get("host"),
    )'''
    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-03837ecb-bae5-4aa2-a319-1afb959284f5"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-b860425a-38b3-4c13-a85c-5b1c0c38605a"

    try:
        langfuse = Langfuse()
        trace = langfuse.trace(name="connection-test", tags=["connectivity"])
        print("✅ Successfully connected and created test trace.")
        print(f"Trace ID: {trace.id}")
    except Exception as e:
        print("❌ Failed to connect to Langfuse API.")
        print("Error:", e)


    # Step 3: Retrieve Prompt from Langfuse
    # Fetch the grammar check prompt from Langfuse using its label.
    langfuse_prompt = langfuse.get_prompt(
        name=promptname, label="production"
    )


    # Step 4: Create a LangChain Prompt Template
    # Use the Langfuse prompt to create a LangChain prompt template.
    langchain_prompt = PromptTemplate.from_template(
        template=langfuse_prompt.prompt,
        template_format="mustache",
        metadata={"langfuse_prompt": langfuse_prompt},
    )


    # Step 5: Initialize the LLM
    # Set up the Google Gemini model with zero temperature for deterministic output.
    llm = GoogleGenerativeAI(model="gemini-2.0-flash", google_api_key="AIzaSyCBSjoQWBDT4vxdaqEky04NizOK7LSkPWg")


    # Step 6: Create an LLMChain
    # Combine the LangChain prompt template and the LLM into an LLMChain.
    chain = LLMChain(llm=llm, prompt=langchain_prompt)


    # Step 7: Run the Chain
    # Execute the chain with the input text and process the response.
    response = chain.invoke({"report": text_to_give})
    tidy_response = response.get("text").replace("```json", "").replace("```", "").strip()
    a = json.loads(tidy_response)
    report = cache.get("selected")
    if Trace.objects.filter(path=report).exists():
        trace = Trace.objects.get(path=report)
        
        for data in a["matches"]:
            trace.review_output["matches"].append(data)
        trace.save()
    else:
        new_trace = Trace(path=report, review_output = a)
        new_trace.save()

    try:
     return json.loads(tidy_response)
    except Exception as e:
     return str(tidy_response)


"""file_path = upload_docx()
text_to_check = read_docx(file_path)
prompts = list(upload_and_read_docx().strip().split('\n'))
number_of_prompts = len(prompts)

for current_prompt_number in range(number_of_prompts):
    if prompts[current_prompt_number] == 'Grammar and Spelling Check':
        grammar_spelling(ai_output(prompts[current_prompt_number], text_to_check), file_path)
    else:
        rules(ai_output(prompts[current_prompt_number], text_to_check), file_path)

insert_text_new_page(file_path, ai_output("Summary", text_to_check))"""