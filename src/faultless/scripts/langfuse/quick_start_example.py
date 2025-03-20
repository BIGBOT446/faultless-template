from pathlib import Path

from langfuse import Langfuse

from base.utils.config import get as get_config

config_file = Path("./src/faultless/config/platforms.yml")
config = get_config(value="langfuse", file=config_file)

# Initialize Langfuse client
langfuse = Langfuse(
    secret_key=config.get("secret_key"),
    public_key=config.get("public_key"),
    host=config.get("host"),
)

# Get production prompt
# prompt = langfuse.get_prompt("[Faultless][Language][Grammar and Spelling Check]") # noqa: ERA001

# Get by label
# You can use as many labels as you'd like to identify different deployment targets
prompt = langfuse.get_prompt("[Faultless][Language][Grammar and Spelling Check]", label="latest")

text = """
Public health leaders say the Goverment's insistence on vetting advise from senior public health doctors is unpresedented and deeply concerning.
But Acting Prime Minister David Seymour has hit back at concerns, saying he's "cheering on Simeon [Brown] putting those mupets back in their box." In doing so, Seymour indicated the vetting directive had come directly from the health minister's offiice.
During a meeting on Tuesday, medical officers of health were told they would need "national-level" aproval before making public statments about health concerns.
"""
