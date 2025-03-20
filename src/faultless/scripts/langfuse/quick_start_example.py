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
prompt = langfuse.get_prompt("[Faultless][Language][Grammar and Spelling Check]")

# Get by label
# You can use as many labels as you'd like to identify different deployment targets
prompt = langfuse.get_prompt("[Faultless][Language][Grammar and Spelling Check]", label="latest")

# Get by version number, usually not recommended as it requires code changes to deploy new prompt versions
langfuse.get_prompt("[Faultless][Language][Grammar and Spelling Check]", version=2)
