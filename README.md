# 🤖 Autonomous Digital Executive Assistant

> An intelligent, voice-enabled scheduling assistant powered by LangGraph and GPT-4o-mini

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-latest-green.svg)](https://github.com/langchain-ai/langgraph)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange.svg)](https://platform.openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🎤 **Voice Control** - Speak naturally to schedule, list, or cancel meetings
- ☁️ **Google Calendar Sync** - Two-way synchronization with your Google Calendar
- ⚠️ **Smart Conflict Detection** - Automatically detects and warns about scheduling conflicts
- 🧠 **Context-Aware** - Remembers your preferences and previous conversations
- 🔄 **Multi-Platform** - Supports Zoom, Teams, Google Meet, calls, and in-person meetings
- 💾 **Local Backup** - Maintains local storage alongside cloud sync
- 🌐 **Natural Language** - Just speak or type what you want, no commands to memorize

## 🎬 Demo

```bash
👤 You: schedule a meeting with John tomorrow at 2pm

🤖 Processing: 'schedule a meeting with John tomorrow at 2pm'
   🎯 Intent: schedule_meeting
   👥 Participants: John
   📅 Date: tomorrow | Time: 2pm
   ✅ Found 1 available slot(s)
   💾 Meeting created
   ✅ Synced to Google Calendar

✅ Meeting confirmed for Thursday, October 31 at 02:00 PM with John (30 minutes).
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- (Optional) Google Calendar API credentials
- (Optional) Microphone for voice features

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/scheduling-assistant.git
   cd scheduling-assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

4. **Run the assistant**
   ```bash
   python scheduling_assistant_fixed.py
   ```

That's it! 🎉

## 📦 Installation Options

### Core Features Only
```bash
pip install langchain-core langgraph langchain-openai python-dotenv
```

### With Voice Features
```bash
pip install SpeechRecognition pyttsx3 pyaudio
```

### With Google Calendar
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### All Features
```bash
pip install -r requirements.txt
```

## 🎯 Usage

### Basic Commands

#### Schedule a Meeting
```
schedule a meeting with John tomorrow at 2pm
book a Zoom call with Sarah next Monday at 10am
set up a 1 hour meeting with the team this Friday afternoon
```

#### List Meetings
```
show my meetings today
list meetings tomorrow
what do I have scheduled this week
```

#### Cancel a Meeting
```
cancel a meeting
```
Then select from the numbered list.

#### Voice Mode
```
voice
```
Toggle voice input/output on or off.

### Advanced Usage

#### Multi-Person Meetings
```
schedule a meeting with John, Sarah, and Bob tomorrow at 2pm
```

#### Platform-Specific
```
schedule a Teams call with Bob tomorrow at 3pm
book a Zoom meeting with the design team Friday
set up an in-person meeting with Jane next week
```

#### Custom Duration
```
schedule a 60 minute meeting with the team tomorrow
book a 90 minute planning session next week
```

#### Context-Aware
```
# First meeting
schedule a meeting with Sarah tomorrow

# Later...
schedule another meeting with her next week  # "her" = Sarah
```

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Google Calendar Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `credentials.json`
6. Place `credentials.json` in the project directory
7. Run the assistant - it will open a browser for authentication

### Voice Configuration

Edit voice settings in `VoiceAssistant.setup_voice()`:

```python
self.engine.setProperty('rate', 175)      # Speech rate (WPM)
self.engine.setProperty('volume', 0.9)    # Volume (0.0-1.0)
```

## 📁 Project Structure

```
scheduling-assistant/
├── scheduling_assistant_fixed.py   # Main application
├── .env                             # API keys (create this)
├── credentials.json                 # Google OAuth (download from Google)
├── token.pickle                     # Auto-generated auth token
├── events.json                      # Local meeting storage
├── chat_memory.json                # Conversation history
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── docs/                           # Additional documentation
    ├── COMPLETE_DOCUMENTATION.md   # Full technical docs
    ├── QUICK_REFERENCE.md         # Developer cheat sheet
    ├── STATE_BREAKDOWN.md         # State management guide
    └── WORKFLOW_VISUALIZATION.md  # Architecture diagrams
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         User Interface                   │
│    (Voice Input / Text Input)           │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       LangGraph Workflow                 │
│                                          │
│  Classifier → Clarify → Route           │
│       ↓                    ↓             │
│    Tools ← ← ← ← ← Cancel               │
│       ↓                                  │
│    Output                                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│          Data Layer                      │
│                                          │
│  Local Store | Google Calendar | Memory │
└──────────────────────────────────────────┘
```

### Key Components

- **Classifier** - Uses GPT-4o-mini to understand user intent
- **Clarify** - Asks for missing information interactively
- **Route** - Directs to appropriate handler based on intent
- **Tools** - Executes calendar operations (find slots, create meetings, etc.)
- **Cancel** - Specialized handler for meeting deletions
- **Output** - Formats responses and saves to memory

## 🎓 How It Works

### 1. Intent Classification
The assistant analyzes your natural language request using GPT-4o-mini to determine:
- **Intent**: What you want to do (schedule, list, cancel)
- **Participants**: Who's involved
- **Time**: When it should happen
- **Duration**: How long
- **Platform**: Where (Zoom, Teams, etc.)

### 2. Smart Slot Finding
The system searches for available times by:
- Checking your local calendar
- Querying Google Calendar (if enabled)
- Detecting conflicts automatically
- Suggesting the best available slot

### 3. Conflict Detection
Before confirming any meeting, it:
- Compares with all existing meetings
- Checks for time overlaps
- Warns you about conflicts
- Suggests alternative times if needed

### 4. Multi-Source Sync
Your meetings are:
- Saved locally (JSON file)
- Synced to Google Calendar
- Linked via unique IDs
- Deduplicated automatically

### 5. Context Memory
The assistant remembers:
- Recent conversations
- Last person you met with
- Your preferred platforms
- Meeting patterns

## 🔧 Troubleshooting

### Voice Features Not Working

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-pyaudio portaudio19-dev
pip install pyaudio
```

**Windows:**
```bash
pip install pyaudio
```

### Google Calendar Not Connecting

1. Verify `credentials.json` exists in project directory
2. Delete `token.pickle` and re-run to re-authenticate
3. Check that Google Calendar API is enabled in Google Cloud Console

### Intent Misclassification

- Be more specific in your requests
- Use keywords: "schedule", "list", "show", "cancel"
- Check context with `memory` command
- Clear memory if needed: `clear memory`

### Max Loops Error

- Restart with a clearer, more complete request
- Ensure all required information is provided
- Check logs for underlying tool errors

## 📊 Features Comparison

| Feature | This Assistant | Google Calendar | Calendar Apps |
|---------|---------------|-----------------|---------------|
| Natural Language | ✅ | ❌ | ❌ |
| Voice Control | ✅ | ❌ | ❌ |
| Conflict Detection | ✅ | ⚠️ Manual | ⚠️ Manual |
| Context Memory | ✅ | ❌ | ❌ |
| Multi-Platform | ✅ | ⚠️ Limited | ⚠️ Limited |
| Local Backup | ✅ | ❌ | ❌ |
| Conversational | ✅ | ❌ | ❌ |

## 🤝 Contributing

Contributions are welcome! Here are some ways you can help:

- 🐛 Report bugs
- 💡 Suggest new features
- 📝 Improve documentation
- 🔧 Submit pull requests

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit: `git commit -am 'Add feature'`
6. Push: `git push origin feature-name`
7. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - For the amazing framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - For workflow orchestration
- [OpenAI](https://openai.com/) - For GPT-4o-mini
- [Google Calendar API](https://developers.google.com/calendar) - For calendar integration

## 📚 Documentation

- [Complete Documentation](docs/COMPLETE_DOCUMENTATION.md) - Full technical manual
- [Quick Reference](docs/QUICK_REFERENCE.md) - Developer cheat sheet
- [State Breakdown](docs/STATE_BREAKDOWN.md) - Understanding state management
- [Workflow Visualization](docs/WORKFLOW_VISUALIZATION.md) - Architecture diagrams

## 🔮 Roadmap

- [ ] Email notifications
- [ ] Recurring meetings support
- [ ] Time zone conversion
- [ ] Integration with Slack/Teams
- [ ] Mobile app
- [ ] Meeting notes and transcription
- [ ] Smart rescheduling suggestions
- [ ] Multi-language support

## 💬 Support

- 📧 Email: support@example.com
- 💬 Discord: [Join our server](https://discord.gg/example)
- 🐦 Twitter: [@scheduling_ai](https://twitter.com/example)
- 📖 Docs: [Full Documentation](docs/COMPLETE_DOCUMENTATION.md)

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

## 🔐 Security

This project handles sensitive data. Please ensure:
- Keep your `.env` file secure and never commit it
- Don't share your `credentials.json` or `token.pickle`
- Review code before running in production
- Use environment variables for all secrets

## 📈 Stats

- 🚀 1,600+ lines of production code
- 📝 100+ pages of documentation
- 🎯 6 main workflow nodes
- 🛠️ 20+ state variables
- ⚡ Sub-second response time

## 🎉 Getting Help

Stuck? Here's what to try:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [Complete Documentation](docs/COMPLETE_DOCUMENTATION.md)
3. Look at code examples in [Quick Reference](docs/QUICK_REFERENCE.md)
4. Open an issue on GitHub
5. Ask in our Discord community

## 💡 Tips

- Use voice mode for hands-free operation: `voice`
- Check your conversation history: `memory`
- Be specific in requests for best results
- The assistant learns from context over time
- Use platform names for automatic platform selection

## 🌟 Example Workflows

### Morning Routine
```
show my meetings today
schedule lunch with John at noon
what do I have this afternoon
```

### Quick Scheduling
```
voice
[Speak] "Schedule a meeting with the team tomorrow at 2pm for one hour"
[Listen] "Meeting confirmed for Thursday, October 31 at 02:00 PM..."
```

### Managing Conflicts
```
schedule a meeting with Sarah tomorrow at 2pm
⚠️ Warning: This meeting conflicts with 1 existing meeting(s).
list meetings tomorrow
cancel a meeting
[Select conflicting meeting]
schedule a meeting with Sarah tomorrow at 2pm
✅ Meeting confirmed (no conflicts)
```

---

<div align="center">

**Made with ❤️ using LangGraph and GPT-4o-mini**

[Report Bug](https://github.com/yourusername/repo/issues) · [Request Feature](https://github.com/yourusername/repo/issues) · [Documentation](docs/COMPLETE_DOCUMENTATION.md)

</div>
