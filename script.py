"""
Autonomous Digital Executive Assistant for Scheduling using LangGraph
ENHANCED VERSION with Voice I/O, Google Calendar, Conflict Detection, and Chat Memory
FIXED: List meetings functionality
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from typing import TypedDict, Annotated, Sequence
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
import operator
from dotenv import load_dotenv

# Voice I/O imports
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_ENABLED = True
except ImportError:
    VOICE_ENABLED = False
    print("⚠️  Voice features disabled. Install: pip install SpeechRecognition pyttsx3 pyaudio")

# Google Calendar imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_CALENDAR_ENABLED = True
    SCOPES = ['https://www.googleapis.com/auth/calendar']
except ImportError:
    GOOGLE_CALENDAR_ENABLED = False
    print("⚠️  Google Calendar disabled. Install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

load_dotenv()


# ============================================================================
# VOICE I/O MODULE
# ============================================================================

class VoiceAssistant:
    """Handle voice input and output"""

    def __init__(self):
        self.enabled = VOICE_ENABLED
        if self.enabled:
            self.recognizer = sr.Recognizer()
            self.engine = pyttsx3.init()
            self.setup_voice()

    def setup_voice(self):
        """Configure voice settings"""
        if not self.enabled:
            return

        # Set voice properties
        voices = self.engine.getProperty('voices')
        # Try to use a female voice if available
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break

        self.engine.setProperty('rate', 175)  # Speed
        self.engine.setProperty('volume', 0.9)  # Volume

    def listen(self, prompt="🎤 Listening...", timeout=5):
        """Listen for voice input"""
        if not self.enabled:
            return None

        print(prompt)

        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)

                # Recognize speech using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                print(f"🎤 You said: {text}")
                return text

        except sr.WaitTimeoutError:
            print("⏱️  No speech detected")
            return None
        except sr.UnknownValueError:
            print("❌ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return None
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            return None

    def speak(self, text):
        """Convert text to speech"""
        if not self.enabled:
            return

        print(f"🔊 Assistant: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"⚠️  Speech output error: {e}")


# ============================================================================
# GOOGLE CALENDAR MODULE
# ============================================================================

class GoogleCalendarManager:
    """Manage Google Calendar integration"""

    def __init__(self):
        self.enabled = GOOGLE_CALENDAR_ENABLED
        self.service = None

        if self.enabled:
            self.authenticate()

    def authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None

        # Token file stores user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    print("⚠️  credentials.json not found. Google Calendar disabled.")
                    print("   Download from: https://console.cloud.google.com/apis/credentials")
                    self.enabled = False
                    return

            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        try:
            self.service = build('calendar', 'v3', credentials=creds)
            print("✅ Google Calendar connected")
        except Exception as e:
            print(f"⚠️  Google Calendar connection failed: {e}")
            self.enabled = False

    def get_events(self, time_min=None, time_max=None, max_results=10):
        """Get events from Google Calendar"""
        if not self.enabled or not self.service:
            return []

        try:
            if not time_min:
                time_min = datetime.utcnow().isoformat() + 'Z'
            elif isinstance(time_min, str) and 'Z' not in time_min and '+' not in time_min:
                # Add Z for UTC if no timezone specified
                time_min = time_min + 'Z'

            if time_max and isinstance(time_max, str) and 'Z' not in time_max and '+' not in time_max:
                time_max = time_max + 'Z'

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            return events_result.get('items', [])

        except HttpError as e:
            print(f"⚠️  Error fetching events: {e}")
            return []
        except Exception as e:
            print(f"⚠️  Unexpected error: {e}")
            return []

    def create_event(self, summary, start_time, end_time, attendees=None, location=None, description=None):
        """Create event in Google Calendar"""
        if not self.enabled or not self.service:
            return None

        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Los_Angeles',
            }
        }

        if attendees:
            event['attendees'] = [{'email': email} for email in attendees if '@' in email]

        if location:
            event['location'] = location

        if description:
            event['description'] = description

        try:
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            return event
        except HttpError as e:
            print(f"⚠️  Error creating event: {e}")
            return None

    def delete_event(self, event_id):
        """Delete event from Google Calendar"""
        if not self.enabled or not self.service:
            return False

        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return True
        except HttpError as e:
            print(f"⚠️  Error deleting event: {e}")
            return False

    def update_event(self, event_id, updates):
        """Update event in Google Calendar"""
        if not self.enabled or not self.service:
            return None

        try:
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            event.update(updates)
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            return updated_event
        except HttpError as e:
            print(f"⚠️  Error updating event: {e}")
            return None


# ============================================================================
# CHAT MEMORY MODULE
# ============================================================================

class ChatMemory:
    """Persistent chat memory system"""

    def __init__(self, memory_file="chat_memory.json"):
        self.memory_file = memory_file
        self.load_memory()

    def load_memory(self):
        """Load chat history from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    self.data = json.load(f)
            except:
                self.data = self.create_empty_memory()
        else:
            self.data = self.create_empty_memory()

    def create_empty_memory(self):
        """Create empty memory structure"""
        return {
            "conversations": [],
            "context": {
                "last_participant": None,
                "last_meeting_time": None,
                "last_duration": 30,
                "preferred_platform": "Meeting",
                "user_preferences": {}
            },
            "created_at": datetime.now().isoformat()
        }

    def save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save memory: {e}")

    def add_conversation(self, user_input, assistant_response, intent, metadata=None):
        """Add conversation to history"""
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "assistant": assistant_response,
            "intent": intent,
            "metadata": metadata or {}
        }

        self.data["conversations"].append(conversation)

        # Keep only last 50 conversations
        if len(self.data["conversations"]) > 50:
            self.data["conversations"] = self.data["conversations"][-50:]

        self.save_memory()

    def update_context(self, **kwargs):
        """Update context information"""
        self.data["context"].update(kwargs)
        self.save_memory()

    def get_context(self, key):
        """Get context value"""
        return self.data["context"].get(key)

    def get_recent_conversations(self, n=5):
        """Get recent conversations"""
        return self.data["conversations"][-n:]

    def clear_memory(self):
        """Clear all memory"""
        self.data = self.create_empty_memory()
        self.save_memory()


