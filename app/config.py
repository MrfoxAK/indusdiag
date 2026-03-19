"""
config.py
Central configuration loaded from environment variables via .env
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- OpenRouter (default LLM backend) ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-3.5-turbo"
)

# --- Anthropic Claude (optional, used with --claude flag) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv(
    "ANTHROPIC_MODEL",
    "claude-sonnet-4-20250514"
)

# --- Agent settings ---
MEMORY_FILE = os.getenv("MEMORY_FILE", "data/memory/agent_memory.json")
SYSTEM_PROMPT_PATH = os.getenv("SYSTEM_PROMPT_PATH", "prompts/system_prompt.txt")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
