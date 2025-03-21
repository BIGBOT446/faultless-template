"""How to Integrate Langfuse with LangChain Using Google Gemini

This guide demonstrates how to integrate Langfuse with LangChain to perform a grammar and spelling
check on a sample text using Google Gemini. Langfuse provides prompt management and tracing, while
LangChain facilitates the interaction with the LLM.

Disclaimer:
Using LangChain is one way to utilize prompts from Langfuse. Depending on your use case, other
solutions might be more suitable.
"""

from pathlib import Path

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from langfuse import Langfuse

from base.utils.config import get as get_config

# Step 1: Load Configuration
# Load Langfuse and LLM configurations from YAML files.
config_file = Path("./src/faultless/config")
langfuse_config = get_config(value="langfuse", file=config_file / "platforms.yml")
llm_config = get_config(value="google", file=config_file / "llm.yml")

# Step 2: Initialize Langfuse Client
# Create a Langfuse client using the configuration values.
langfuse = Langfuse(
    secret_key=langfuse_config.get("secret_key"),
    public_key=langfuse_config.get("public_key"),
    host=langfuse_config.get("host"),
)

# Step 3: Retrieve Prompt from Langfuse
# Fetch the grammar check prompt from Langfuse using its label.
langfuse_prompt = langfuse.get_prompt(
    name="[Faultless][Language][Grammar and Spelling Check]", label="production"
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
llm = GoogleGenerativeAI(model=llm_config.get("model"), google_api_key=llm_config.get("api_key"))

# Step 6: Create an LLMChain
# Combine the LangChain prompt template and the LLM into an LLMChain.
chain = LLMChain(llm=llm, prompt=langchain_prompt)

# Step 7: Provide Input Text
# Define the sample text for grammar and spelling check.
text_to_check = (
    "Public health leaders say the Goverment's insistence on vetting advise from "
    "senior public health doctors is unpresedented and deeply concerning.\n"
    "But Acting Prime Minister David Seymour has hit back at concerns, saying he's "
    '"cheering on Simeon [Brown] putting those mupets back in their box." In doing so, '
    "Seymour indicated the vetting directive had come directly from the health minister's offiice.\n"
    "During a meeting on Tuesday, medical officers of health were told they would need "
    '"national-level" aproval before making public statments about health concerns.'
)

# Step 8: Run the Chain
# Execute the chain with the input text and process the response.
response = chain.invoke({"text": text_to_check})
tidy_response = response.get("text").replace("```json", "").replace("```", "").strip()

# Step 9: Output the Result
# Print the cleaned-up response.
print(tidy_response)