# ============================================================================
# CONFLICT DETECTION MODULE
# ============================================================================

class ConflictDetector:
    """Detect and resolve scheduling conflicts"""

    @staticmethod
    def detect_conflicts(new_start, new_end, existing_events):
        """Detect if new event conflicts with existing events"""
        conflicts = []

        # Parse and normalize datetime objects
        if isinstance(new_start, str):
            new_start_dt = datetime.fromisoformat(new_start.replace('Z', '+00:00'))
        else:
            new_start_dt = new_start

        if isinstance(new_end, str):
            new_end_dt = datetime.fromisoformat(new_end.replace('Z', '+00:00'))
        else:
            new_end_dt = new_end

        # Make timezone-naive if needed (remove timezone info for comparison)
        if new_start_dt.tzinfo is not None:
            new_start_dt = new_start_dt.replace(tzinfo=None)
        if new_end_dt.tzinfo is not None:
            new_end_dt = new_end_dt.replace(tzinfo=None)

        for event in existing_events:
            # Handle both dict and Google Calendar event formats
            if isinstance(event, dict):
                if 'start' in event and isinstance(event['start'], dict) and 'dateTime' in event['start']:
                    # Google Calendar format
                    event_start_str = event['start']['dateTime'].replace('Z', '+00:00')
                    event_end_str = event['end']['dateTime'].replace('Z', '+00:00')
                    event_start = datetime.fromisoformat(event_start_str)
                    event_end = datetime.fromisoformat(event_end_str)
                else:
                    # Local format
                    event_start = datetime.fromisoformat(event.get('start_time', event.get('start', '')))
                    event_end = datetime.fromisoformat(event.get('end_time', event.get('end', '')))

                # Make timezone-naive for comparison
                if event_start.tzinfo is not None:
                    event_start = event_start.replace(tzinfo=None)
                if event_end.tzinfo is not None:
                    event_end = event_end.replace(tzinfo=None)

                # Check for overlap
                if (new_start_dt < event_end and new_end_dt > event_start):
                    conflicts.append(event)

        return conflicts

    @staticmethod
    def suggest_alternatives(conflicts, duration_minutes, date):
        """Suggest alternative times when conflicts exist"""
        suggestions = []

        # Ensure date is timezone-naive
        if date.tzinfo is not None:
            date = date.replace(tzinfo=None)

        # Try slots throughout the day
        start_hour = 9
        end_hour = 17

        current_time = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)

        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=duration_minutes)

            # Check if this slot conflicts
            test_conflicts = ConflictDetector.detect_conflicts(
                current_time.isoformat(),
                slot_end.isoformat(),
                conflicts
            )

            if not test_conflicts:
                suggestions.append({
                    "start": current_time.isoformat(),
                    "end": slot_end.isoformat(),
                    "start_display": current_time.strftime("%I:%M %p"),
                    "end_display": slot_end.strftime("%I:%M %p")
                })

            current_time += timedelta(minutes=30)

            # Return first 3 alternatives
            if len(suggestions) >= 3:
                break

        return suggestions


# ============================================================================
# INITIALIZE MODULES
# ============================================================================

voice_assistant = VoiceAssistant()
google_calendar = GoogleCalendarManager()
chat_memory = ChatMemory()


# ============================================================================
# STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """State for the scheduling assistant agent"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_request: str
    intent: str
    participants: list[str]
    duration: int
    preferred_time: str
    date_info: str
    platform: str
    timezone: str
    available_slots: list[dict]
    selected_slot: dict
    meeting_created: bool
    meetings_list: list[dict]
    meeting_to_modify: dict
    conflicts: list[dict]
    alternative_slots: list[dict]
    loop_count: int
    next_action: str
    needs_clarification: bool
    missing_info: list[str]
    clarification_response: str
    google_event_id: str
    use_voice: bool


# ============================================================================
# CALENDAR DATA STORE (Local backup)
# ============================================================================

