# Full Plugin Example

This example shows a complete plugin that fetches weather data and stores it in the database.

## Directory structure

```
ai-mini-box-weather/
├── ai_mini_box_weather/
│   ├── __init__.py
│   ├── commands.py
│   ├── fetcher.py
│   └── help/
│       00-installation.md
│       01-commands.md
├── tests/
│   ├── __init__.py
│   ├── test_commands.py
│   └── test_fetcher.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-mini-box-weather"
version = "0.1.0"
description = "Weather plugin for ai-mini-box"
requires-python = ">=3.12"
readme = "README.md"
license = { file = "LICENSE" }
dependencies = [
    "ai-mini-box-core>=5.0.0",
    "requests>=2.31",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-mock>=3"]

[project.entry-points."ai_mini_box.tools"]
weather = "ai_mini_box_weather.commands:register"

[project.entry-points."ai_mini_box.help"]
weather = "ai_mini_box_weather"

[tool.hatch.build]
include = ["ai_mini_box_weather/**"]
```

## commands.py

```python
import typer
from loguru import logger
from ai_mini_box.infrastructure.database import get_db
from ai_mini_box.infrastructure.config import JsonConfigManager

logger.add("logs/plugin_weather.log", rotation="1 MB", retention=3)


def register(app: typer.Typer):
    weather = typer.Typer(help="Weather commands")
    app.add_typer(weather, name="weather")

    @weather.command()
    def fetch(city: str = typer.Argument(..., help="City name")):
        """Fetch weather for a city."""
        from .fetcher import get_weather
        config = JsonConfigManager().load()
        api_key = config.telegram_token  # example: reuse telegram_token field
        if not api_key:
            typer.echo("Error: api key not configured")
            raise typer.Exit(1)
        try:
            data = get_weather(city, api_key)
            typer.echo(f"Weather in {city}: {data['temp']}°C, {data['description']}")
            logger.info(f"Fetched weather for {city}: {data['temp']}°C")
        except Exception as e:
            logger.error(f"Failed to fetch weather: {e}")
            typer.echo(f"Error: {e}")
            raise typer.Exit(1)
```

## fetcher.py

```python
import requests


def get_weather(city: str, api_key: str) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "temp": data["main"]["temp"],
        "description": data["weather"][0]["description"],
    }
```

## help/00-installation.md

```markdown
# Weather Plugin

Fetches current weather data from OpenWeatherMap.

## Install

```bash
pip install ai-mini-box-weather
```

## Configure

```bash
ai-mini-box config set telegram_token "your_openweathermap_api_key"
```
```

## help/01-commands.md

```markdown
# Commands

| Command | Description |
|---|---|
| `ai-mini-box weather fetch <city>` | Fetch weather for a city |
```

## tests/test_fetcher.py

```python
import pytest
from ai_mini_box_weather.fetcher import get_weather


class TestGetWeather:
    def test_returns_temp_and_description(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {
            "main": {"temp": 22.5},
            "weather": [{"description": "clear sky"}],
        }
        mock_resp.raise_for_status.return_value = None
        mocker.patch("requests.get", return_value=mock_resp)

        result = get_weather("London", "fake_key")
        assert result["temp"] == 22.5
        assert result["description"] == "clear sky"

    def test_raises_on_network_error(self, mocker):
        mocker.patch("requests.get", side_effect=requests.ConnectionError)
        with pytest.raises(requests.ConnectionError):
            get_weather("London", "fake_key")
```

## After publishing

Users install and use:

```bash
pip install ai-mini-box-weather
ai-mini-box weather fetch Moscow
```
