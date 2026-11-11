import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def get_groq_client() -> Groq:
    """Initialize Groq client using Streamlit secrets or local .env file."""
    api_key = None
    try:
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Add it to .streamlit/secrets.toml or your .env file."
        )

    return Groq(api_key=api_key)