class CalendarStore:
    """Local calendar data store with conflict detection"""

    def __init__(self, calendar_file: str = "events.json"):
        self.calendar_file = calendar_file
        self.load_calendar()

    def load_calendar(self):
        """Load calendar from JSON file"""
        if os.path.exists(self.calendar_file):
            try:
                with open(self.calendar_file, 'r') as f:
                    self.data = json.load(f)
                if "users" not in self.data:
                    self.data["users"] = {}
                if "meetings" not in self.data:
                    self.data["meetings"] = []
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️  Warning: Invalid JSON in {self.calendar_file}. Creating new file.")
                if os.path.exists(self.calendar_file):
                    backup_name = f"{self.calendar_file}.backup"
                    os.rename(self.calendar_file, backup_name)
                self.data = self.create_empty_calendar()
                self.save_calendar()
        else:
            self.data = self.create_empty_calendar()
            self.save_calendar()

    def create_empty_calendar(self):
        """Create empty calendar structure"""
        return {
            "users": {
                "current_user": {
                    "name": "You",
                    "timezone": "PST",
                    "busy_slots": []
                }
            },
            "meetings": []
        }

    def save_calendar(self):
        """Save calendar to JSON file"""
        try:
            with open(self.calendar_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Could not save calendar: {str(e)}")

    def get_user_availability(self, user: str, date: datetime):
        """Get available slots for a user"""
        user_key = user.lower().replace(" ", "_")

        if user_key not in self.data["users"]:
            self.data["users"][user_key] = {
                "name": user,
                "busy_slots": []
            }
            self.save_calendar()

        busy_slots = self.data["users"][user_key]["busy_slots"]
        return {
            "user": user,
            "date": date.isoformat(),
            "busy_slots": busy_slots
        }

    def add_meeting(self, participants: list[str], start_time: str, end_time: str, title: str, platform: str = "Meeting", google_event_id: str = None):
        """Add a meeting with conflict detection"""
        # Check for conflicts
        conflicts = ConflictDetector.detect_conflicts(start_time, end_time, self.data["meetings"])

        meeting = {
            "id": len(self.data["meetings"]) + 1,
            "title": title,
            "participants": participants,
            "start_time": start_time,
            "end_time": end_time,
            "platform": platform,
            "google_event_id": google_event_id,
            "created_at": datetime.now().isoformat(),
            "conflicts": len(conflicts) > 0
        }

        self.data["meetings"].append(meeting)

        # Add to busy slots
        for participant in participants:
            user_key = participant.lower().replace(" ", "_")
            if user_key in self.data["users"]:
                self.data["users"][user_key]["busy_slots"].append({
                    "start": start_time,
                    "end": end_time
                })

        self.save_calendar()
        return meeting, conflicts

    def get_meetings(self, date_filter: str = None):
        """Get all meetings with optional date filter - FIXED VERSION"""
        meetings = self.data["meetings"]

        if not date_filter:
            return meetings

        # Parse date filter
        date_filter_lower = date_filter.lower().strip()
        target_date = None

        if date_filter_lower == "today":
            target_date = datetime.now().date()
        elif date_filter_lower in ["tomorrow", "tmrw"]:
            target_date = (datetime.now() + timedelta(days=1)).date()
        elif date_filter_lower == "this week":
            # Return all meetings in the next 7 days
            today = datetime.now().date()
            filtered = []
            for meeting in meetings:
                try:
                    meeting_date = datetime.fromisoformat(meeting["start_time"]).date()
                    days_diff = (meeting_date - today).days
                    if 0 <= days_diff <= 7:
                        filtered.append(meeting)
                except (ValueError, KeyError) as e:
                    print(f"⚠️  Skipping invalid meeting entry: {e}")
                    continue
            return filtered
        else:
            # Try to parse as a specific date
            try:
                target_date = datetime.fromisoformat(date_filter).date()
            except:
                # Invalid date format, return all meetings
                return meetings

        # Filter by target date
        if target_date:
            filtered = []
            for meeting in meetings:
                try:
                    # Handle timezone-aware and naive datetimes
                    start_time_str = meeting["start_time"]
                    if 'Z' in start_time_str or '+' in start_time_str:
                        # Timezone-aware
                        meeting_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        meeting_date = meeting_dt.date()
                    else:
                        # Naive datetime
                        meeting_date = datetime.fromisoformat(start_time_str).date()

                    if meeting_date == target_date:
                        filtered.append(meeting)
                except (ValueError, KeyError) as e:
                    print(f"⚠️  Skipping invalid meeting entry: {e}")
                    continue
            return filtered

        return meetings

    def update_meeting(self, meeting_id: int, updates: dict):
        """Update a meeting"""
        for meeting in self.data["meetings"]:
            if meeting["id"] == meeting_id:
                meeting.update(updates)
                self.save_calendar()
                return meeting
        return None

    def delete_meeting(self, meeting_id: int):
        """Delete a meeting"""
        self.data["meetings"] = [m for m in self.data["meetings"] if m["id"] != meeting_id]
        self.save_calendar()
        return True


calendar_store = CalendarStore()


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

@tool
def find_available_slots_with_conflicts(participants: list[str], duration_minutes: int, date_str: str, preferred_time: str = "afternoon") -> str:
    """Find available slots with conflict detection"""
    from datetime import timedelta
    import re

    # Parse date
    date = None
    date_str_lower = date_str.lower().strip()

    if date_str_lower in ["tomorrow", "tmrw", "tommorow"]:
        date = datetime.now() + timedelta(days=1)
    elif date_str_lower in ["today", "2day"]:
        date = datetime.now()
    elif "next" in date_str_lower or "this" in date_str_lower:
        days_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        for day_name, day_num in days_map.items():
            if day_name in date_str_lower:
                current_day = datetime.now().weekday()
                days_ahead = day_num - current_day

                if "next" in date_str_lower:
                    if days_ahead <= 0:
                        days_ahead += 7
                elif "this" in date_str_lower:
                    if days_ahead < 0:
                        days_ahead += 7

                date = datetime.now() + timedelta(days=days_ahead)
                break

    if date is None:
        date = datetime.now() + timedelta(days=1)

    # Get existing meetings (local + Google Calendar)
    all_meetings = calendar_store.get_meetings()

    if google_calendar.enabled:
        time_min = date.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        time_max = date.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        google_events = google_calendar.get_events(time_min=time_min, time_max=time_max)
        all_meetings.extend(google_events)

    # Parse time
    preferred_time_lower = preferred_time.lower().strip()
    time_match = re.search(r'(\d{1,2}):?(\d{2})?(?:\s*)?([ap]m?)?', preferred_time_lower)

    if time_match or "o'clock" in preferred_time_lower:
        if "o'clock" in preferred_time_lower:
            hour_match = re.search(r'(\d{1,2})', preferred_time_lower)
            hour = int(hour_match.group(1)) if hour_match else 14
            minute = 0

            if 'pm' in preferred_time_lower and hour < 12:
                hour += 12
            elif 'am' in preferred_time_lower and hour == 12:
                hour = 0
            elif hour < 8:  # Assume PM for single digit hours < 8
                hour += 12
        elif time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(3)

            # Convert to 24-hour format
            if meridiem:
                if 'p' in meridiem and hour < 12:
                    hour += 12
                elif 'a' in meridiem and hour == 12:
                    hour = 0
            else:
                # No AM/PM specified - use context
                if hour < 8:  # Early hours without AM/PM -> assume PM
                    hour += 12
                elif hour >= 8 and hour <= 11:  # 8-11 without AM/PM -> could be either, assume AM
                    pass  # Keep as is
                # hour >= 12 -> already in 24-hour format
        else:
            hour = 14
            minute = 0

        # For specific time requests, search exactly at that time
        # Not before or after - the user wants 5pm, give them 5pm
        start_hour = hour
        end_hour = hour + 1  # Just check the requested hour
    else:
        time_ranges = {
            "morning": (9, 12),
            "afternoon": (12, 17),
            "evening": (17, 20)
        }
        start_hour, end_hour = time_ranges.get(preferred_time_lower, (9, 17))

    # Generate slots
    available_slots = []
    current_time = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end_time = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)

    while current_time < end_time:
        slot_end = current_time + timedelta(minutes=duration_minutes)

        # Check for conflicts
        conflicts = ConflictDetector.detect_conflicts(
            current_time.isoformat(),
            slot_end.isoformat(),
            all_meetings
        )

        if not conflicts:
            available_slots.append({
                "start": current_time.isoformat(),
                "end": slot_end.isoformat(),
                "start_display": current_time.strftime("%I:%M %p"),
                "end_display": slot_end.strftime("%I:%M %p"),
                "date_display": current_time.strftime("%A, %B %d")
            })

        current_time += timedelta(minutes=30)

    return json.dumps({"available_slots": available_slots[:5]}, indent=2)


