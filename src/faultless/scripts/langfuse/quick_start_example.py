"""Example script demonstrating LangChain integration with Google Gemini and Langfuse.

This script performs a grammar and spelling check on a sample text using Google Gemini,
with prompt management and tracing provided by Langfuse.
"""

from pathlib import Path

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
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

# Retrieve the grammar check prompt from Langfuse using its label
langfuse_prompt = langfuse.get_prompt(
    name="[Faultless][Language][Grammar and Spelling Check]", label="production"
)

# Create a LangChain prompt template with "text" as input variable
langchain_prompt = PromptTemplate.from_template(
    template=langfuse_prompt.prompt,
    template_format="mustache",
    metadata={"langfuse_prompt": langfuse_prompt},
)

# Initialize the Gemini model with zero temperature for deterministic output
llm = GoogleGenerativeAI(model=llm_config.get("model"), google_api_key=llm_config.get("api_key"))

# Create an LLMChain with the prompt and the Gemini model
chain = LLMChain(llm=llm, prompt=langchain_prompt)

# Sample text for grammar and spelling check
text_to_check = (
    "Public health leaders say the Goverment's insistence on vetting advise from "
    "senior public health doctors is unpresedented and deeply concerning.\n"
    "But Acting Prime Minister David Seymour has hit back at concerns, saying he's "
    '"cheering on Simeon [Brown] putting those mupets back in their box." In doing so, '
    "Seymour indicated the vetting directive had come directly from the health minister's offiice.\n"
    "During a meeting on Tuesday, medical officers of health were told they would need "
    '"national-level" aproval before making public statments about health concerns.'
)

# Run the chain with the input text
response = chain.invoke({"text": text_to_check})
tidy_response = response.get("text").replace("```json", "").replace("```", "").strip()
print(tidy_response)
