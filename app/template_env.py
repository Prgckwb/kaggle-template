"""Shared Jinja2 template environment — single instance for all routers."""

from pathlib import Path

import yaml
from fastapi.templating import Jinja2Templates

from app.services.data import data_file_icon
from app.services.helpers import file_icon, human_filesize, timeago

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Filters
templates.env.filters["filesize"] = human_filesize
templates.env.filters["timeago"] = timeago
templates.env.filters["yaml_dump"] = lambda d: yaml.dump(
    d, default_flow_style=False, allow_unicode=True, sort_keys=False
)
templates.env.filters["toyaml"] = lambda d: yaml.dump(
    d, default_flow_style=False, allow_unicode=True, sort_keys=False
).rstrip()

# Globals
templates.env.globals["file_icon"] = file_icon
templates.env.globals["data_file_icon"] = data_file_icon
