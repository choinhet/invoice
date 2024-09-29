import logging
from functools import wraps

import streamlit as st

log = logging.getLogger("invoice")


def cache_async(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        name = func.__name__ + "".join(sorted(str(args))) + "".join(sorted(str(kwargs)))
        if name in st.session_state:
            log.info(f"Getting result from function '{func.__name__}' from cache.")
            return st.session_state.get(name)
        result = await func(*args, **kwargs)
        st.session_state[name] = result
        log.info(f"Adding result from function '{func.__name__}' to cache.")
        return result

    return wrapper
