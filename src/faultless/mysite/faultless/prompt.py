from pathlib import Path
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
import os
from .config import get
from docx import Document
from .models import Trace, Rules

def send_prompt(new_rules, report):
    config_file = Path("./src/faultless/config")
    langfuse_config = get(value="langfuse", file=config_file / "platforms.yml")
    llm_config = get(value="google", file=config_file / "llm.yml")
    
    # get keys for your project from https://cloud.langfuse.com
    os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_config["public_key"]
    os.environ["LANGFUSE_SECRET_KEY"] = langfuse_config["secret_key"]
    os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"
    
    # your openai key
    os.environ["LANGFUSE_GOOGLE_API_KEY"] = llm_config["api_key"]
    
    langfuse = Langfuse()

    def create_prompt(new_rule):
        format = str(new_rule.output_format).strip().replace("{", " ").replace("}", " ")

        langfuse.create_prompt(
            name=new_rule.name,
            prompt="You are a proofreader, designed to review an engineering report(it might contains sepcial words in engineering area so please be careful when you review) and find all the errors in it, please use the original report to find all the errors before you modify it. below there are some rules that help you to check the report\n"
            + "\n"
            + "error name: " + new_rule.name
            + "\n"
            + new_rule.description
            + "\n"
            "return in a json object with following structure:"
            + "\n"
            + format
            + "\n"
            + "\n"
            "Report: " 
            + "\n"
            + "\n"
            "{{report}}",
            config={
                "model": "gemini-2.0-flash",
                "temperature": 0,
            },
            labels=["production"],
        )


    langfuse_callback_handler = CallbackHandler()

    # Get production prompt
    for new_rule in new_rules:
        create_prompt(new_rule)

    # Get report from the doc
    body = Document(report)
    text = "\n".join([para.text for para in body.paragraphs])
    #text = DocxExtractor(report).extractDocumentBodyText()

    return text


