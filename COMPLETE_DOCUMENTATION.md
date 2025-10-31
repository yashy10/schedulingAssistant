# 📚 Autonomous Digital Executive Assistant - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Installation & Setup](#installation)
3. [Architecture](#architecture)
4. [Module Documentation](#modules)
5. [API Reference](#api-reference)
6. [Usage Guide](#usage-guide)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)

---

## 1. Overview {#overview}

### What is this?

An intelligent, voice-enabled scheduling assistant that manages meetings using natural language. Built with LangGraph and GPT-4o-mini, it features:

- 🎤 **Voice I/O** - Speak to schedule, listen to confirmations
- ☁️ **Google Calendar Sync** - Two-way synchronization
- ⚠️ **Conflict Detection** - Smart scheduling that avoids overlaps
- 🧠 **Chat Memory** - Remembers your preferences and context
- 🔄 **Multi-Source** - Combines local storage and Google Calendar

### Key Features

| Feature | Description |
|---------|-------------|
| Natural Language | "Schedule a meeting with John tomorrow at 2pm" |
| Voice Control | Optional hands-free operation |
| Conflict Detection | Warns about scheduling conflicts |
| Google Calendar Sync | Keeps all calendars in sync |
| Context Awareness | Remembers previous conversations |
| Multi-Platform | Supports Zoom, Teams, Meet, calls, in-person |

### Technology Stack

- **Framework:** LangGraph (StateGraph)
- **LLM:** OpenAI GPT-4o-mini
- **Speech Recognition:** Google Speech Recognition
- **TTS:** pyttsx3
- **Calendar:** Google Calendar API
- **Storage:** JSON files (local backup)

---

## 2. Installation & Setup {#installation}

### Prerequisites

- Python 3.8+
- OpenAI API key
- (Optional) Google Calendar API credentials
- (Optional) Microphone for voice features

### Installation Steps

#### Step 1: Install Dependencies

```bash
# Core dependencies
pip install langchain-core langgraph langchain-openai python-dotenv

# Voice features (optional)
pip install SpeechRecognition pyttsx3 pyaudio

# Google Calendar (optional)
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

#### Step 2: Environment Configuration

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

#### Step 3: Google Calendar Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Download `credentials.json` to project directory

#### Step 4: First Run

```bash
python scheduling_assistant_fixed.py
```

On first run with Google Calendar:
- Browser will open for authentication
- Grant calendar access
- `token.pickle` will be created automatically

---

## 3. Architecture {#architecture}

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│            (Voice Input / Text Input)                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 LANGGRAPH WORKFLOW                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Classifier│→ │  Route   │→ │  Tools   │             │
│  └────┬─────┘  └──────────┘  └────┬─────┘             │
│       │                             │                    │
│  ┌────▼─────┐                  ┌───▼──────┐            │
│  │ Clarify  │                  │  Cancel  │            │
│  └──────────┘                  └────┬─────┘            │
│                                      │                   │
│                               ┌──────▼─────┐            │
│                               │   Output   │            │
│                               └────────────┘            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                 DATA LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Local Store  │  │Google Calendar│  │Chat Memory   │ │
│  │ (events.json)│  │   (OAuth)     │  │(memory.json) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input** → User speaks or types request
2. **Classification** → GPT-4o-mini analyzes intent
3. **Clarification** → Asks for missing info (if needed)
4. **Routing** → Directs to appropriate handler
5. **Execution** → Tools perform operations
6. **Sync** → Updates local storage + Google Calendar
7. **Output** → Formats response, speaks (if voice mode)
8. **Memory** → Saves conversation for context

### File Structure

```
project/
├── scheduling_assistant_fixed.py  # Main application
├── .env                           # Environment variables
├── credentials.json               # Google OAuth (if using Calendar)
├── token.pickle                   # Google auth token (auto-generated)
├── events.json                    # Local meeting storage
├── chat_memory.json              # Conversation history
└── README.md                      # This file
```

---

## 4. Module Documentation {#modules}

### Module 1: VoiceAssistant

**Purpose:** Handles voice input and text-to-speech output

#### Class: `VoiceAssistant`

```python
class VoiceAssistant:
    """Handle voice input and output using speech recognition and TTS"""
```

##### Methods

###### `__init__()`
```python
def __init__(self)
```
**Description:** Initializes voice assistant with speech recognizer and TTS engine

**Behavior:**
- Checks if voice libraries are available
- Sets `self.enabled` flag
- Initializes `speech_recognition.Recognizer()`
- Initializes `pyttsx3.init()`
- Calls `setup_voice()` if enabled

**Example:**
```python
voice = VoiceAssistant()
if voice.enabled:
    print("Voice features ready!")
```

---

###### `setup_voice()`
```python
def setup_voice(self)
```
**Description:** Configures voice engine properties

**Configuration:**
- Attempts to select female voice
- Sets speech rate to 175 WPM
- Sets volume to 0.9 (90%)

**Voice Selection Priority:**
1. Voices with "female" in name
2. Voices with "zira" in name
3. Default system voice

---

###### `listen(prompt, timeout)`
```python
def listen(self, prompt="🎤 Listening...", timeout=5) -> str | None
```
**Description:** Captures and recognizes speech input

**Parameters:**
- `prompt` (str): Display message while listening (default: "🎤 Listening...")
- `timeout` (int): Seconds to wait for speech (default: 5)

**Returns:**
- `str`: Recognized text
- `None`: If timeout, error, or not enabled

**Exceptions Handled:**
- `sr.WaitTimeoutError` - No speech detected
- `sr.UnknownValueError` - Speech not understood
- `sr.RequestError` - API error

**Example:**
```python
voice = VoiceAssistant()
text = voice.listen("Speak your request...", timeout=10)
if text:
    print(f"You said: {text}")
```

---

###### `speak(text)`
```python
def speak(self, text: str)
```
**Description:** Converts text to speech output

**Parameters:**
- `text` (str): Text to speak

**Behavior:**
- Prints text to console
- Speaks text using TTS engine
- Blocks until speech completes

**Example:**
```python
voice = VoiceAssistant()
voice.speak("Meeting confirmed for tomorrow at 2 PM")
```

---

### Module 2: GoogleCalendarManager

**Purpose:** Manages Google Calendar API integration

#### Class: `GoogleCalendarManager`

```python
class GoogleCalendarManager:
    """Manage Google Calendar integration with OAuth authentication"""
```

##### Methods

###### `__init__()`
```python
def __init__(self)
```
**Description:** Initializes Google Calendar manager

**Behavior:**
- Sets `self.enabled` based on library availability
- Calls `authenticate()` if enabled
- Sets `self.service` to Calendar API service

---

###### `authenticate()`
```python
def authenticate(self)
```
**Description:** Handles OAuth 2.0 authentication flow

**Authentication Process:**
1. Checks for existing `token.pickle`
2. Refreshes token if expired
3. Initiates OAuth flow if no valid token
4. Saves token to `token.pickle`
5. Builds Calendar API service

**Files Used:**
- `credentials.json` - OAuth client credentials (required)
- `token.pickle` - Stored authentication token (auto-generated)

**Error Handling:**
- Missing `credentials.json` → Disables Google Calendar
- Authentication failure → Disables Google Calendar
- Prints error messages for debugging

**Example:**
```python
gcal = GoogleCalendarManager()
if gcal.enabled:
    print("✅ Google Calendar connected")
```

---

###### `get_events(time_min, time_max, max_results)`
```python
def get_events(self, time_min=None, time_max=None, max_results=10) -> list[dict]
```
**Description:** Retrieves events from Google Calendar

**Parameters:**
- `time_min` (str | None): Start time in RFC3339 format (default: now)
- `time_max` (str | None): End time in RFC3339 format (default: None)
- `max_results` (int): Maximum events to return (default: 10)

**Returns:**
- `list[dict]`: List of event objects from Google Calendar API
- `[]`: Empty list if error or not enabled

**Event Object Structure:**
```python
{
    'id': 'abc123...',
    'summary': 'Meeting Title',
    'start': {'dateTime': '2024-10-31T14:00:00Z'},
    'end': {'dateTime': '2024-10-31T15:00:00Z'},
    'attendees': [{'email': 'user@example.com'}],
    'description': 'Meeting description'
}
```

**Example:**
```python
gcal = GoogleCalendarManager()
# Get today's events
today_start = datetime.now().replace(hour=0, minute=0).isoformat() + 'Z'
today_end = datetime.now().replace(hour=23, minute=59).isoformat() + 'Z'
events = gcal.get_events(time_min=today_start, time_max=today_end)

for event in events:
    print(f"{event['summary']}: {event['start']['dateTime']}")
```

---

###### `create_event(summary, start_time, end_time, attendees, location, description)`
```python
def create_event(self, summary: str, start_time: str, end_time: str, 
                 attendees=None, location=None, description=None) -> dict | None
```
**Description:** Creates a new event in Google Calendar

**Parameters:**
- `summary` (str): Event title
- `start_time` (str): Start time in ISO format
- `end_time` (str): End time in ISO format
- `attendees` (list[str] | None): Email addresses (optional)
- `location` (str | None): Meeting location (optional)
- `description` (str | None): Event description (optional)

**Returns:**
- `dict`: Created event object with Google Calendar ID
- `None`: If error or not enabled

**Timezone:** Hardcoded to 'America/Los_Angeles' (PST)

**Example:**
```python
gcal = GoogleCalendarManager()
event = gcal.create_event(
    summary="Team Standup",
    start_time="2024-10-31T09:00:00",
    end_time="2024-10-31T09:30:00",
    attendees=["team@company.com"],
    description="Daily sync"
)
if event:
    print(f"Event created: {event['id']}")
```

---

###### `delete_event(event_id)`
```python
def delete_event(self, event_id: str) -> bool
```
**Description:** Deletes an event from Google Calendar

**Parameters:**
- `event_id` (str): Google Calendar event ID

**Returns:**
- `True`: Success
- `False`: Error or not enabled

**Example:**
```python
gcal = GoogleCalendarManager()
success = gcal.delete_event("abc123def456")
if success:
    print("Event deleted")
```

---

###### `update_event(event_id, updates)`
```python
def update_event(self, event_id: str, updates: dict) -> dict | None
```
**Description:** Updates an existing event in Google Calendar

**Parameters:**
- `event_id` (str): Google Calendar event ID
- `updates` (dict): Dictionary of fields to update

**Returns:**
- `dict`: Updated event object
- `None`: If error or not enabled

**Updatable Fields:**
- `summary` - Title
- `start` / `end` - Times
- `attendees` - Attendee list
- `location` - Location
- `description` - Description

**Example:**
```python
gcal = GoogleCalendarManager()
updated = gcal.update_event("abc123", {
    "summary": "Updated Meeting Title",
    "location": "Conference Room B"
})
```

---

### Module 3: ChatMemory

**Purpose:** Persistent conversation history and context management

#### Class: `ChatMemory`

```python
class ChatMemory:
    """Persistent chat memory system for context-aware conversations"""
```

##### Methods

###### `__init__(memory_file)`
```python
def __init__(self, memory_file="chat_memory.json")
```
**Description:** Initializes chat memory with persistent storage

**Parameters:**
- `memory_file` (str): JSON file path (default: "chat_memory.json")

**Behavior:**
- Loads existing memory if file exists
- Creates new memory structure if file missing
- Initializes `self.data` with memory structure

---

###### `load_memory()`
```python
def load_memory(self)
```
**Description:** Loads conversation history from JSON file

**Behavior:**
- Reads JSON from `self.memory_file`
- Falls back to empty structure on error
- Handles corrupted files gracefully

---

###### `create_empty_memory()`
```python
def create_empty_memory(self) -> dict
```
**Description:** Creates initial memory structure

**Returns:**
```python
{
    "conversations": [],
    "context": {
        "last_participant": None,
        "last_meeting_time": None,
        "last_duration": 30,
        "preferred_platform": "Meeting",
        "user_preferences": {}
    },
    "created_at": "2024-10-31T12:00:00.000000"
}
```

---

###### `save_memory()`
```python
def save_memory(self)
```
**Description:** Saves memory to JSON file

**Behavior:**
- Writes `self.data` to JSON
- Pretty-prints with 2-space indent
- Catches and logs save errors

---

###### `add_conversation(user_input, assistant_response, intent, metadata)`
```python
def add_conversation(self, user_input: str, assistant_response: str, 
                     intent: str, metadata=None)
```
**Description:** Adds conversation to history

**Parameters:**
- `user_input` (str): User's request
- `assistant_response` (str): Assistant's reply
- `intent` (str): Classified intent
- `metadata` (dict | None): Additional data (optional)

**Behavior:**
- Timestamps conversation
- Appends to conversations list
- Keeps only last 50 conversations
- Auto-saves to file

**Example:**
```python
memory = ChatMemory()
memory.add_conversation(
    user_input="Schedule meeting with John tomorrow",
    assistant_response="Meeting confirmed for Oct 31 at 2 PM",
    intent="schedule_meeting",
    metadata={"participants": ["John"], "conflicts": 0}
)
```

---

###### `update_context(**kwargs)`
```python
def update_context(self, **kwargs)
```
**Description:** Updates context information

**Parameters:**
- `**kwargs`: Key-value pairs to update

**Updatable Context:**
- `last_participant` (str)
- `last_meeting_time` (str)
- `last_duration` (int)
- `preferred_platform` (str)
- `user_preferences` (dict)

**Example:**
```python
memory = ChatMemory()
memory.update_context(
    last_participant="Sarah",
    preferred_platform="Zoom"
)
```

---

###### `get_context(key)`
```python
def get_context(self, key: str) -> Any
```
**Description:** Retrieves context value

**Parameters:**
- `key` (str): Context key

**Returns:**
- Value if key exists
- `None` if key missing

**Example:**
```python
memory = ChatMemory()
last_person = memory.get_context("last_participant")
print(f"Last meeting with: {last_person}")
```

---

###### `get_recent_conversations(n)`
```python
def get_recent_conversations(self, n=5) -> list[dict]
```
**Description:** Retrieves recent conversations

**Parameters:**
- `n` (int): Number of conversations (default: 5)

**Returns:**
- List of last N conversation dicts

**Example:**
```python
memory = ChatMemory()
recent = memory.get_recent_conversations(3)
for conv in recent:
    print(f"User: {conv['user']}")
    print(f"Assistant: {conv['assistant']}")
```

---

###### `clear_memory()`
```python
def clear_memory(self)
```
**Description:** Clears all memory

**Behavior:**
- Resets to empty structure
- Saves cleared state to file
- Preserves created_at timestamp

---

### Module 4: ConflictDetector

**Purpose:** Detect and resolve scheduling conflicts

#### Class: `ConflictDetector`

```python
class ConflictDetector:
    """Detect and resolve scheduling conflicts using static methods"""
```

##### Methods

###### `detect_conflicts(new_start, new_end, existing_events)`
```python
@staticmethod
def detect_conflicts(new_start, new_end, existing_events) -> list[dict]
```
**Description:** Detects if new event overlaps with existing events

**Parameters:**
- `new_start` (str | datetime): Start time of new event
- `new_end` (str | datetime): End time of new event
- `existing_events` (list[dict]): List of existing events

**Returns:**
- `list[dict]`: Events that conflict
- `[]`: No conflicts found

**Conflict Logic:**
```python
# Conflict exists if:
new_start < existing_end AND new_end > existing_start
```

**Handles:**
- Timezone-aware and naive datetimes
- ISO format strings
- Both local and Google Calendar event formats

**Example:**
```python
conflicts = ConflictDetector.detect_conflicts(
    new_start="2024-10-31T14:00:00",
    new_end="2024-10-31T15:00:00",
    existing_events=[
        {"start_time": "2024-10-31T14:30:00", 
         "end_time": "2024-10-31T15:30:00"}
    ]
)
# Returns: [conflicting_event]
```

---

###### `suggest_alternatives(conflicts, duration_minutes, date)`
```python
@staticmethod
def suggest_alternatives(conflicts, duration_minutes, date) -> list[dict]
```
**Description:** Suggests alternative time slots when conflicts exist

**Parameters:**
- `conflicts` (list[dict]): Conflicting events
- `duration_minutes` (int): Meeting duration
- `date` (datetime): Target date

**Returns:**
- `list[dict]`: Up to 3 alternative slots

**Search Window:**
- 9 AM to 5 PM (business hours)
- 30-minute increments
- Skips conflicting times

**Alternative Slot Structure:**
```python
{
    "start": "2024-10-31T15:00:00",
    "end": "2024-10-31T15:30:00",
    "start_display": "03:00 PM",
    "end_display": "03:30 PM"
}
```

**Example:**
```python
alternatives = ConflictDetector.suggest_alternatives(
    conflicts=[conflict1, conflict2],
    duration_minutes=30,
    date=datetime(2024, 10, 31)
)
# Returns: [slot1, slot2, slot3]
```

---

### Module 5: CalendarStore

**Purpose:** Local calendar data storage with JSON persistence

#### Class: `CalendarStore`

```python
class CalendarStore:
    """Local calendar data store with conflict detection"""
```

##### Methods

###### `__init__(calendar_file)`
```python
def __init__(self, calendar_file: str = "events.json")
```
**Description:** Initializes local calendar storage

**Parameters:**
- `calendar_file` (str): JSON file path (default: "events.json")

**Behavior:**
- Loads existing calendar from file
- Creates new calendar if file missing
- Handles corrupted JSON with backup

---

###### `load_calendar()`
```python
def load_calendar(self)
```
**Description:** Loads calendar data from JSON file

**Error Handling:**
- Creates backup of corrupted file
- Falls back to empty calendar structure
- Logs warnings for issues

---

###### `create_empty_calendar()`
```python
def create_empty_calendar(self) -> dict
```
**Description:** Creates empty calendar structure

**Returns:**
```python
{
    "users": {
        "current_user": {
            "name": "You",
            "timezone": "PST",
            "busy_slots": []
        }
    },
    "meetings": []
}
```

---

###### `save_calendar()`
```python
def save_calendar(self)
```
**Description:** Saves calendar to JSON file

**Behavior:**
- Pretty-prints with 2-space indent
- Catches and logs save errors

---

###### `get_user_availability(user, date)`
```python
def get_user_availability(self, user: str, date: datetime) -> dict
```
**Description:** Gets available slots for a user

**Parameters:**
- `user` (str): User name
- `date` (datetime): Date to check

**Returns:**
```python
{
    "user": "John Smith",
    "date": "2024-10-31T00:00:00",
    "busy_slots": [...]
}
```

**Behavior:**
- Creates user if doesn't exist
- Auto-saves when creating user

---

###### `add_meeting(participants, start_time, end_time, title, platform, google_event_id)`
```python
def add_meeting(self, participants: list[str], start_time: str, end_time: str, 
                title: str, platform: str = "Meeting", 
                google_event_id: str = None) -> tuple[dict, list[dict]]
```
**Description:** Adds meeting with conflict detection

**Parameters:**
- `participants` (list[str]): Attendees
- `start_time` (str): Start in ISO format
- `end_time` (str): End in ISO format
- `title` (str): Meeting title
- `platform` (str): Platform (default: "Meeting")
- `google_event_id` (str | None): Google Calendar ID (optional)

**Returns:**
- `tuple`: (meeting_dict, conflicts_list)

**Meeting Structure:**
```python
{
    "id": 1,
    "title": "Meeting with John",
    "participants": ["John"],
    "start_time": "2024-10-31T14:00:00",
    "end_time": "2024-10-31T14:30:00",
    "platform": "Zoom",
    "google_event_id": "abc123",
    "created_at": "2024-10-31T12:00:00.000000",
    "conflicts": False
}
```

**Example:**
```python
store = CalendarStore()
meeting, conflicts = store.add_meeting(
    participants=["Sarah"],
    start_time="2024-10-31T14:00:00",
    end_time="2024-10-31T14:30:00",
    title="1:1 with Sarah",
    platform="Zoom"
)
if conflicts:
    print(f"⚠️ {len(conflicts)} conflicts detected")
```

---

###### `get_meetings(date_filter)`
```python
def get_meetings(self, date_filter: str = None) -> list[dict]
```
**Description:** Gets meetings with optional date filtering

**Parameters:**
- `date_filter` (str | None): Filter criteria

**Supported Filters:**
- `None` - All meetings
- `"today"` - Today's meetings
- `"tomorrow"` or `"tmrw"` - Tomorrow's meetings
- `"this week"` - Next 7 days
- ISO date string - Specific date

**Returns:**
- `list[dict]`: Filtered meeting list

**Error Handling:**
- Skips invalid meeting entries
- Logs warnings for malformed data
- Handles timezone-aware and naive datetimes

**Example:**
```python
store = CalendarStore()

# All meetings
all_meetings = store.get_meetings()

# Today only
today = store.get_meetings("today")

# This week
week = store.get_meetings("this week")
```

---

###### `update_meeting(meeting_id, updates)`
```python
def update_meeting(self, meeting_id: int, updates: dict) -> dict | None
```
**Description:** Updates a meeting

**Parameters:**
- `meeting_id` (int): Local meeting ID
- `updates` (dict): Fields to update

**Returns:**
- `dict`: Updated meeting
- `None`: If meeting not found

**Example:**
```python
store = CalendarStore()
updated = store.update_meeting(1, {
    "title": "Updated Meeting Title",
    "platform": "Teams"
})
```

---

###### `delete_meeting(meeting_id)`
```python
def delete_meeting(self, meeting_id: int) -> bool
```
**Description:** Deletes a meeting

**Parameters:**
- `meeting_id` (int): Local meeting ID

**Returns:**
- `True`: Always (even if not found)

**Behavior:**
- Removes meeting from list
- Auto-saves calendar

**Example:**
```python
store = CalendarStore()
store.delete_meeting(1)
```

---

### Module 6: LangGraph Tools

**Purpose:** Tool functions for LangGraph nodes

#### Tool Functions

###### `find_available_slots_with_conflicts`
```python
@tool
def find_available_slots_with_conflicts(participants: list[str], 
                                        duration_minutes: int, 
                                        date_str: str, 
                                        preferred_time: str = "afternoon") -> str
```
**Description:** Finds available time slots with conflict detection

**Parameters:**
- `participants` (list[str]): Meeting attendees
- `duration_minutes` (int): Meeting length
- `date_str` (str): Date ("today", "tomorrow", "monday", etc.)
- `preferred_time` (str): Time preference (default: "afternoon")

**Returns:**
- JSON string with available slots

**Time Parsing:**
- Specific times: `"2pm"`, `"14:00"`, `"2 o'clock"`
- Ranges: `"morning"` (9-12), `"afternoon"` (12-17), `"evening"` (17-20)
- Auto: `"auto_find"` uses afternoon

**Date Parsing:**
- `"today"`, `"tomorrow"`, `"tmrw"`
- `"next monday"`, `"this friday"`
- Weekday names with relative indicators

**Conflict Detection:**
- Checks local storage
- Checks Google Calendar (if enabled)
- Returns only non-conflicting slots

**Output Format:**
```json
{
  "available_slots": [
    {
      "start": "2024-10-31T14:00:00",
      "end": "2024-10-31T14:30:00",
      "start_display": "02:00 PM",
      "end_display": "02:30 PM",
      "date_display": "Thursday, October 31"
    }
  ]
}
```

**Example:**
```python
result = find_available_slots_with_conflicts(
    participants=["John"],
    duration_minutes=30,
    date_str="tomorrow",
    preferred_time="2pm"
)
data = json.loads(result)
slots = data["available_slots"]
```

---

###### `create_meeting_with_sync`
```python
@tool
def create_meeting_with_sync(participants: list[str], 
                             start_time: str, 
                             end_time: str, 
                             title: str, 
                             platform: str = "Meeting") -> str
```
**Description:** Creates meeting in local storage and Google Calendar

**Parameters:**
- `participants` (list[str]): Attendees
- `start_time` (str): Start in ISO format
- `end_time` (str): End in ISO format
- `title` (str): Meeting title
- `platform` (str): Platform (default: "Meeting")

**Returns:**
- JSON string with result

**Behavior:**
1. Creates in Google Calendar (if enabled)
2. Creates in local storage
3. Runs conflict detection
4. Links via `google_event_id`

**Output Format:**
```json
{
  "success": true,
  "meeting": {
    "id": 1,
    "title": "Meeting with John",
    "participants": ["John"],
    "date": "Thursday, October 31, 2024",
    "time": "02:00 PM - 02:30 PM",
    "duration": 30,
    "platform": "Zoom",
    "google_synced": true,
    "conflicts": 0
  },
  "conflicts_detected": []
}
```

**Example:**
```python
result = create_meeting_with_sync(
    participants=["Sarah"],
    start_time="2024-10-31T14:00:00",
    end_time="2024-10-31T14:30:00",
    title="1:1 with Sarah",
    platform="Zoom"
)
data = json.loads(result)
if data["success"]:
    print("Meeting created!")
```

---

###### `list_meetings_with_sync`
```python
@tool
def list_meetings_with_sync(date_filter: str = None) -> str
```
**Description:** Lists meetings from local storage and Google Calendar

**Parameters:**
- `date_filter` (str | None): Filter ("today", "tomorrow", "this week")

**Returns:**
- JSON string with meetings list

**Behavior:**
1. Gets local meetings
2. Gets Google Calendar events (if enabled)
3. Removes duplicates (via `google_event_id`)
4. Sorts chronologically
5. Adds date display to each meeting

**Output Format:**
```json
{
  "meetings": [
    {
      "id": 1,
      "time": "09:00 AM - 10:00 AM",
      "date": "Thursday, October 31, 2024",
      "title": "Team Standup",
      "participants": ["team@company.com"],
      "platform": "Zoom",
      "source": "google"
    }
  ],
  "count": 1
}
```

**Example:**
```python
result = list_meetings_with_sync(date_filter="today")
data = json.loads(result)
for meeting in data["meetings"]:
    print(f"{meeting['time']} - {meeting['title']}")
```

---

## 5. API Reference {#api-reference}

### AgentState Type Definition

```python
class AgentState(TypedDict):
    # Communication
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_request: str
    use_voice: bool
    
    # Intent & Classification
    intent: str
    participants: list[str]
    duration: int
    preferred_time: str
    date_info: str
    platform: str
    timezone: str
    
    # Meeting Management
    available_slots: list[dict]
    selected_slot: dict
    meeting_created: bool
    meetings_list: list[dict]
    meeting_to_modify: dict
    
    # Conflict Management
    conflicts: list[dict]
    alternative_slots: list[dict]
    
    # Flow Control
    next_action: str
    loop_count: int
    needs_clarification: bool
    missing_info: list[str]
    clarification_response: str
    
    # Integration
    google_event_id: str
```

### LangGraph Nodes

#### `intent_classifier(state: AgentState) -> AgentState`
**Purpose:** Analyzes user request and classifies intent

**Reads:**
- `user_request`, `messages`

**Writes:**
- `intent`, `participants`, `duration`, `preferred_time`, `date_info`, `platform`
- `needs_clarification`, `missing_info`, `next_action`
- `messages`, `loop_count`

**LLM:** GPT-4o-mini (temperature=0)

**Intent Categories:**
- `schedule_meeting`
- `list_meetings`
- `cancel_meeting`
- `update_meeting`
- `reschedule_meeting`

---

#### `clarification_node(state: AgentState) -> AgentState`
**Purpose:** Asks for missing information

**Reads:**
- `missing_info`, `use_voice`

**Writes:**
- `user_request` (appends response)
- `clarification_response`

**Behavior:**
- Generates questions based on `missing_info`
- Supports voice/text input
- Returns to `intent_classifier`

---

#### `route_intent(state: AgentState) -> AgentState`
**Purpose:** Routes to appropriate handler

**Reads:**
- `intent`

**Writes:**
- `next_action`

**Routing Map:**
```python
schedule_meeting → find_slots
list_meetings → list
cancel_meeting → cancel
update_meeting → update
reschedule_meeting → reschedule
```

---

#### `tool_executor(state: AgentState) -> AgentState`
**Purpose:** Executes calendar operations

**Actions:**
- `find_slots` - Search for available times
- `select_slot` - Pick best slot
- `create_meeting` - Create meeting with sync
- `list` - List meetings

**Loop Behavior:**
- Can call itself (max 5 loops)
- Tracks iterations via `loop_count`

---

#### `cancel_meeting_node(state: AgentState) -> AgentState`
**Purpose:** Handles meeting cancellation

**Reads:**
- `meetings_list`, `use_voice`

**Writes:**
- `meeting_to_modify`, `next_action`

**Behavior:**
1. Displays numbered meeting list
2. Gets user selection
3. Deletes from local + Google
4. Sets `meeting_to_modify`

---

#### `output_formatter(state: AgentState) -> AgentState`
**Purpose:** Formats and delivers final response

**Reads:**
- All state fields

**Writes:**
- `messages` (final response)
- Saves to chat memory

**Behavior:**
- Formats response based on intent
- Adds conflict warnings
- Speaks (if voice enabled)
- Saves conversation

---

### Conditional Edge Functions

#### `should_continue(state: AgentState) -> str`
**Purpose:** Determines next node

**Returns:**
- `"clarify"` - Go to clarification
- `"route"` - Go to routing
- `"tools"` - Go to tools
- `"cancel"` - Go to cancel
- `"output"` - Go to output

**Logic:**
```python
if next_action == "clarify": return "clarify"
elif next_action in ["find_slots", "create_meeting"]: return "tools"
elif next_action == "confirm_cancel": return "cancel"
elif next_action in ["finish", "error"]: return "output"
```

---

## 6. Usage Guide {#usage-guide}

### Basic Usage

#### Starting the Assistant

```bash
python scheduling_assistant_fixed.py
```

#### Text Mode (Default)

```
📝 What would you like me to do?
👤 You: schedule a meeting with John tomorrow at 2pm

🤖 Processing: 'schedule a meeting with John tomorrow at 2pm'
======================================================================
   🎯 Intent: schedule_meeting
   👥 Participants: John
   📅 Date: tomorrow | Time: 2pm
   ⏱️  Duration: 30 min | Platform: Meeting
   ✅ Found 1 available slot(s)
   📅 Selected: 02:00 PM
   💾 Meeting created

✅ Meeting confirmed for Thursday, October 31 at 02:00 PM with John (30 minutes).
```

#### Voice Mode

```
📝 What would you like me to do?
👤 You: voice

🎤 Voice mode enabled

📝 What would you like me to do?
🎤 Voice mode active - speak now...
🎤 Listening...
🎤 You said: schedule a meeting with Sarah tomorrow afternoon

[Processing continues as normal, with spoken output]
```

### Common Commands

#### Scheduling

```
# Basic scheduling
"schedule a meeting with John tomorrow at 2pm"
"set up a call with Sarah next Monday at 10am"
"book a 1 hour meeting with the team this Friday afternoon"

# With platform
"schedule a Zoom call with Bob tomorrow at 3pm"
"set up an in-person meeting with Jane next week"

# Let assistant find time
"schedule a meeting with the team tomorrow"
(Assistant will ask for preferred time)
```

#### Listing Meetings

```
# Filter by date
"show my meetings today"
"list meetings tomorrow"
"what do I have scheduled this week"

# All meetings
"show all my meetings"
"list my schedule"
```

#### Canceling Meetings

```
"cancel a meeting"
"delete my meeting with John"

# Assistant shows numbered list
📋 Your current meetings:
1. [Thursday, October 31, 2024] 09:00 AM - 10:00 AM — Team Standup (Zoom) ☁️
2. [Thursday, October 31, 2024] 02:00 PM - 02:30 PM — Meeting with John (Meeting) 💾

🗑️  Which meeting would you like to cancel? (Enter the number)
👤 You: 2
```

#### Special Commands

```
"voice"         # Toggle voice mode
"memory"        # View recent conversation history
"clear memory"  # Clear chat memory
"quit" or "q"   # Exit assistant
```

### Advanced Usage

#### Multi-Person Meetings

```
"schedule a meeting with John, Sarah, and Bob tomorrow at 2pm"
```

The assistant will:
- Extract all participants
- Check availability for all
- Send Google Calendar invites (if emails provided)

#### Custom Duration

```
"schedule a 60 minute meeting with the team tomorrow"
"book a 90 minute planning session next week"
```

Default is 30 minutes if not specified.

#### Platform Specification

```
"schedule a Teams call with Bob tomorrow"
"book a Zoom meeting with the design team Friday"
"set up an in-person meeting with Jane next week"
```

Supported platforms:
- Zoom
- Teams (Microsoft Teams)
- Meet (Google Meet)
- call (phone call)
- in-person
- Meeting (generic)

#### Context-Aware Scheduling

```
# First meeting
👤 You: schedule a meeting with Sarah tomorrow

# Later...
👤 You: schedule another meeting with her next week

# Assistant remembers "her" = Sarah from chat memory
```

---

## 7. Configuration {#configuration}

### Environment Variables

Create `.env` file:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional (for custom configuration)
DEFAULT_DURATION=30
DEFAULT_TIMEZONE=PST
MEMORY_FILE=chat_memory.json
EVENTS_FILE=events.json
```

### Voice Configuration

Edit `VoiceAssistant.setup_voice()`:

```python
# Speech rate (words per minute)
self.engine.setProperty('rate', 175)  # Default: 175

# Volume (0.0 to 1.0)
self.engine.setProperty('volume', 0.9)  # Default: 0.9

# Voice selection (platform-dependent)
# macOS: "com.apple.speech.synthesis.voice.samantha"
# Windows: "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
```

### Google Calendar Configuration

#### Timezone

Edit `GoogleCalendarManager.create_event()`:

```python
'start': {
    'dateTime': start_time,
    'timeZone': 'America/Los_Angeles',  # Change this
},
```

Supported timezones: [IANA Time Zone Database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

#### OAuth Scopes

Edit SCOPES constant:

```python
SCOPES = [
    'https://www.googleapis.com/auth/calendar',      # Full access
    # OR
    'https://www.googleapis.com/auth/calendar.events'  # Events only
]
```

### Conflict Detection

Edit `ConflictDetector.suggest_alternatives()`:

```python
# Business hours
start_hour = 9   # Default: 9 AM
end_hour = 17    # Default: 5 PM

# Time slot increments
current_time += timedelta(minutes=30)  # Default: 30 min
```

### Memory Settings

Edit `ChatMemory.add_conversation()`:

```python
# Keep only last N conversations
if len(self.data["conversations"]) > 50:  # Default: 50
    self.data["conversations"] = self.data["conversations"][-50:]
```

### Loop Safety

Edit `tool_executor()`:

```python
if state["loop_count"] >= 5:  # Default: 5
    print(f"   ⚠️ Max loops reached")
    state["next_action"] = "error"
```

---

## 8. Troubleshooting {#troubleshooting}

### Common Issues

#### "OPENAI_API_KEY not found"

**Solution:**
1. Create `.env` file in project directory
2. Add: `OPENAI_API_KEY=your_key_here`
3. Ensure `.env` is in same directory as script

---

#### Voice features not working

**Error:** `ModuleNotFoundError: No module named 'speech_recognition'`

**Solution:**
```bash
pip install SpeechRecognition pyttsx3

# macOS
brew install portaudio
pip install pyaudio

# Ubuntu/Debian
sudo apt-get install python3-pyaudio portaudio19-dev

# Windows
pip install pyaudio
```

**Microphone not detected:**
```python
# Test microphone
import speech_recognition as sr
r = sr.Recognizer()
print(sr.Microphone.list_microphone_names())
```

---

#### Google Calendar not connecting

**Error:** `credentials.json not found`

**Solution:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Download as `credentials.json`
6. Place in project directory

**Error:** `Invalid grant` or `Token expired`

**Solution:**
```bash
# Delete old token
rm token.pickle

# Re-run script (will re-authenticate)
python scheduling_assistant_fixed.py
```

---

#### Meetings not syncing

**Check sync status:**
```python
# In output, look for:
✅ Synced to Google Calendar  # Success
⚠️  Google Calendar disabled  # Check credentials
```

**Verify Google Calendar is enabled:**
```python
from scheduling_assistant_fixed import google_calendar
print(f"Enabled: {google_calendar.enabled}")
```

---

#### JSON file corruption

**Error:** `Invalid JSON in events.json`

**Solution:**
- Script automatically creates backup: `events.json.backup`
- Restore manually if needed:
```bash
cp events.json.backup events.json
```

Or reset:
```bash
rm events.json
# Script will create new file on next run
```

---

#### Intent misclassification

**Symptoms:**
- Assistant doesn't understand request
- Wrong action taken

**Solutions:**
1. Be more specific:
   - ❌ "meeting"
   - ✅ "schedule a meeting with John tomorrow at 2pm"

2. Use keywords:
   - Schedule: "schedule", "book", "set up"
   - List: "show", "list", "what meetings"
   - Cancel: "cancel", "delete", "remove"

3. Check chat memory:
```
👤 You: memory
[Shows recent conversations and context]
```

4. Clear memory if context is wrong:
```
👤 You: clear memory
```

---

#### Conflict detection not working

**Verify meetings exist:**
```python
from scheduling_assistant_fixed import calendar_store
meetings = calendar_store.get_meetings()
print(f"Total meetings: {len(meetings)}")
```

**Check date format:**
- All times must be in ISO format: `2024-10-31T14:00:00`
- Timezone-aware: `2024-10-31T14:00:00-07:00` or `2024-10-31T14:00:00Z`

---

#### Max loops reached

**Error:** `⚠️ Max loops reached`

**Cause:**
- Missing information not provided
- Tool execution failing repeatedly

**Solution:**
1. Check that all required info is present
2. Restart with clearer request
3. If persistent, check logs for tool errors

---

### Debug Mode

Enable verbose logging:

```python
# Add at top of main execution
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help

1. **Check logs** - Console output shows each step
2. **Inspect state** - Add debug prints in nodes
3. **Test components individually** - Import and test classes
4. **Review documentation** - All classes and methods documented

### Support Resources

- **LangGraph:** https://langchain-ai.github.io/langgraph/
- **OpenAI API:** https://platform.openai.com/docs
- **Google Calendar API:** https://developers.google.com/calendar
- **Speech Recognition:** https://pypi.org/project/SpeechRecognition/

---

## Appendix

### File Formats

#### events.json
```json
{
  "users": {
    "current_user": {
      "name": "You",
      "timezone": "PST",
      "busy_slots": []
    }
  },
  "meetings": [
    {
      "id": 1,
      "title": "Team Standup",
      "participants": ["team@company.com"],
      "start_time": "2024-10-31T09:00:00",
      "end_time": "2024-10-31T09:30:00",
      "platform": "Zoom",
      "google_event_id": "abc123",
      "created_at": "2024-10-31T08:00:00",
      "conflicts": false
    }
  ]
}
```

#### chat_memory.json
```json
{
  "conversations": [
    {
      "timestamp": "2024-10-31T12:00:00",
      "user": "schedule a meeting with John",
      "assistant": "Meeting confirmed...",
      "intent": "schedule_meeting",
      "metadata": {
        "participants": ["John"],
        "conflicts": 0
      }
    }
  ],
  "context": {
    "last_participant": "John",
    "last_meeting_time": null,
    "last_duration": 30,
    "preferred_platform": "Zoom",
    "user_preferences": {}
  },
  "created_at": "2024-10-31T00:00:00"
}
```

### Glossary

- **Agent:** The LangGraph workflow that processes requests
- **Node:** A processing step in the workflow
- **State:** Data structure passed between nodes
- **Tool:** Function that performs operations (find slots, create meeting, etc.)
- **Intent:** User's goal (schedule, list, cancel, etc.)
- **Conflict:** Overlapping meeting times
- **Sync:** Two-way data exchange with Google Calendar
- **Memory:** Persistent conversation history

---

**Last Updated:** 2024-10-31  
**Version:** 2.0 (Enhanced with fixes)  
**Author:** AI Scheduling Assistant Team