@tool
def create_meeting_with_sync(participants: list[str], start_time: str, end_time: str, title: str, platform: str = "Meeting") -> str:
    """Create meeting in both local storage and Google Calendar"""

    google_event_id = None

    # Create in Google Calendar if enabled
    if google_calendar.enabled:
        attendees = [p for p in participants if '@' in p]
        google_event = google_calendar.create_event(
            summary=title,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees if attendees else None,
            description=f"Platform: {platform}"
        )

        if google_event:
            google_event_id = google_event.get('id')
            print(f"   ✅ Synced to Google Calendar")

    # Create in local storage with conflict detection
    meeting, conflicts = calendar_store.add_meeting(
        participants, start_time, end_time, title, platform, google_event_id
    )

    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time)
    duration = int((end_dt - start_dt).total_seconds() / 60)

    result = {
        "success": True,
        "meeting": {
            "id": meeting["id"],
            "title": title,
            "participants": participants,
            "date": start_dt.strftime("%A, %B %d, %Y"),
            "time": f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}",
            "duration": duration,
            "platform": platform,
            "google_synced": google_event_id is not None,
            "conflicts": len(conflicts)
        }
    }

    if conflicts:
        result["conflicts_detected"] = [
            {
                "title": c.get("title", c.get("summary", "Unknown")),
                "time": c.get("start_time", c.get("start", {}).get("dateTime", "Unknown"))
            }
            for c in conflicts
        ]

    return json.dumps(result, indent=2)


