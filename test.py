from rich.console import Console
from time import sleep
import json

with open("config.json", "r") as config:
    _config = json.load(config)


console = Console()
with console.status("Initial status") as status:
    modules = []
    for key in _config['enabledModules']:
        if _config['enabledModules'][key] == 1:
            modules.append(key)
    for stat in modules:
        status.update(f"Loading {stat}...")
        sleep(0.5)