# backend/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# ✅ Correct relative imports inside backend/
from .services.agent_logic import run_langgraph_agent
from .services.calendar_utils import is_time_slot_free, book_event_at

from dateutil.parser import isoparse
from datetime import timedelta

app = FastAPI(title="TailorTalk AI API")

# Allow all origins for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 Input Model
class BookingRequest(BaseModel):
    user_input: str

# 📦 Output Model
class BookingResponse(BaseModel):
    success: bool
    message: str
    start_time: str = None
    end_time: str = None
    calendar_link: str = None


@app.post("/book", response_model=BookingResponse)
def book_meeting(request: BookingRequest):
    parsed = run_langgraph_agent(request.user_input)

    if "error" in parsed:
        raise HTTPException(status_code=400, detail=parsed["error"])

    try:
        start = isoparse(parsed["start_time"])
        end = isoparse(parsed["end_time"])
        invitees = parsed.get("invitees", [])

        if not is_time_slot_free(start.isoformat(), end.isoformat()):
            return BookingResponse(
                success=False,
                message="Time slot is already booked. Try another.",
            )

        result = book_event_at(start, 30, request.user_input, invitees)

        return BookingResponse(
            success=True,
            message="Meeting booked successfully!",
            start_time=result["start"],
            end_time=result["end"],
            calendar_link=result["link"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
