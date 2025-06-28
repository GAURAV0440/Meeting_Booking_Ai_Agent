# backend/services/gemini_chain.py

import os
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()


# 🔐 Validate that the Gemini API key is set
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise EnvironmentError("❌ GEMINI_API_KEY not found in .env file or environment variables.")

# ✅ Configure Gemini LLM via API key
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=api_key,
    temperature=0.4,
)

# 💬 Prompt template to extract structured calendar data
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a calendar agent. Extract structured info from user input.

Return JSON like:
{{
  "start_time": "YYYY-MM-DDTHH:MM:SS",
  "end_time": "YYYY-MM-DDTHH:MM:SS",
  "invitees": ["email1@example.com", "email2@example.com"]
}}

Meeting is 30 minutes. Today is {today}."""),

    ("user", "{input}")
])

# 🔗 Combine prompt → Gemini model → parser
chain = prompt | llm | StrOutputParser()

# ✅ Entry point: Call this from agent_logic
def run_gemini_chain(user_text: str) -> str:
    today = datetime.now().strftime("%A, %Y-%m-%d")
    return chain.invoke({"input": user_text, "today": today})
