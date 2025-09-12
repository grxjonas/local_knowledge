from __future__ import annotations
from typing import Literal, TypedDict
import asyncio
import os
import uuid
import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from openai import AsyncOpenAI
import base64
import logfire
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN", None)
# pydantic-ai message helpers
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    UserPromptPart,
    TextPart,
)

# load your agent (unchanged)
import clients.agent as agent_script
import importlib
importlib.reload(agent_script)
expert = agent_script.agent

if "logfire_configured" not in st.session_state:
    # programmatic configuration (or rely on env vars)
    import logfire
    logfire.configure(token="pylf_v1_eu_Ws6XwsLq0GGmwCV1pQtzPZLZbkZg6h04kLmcwsqZWxM0",
    service_name="Hypergene Local Knowledge")
    # instrument the pydantic-ai agent object you imported
    # (call after expert is loaded)
    try:
        logfire.instrument_pydantic_ai(expert)
    except Exception:
        # safe fallback if instrumentation already done or not available
        pass
    st.session_state.logfire_configured = True

# env / deps
from dotenv import load_dotenv
load_dotenv()
WHOAMI = os.getenv("WHOAMI", "BI-Consultant at Hypergene AB")
LANGUAGE = os.getenv("LANGUAGE", "ENG")


def render_svg(svg_path: str):
    with open(svg_path, "r", encoding="utf-8") as f:
        svg = f.read()
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = f'<img src="data:image/svg+xml;base64,{b64}" />'
    st.write(html, unsafe_allow_html=True)

def create_deps():
    now = datetime.datetime.now(tz=ZoneInfo("Europe/Madrid"))
    return {"name": WHOAMI, "current_time": now.isoformat()}

deps = create_deps()

# -----------------------
# Session history: keep the REAL pydantic-ai messages
# -----------------------
if "messages" not in st.session_state:
    st.session_state.messages: list[ModelMessage] = []

# -----------------------
# Render helpers (same layout)
# -----------------------
def display_message_part(part):
    if getattr(part, "part_kind", "") == "user-prompt":
        with st.chat_message("user"):
            st.markdown(part.content)
    elif getattr(part, "part_kind", "") == "text":
        with st.chat_message("assistant"):
            st.markdown(part.content)

# -----------------------
# Streaming runner — do NOT handcraft history
# -----------------------
async def run_agent_with_streaming(user_input: str, placeholder):
    logfire.trace("agent.run.start", prompt=user_input)
    history = st.session_state.messages or None

    async with expert.run_stream(
        user_input,
        deps=deps,
        message_history=history,
    ) as result:
        # IMPORTANT: use non-delta streaming so final message is added to result messages
        full_text = ""
        async for text in result.stream_text():
            full_text = text
            placeholder.markdown(full_text)

        # Replace our saved history with the authoritative messages from result
        st.session_state.messages = result.all_messages()
    logfire.trace("agent.run.end", status="ok", result_length=len(full_text))

# -----------------------
# UI (same layout)
# -----------------------
st.set_page_config(layout="wide")
with st.sidebar:
    try:
        render_svg("logo-hypergene.svg")
    except Exception:
        pass
if LANGUAGE == "SWE":
    greeting_title =f"Välkommen {WHOAMI}!"
else:
    greeting_title =f"Welcome {WHOAMI}!"

st.title(greeting_title)
# Render entire history (hide system prompts)
for msg in st.session_state.messages:
    if isinstance(msg, (ModelRequest, ModelResponse)):
        for part in msg.parts:
            # don't show system prompt parts
            if getattr(part, "part_kind", "") in {"user-prompt", "text"}:
                display_message_part(part)

if LANGUAGE == "SWE":
    input_prompt ="Fråga någonting ..."
else:
    input_prompt ="Ask something ..."
user_input = st.chat_input(input_prompt)

if user_input:
    # Show the user's message immediately (do NOT push into session history yourself)
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        spinner_html = """
        <div style="display:flex;align-items:center;gap:10px">
          <div style="width:20px;height:20px;">
            <div style="box-sizing:border-box;width:20px;height:20px;border:3px solid rgba(0,0,0,0.12);border-top-color:#0ea5e9;border-radius:50%;animation:spin 1s linear infinite;"></div>
          </div>
          <div style="font-weight:600">Thinking <span style="margin-left:6px"><span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span></div>
        </div>
        <style>
        @keyframes spin{to{transform:rotate(360deg)}}
        .dot{display:inline-block;opacity:0.25;margin:0 1px;animation:blink 1s infinite}
        .dot:nth-child(1){animation-delay:0s}
        .dot:nth-child(2){animation-delay:0.15s}
        .dot:nth-child(3){animation-delay:0.3s}
        @keyframes blink{0%,80%{opacity:0.25}40%{opacity:1}}
        </style>
        """
        placeholder.markdown(spinner_html, unsafe_allow_html=True)
        asyncio.run(run_agent_with_streaming(user_input, placeholder))
    # Create assistant placeholder and stream into it
    # with st.chat_message("assistant"):
    #     placeholder = st.empty()
    #     asyncio.run(run_agent_with_streaming(user_input, placeholder))
