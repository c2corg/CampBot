# CampBot

[![PyPI version](https://badge.fury.io/py/campbot.svg)](https://pypi.org/project/campbot/) 
[![Build](https://github.com/c2corg/CampBot/workflows/build/badge.svg)](https://github.com/c2corg/CampBot/actions)
[![Documentation Status](https://readthedocs.org/projects/campbot/badge/?version=latest)](https://campbot.readthedocs.io/en/latest/?badge=latest)
 

Bot framework for [camptocamp.org](https://www.camptocamp.org/)

## Installation

```batch
pip install campbot
```

## Name your tool

Every request sends a `User-Agent` header like
`CampBot/2.2.0 (+https://github.com/c2corg/CampBot)`.
If you build a tool on CampBot, put its name first:

```python
from campbot import CampBot

bot = CampBot(user_agent="MyTool/1.2 (+https://example.org/mytool)")
# User-Agent: MyTool/1.2 (+https://example.org/mytool) CampBot/2.2.0 (+https://github.com/c2corg/CampBot)
```

On the command line, use `--user-agent=MyTool/1.2`.

The camptocamp.org team can then tell your traffic apart from other CampBot users,
and contact you rather than block it if something goes wrong.

## Contribute

```batch
git clone git@github.com:c2corg/CampBot.git
cd CampBot
pip install -r requirements.txt -r dev-requirements.txt black==19.10b0
pytest --cov=campbot --cov-report=html
```

Before commit, check your format with `black campbot` :pray:

## Documentation

[Read the docs!](https://campbot.readthedocs.io/)