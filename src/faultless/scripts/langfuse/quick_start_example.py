"""Example script demonstrating LangChain integration with Google Gemini and Langfuse.

This script performs a grammar and spelling check on a sample text using Google Gemini,
with prompt management and tracing provided by Langfuse.
"""

import os
from pathlib import Path

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langfuse import Langfuse

from base.utils.config import get as get_config

# Get Langfuse config
config_file = Path("./src/faultless/config")
langfuse_config = get_config(value="langfuse", file=config_file / "platforms.yml")
llm_config = get_config(value="google", file=config_file / "llm.yml")

# Initialize Langfuse client
langfuse = Langfuse(
    secret_key=langfuse_config.get("secret_key"),
    public_key=langfuse_config.get("public_key"),
    host=langfuse_config.get("host"),
)

# Set your Google API key explicitly (replace with your real token)
os.environ["GOOGLE_API_KEY"] = llm_config.get("api_key")

# Retrieve the grammar check prompt from Langfuse using its label
prompt_data = langfuse.get_prompt(
    "[Faultless][Language][Grammar and Spelling Check]", label="latest"
)
prompt_template = prompt_data.prompt  # This should be a string template
if isinstance(prompt_template, list):
    prompt_template = "".join([item.get("text", "") for item in prompt_template])

# Create a LangChain prompt template with "text" as input variable
prompt = PromptTemplate(template=prompt_template, input_variables=["text"])

# Initialize the Gemini model with zero temperature for deterministic output
llm = ChatVertexAI(model_name="gemini-2.0-flash", temperature=0)

# Create an LLMChain with the prompt and the Gemini model
chain = LLMChain(llm=llm, prompt=prompt)

# Sample text for grammar and spelling check
text = (
    "Public health leaders say the Goverment's insistence on vetting advise from "
    "senior public health doctors is unpresedented and deeply concerning.\n"
    "But Acting Prime Minister David Seymour has hit back at concerns, saying he's "
    '"cheering on Simeon [Brown] putting those mupets back in their box." In doing so, '
    "Seymour indicated the vetting directive had come directly from the health minister's offiice.\n"
    "During a meeting on Tuesday, medical officers of health were told they would need "
    '"national-level" aproval before making public statments about health concerns.'
)

# Retrieve the grammar check prompt from Langfuse using its label
prompt_data = langfuse.get_prompt(
    "[Faultless][Language][Grammar and Spelling Check]", label="latest"
)
prompt_template = prompt_data.prompt  # This should be a string template

# Create a LangChain prompt template with "text" as input variable
prompt = PromptTemplate(template=prompt_template, input_variables=["text"])

# Initialize the Gemini model with zero temperature for deterministic output
llm = ChatVertexAI(model_name="gemini-1.5-flash", temperature=0)

# Create an LLMChain with the prompt and the Gemini model
chain = LLMChain(llm=llm, prompt=prompt)

# Sample text for grammar and spelling check
text = (
    "Public health leaders say the Goverment's insistence on vetting advise from "
    "senior public health doctors is unpresedented and deeply concerning.\n"
    "But Acting Prime Minister David Seymour has hit back at concerns, saying he's "
    '"cheering on Simeon [Brown] putting those mupets back in their box." In doing so, '
    "Seymour indicated the vetting directive had come directly from the health minister's offiice.\n"
    "During a meeting on Tuesday, medical officers of health were told they would need "
    '"national-level" aproval before making public statments about health concerns.'
)

# Run the chain with the input text
response = chain.run(text=text)
print(response)

# Track the grammar check operation in Langfuse
trace = langfuse.trace(name="grammar_check", metadata={"text_length": len(text)})
generation = trace.generation(
    name="grammar_correction",
    model="google:gemini-2.0-flash",
    prompt=prompt_template,
    completion=response,
)
trace.end()

if __name__ == "__main__":
    print("Grammar and spelling check completed successfully.")
