import importlib.resources as importlib_resources
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

import aiofile
import aiohttp
import toml
from cryptography.fernet import Fernet

import resources
from backend.util.decorators import cache_async

log = logging.getLogger("invoice")


@cache_async
async def get_configs(config_filename="app.toml") -> Dict[str, Any]:
    _toml = Path(str(importlib_resources.files(resources))) / config_filename
    async with aiofile.async_open(str(_toml.absolute())) as file:
        return toml.loads(await file.read())


async def gen_data():
    today = datetime.today()
    adjusted_date = today.replace(day=1) - timedelta(days=1) if today.day < 20 else today
    first_day = adjusted_date.replace(day=1)
    last_day = (first_day.replace(month=first_day.month % 12 + 1, day=1) - timedelta(days=1))
    current_number = max(adjusted_date.month - datetime.fromisoformat(await get_element("reference", "start")).month + 1, 1)
    current_date = today.strftime("%b %d, %Y")
    cover_period = f"1st-{last_day.day}st {adjusted_date.strftime('%B')}"

    return {
        "number": "RC" + str(current_number).zfill(4),
        "from": await get_element("details", "from"),
        "to": await get_element("details", "bill_to"),
        "terms": await get_element("details", "terms"),
        "items": [{
            "name": await get_element("details", "description") + cover_period,
            "unit_cost": await get_element("details", "rate"),
            "quantity": 1,
        }],
        "date": current_date,
        "due_date": (today + timedelta(days=10)).strftime("%b %d, %Y"),
        "discounts": 0,
        "tax": 0,
        "shipping": 0,
        "amount_paid": 0,
    }


async def get_invoice():
    api_key = os.getenv("API")
    url = await get_element("http", "url")
    data = await gen_data()
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept-Language": "en-US",
        }
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                result = await response.read()
                log.info("PDF Retrieved successfully!")
                return result
            else:
                error_message = await response.json()
                log.info(f"Error: {error_message}")


@cache_async
async def get_os_env(var: str) -> Fernet:
    key = os.getenv(var)
    if key is None:
        raise ValueError("Could not read 'key' environment variable.")
    f = Fernet(key)
    return f


async def get_element(cat: str, subcat: str, encoding="utf-8") -> str:
    try:
        f = await get_os_env("KEY")
        configs = await get_configs()
        encrypted_value = configs.get(cat, {}).get(subcat)
        binary_str = encrypted_value.encode(encoding)
        decoded_value = f.decrypt(binary_str).decode(encoding)
        if not decoded_value or not isinstance(decoded_value, str):
            raise ValueError(f"Could not find a valid value for config with name '{cat}.{subcat}'")
        return decoded_value
    except ValueError:
        raise ValueError(f"Could not find a valid value for config with name '{cat}.{subcat}'")
