from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
import os
from .config import get
from docx import Document


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
    def create_prompt(new_rules):
        langfuse.create_prompt(
            name="report_check",
            prompt="You are designed to review a report {{report}}, below there are some rules that help you to check the report(ignore the scale now)\n"
            + new_rules
            + "\n"
            "return in a json object with following structure:"
            "'matches': [ 'message': 'error description', 'original': 'original word or phrase', 'corrected': 'the word or phrase after correction', ...],"
            "'output': 'the modified report'",
            config={
                "model": "gemini-2.0-flash",
                "temperature": 0,
            },
            labels=["production"],
        )

    langfuse = Langfuse()

    langfuse_callback_handler = CallbackHandler()

    # Get production prompt
    create_prompt(new_rules)
    langfuse_prompt = langfuse.get_prompt("report_check")

    langchain_prompt = ChatPromptTemplate.from_template(
        langfuse_prompt.get_langchain_prompt(),
        metadata={"langfuse_prompt": langfuse_prompt},
    )

    model = langfuse_prompt.config["model"]

    temperature = str(langfuse_prompt.config["temperature"])
    model = ChatGoogleGenerativeAI(model=model, temperature=temperature)
    chain = langchain_prompt | model

    # Get report from the doc
    report = Document(report)
    text = "\n".join([para.text for para in report.paragraphs])
    

    example_input = {
        "report": text
    }
    response = chain.invoke(input=example_input, config={"callbacks": [langfuse_callback_handler]})

    return response.content
