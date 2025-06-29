import streamlit as st
from agent_logic import run_langgraph_agent
from calendar_utils import is_time_slot_free, book_event_at
from dateutil.parser import isoparse
from datetime import timedelta
import json
import os

st.set_page_config(page_title="TailorTalk AI", layout="wide")

# 🧠 Chat history state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "options" not in st.session_state:
    st.session_state.options = []

if "last_input" not in st.session_state:
    st.session_state.last_input = ""

if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = []

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

if "selected_session" not in st.session_state:
    st.session_state.selected_session = None

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "calendar_available" not in st.session_state:
    st.session_state.calendar_available = None

# Function to check calendar availability
def check_calendar_availability():
    """Check if calendar service is available"""
    try:
        # Try to import and test calendar functions
        from calendar_utils import is_time_slot_free
        # Test with a simple call
        test_result = is_time_slot_free("2024-01-01T10:00:00", "2024-01-01T11:00:00")
        return True
    except Exception as e:
        st.error(f"Calendar service unavailable: {str(e)}")
        return False

# Function to create a mock booking result for demo purposes
def create_mock_booking(start_time, duration_minutes, description, invitees):
    """Create a mock booking result when calendar service is unavailable"""
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Create a mock Google Calendar link
    start_str = start_time.strftime("%Y%m%dT%H%M%S")
    end_str = end_time.strftime("%Y%m%dT%H%M%S")
    
    # Basic Google Calendar URL format
    calendar_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={description}&dates={start_str}/{end_str}"
    
    return {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "link": calendar_url,
        "description": description,
        "invitees": invitees,
        "mock": True
    }

# Function to save booking data locally (for demo/development)
def save_booking_locally(booking_data):
    """Save booking data to session state for demo purposes"""
    if "local_bookings" not in st.session_state:
        st.session_state.local_bookings = []
    
    st.session_state.local_bookings.append(booking_data)

# Check calendar availability once
if st.session_state.calendar_available is None:
    st.session_state.calendar_available = check_calendar_availability()

# Create two columns layout
col1, col2 = st.columns([1, 2])

# Left column - Chat History
with col1:
    st.markdown("### 💬 Chats")
    
    # User name input
    user_name = st.text_input("👤 Your Name:", value=st.session_state.current_user, key="user_name_input")
    if user_name != st.session_state.current_user:
        st.session_state.current_user = user_name
    
    # New Chat button
    if st.button("➕ New Chat", use_container_width=True):
        # Save current session if it has messages and user name
        if st.session_state.messages and st.session_state.current_user:
            # Only save if it's not already saved
            if st.session_state.current_session_id is None:
                session_title = f"Booking by {st.session_state.current_user}"
                session_data = {
                    "id": len(st.session_state.chat_sessions),
                    "title": session_title,
                    "messages": st.session_state.messages.copy(),
                    "user": st.session_state.current_user,
                    "timestamp": st.session_state.messages[0]["content"] if st.session_state.messages else ""
                }
                st.session_state.chat_sessions.append(session_data)
            else:
                # Update existing session
                session_idx = st.session_state.current_session_id
                if session_idx < len(st.session_state.chat_sessions):
                    st.session_state.chat_sessions[session_idx]["messages"] = st.session_state.messages.copy()
        
        # Clear current session
        st.session_state.messages = []
        st.session_state.options = []
        st.session_state.selected_session = None
        st.session_state.current_session_id = None
        st.rerun()
    
    st.markdown("---")
    
    # Display chat sessions
    if st.session_state.chat_sessions:
        for i, session in enumerate(reversed(st.session_state.chat_sessions)):
            original_index = len(st.session_state.chat_sessions) - 1 - i
            # Create a button for each chat session
            session_button_key = f"session_{original_index}"
            
            # Highlight current session
            button_style = ""
            if st.session_state.current_session_id == original_index:
                button_style = "🔵 "
            
            if st.button(
                f"{button_style}{session['title']}", 
                key=session_button_key,
                use_container_width=True,
                help=f"Messages: {len(session['messages'])} | Last: {session['timestamp'][:50]}..."
            ):
                # Load selected session
                st.session_state.messages = session["messages"].copy()
                st.session_state.current_user = session["user"]
                st.session_state.selected_session = original_index
                st.session_state.current_session_id = original_index
                st.rerun()
    else:
        st.markdown("*No previous chats. Start a new conversation!*")
    
    # Show current session indicator
    st.markdown("---")
    if st.session_state.current_session_id is not None:
        # Existing session
        current_session = st.session_state.chat_sessions[st.session_state.current_session_id]
        st.markdown(f"**Current:** {current_session['title']}")
        st.markdown(f"*Messages: {len(st.session_state.messages)}*")
    elif st.session_state.messages and st.session_state.current_user:
        # New unsaved session
        st.markdown(f"**Current:** New Booking by {st.session_state.current_user}")
        st.markdown(f"*Messages: {len(st.session_state.messages)}*")
    else:
        st.markdown("**Current:** No active session")