@tool
def list_meetings_with_sync(date_filter: str = None) -> str:
    """List meetings from both local and Google Calendar - FIXED VERSION"""

    # Get local meetings with improved date filtering
    local_meetings = calendar_store.get_meetings(date_filter)

    all_meetings = []
    google_event_ids = set()  # Track Google Calendar IDs to prevent duplicates

    # Add local meetings
    for meeting in local_meetings:
        try:
            start_time_str = meeting["start_time"]
            end_time_str = meeting["end_time"]

            # Handle timezone-aware and naive datetimes
            if 'Z' in start_time_str or '+' in start_time_str:
                start = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                # Remove timezone for display
                if start.tzinfo:
                    start = start.replace(tzinfo=None)
                if end.tzinfo:
                    end = end.replace(tzinfo=None)
            else:
                start = datetime.fromisoformat(start_time_str)
                end = datetime.fromisoformat(end_time_str)

            all_meetings.append({
                "id": meeting["id"],
                "time": f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}",
                "date": start.strftime("%A, %B %d, %Y"),
                "title": meeting["title"],
                "participants": meeting.get("participants", []),
                "platform": meeting.get("platform", "Meeting"),
                "source": "local",
                "sort_key": start
            })

            # Track Google event IDs that are already in local storage
            if meeting.get("google_event_id"):
                google_event_ids.add(meeting["google_event_id"])

        except (ValueError, KeyError) as e:
            print(f"⚠️  Skipping invalid local meeting: {e}")
            continue

    # Add Google Calendar meetings if enabled
    if google_calendar.enabled:
        try:
            # Determine date range based on filter
            if date_filter:
                date_filter_lower = date_filter.lower().strip()

                if date_filter_lower == "today":
                    date = datetime.now()
                elif date_filter_lower in ["tomorrow", "tmrw"]:
                    date = datetime.now() + timedelta(days=1)
                elif date_filter_lower == "this week":
                    # Get all events for the next 7 days
                    date = datetime.now()
                    time_min = date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
                    time_max = (date + timedelta(days=7)).replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + 'Z'
                    google_events = google_calendar.get_events(time_min=time_min, time_max=time_max, max_results=50)
                else:
                    # Try to use the filter as is
                    date = datetime.now()

                if date_filter_lower != "this week":
                    # Create timezone-aware UTC times for Google Calendar API
                    time_min = date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
                    time_max = date.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + 'Z'
                    google_events = google_calendar.get_events(time_min=time_min, time_max=time_max)
            else:
                # No filter - get upcoming events
                google_events = google_calendar.get_events(max_results=20)

            # Process Google Calendar events
            for event in google_events:
                event_id = event.get('id')

                # Skip if already in local storage
                if event_id in google_event_ids:
                    continue

                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))

                # Only process datetime events, not all-day events
                if start and 'T' in start:
                    try:
                        # Parse datetime with timezone
                        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))

                        # Remove timezone for display
                        if start_dt.tzinfo:
                            start_dt = start_dt.replace(tzinfo=None)
                        if end_dt.tzinfo:
                            end_dt = end_dt.replace(tzinfo=None)

                        # Extract attendees
                        attendees = []
                        for attendee in event.get('attendees', []):
                            email = attendee.get('email', '')
                            if email:
                                attendees.append(email)

                        all_meetings.append({
                            "id": event_id,
                            "time": f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}",
                            "date": start_dt.strftime("%A, %B %d, %Y"),
                            "title": event.get('summary', 'No title'),
                            "participants": attendees,
                            "platform": "Google Calendar",
                            "source": "google",
                            "sort_key": start_dt
                        })

                    except (ValueError, KeyError) as e:
                        print(f"⚠️  Error parsing Google event: {e}")
                        continue

        except Exception as e:
            print(f"⚠️  Error fetching Google events: {e}")

    # Sort meetings by date and time
    all_meetings.sort(key=lambda x: x.get('sort_key', datetime.min))

    # Remove sort_key from output
    for meeting in all_meetings:
        meeting.pop('sort_key', None)

    if not all_meetings:
        return json.dumps({"meetings": [], "message": "No meetings found"}, indent=2)

    return json.dumps({"meetings": all_meetings, "count": len(all_meetings)}, indent=2)


# ============================================================================
# AGENT NODES (Enhanced with memory and conflict detection)
# ============================================================================

def intent_classifier(state: AgentState) -> AgentState:
    """Classify user intent using chat memory context"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Get recent context from memory
    recent_convos = chat_memory.get_recent_conversations(3)
    context_str = ""
    if recent_convos:
        context_str = "\n\nRecent conversation context:\n"
        for conv in recent_convos:
            context_str += f"User: {conv['user']}\nAssistant: {conv['assistant']}\n"

    # Get last context
    last_participant = chat_memory.get_context("last_participant")
    if last_participant:
        context_str += f"\nLast mentioned participant: {last_participant}"

    system_prompt = f"""You are an intent classifier for a scheduling assistant with memory.

Classify the user's intent into ONE of these categories:
- schedule_meeting: Create new meeting
- list_meetings: View meetings
- update_meeting: Modify existing meeting
- cancel_meeting: Cancel a meeting
- reschedule_meeting: Move meeting to different time

Extract ALL relevant information:
- participants: List of names
- duration: In minutes (default 30)
- preferred_time: Specific time or "morning"/"afternoon"/"evening" or "auto_find"
- date: "today", "tomorrow", "monday", etc.
- platform: "Zoom", "Teams", "Meet", "call", "in-person"

CONTEXT AWARENESS:
- If user says "with them" or "same person", use last participant: {last_participant}
- If user says "that meeting" or "the meeting", refer to recent context

Return JSON:
{{
  "intent": "schedule_meeting",
  "participants": ["Name"] or null,
  "duration": 30,
  "preferred_time": "2pm" or "auto_find" or null,
  "date": "tomorrow" or null,
  "platform": "Zoom" or "Meeting"
}}
{context_str}
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User: {state['user_request']}")
    ]

    response = llm.invoke(messages)

    try:
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)

        state["intent"] = parsed.get("intent", "schedule_meeting")
        state["participants"] = parsed.get("participants") or []
        state["duration"] = parsed.get("duration", 30)

        # Handle preferred_time more carefully
        pref_time = parsed.get("preferred_time")
        if pref_time and pref_time != "null":
            state["preferred_time"] = pref_time
        else:
            state["preferred_time"] = "auto_find"

        # Handle date_info
        date_val = parsed.get("date")
        if date_val and date_val != "null":
            state["date_info"] = date_val
        else:
            state["date_info"] = ""

        # Handle platform
        plat_val = parsed.get("platform")
        if plat_val and plat_val != "null":
            state["platform"] = plat_val
        else:
            state["platform"] = "Meeting"

        # Update memory context
        if state["participants"]:
            chat_memory.update_context(last_participant=state["participants"][0])

        # Check for missing info
        missing = []
        if state["intent"] == "schedule_meeting":
            if not state["participants"]:
                missing.append("participants")
            if not state["date_info"]:
                missing.append("date")

        if missing:
            state["needs_clarification"] = True
            state["missing_info"] = missing
            state["next_action"] = "clarify"
        else:
            state["needs_clarification"] = False
            state["missing_info"] = []
            state["next_action"] = state["intent"]

        print(f"   🎯 Intent: {state['intent']}")
        if state["participants"]:
            print(f"   👥 Participants: {', '.join(state['participants'])}")
        if state["intent"] == "schedule_meeting":
            print(f"   📅 Date: {state.get('date_info', '[Missing]')} | Time: {state.get('preferred_time', 'auto_find')}")
            print(f"   ⏱️  Duration: {state['duration']} min | Platform: {state['platform']}")

    except Exception as e:
        print(f"   ⚠️ Classification error: {str(e)}")
        print(f"   📄 Response: {response.content[:200]}")
        state["next_action"] = "error"

    state["messages"] = state.get("messages", []) + [response]
    state["loop_count"] = state.get("loop_count", 0) + 1

    return state


