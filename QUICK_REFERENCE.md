# 📖 Quick Reference Guide - Scheduling Assistant

## 🚀 Quick Start

```bash
# Install
pip install langchain-core langgraph langchain-openai python-dotenv

# Setup
echo "OPENAI_API_KEY=your_key" > .env

# Run
python scheduling_assistant_fixed.py
```

---

## 📚 Classes at a Glance

### VoiceAssistant
```python
voice = VoiceAssistant()
text = voice.listen(timeout=5)         # Get voice input
voice.speak("Hello!")                   # Text-to-speech
```

### GoogleCalendarManager
```python
gcal = GoogleCalendarManager()
events = gcal.get_events()                          # List events
event = gcal.create_event("Meeting", start, end)    # Create
gcal.delete_event(event_id)                         # Delete
```

### ChatMemory
```python
memory = ChatMemory()
memory.add_conversation(user, assistant, intent)    # Save
recent = memory.get_recent_conversations(5)         # Retrieve
memory.update_context(last_participant="John")      # Update context
```

### CalendarStore
```python
store = CalendarStore()
meeting, conflicts = store.add_meeting(...)         # Add with conflict check
meetings = store.get_meetings("today")              # Filter by date
store.delete_meeting(meeting_id)                    # Delete
```

### ConflictDetector
```python
conflicts = ConflictDetector.detect_conflicts(
    new_start, new_end, existing_events
)
alternatives = ConflictDetector.suggest_alternatives(
    conflicts, duration, date
)
```

---

## 🛠️ LangGraph Tools

### find_available_slots_with_conflicts
```python
result = find_available_slots_with_conflicts(
    participants=["John"],
    duration_minutes=30,
    date_str="tomorrow",
    preferred_time="2pm"
)
# Returns JSON with available_slots list
```

### create_meeting_with_sync
```python
result = create_meeting_with_sync(
    participants=["Sarah"],
    start_time="2024-10-31T14:00:00",
    end_time="2024-10-31T14:30:00",
    title="1:1 with Sarah",
    platform="Zoom"
)
# Returns JSON with success status and meeting details
```

### list_meetings_with_sync
```python
result = list_meetings_with_sync(date_filter="today")
# Returns JSON with meetings array
```

---

## 🎯 Node Functions

### intent_classifier(state) → state
**Purpose:** Classifies user intent using GPT-4o-mini  
**Sets:** `intent`, `participants`, `date_info`, `preferred_time`, `needs_clarification`

### clarification_node(state) → state
**Purpose:** Asks for missing information  
**Uses:** `missing_info` to generate questions  
**Returns:** Back to classifier with updated `user_request`

### route_intent(state) → state
**Purpose:** Routes based on intent  
**Maps:** 
- `schedule_meeting` → `find_slots`
- `list_meetings` → `list`
- `cancel_meeting` → `cancel`

### tool_executor(state) → state
**Purpose:** Executes calendar operations  
**Actions:** `find_slots`, `select_slot`, `create_meeting`, `list`  
**Can Loop:** Up to 5 times

### cancel_meeting_node(state) → state
**Purpose:** Interactive cancellation  
**Shows:** Numbered list of meetings  
**Deletes:** From local + Google Calendar

### output_formatter(state) → state
**Purpose:** Formats final response  
**Adds:** Conflict warnings, voice output  
**Saves:** To chat memory

---

## 📊 State Variables Quick Ref

| Variable | Type | Purpose |
|----------|------|---------|
| `user_request` | str | User's input |
| `intent` | str | "schedule_meeting", "list_meetings", etc. |
| `participants` | list[str] | ["John", "Sarah"] |
| `duration` | int | Minutes (default: 30) |
| `preferred_time` | str | "2pm", "afternoon", "auto_find" |
| `date_info` | str | "today", "tomorrow", "next monday" |
| `platform` | str | "Zoom", "Teams", "Meeting" |
| `available_slots` | list[dict] | Found time slots |
| `selected_slot` | dict | Chosen slot |
| `meeting_created` | bool | Success flag |
| `meetings_list` | list[dict] | Retrieved meetings |
| `conflicts` | list[dict] | Detected conflicts |
| `next_action` | str | Where to go next (critical!) |
| `loop_count` | int | Prevents infinite loops (max: 5) |
| `needs_clarification` | bool | Missing info flag |
| `missing_info` | list[str] | ["participants", "date"] |
| `google_event_id` | str | Google Calendar link |
| `use_voice` | bool | Voice mode toggle |

---

## 🔀 Workflow Paths

### Schedule Meeting (Complete)
```
START → CLASSIFIER → ROUTE → TOOLS (find) 
      → TOOLS (select) → TOOLS (create) → OUTPUT → END
```

### Schedule with Missing Info
```
START → CLASSIFIER → CLARIFY → CLASSIFIER 
      → ROUTE → TOOLS → OUTPUT → END
```

### List Meetings
```
START → CLASSIFIER → ROUTE → TOOLS (list) → OUTPUT → END
```

### Cancel Meeting
```
START → CLASSIFIER → ROUTE → TOOLS (list) 
      → CANCEL → OUTPUT → END
```

---

## 🎤 User Commands

### Scheduling
```
"schedule a meeting with John tomorrow at 2pm"
"book a Zoom call with Sarah next Monday at 10am"
"set up a 1 hour meeting with the team Friday afternoon"
```

### Listing
```
"show my meetings today"
"list meetings tomorrow"
"what do I have scheduled this week"
```

### Canceling
```
"cancel a meeting"
```

### Special
```
"voice"         - Toggle voice mode
"memory"        - Show recent conversations
"clear memory"  - Clear chat memory
"quit"          - Exit
```

---

## ⚙️ Configuration

