from pathlib import Path

from docx import Document
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

from .config import get
from .llm_factory import model_name


def send_prompt(new_rules, report):
    load_dotenv()
    config_file = Path("./src/faultless/config")

    _ = get(value="langfuse", file=config_file / "platforms.yml")
    _ = get(value="deepseek", file=config_file / "llm.yml")

    langfuse = Langfuse()

    def create_prompt(new_rule):
        format = str(new_rule.output_format).strip().replace("{", " ").replace("}", " ")

        langfuse.create_prompt(
            name=new_rule.name,
            prompt="You are a proofreader, designed to review an engineering report(it might contains sepcial words in engineering area so please be careful when you review) and find all the errors in it, please use the original report to find all the errors before you modify it. below there are some rules that help you to check the report\n"
            + "\n"
            + "error name: "
            + new_rule.name
            + "\n"
            + new_rule.description
            + "\n"
            "return in a json object with following structure:" + "\n" + format + "\n" + "\n"
            "Report: " + "\n" + "\n"
            "{{report}}",
            config={
                "model": model_name(),
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
    # text = DocxExtractor(report).extractDocumentBodyText()

    return text