def clarification_node(state: AgentState) -> AgentState:
    """Ask user for missing information with voice support"""
    missing = state.get("missing_info", [])

    questions = []
    if "participants" in missing:
        questions.append("👥 Who would you like to meet with?")
    if "date" in missing:
        questions.append("📅 When would you like to schedule this meeting?")
    if "time" in missing:
        questions.append("🕐 What time works best?")

    clarification_msg = "\n".join(questions)

    print(f"\n💬 I need more information:\n{clarification_msg}\n")

    # Voice output
    if state.get("use_voice"):
        voice_assistant.speak("I need more information. " + questions[0].replace("👥 ", "").replace("📅 ", "").replace("🕐 ", ""))

    # Get response (voice or text)
    if state.get("use_voice"):
        user_response = voice_assistant.listen()
        if not user_response:
            user_response = input("👤 You: ").strip()
    else:
        user_response = input("👤 You: ").strip()

    if not user_response:
        state["next_action"] = "error"
        return state

    state["user_request"] = state["user_request"] + " " + user_response
    state["clarification_response"] = user_response

    return intent_classifier(state)


def route_intent(state: AgentState) -> AgentState:
    """Route to appropriate handler"""
    intent = state.get("intent", "schedule_meeting")

    if intent == "schedule_meeting":
        state["next_action"] = "find_slots"
    elif intent == "list_meetings":
        state["next_action"] = "list"
    elif intent == "cancel_meeting":
        state["next_action"] = "cancel"
    elif intent == "update_meeting":
        state["next_action"] = "update"
    elif intent == "reschedule_meeting":
        state["next_action"] = "reschedule"
    else:
        state["next_action"] = "find_slots"

    return state


def tool_executor(state: AgentState) -> AgentState:
    """Execute tools with conflict detection"""
    action = state.get("next_action", "")

    if action == "find_slots":
        preferred_time = state.get("preferred_time", "auto_find")
        if not preferred_time or preferred_time == "auto_find":
            preferred_time = "afternoon"

        # Ensure we have participants and date
        participants = state.get("participants", [])
        date_info = state.get("date_info", "tomorrow")

        if not participants or not date_info:
            print(f"   ⚠️ Missing required info: participants={participants}, date={date_info}")
            state["next_action"] = "clarify"
            return state

        tool_input = {
            "participants": participants,
            "duration_minutes": state.get("duration", 30),
            "date_str": date_info,
            "preferred_time": preferred_time
        }

        try:
            result = find_available_slots_with_conflicts.invoke(tool_input)
            slots_data = json.loads(result)
            state["available_slots"] = slots_data.get("available_slots", [])

            if state["available_slots"]:
                print(f"   ✅ Found {len(state['available_slots'])} available slot(s)")
                state["next_action"] = "select_slot"
            else:
                print(f"   ⚠️ No available slots found")
                state["next_action"] = "error"
        except Exception as e:
            print(f"   ⚠️ Error finding slots: {str(e)}")
            state["next_action"] = "error"

    elif action == "select_slot":
        if state.get("available_slots"):
            state["selected_slot"] = state["available_slots"][0]
            print(f"   📅 Selected: {state['selected_slot']['start_display']}")
            state["next_action"] = "create_meeting"
        else:
            state["next_action"] = "error"

    elif action == "create_meeting":
        slot = state.get("selected_slot", {})
        participants = state.get("participants", [])

        if slot and participants:
            if len(participants) == 1:
                title = f"Meeting with {participants[0]}"
            else:
                title = f"Meeting with {', '.join(participants)}"

            # Ensure platform is always a string, never None
            platform = state.get("platform")
            if not platform or platform == "null":
                platform = "Meeting"

            try:
                result = create_meeting_with_sync.invoke({
                    "participants": participants,
                    "start_time": slot["start"],
                    "end_time": slot["end"],
                    "title": title,
                    "platform": platform
                })

                result_data = json.loads(result)
                state["meeting_created"] = True

                # Check for conflicts
                if result_data.get("conflicts_detected"):
                    state["conflicts"] = result_data["conflicts_detected"]
                    print(f"   ⚠️ Conflict detected with {len(state['conflicts'])} meeting(s)")

                print(f"   💾 Meeting created")
                state["next_action"] = "finish"
            except Exception as e:
                print(f"   ⚠️ Error creating meeting: {str(e)}")
                state["next_action"] = "error"
        else:
            print(f"   ⚠️ Missing slot or participants")
            state["next_action"] = "error"

    elif action == "list":
        date_filter = state.get("date_info")
        try:
            result = list_meetings_with_sync.invoke({"date_filter": date_filter})
            meetings_data = json.loads(result)
            state["meetings_list"] = meetings_data.get("meetings", [])
            print(f"   ✅ Found {meetings_data.get('count', 0)} meeting(s)")
            state["next_action"] = "finish"
        except Exception as e:
            print(f"   ⚠️ Error listing meetings: {str(e)}")
            state["meetings_list"] = []
            state["next_action"] = "finish"

    elif action == "cancel":
        try:
            result = list_meetings_with_sync.invoke({})
            meetings_data = json.loads(result)
            meetings = meetings_data.get("meetings", [])

            if not meetings:
                state["meetings_list"] = []
                state["next_action"] = "finish"
            else:
                state["meetings_list"] = meetings
                state["next_action"] = "confirm_cancel"
        except Exception as e:
            print(f"   ⚠️ Error fetching meetings: {str(e)}")
            state["meetings_list"] = []
            state["next_action"] = "finish"

    state["loop_count"] = state.get("loop_count", 0) + 1

    if state["loop_count"] >= 5:
        print(f"   ⚠️ Max loops reached")
        state["next_action"] = "error"

    return state


