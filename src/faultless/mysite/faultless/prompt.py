from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
import os
from .config import get
from docx import Document
from .doc_extractor import DocxExtractor
from .models import Trace, Rules


def send_prompt(new_rules, report):
    # get keys for your project from https://cloud.langfuse.com
    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-03837ecb-bae5-4aa2-a319-1afb959284f5"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-b860425a-38b3-4c13-a85c-5b1c0c38605a"
    os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"
    os.environ["GOOGLE_API_KEY"] = "AIzaSyBBYnENqtXiXais7x7t9LANWGEcOQLzA4Q"

    """config_file = Path("./src/faultless/config")
    langfuse_config = get(value="langfuse", file=config_file / "platforms.yml")
    llm_config = get(value="google", file=config_file / "llm.yml")"""

    """langfuse = Langfuse(
        secret_key=langfuse_config["secret_key"],
        public_key=langfuse_config["public_key"],
        host=langfuse_config["host"],
    )"""

    langfuse = Langfuse()
    def create_prompt(new_rule):
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
            "'matches': ['error_type': 'error name(only use the name i gave you)', 'message': 'simple description of the error and how to correct it', 'original': 'the error word or phrase or sentence(depend on different type of error)','occurrence_index': 'occurrence times of the error', ...]"
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

    langfuse = Langfuse()

    langfuse_callback_handler = CallbackHandler()

    # Get production prompt
    for new_rule in new_rules:
        create_prompt(new_rule)

    # Get report from the doc
    body = Document(report)
    text = "\n".join([para.text for para in body.paragraphs])
    #text = DocxExtractor(report).extractDocumentBodyText()

    return text
    """langfuse_prompt = langfuse.get_prompt("report_check")

    langchain_prompt = ChatPromptTemplate.from_template(
        langfuse_prompt.get_langchain_prompt(),
        metadata={"langfuse_prompt": langfuse_prompt},
    )

    model = langfuse_prompt.config["model"]

    temperature = str(langfuse_prompt.config["temperature"])
    model = ChatGoogleGenerativeAI(model=model, temperature=temperature)
    chain = langchain_prompt | model
    
    example_input = {
        "report": text
    }
    response = chain.invoke(input=example_input, config={"callbacks": [langfuse_callback_handler]})

    new_trace = Trace(path=report, review_output = response.content[7:-3])
    new_trace.save()"""

