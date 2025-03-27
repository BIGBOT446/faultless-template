from pathlib import Path

import requests

from base.utils.config import get as get_config

# Step 1: Load Configuration
config_file = Path("./src/faultless/config")
onlyoffice_config = get_config(value="onlyoffice", file=config_file / "platforms.yml")
address = onlyoffice_config.get("address")
port = onlyoffice_config.get("port")

url = f"{address}:{port}"


def verify_server(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raises an error for 4xx/5xx responses
        print(f"Server at {url} is operational. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Server at {url} did not respond as expected.")
        print("Error:", e)


if __name__ == "__main__":
    verify_server(url)
