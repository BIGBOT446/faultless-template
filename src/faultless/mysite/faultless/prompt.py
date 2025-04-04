from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import Langfuse
from langfuse.callback import CallbackHandler

from .config import get


def send_prompt(new_rules, report):
    # get keys for your project from https://cloud.langfuse.com
    # os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-03837ecb-bae5-4aa2-a319-1afb959284f5"
    # os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-b860425a-38b3-4c13-a85c-5b1c0c38605a"
    # os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"
    # os.environ["GOOGLE_API_KEY"] = "AIzaSyBBYnENqtXiXais7x7t9LANWGEcOQLzA4Q"

    config_file = Path("./src/faultless/config")
    langfuse_config = get(value="langfuse", file=config_file / "platforms.yml")
    print(langfuse_config["secret_key"])
    llm_config = get(value="google", file=config_file / "llm.yml")

    langfuse = Langfuse(
        secret_key=langfuse_config["secret_key"],
        public_key=langfuse_config["public_key"],
        host=langfuse_config["host"],
    )

    # langfuse = Langfuse()
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

    report = open(report, "r")

    example_input = {
        "report": "In the lates newz, politic are continueing to develope rapidly across the globel. "
        "Presidant Johnson has annouced a new policey that will effected multiple countrys, "
        "sparking intence debate among internashional leders. Experts argues that the proposel could potenshally change the geopolitical landscap, "
        "but many citisen remains skeptical of its potenshial impakt. "
        "The media has been reportting on these developements with vary degrees of intensitee,"
        "leaving the publik wondering about the true significanse of these unfolding events."
    }
    response = chain.invoke(input=example_input, config={"callbacks": [langfuse_callback_handler]})

    return response.content
