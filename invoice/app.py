import asyncio
import logging
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from rich.logging import RichHandler

from backend.simple import get_invoice, get_element

# Set page configuration
st.set_page_config("Invoice Generator", "🌎", "wide")


# Simple login system
async def login():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    _login = await get_element("auth", "username")
    _pass = await get_element("auth", "password")
    if st.sidebar.button("Login"):
        if username == _login and password == _pass:
            return True
        else:
            st.sidebar.error("Invalid username or password")
            return False
    return False


async def main():
    if await login():  # Only run if logged in
        result = await get_invoice()
        today = datetime.today().date().isoformat()
        st.download_button(
            label="Download Invoice",
            use_container_width=True,
            data=result,  # pyright: ignore [reportArgumentType]
            file_name=f"Rafael_Choinhet_Invoice_{today}.pdf",
            mime="application/pdf",
        )


if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
    asyncio.run(main())