### Environment (.env)
```env
OPENAI_API_KEY=sk-...
```

### Voice Settings
```python
self.engine.setProperty('rate', 175)      # Speed
self.engine.setProperty('volume', 0.9)    # Volume
```

### Business Hours
```python
start_hour = 9    # 9 AM
end_hour = 17     # 5 PM
```

### Loop Safety
```python
if state["loop_count"] >= 5:  # Max loops
```

### Memory Limit
```python
if len(conversations) > 50:  # Keep last 50
```

---

## 🐛 Quick Debugging

### Check Module Status
```python
from scheduling_assistant_fixed import VOICE_ENABLED, GOOGLE_CALENDAR_ENABLED
print(f"Voice: {VOICE_ENABLED}")
print(f"Google: {GOOGLE_CALENDAR_ENABLED}")
```

### Test Voice
```python
from scheduling_assistant_fixed import voice_assistant
text = voice_assistant.listen()
voice_assistant.speak("Testing")
```

### Test Google Calendar
```python
from scheduling_assistant_fixed import google_calendar
events = google_calendar.get_events()
print(f"Found {len(events)} events")
```

### View Local Meetings
```python
from scheduling_assistant_fixed import calendar_store
meetings = calendar_store.get_meetings()
print(f"Total: {len(meetings)}")
```

### Check Memory
```python
from scheduling_assistant_fixed import chat_memory
recent = chat_memory.get_recent_conversations(3)
for conv in recent:
    print(conv['user'])
```

---

## 🔧 Common Fixes

### Reset Google Auth
```bash
rm token.pickle
# Re-run script to re-authenticate
```

### Reset Calendar
```bash
rm events.json
# Script creates new file
```

### Reset Memory
```bash
rm chat_memory.json
# Or in app: "clear memory"
```

### Fix Corrupted JSON
```bash
# Backup is auto-created
cp events.json.backup events.json
```

---

## 📝 Code Snippets

### Custom Node Function
```python
def my_custom_node(state: AgentState) -> AgentState:
    """Custom processing node"""
    # Read from state
    user_input = state.get("user_request")
    
    # Process
    result = do_something(user_input)
    
    # Write to state
    state["my_result"] = result
    state["next_action"] = "output"
    state["loop_count"] = state.get("loop_count", 0) + 1
    
    return state
```

### Add Custom Tool
```python
@tool
def my_custom_tool(param1: str, param2: int) -> str:
    """Custom tool for LangGraph"""
    result = perform_operation(param1, param2)
    return json.dumps({"result": result})
```

### Extend State
```python
class AgentState(TypedDict):
    # ... existing fields
    my_custom_field: str
    my_custom_list: list[dict]
```

### Add Node to Workflow
```python
workflow = StateGraph(AgentState)
workflow.add_node("my_node", my_custom_node)
workflow.add_edge("classifier", "my_node")
workflow.add_edge("my_node", "output")
```

---

## 📚 Data Structures

### Available Slot
```python
{
    "start": "2024-10-31T14:00:00",
    "end": "2024-10-31T14:30:00",
    "start_display": "02:00 PM",
    "end_display": "02:30 PM",
    "date_display": "Thursday, October 31"
}
```

### Meeting
```python
{
    "id": 1,
    "title": "Meeting with John",
    "participants": ["John"],
    "start_time": "2024-10-31T14:00:00",
    "end_time": "2024-10-31T14:30:00",
    "platform": "Zoom",
    "google_event_id": "abc123",
    "created_at": "2024-10-31T12:00:00",
    "conflicts": false
}
```

### Conversation
```python
{
    "timestamp": "2024-10-31T12:00:00",
    "user": "schedule meeting with John",
    "assistant": "Meeting confirmed...",
    "intent": "schedule_meeting",
    "metadata": {"participants": ["John"]}
}
```

### Google Calendar Event
```python
{
    'id': 'abc123',
    'summary': 'Meeting Title',
    'start': {'dateTime': '2024-10-31T14:00:00Z'},
    'end': {'dateTime': '2024-10-31T15:00:00Z'},
    'attendees': [{'email': 'user@example.com'}]
}
```

---

## 🎓 Key Concepts

### State Flow
- State passes through nodes
- Each node reads and writes
- Never lost between nodes

### Next Action
- Critical for routing
- Set by every node
- Determines which node runs next

### Loop Safety
- `loop_count` prevents infinite loops
- Max 5 iterations
- Breaks to error on exceed

### Conflict Detection
- Checks every new meeting
- Compares with local + Google
- Warns but doesn't block

### Memory Context
- Remembers recent conversations
- Tracks last participant
- Enables "with them" references

---

## 📞 Quick Help

**Voice not working?**
```bash
pip install SpeechRecognition pyttsx3 pyaudio
```

**Google Calendar not syncing?**
- Check `credentials.json` exists
- Delete `token.pickle` and re-auth
- Verify API enabled in Google Cloud Console

**Intent misclassified?**
- Be more specific
- Use command keywords
- Check chat memory: `"memory"`

**Max loops error?**
- Restart with clearer request
- Ensure all info provided
- Check tool execution logs

---

## 📄 File Reference

| File | Purpose |
|------|---------|
| `scheduling_assistant_fixed.py` | Main application |
| `.env` | API keys |
| `credentials.json` | Google OAuth |
| `token.pickle` | Google auth token |
| `events.json` | Local meetings |
| `chat_memory.json` | Conversation history |

---

## 🔗 Resources

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [OpenAI API](https://platform.openai.com/docs)
- [Google Calendar API](https://developers.google.com/calendar)
- [Speech Recognition](https://pypi.org/project/SpeechRecognition/)

---

**Quick Tip:** Use `memory` command to debug context issues!
