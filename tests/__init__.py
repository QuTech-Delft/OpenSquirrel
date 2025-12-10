import json
import pathlib

PROJECT_ROOT_PATH = pathlib.Path(__file__).parents[1]

with pathlib.Path(PROJECT_ROOT_PATH / "data" / "static.json").open("r") as f:
    STATIC_DATA = json.load(f)