def cancel_meeting_node(state: AgentState) -> AgentState:
    """Handle meeting cancellation with Google Calendar sync"""
    meetings = state.get("meetings_list", [])

    print("\n📋 Your current meetings:")
    for i, meeting in enumerate(meetings, 1):
        source_icon = "☁️" if meeting.get("source") == "google" else "💾"
        print(f"{i}. [{meeting.get('date', 'No date')}] {meeting['time']} — {meeting['title']} ({meeting.get('platform', 'Meeting')}) {source_icon}")

    print("\n🗑️  Which meeting would you like to cancel? (Enter the number)")

    # Voice support
    if state.get("use_voice"):
        voice_assistant.speak("Which meeting number would you like to cancel?")
        choice = voice_assistant.listen()
        if not choice:
            choice = input("👤 You: ").strip()
    else:
        choice = input("👤 You: ").strip()

    try:
        meeting_num = int(choice)

        if 1 <= meeting_num <= len(meetings):
            meeting_to_cancel = meetings[meeting_num - 1]

            # Delete from local
            if meeting_to_cancel.get("source") == "local":
                calendar_store.delete_meeting(meeting_to_cancel["id"])

            # Delete from Google Calendar
            if meeting_to_cancel.get("source") == "google" and google_calendar.enabled:
                google_calendar.delete_event(meeting_to_cancel["id"])
                print(f"   ✅ Deleted from Google Calendar")

            state["meeting_to_modify"] = meeting_to_cancel
            state["next_action"] = "finish"
            print(f"   ✅ Meeting #{meeting_num} cancelled")
        else:
            print(f"   ⚠️ Invalid number")
            state["next_action"] = "error"
    except:
        print(f"   ⚠️ Invalid input")
        state["next_action"] = "error"

    return state


def output_formatter(state: AgentState) -> AgentState:
    """Format final output with voice support"""
    intent = state.get("intent", "schedule_meeting")

    if intent == "schedule_meeting" and state.get("meeting_created"):
        slot = state.get("selected_slot", {})
        participants = state.get("participants", [])

        if len(participants) == 1:
            participant_text = participants[0]
        elif len(participants) == 2:
            participant_text = f"{participants[0]} and {participants[1]}"
        else:
            participant_text = f"{', '.join(participants[:-1])}, and {participants[-1]}"

        platform = state.get("platform", "Meeting")
        platform_text = f" via {platform}" if platform != "Meeting" else ""

        output = f"✅ Meeting confirmed for {slot.get('date_display', 'tomorrow')} at {slot.get('start_display', 'TBD')} with {participant_text} ({state.get('duration', 30)} minutes{platform_text})."

        # Add conflict warning
        if state.get("conflicts"):
            conflict_count = len(state["conflicts"])
            output += f"\n\n⚠️ Warning: This meeting conflicts with {conflict_count} existing meeting(s). You may want to reschedule."

    elif intent == "list_meetings":
        meetings = state.get("meetings_list", [])

        if not meetings:
            date_filter = state.get("date_info", "")
            if date_filter:
                output = f"You have no scheduled meetings for {date_filter}."
            else:
                output = "You currently have no scheduled meetings."
        else:
            date_filter = state.get("date_info", "")
            if date_filter:
                output = f"📅 Your meetings for {date_filter}:\n\n"
            else:
                output = "📅 Your scheduled meetings:\n\n"

            for i, meeting in enumerate(meetings, 1):
                source_icon = "☁️" if meeting.get("source") == "google" else "💾"
                date_str = meeting.get('date', 'No date')
                output += f"{i}. [{date_str}] {meeting['time']} — {meeting['title']} ({meeting.get('platform', 'Meeting')}) {source_icon}\n"

    elif intent == "cancel_meeting":
        meetings = state.get("meetings_list", [])

        if not meetings:
            output = "You currently have no scheduled meetings."
        elif state.get("meeting_to_modify"):
            meeting = state["meeting_to_modify"]
            output = f"✅ Meeting '{meeting['title']}' at {meeting['time']} has been cancelled."
        else:
            output = "Meeting cancellation initiated."

    else:
        if state.get("next_action") == "error":
            output = "I couldn't complete that request. Could you please provide more details?"
        else:
            output = "Request processed."

    # Save to memory
    chat_memory.add_conversation(
        user_input=state["user_request"],
        assistant_response=output,
        intent=state.get("intent", "unknown"),
        metadata={
            "participants": state.get("participants", []),
            "platform": state.get("platform", "Meeting"),
            "conflicts": len(state.get("conflicts", []))
        }
    )

    state["messages"] = state.get("messages", []) + [AIMessage(content=output)]
    print(f"\n{output}")

    # Voice output
    if state.get("use_voice"):
        # Clean output for speech
        speech_output = output.replace("✅", "").replace("📅", "").replace("☁️", "").replace("💾", "").replace("⚠️", "Warning:")
        voice_assistant.speak(speech_output)

    return state


