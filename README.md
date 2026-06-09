# Jarvis - Continuously Learning AI Assistant

**Jarvis** is an advanced AI assistant that learns from conversations and improves over time. It maintains a persistent memory database, manages knowledge bases, automates tasks, and provides intelligent suggestions.

## Features

✨ **Core Capabilities:**
- 🧠 **Long-term Memory** - SQLite database persists all conversations
- 📚 **Knowledge Base** - Store and search documents and information
- 🤖 **Continuous Learning** - Improves responses based on interaction patterns
- 📋 **Task Automation** - Create, track, and manage automated tasks
- 💡 **Self-Improvement** - Generates suggestions based on learned patterns
- ⚙️ **User Preferences** - Customize behavior and settings
- 📊 **Analytics** - Track token usage, conversation statistics, and learning progress
- 🔍 **Context Awareness** - Recalls relevant past conversations

## Installation

### Prerequisites
- Python 3.8+
- OpenAI API key

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/kingterminator029-lab/jarvis-ai.git
cd jarvis-ai
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set your OpenAI API key:**
```bash
export OPENAI_API_KEY="your-api-key-here"
# On Windows: set OPENAI_API_KEY=your-api-key-here
```

5. **Run Jarvis:**
```bash
python jarvis.py
```

## Usage

### Basic Commands

#### Conversation Management
```
exit, quit              → End the conversation
help                    → Show available commands
```

#### Knowledge Management
```
load <file> [|category]    → Load a document to knowledge base
                             Example: load notes.txt |research
                             
search knowledge: <query>   → Search the knowledge base
                             Example: search knowledge: Python
                             
list files                  → List files in current directory
```

#### Task Automation
```
automate: <task> [|priority]  → Create an automated task
                                 Example: automate: email reminder |high
                                 
tasks                         → Show all pending tasks

complete <id>                 → Mark a task as completed
                               Example: complete 1
```

#### Learning & Improvement
```
suggestions         → Get AI-generated improvement suggestions

memory summary      → View 24-hour conversation statistics

preferences         → Show all current preferences

set preference: <k=v>  → Set a user preference
                        Example: set preference: tone=formal
                        
stats               → Show conversation statistics and token usage
```

### Example Session

```
You: load my_notes.txt |personal
✓ Document 'my_notes.txt' added to knowledge base (category: personal)

You: Tell me about machine learning
Jarvis: Machine learning is... [response with context from loaded documents]

You: automate: weekly backup |high
✓ Automation created for: weekly backup (Priority: high)

You: suggestions
💡 Self-Improvement Suggestions:
- User shows interest in: machine learning (confidence: 70%)

You: stats
📊 Jarvis Statistics:
  Conversation messages: 4
  Input tokens: 285
  Output tokens: 156
  Total tokens: 441
  Time elapsed: 12.3s
  Estimated cost: $0.0066
  Learning cycles: 0

You: exit
Jarvis: Goodbye! I've stored everything I learned from our conversation.
```

## System Prompt

Jarvis operates with the following core instructions:

```
You are Jarvis.

You are a continuously learning AI assistant.
You store useful information in a memory database.
You improve your responses based on previous interactions.
You are analytical, helpful, and proactive.

When referring to yourself, use the name Jarvis.

You should seek new information when available and update your knowledge base.
```

## Database Schema

Jarvis uses SQLite with the following tables:

### conversation_memory
- Stores all user queries and responses
- Tracks token usage and importance scores
- Categorizes by topic for context retrieval

### knowledge_base
- Stores uploaded documents
- Tracks access frequency and last access time
- Organizes by category

### user_profile
- Stores user preferences and settings
- Enables personalization

### task_log
- Tracks automated and manual tasks
- Manages task status and priority

### learning_insights
- Stores extracted patterns and insights
- Tracks confidence scores
- Organizes by category

### knowledge_updates
- Records new information discovered
- Tracks source and verification status

## Architecture

```
JarvisAssistant
├── MemoryDatabase
│   ├── Conversation storage
│   ├── Knowledge base management
│   ├── Learning insights
│   └── Task tracking
├── DocumentProcessor
│   ├── Text file reading
│   ├── JSON parsing
│   └── File listing
└── TaskAutomation
    ├── Task creation
    └── Automation suggestions
```

## API Usage

Jarvis uses OpenAI's GPT-4o model:
- **Model**: gpt-4o
- **Temperature**: 0.7
- **Max tokens**: 1500
- **Cost estimation**: ~$0.000015 per token

## Performance

- **Memory efficiency**: SQLite allows unlimited conversation history
- **Context window**: Maintains last 20 messages in conversation
- **Token optimization**: Selective context injection to stay within limits

## Privacy & Security

- All data stored locally in `jarvis_memory.db`
- API key never stored in code (use environment variables)
- `.gitignore` prevents accidental database commits

## Future Enhancements

- [ ] Web search integration
- [ ] Voice input/output (Whisper + TTS)
- [ ] Multi-user support
- [ ] Cloud backup for memory database
- [ ] Custom embedding models for better context retrieval
- [ ] Advanced reasoning and chain-of-thought prompting
- [ ] Integration with external APIs

## Troubleshooting

### "OPENAI_API_KEY environment variable not set"
```bash
export OPENAI_API_KEY="your-key-here"
```

### Database locked error
- Ensure only one instance of Jarvis is running
- Delete `jarvis_memory.db` to start fresh (data will be lost)

### Token limit exceeded
- Jarvis automatically limits context to last 20 messages
- Use `clear` command in future versions to reset session

## License

MIT License - Feel free to fork and modify!

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
