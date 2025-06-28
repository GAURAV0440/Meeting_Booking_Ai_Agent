# TailorTalk AI – Smart Calendar Booking Assistant

TailorTalk is a conversational AI tool that helps you book Google Calendar meetings using natural language. Just type something like “Book a meeting next Friday at 6 PM with john@example.com” — and it takes care of the rest!

---

## Features

- Understands natural language like “tomorrow afternoon”
- Checks your Google Calendar availability
- Suggests alternate times if the slot is busy
- Books meetings and gives a Google Calendar link
- Chat-style UI with session history
- FastAPI backend and Streamlit frontend

---

## How to Run the Project

### 1. Clone the repo and install dependencies
pip install -r requirements.txt

### 2. Setup your .env file in the root folder
Create a .env file with:
GOOGLE_CLIENT_ID=xxxxxxxxxxxxxxxxxx.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxxxxxxxxxXEABKIHzJKEbHDtZXwExf3K
GOOGLE_REDIRECT_URI=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SCOPES=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AxxxxxxxxxxxxxxxU78OWgLJysD3TRlXqXDER8

Also add your credentials.json from Google Cloud Console (OAuth credentials).

### 3. Run the backend (FastAPI)
uvicorn backend.main:app --reload
API will be live at: http://127.0.0.1:8000/docs

### 4. Run the frontend (Streamlit)
streamlit run streamlit_app.py
Streamlit will open in your browser at: http://localhost:8501


### Sample Input Examples
Try phrases like:

Book a meeting this Friday at 4 PM with john@example.com

Schedule a call next Monday between 3 to 5 PM

Do you have free time tomorrow afternoon?


### Folder Structure
TailorTalk/
├── backend/
│   ├── main.py
│   └── services/
│       ├── agent_logic.py
│       ├── calendar_utils.py
│       └── gemini_chain.py
├── streamlit_app.py
├── requirements.txt
├── credentials.json
├── .env (not shared)


### Notes
Don’t forget to authenticate with Google Calendar at least once to generate token.pkl
Do not share your .env or credentials.json in public