# Right column - Main booking area
with col2:
    st.title("🧵 TailorTalk AI - Smart Meeting Booker")
    
    # Show calendar service status
    if not st.session_state.calendar_available:
        st.warning("⚠️ Calendar service is currently unavailable. Running in demo mode - you'll get calendar links to manually add events.")
    
    st.markdown("Try: `Book a meeting next Friday at 6 PM with john@example.com`")
    
    user_input = st.text_input("What would you like to schedule?")
    
    # 📩 User input submission
    if st.button("Submit"):
        if not st.session_state.current_user.strip():
            st.error("Please enter your name first!")
            st.stop()
            
        st.session_state.options = []
        st.session_state.last_input = user_input
        st.session_state.messages.append({"role": "user", "content": user_input})

        if user_input.strip():
            with st.spinner("Understanding your request..."):
                try:
                    parsed = run_langgraph_agent(user_input)
                except Exception as e:
                    parsed = {"error": f"Agent processing error: {str(e)}"}

            if "error" in parsed:
                error_msg = f"LangGraph Error: {parsed['error']}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            else:
                start = isoparse(parsed["start_time"])
                end = isoparse(parsed["end_time"])
                invitees = parsed.get("invitees", [])

                with st.spinner("Processing booking..."):
                    try:
                        if st.session_state.calendar_available:
                            # Try real calendar booking
                            if is_time_slot_free(start.isoformat(), end.isoformat()):
                                result = book_event_at(start, 30, user_input, invitees)
                                
                                start_fmt = isoparse(result['start']).strftime("%A, %d %B %Y — %I:%M %p")
                                end_fmt = isoparse(result['end']).strftime("%I:%M %p")

                                success_msg = f"✅ Meeting booked from **{start_fmt} to {end_fmt}**. [View on Google Calendar]({result['link']})"
                                st.success("✅ Meeting booked!")
                                st.markdown(f"🕒 {start_fmt} to {end_fmt}")
                                st.markdown(f"🔗 [View on Google Calendar]({result['link']})")
                                st.session_state.messages.append({"role": "assistant", "content": success_msg})
                                
                            else:
                                st.warning("⚠️ That time slot is already booked.")
                                st.info("Here are some alternate time suggestions:")

                                st.session_state.options = [
                                    start + timedelta(hours=1),
                                    start + timedelta(hours=2),
                                    start + timedelta(hours=3)
                                ]
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": "Time is busy. Suggested options: " + ", ".join(
                                        slot.strftime("%A %I:%M %p") for slot in st.session_state.options
                                    )
                                })
                        else:
                            # Demo mode - create mock booking
                            result = create_mock_booking(start, 30, user_input, invitees)
                            save_booking_locally(result)
                            
                            start_fmt = isoparse(result['start']).strftime("%A, %d %B %Y — %I:%M %p")
                            end_fmt = isoparse(result['end']).strftime("%I:%M %p")

                            success_msg = f"✅ Meeting scheduled from **{start_fmt} to {end_fmt}**. [Add to Google Calendar]({result['link']})"
                            st.success("✅ Meeting scheduled! (Demo Mode)")
                            st.markdown(f"🕒 {start_fmt} to {end_fmt}")
                            st.markdown(f"🔗 [Add to Google Calendar]({result['link']})")
                            st.info("📝 In demo mode - click the link above to manually add this event to your calendar")
                            st.session_state.messages.append({"role": "assistant", "content": success_msg})
                            
                    except Exception as e:
                        # Fallback to demo mode if calendar fails
                        st.warning(f"Calendar service error: {str(e)}")
                        st.info("Falling back to demo mode...")
                        
                        result = create_mock_booking(start, 30, user_input, invitees)
                        save_booking_locally(result)
                        
                        start_fmt = isoparse(result['start']).strftime("%A, %d %B %Y — %I:%M %p")
                        end_fmt = isoparse(result['end']).strftime("%I:%M %p")

                        success_msg = f"✅ Meeting scheduled from **{start_fmt} to {end_fmt}**. [Add to Google Calendar]({result['link']})"
                        st.success("✅ Meeting scheduled! (Demo Mode)")
                        st.markdown(f"🕒 {start_fmt} to {end_fmt}")
                        st.markdown(f"🔗 [Add to Google Calendar]({result['link']})")
                        st.info("📝 Click the link above to manually add this event to your calendar")
                        st.session_state.messages.append({"role": "assistant", "content": success_msg})
                    
                    # Auto-save session after successful booking
                    if st.session_state.current_session_id is None:
                        session_title = f"Booking by {st.session_state.current_user}"
                        session_data = {
                            "id": len(st.session_state.chat_sessions),
                            "title": session_title,
                            "messages": st.session_state.messages.copy(),
                            "user": st.session_state.current_user,
                            "timestamp": st.session_state.messages[0]["content"] if st.session_state.messages else ""
                        }
                        st.session_state.chat_sessions.append(session_data)
                        st.session_state.current_session_id = len(st.session_state.chat_sessions) - 1
                    else:
                        # Update existing session
                        session_idx = st.session_state.current_session_id
                        if session_idx < len(st.session_state.chat_sessions):
                            st.session_state.chat_sessions[session_idx]["messages"] = st.session_state.messages.copy()

    # ⏱ Suggested time rebooking buttons
    if st.session_state.options:
        st.markdown("---")
        st.subheader("🕓 Suggested Time Slots")
        for slot in st.session_state.options:
            btn_label = slot.strftime("%A %I:%M %p")
            if st.button(btn_label):
                end = slot + timedelta(minutes=30)
                try:
                    invitees = run_langgraph_agent(st.session_state.last_input).get("invitees", [])
                except:
                    invitees = []
                
                try:
                    if st.session_state.calendar_available and is_time_slot_free(slot.isoformat(), end.isoformat()):
                        result = book_event_at(slot, 30, st.session_state.last_input, invitees)
                        
                        start_fmt = isoparse(result['start']).strftime("%A, %d %B %Y — %I:%M %p")
                        end_fmt = isoparse(result['end']).strftime("%I:%M %p")

                        confirm_msg = f"✅ Meeting rescheduled from **{start_fmt} to {end_fmt}**. [View on Google Calendar]({result['link']})"
                        st.success(f"✅ Meeting booked at {btn_label}!")
                        st.markdown(f"🕒 {start_fmt} to {end_fmt}")
                        st.markdown(f"🔗 [View on Google Calendar]({result['link']})")
                        st.session_state.messages.append({"role": "assistant", "content": confirm_msg})
                        
                    else:
                        # Demo mode or slot busy
                        if not st.session_state.calendar_available:
                            result = create_mock_booking(slot, 30, st.session_state.last_input, invitees)
                            save_booking_locally(result)
                            
                            start_fmt = isoparse(result['start']).strftime("%A, %d %B %Y — %I:%M %p")
                            end_fmt = isoparse(result['end']).strftime("%I:%M %p")

                            confirm_msg = f"✅ Meeting scheduled from **{start_fmt} to {end_fmt}**. [Add to Google Calendar]({result['link']})"
                            st.success(f"✅ Meeting scheduled at {btn_label}! (Demo Mode)")
                            st.markdown(f"🕒 {start_fmt} to {end_fmt}")
                            st.markdown(f"🔗 [Add to Google Calendar]({result['link']})")
                            st.session_state.messages.append({"role": "assistant", "content": confirm_msg})
                        else:
                            st.warning(f"Slot {btn_label} is already booked.")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"❌ {btn_label} is also booked. Try another slot."
                            })
                            continue
                    
                except Exception as e:
                    # Fallback to demo mode
                    result = create_mock_booking(slot, 30, st.session_state.last_input, invitees)
                    save_booking_locally(result)
                    
                    start_fmt = isoparse(result['start']).strftime("%A, %d %B %Y — %I:%M %p")
                    end_fmt = isoparse(result['end']).strftime("%I:%M %p")

                    confirm_msg = f"✅ Meeting scheduled from **{start_fmt} to {end_fmt}**. [Add to Google Calendar]({result['link']})"
                    st.success(f"✅ Meeting scheduled at {btn_label}! (Demo Mode)")
                    st.markdown(f"🕒 {start_fmt} to {end_fmt}")
                    st.markdown(f"🔗 [Add to Google Calendar]({result['link']})")
                    st.session_state.messages.append({"role": "assistant", "content": confirm_msg})
                
                st.session_state.options = []
                
                # Auto-save session after successful booking
                if st.session_state.current_session_id is None:
                    session_title = f"Booking by {st.session_state.current_user}"
                    session_data = {
                        "id": len(st.session_state.chat_sessions),
                        "title": session_title,
                        "messages": st.session_state.messages.copy(),
                        "user": st.session_state.current_user,
                        "timestamp": st.session_state.messages[0]["content"] if st.session_state.messages else ""
                    }
                    st.session_state.chat_sessions.append(session_data)
                    st.session_state.current_session_id = len(st.session_state.chat_sessions) - 1
                else:
                    # Update existing session
                    session_idx = st.session_state.current_session_id
                    if session_idx < len(st.session_state.chat_sessions):
                        st.session_state.chat_sessions[session_idx]["messages"] = st.session_state.messages.copy()
                break

    # Display chat history in the main area
    if st.session_state.messages:
        st.markdown("---")
        st.subheader("💬 Conversation History")
        
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                # User message with better styling
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 12px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #4CAF50; color: #1a1a1a;">
                    <strong style="color: #2d5016;">🧑‍💼 You:</strong><br>
                    <span style="color: #333333; font-size: 14px;">{message['content']}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Assistant message with enhanced formatting
                content = message['content']
                
                # Check if it's a booking confirmation message
                if "✅ Meeting booked" in content or "✅ Meeting scheduled" in content:
                    # Extract the calendar link
                    import re
                    link_match = re.search(r'\[(?:View on Google Calendar|Add to Google Calendar)\]\((https?://[^\)]+)\)', content)
                    calendar_link = link_match.group(1) if link_match else "#"
                    
                    # Extract booking details
                    details = content.split('**')[1] if '**' in content else 'Meeting scheduled'
                    
                    # Determine if it's demo mode
                    is_demo = "Add to Google Calendar" in content
                    demo_text = " (Demo Mode)" if is_demo else ""
                    action_text = "Add to" if is_demo else "View on"
                    
                    # Format as a booking confirmation card
                    st.markdown(f"""
                    <div style="background-color: #e8f5e8; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #4CAF50; color: #1a1a1a;">
                        <strong style="color: #2d5016;">🤖 TailorTalk AI:</strong><br>
                        <div style="margin-top: 8px;">
                            <span style="color: #155724; font-weight: bold;">✅ Meeting Successfully Scheduled{demo_text}!</span><br>
                            <span style="color: #333333;"><strong>📅 Time:</strong> {details}</span><br>
                            <a href="{calendar_link}" target="_blank" style="color: #1976d2; text-decoration: none; font-weight: bold;">
                                🔗 {action_text} Google Calendar →
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif "Time is busy" in content or "Suggested options" in content:
                    # Format as a suggestion message
                    st.markdown(f"""
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #ffc107; color: #1a1a1a;">
                        <strong style="color: #856404;">🤖 TailorTalk AI:</strong><br>
                        <div style="margin-top: 8px;">
                            <span style="color: #856404; font-weight: bold;">⚠️ Time Conflict Detected</span><br>
                            <span style="color: #333333; font-size: 14px;">{content}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif "Error" in content:
                    # Format error messages
                    st.markdown(f"""
                    <div style="background-color: #f8d7da; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #dc3545; color: #1a1a1a;">
                        <strong style="color: #721c24;">🤖 TailorTalk AI:</strong><br>
                        <div style="margin-top: 8px;">
                            <span style="color: #721c24; font-weight: bold;">❌ Error:</span><br>
                            <span style="color: #333333; font-size: 14px;">{content}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    # Regular assistant message
                    st.markdown(f"""
                    <div style="background-color: #e3f2fd; padding: 12px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #2196F3; color: #1a1a1a;">
                        <strong style="color: #0d47a1;">🤖 TailorTalk AI:</strong><br>
                        <div style="margin-top: 8px;">
                            <span style="color: #333333; font-size: 14px;">{content}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Show local bookings in demo mode
    if not st.session_state.calendar_available and "local_bookings" in st.session_state and st.session_state.local_bookings:
        st.markdown("---")
        st.subheader("📋 Your Scheduled Meetings (Demo Mode)")
        
        for i, booking in enumerate(st.session_state.local_bookings):
            start_fmt = isoparse(booking['start']).strftime("%A, %d %B %Y — %I:%M %p")
            end_fmt = isoparse(booking['end']).strftime("%I:%M %p")
            
            with st.expander(f"Meeting {i+1}: {start_fmt}"):
                st.write(f"**Time:** {start_fmt} to {end_fmt}")
                st.write(f"**Description:** {booking['description']}")
                if booking['invitees']:
                    st.write(f"**Invitees:** {', '.join(booking['invitees'])}")
                st.markdown(f"[Add to Google Calendar]({booking['link']})")

# Add some custom CSS for better styling
st.markdown("""
<style>
.stColumn:first-child {
    padding-right: 2rem;
    border-right: 1px solid #e6e6e6;
}
.stColumn:last-child {
    padding-left: 2rem;
}
</style>
""", unsafe_allow_html=True)