def should_continue(state: AgentState) -> str:
    """Determine next node"""
    action = state.get("next_action", "")

    if action == "clarify":
        return "clarify"
    elif action in ["schedule_meeting", "list_meetings", "cancel_meeting"]:
        return "route"
    elif action in ["find_slots", "select_slot", "create_meeting", "list"]:
        return "tools"
    elif action == "confirm_cancel":
        return "cancel"
    elif action in ["finish", "error"]:
        return "output"
    else:
        return "route"


# ============================================================================
# BUILD WORKFLOW
# ============================================================================

def create_scheduling_agent():
    """Create the LangGraph scheduling agent"""
    workflow = StateGraph(AgentState)

    workflow.add_node("classifier", intent_classifier)
    workflow.add_node("clarify", clarification_node)
    workflow.add_node("route", route_intent)
    workflow.add_node("tools", tool_executor)
    workflow.add_node("cancel", cancel_meeting_node)
    workflow.add_node("output", output_formatter)

    workflow.set_entry_point("classifier")
    workflow.add_conditional_edges(
        "classifier",
        should_continue,
        {
            "clarify": "clarify",
            "route": "route",
            "tools": "tools",
            "output": "output"
        }
    )
    workflow.add_edge("clarify", "route")
    workflow.add_edge("route", "tools")
    workflow.add_conditional_edges(
        "tools",
        should_continue,
        {
            "tools": "tools",
            "cancel": "cancel",
            "output": "output"
        }
    )
    workflow.add_edge("cancel", "output")
    workflow.add_edge("output", END)

    return workflow.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_scheduling_assistant(user_request: str, use_voice: bool = False):
    """Run the scheduling assistant"""

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found.")
        return

    print(f"\n🤖 Processing: '{user_request}'")
    print("=" * 70)

    agent = create_scheduling_agent()

    initial_state = {
        "user_request": user_request,
        "messages": [],
        "intent": "",
        "participants": [],
        "duration": 30,
        "preferred_time": "auto_find",
        "date_info": "",
        "platform": "Meeting",
        "timezone": "PST",
        "available_slots": [],
        "selected_slot": {},
        "meeting_created": False,
        "meetings_list": [],
        "meeting_to_modify": {},
        "conflicts": [],
        "alternative_slots": [],
        "loop_count": 0,
        "next_action": "",
        "needs_clarification": False,
        "missing_info": [],
        "clarification_response": "",
        "google_event_id": "",
        "use_voice": use_voice
    }

    try:
        result = agent.invoke(initial_state)
        return result
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Autonomous Digital Executive Assistant (ENHANCED & FIXED)")
    print("=" * 70)
    print("\n✨ NEW FEATURES:")
    print("  🎤 Voice Input/Output (say 'voice' to enable)")
    print("  ☁️  Google Calendar Integration")
    print("  ⚠️  Conflict Detection & Resolution")
    print("  🧠 Chat Memory (remembers context)")
    print("  ✅ FIXED: List meetings functionality with proper date filtering")
    print("\n💡 I can help you:")
    print("  • Schedule meetings with voice or text")
    print("  • Detect and warn about conflicts")
    print("  • Sync with Google Calendar")
    print("  • Remember your preferences")
    print("  • List meetings by date (today, tomorrow, this week)")
    print("\n" + "=" * 70)

    # Check module status
    print("\n📊 Module Status:")
    print(f"  Voice I/O: {'✅ Enabled' if VOICE_ENABLED else '❌ Disabled'}")
    print(f"  Google Calendar: {'✅ Enabled' if google_calendar.enabled else '❌ Disabled'}")
    print(f"  Chat Memory: ✅ Enabled")
    print(f"  Conflict Detection: ✅ Enabled")
    print("\n" + "=" * 70)

    use_voice_mode = False

    while True:
        print("\n📝 What would you like me to do? (or 'quit' to exit, 'voice' to toggle voice mode)")

        if use_voice_mode and VOICE_ENABLED:
            print("🎤 Voice mode active - speak now...")
            user_input = voice_assistant.listen(timeout=10)
            if not user_input:
                user_input = input("👤 You (text): ").strip()
        else:
            user_input = input("👤 You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye! Your chat history has been saved.")
            if use_voice_mode:
                voice_assistant.speak("Goodbye! Have a productive day!")
            break

        if user_input.lower() == 'voice':
            if VOICE_ENABLED:
                use_voice_mode = not use_voice_mode
                status = "enabled" if use_voice_mode else "disabled"
                print(f"🎤 Voice mode {status}")
                if use_voice_mode:
                    voice_assistant.speak(f"Voice mode {status}")
            else:
                print("❌ Voice features not available. Install: pip install SpeechRecognition pyttsx3 pyaudio")
            continue

        if user_input.lower() == 'memory':
            recent = chat_memory.get_recent_conversations(5)
            print("\n🧠 Recent conversation history:")
            for conv in recent:
                print(f"\n  User: {conv['user']}")
                print(f"  Assistant: {conv['assistant'][:100]}...")
            continue

        if user_input.lower() == 'clear memory':
            chat_memory.clear_memory()
            print("🗑️ Chat memory cleared")
            continue

        if not user_input:
            continue

        try:
            run_scheduling_assistant(user_input, use_voice=use_voice_mode)
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")

        print("\n" + "-" * 70)