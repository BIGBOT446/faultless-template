"""Example script demonstrating LangChain integration with Google Gemini and Langfuse.

This script performs a grammar and spelling check on a sample text using Google's Gemini model,
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
config_file = Path("./src/faultless/config/platforms.yml")
langfuse_config = get_config(value="langfuse", file=config_file)

# Initialize Langfuse client
langfuse = Langfuse(
    secret_key=langfuse_config.get("secret_key"),
    public_key=langfuse_config.get("public_key"),
    host=langfuse_config.get("host"),
)

# Set Google API key (you'll replace this with the real value)
os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY_HERE"

# Get grammar check prompt from Langfuse by label
prompt_data = langfuse.get_prompt(
    "[Faultless][Language][Grammar and Spelling Check]", label="latest"
)
prompt_template = prompt_data.prompt

# Create a PromptTemplate for LangChain
prompt = PromptTemplate(template=prompt_template, input_variables=["text"])

# Initialize the Gemini model
llm = ChatVertexAI(model_name="gemini-1.5-flash", temperature=0)

# Create a chain that will use the prompt and the LLM
chain = LLMChain(llm=llm, prompt=prompt)

text = """
Public health leaders say the Goverment's insistence on vetting advise from senior public health doctors is unpresedented and deeply concerning.
But Acting Prime Minister David Seymour has hit back at concerns, saying he's "cheering on Simeon [Brown] putting those mupets back in their box." In doing so, Seymour indicated the vetting directive had come directly from the health minister's offiice.
During a meeting on Tuesday, medical officers of health were told they would need "national-level" aproval before making public statments about health concerns.
"""

# Run the chain with the input text
response = chain.run(text=text)

# Print the response
print(response)

# Track the grammar check in Langfuse
trace = langfuse.trace(name="grammar_check", metadata={"text_length": len(text)})

generation = trace.generation(
    name="grammar_correction",
    model="google:gemini-1.5-flash",
    prompt=prompt_template,
    completion=response,
)

# End the trace
trace.end()

if __name__ == "__main__":
    print("Grammar and spelling check completed successfully.")
