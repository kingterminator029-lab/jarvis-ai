import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from openai import OpenAI
import tiktoken
from pathlib import Path
import hashlib

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(api_key=api_key)

MODEL = "gpt-4o"
SYSTEM_PROMPT = """
You are Jarvis.

You are a continuously learning AI assistant.
You store useful information in a memory database.
You improve your responses based on previous interactions.
You are analytical, helpful, and proactive.

When referring to yourself, use the name Jarvis.

You should seek new information when available and update your knowledge base.
"""

encoding = tiktoken.encoding_for_model(MODEL)


class MemoryDatabase:
    """Manages long-term memory with SQLite"""
    
    def __init__(self, db_path: str = "jarvis_memory.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Conversation memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_memory (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_message TEXT,
                assistant_response TEXT,
                tokens_used INTEGER,
                context_tags TEXT,
                importance_score REAL DEFAULT 0.5,
                topic TEXT
            )
        """)
        
        # Personal knowledge base
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY,
                document_name TEXT UNIQUE,
                content TEXT,
                content_hash TEXT,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME,
                access_count INTEGER DEFAULT 0,
                category TEXT
            )
        """)
        
        # User preferences and personality
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY,
                preference_key TEXT UNIQUE,
                preference_value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Task automation log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_log (
                id INTEGER PRIMARY KEY,
                task_name TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                status TEXT DEFAULT 'pending',
                automation_type TEXT,
                priority TEXT DEFAULT 'normal'
            )
        """)
        
        # Learning insights and patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_insights (
                id INTEGER PRIMARY KEY,
                insight_type TEXT,
                content TEXT,
                confidence_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                applied_count INTEGER DEFAULT 0,
                category TEXT
            )
        """)
        
        # Knowledge updates
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_updates (
                id INTEGER PRIMARY KEY,
                update_type TEXT,
                topic TEXT,
                new_information TEXT,
                source TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 0
            )
        """)
        
        self.conn.commit()
    
    def store_conversation(self, user_msg: str, assistant_msg: str, tokens: int, tags: str = "", topic: str = ""):
        """Store conversation in memory with topic classification"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO conversation_memory (user_message, assistant_response, tokens_used, context_tags, topic)
            VALUES (?, ?, ?, ?, ?)
        """, (user_msg, assistant_msg, tokens, tags, topic))
        self.conn.commit()
    
    def retrieve_relevant_memories(self, query: str, limit: int = 5, topic: str = "") -> List[Dict]:
        """Retrieve relevant past conversations"""
        cursor = self.conn.cursor()
        
        if topic:
            cursor.execute("""
                SELECT user_message, assistant_response, timestamp, importance_score, topic
                FROM conversation_memory
                WHERE (user_message LIKE ? OR context_tags LIKE ? OR topic = ?)
                ORDER BY importance_score DESC, timestamp DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", topic, limit))
        else:
            cursor.execute("""
                SELECT user_message, assistant_response, timestamp, importance_score, topic
                FROM conversation_memory
                WHERE user_message LIKE ? OR context_tags LIKE ?
                ORDER BY importance_score DESC, timestamp DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def add_document(self, name: str, content: str, category: str = "general"):
        """Add document to knowledge base"""
        cursor = self.conn.cursor()
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        cursor.execute("""
            INSERT OR REPLACE INTO knowledge_base (document_name, content, content_hash, category)
            VALUES (?, ?, ?, ?)
        """, (name, content, content_hash, category))
        self.conn.commit()
        print(f"✓ Document '{name}' added to knowledge base (category: {category})")
    
    def search_knowledge_base(self, query: str, limit: int = 3, category: str = "") -> List[Dict]:
        """Search personal knowledge base"""
        cursor = self.conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT document_name, content, access_count, category
                FROM knowledge_base
                WHERE (content LIKE ? OR document_name LIKE ?) AND category = ?
                ORDER BY access_count DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", category, limit))
        else:
            cursor.execute("""
                SELECT document_name, content, access_count, category
                FROM knowledge_base
                WHERE content LIKE ? OR document_name LIKE ?
                ORDER BY access_count DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        # Update access count
        for result in results:
            cursor.execute("""
                UPDATE knowledge_base 
                SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
                WHERE document_name = ?
            """, (result['document_name'],))
        self.conn.commit()
        
        return results
    
    def set_preference(self, key: str, value: str):
        """Store user preference"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_profile (preference_key, preference_value)
            VALUES (?, ?)
        """, (key, value))
        self.conn.commit()
    
    def get_preference(self, key: str) -> Optional[str]:
        """Retrieve user preference"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT preference_value FROM user_profile WHERE preference_key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def get_all_preferences(self) -> Dict[str, str]:
        """Get all user preferences"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT preference_key, preference_value FROM user_profile")
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def log_task(self, task_name: str, description: str, automation_type: str = "manual", priority: str = "normal"):
        """Log a task"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO task_log (task_name, description, automation_type, priority)
            VALUES (?, ?, ?, ?)
        """, (task_name, description, automation_type, priority))
        self.conn.commit()
    
    def get_pending_tasks(self) -> List[Dict]:
        """Get pending tasks"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM task_log WHERE status = 'pending'
            ORDER BY priority DESC, created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def complete_task(self, task_id: int):
        """Mark task as completed"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE task_log SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (task_id,))
        self.conn.commit()
    
    def add_learning_insight(self, insight_type: str, content: str, confidence: float = 0.8, category: str = "general"):
        """Store learning insights"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO learning_insights (insight_type, content, confidence_score, category)
            VALUES (?, ?, ?, ?)
        """, (insight_type, content, confidence, category))
        self.conn.commit()
    
    def get_improvement_suggestions(self, limit: int = 5) -> List[Dict]:
        """Get self-improvement suggestions"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM learning_insights
            WHERE confidence_score > 0.7
            ORDER BY confidence_score DESC, created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def add_knowledge_update(self, update_type: str, topic: str, information: str, source: str = ""):
        """Add knowledge update"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO knowledge_updates (update_type, topic, new_information, source)
            VALUES (?, ?, ?, ?)
        """, (update_type, topic, information, source))
        self.conn.commit()
        print(f"✓ Knowledge updated: {topic} ({update_type})")
    
    def get_knowledge_updates(self, verified_only: bool = False, limit: int = 10) -> List[Dict]:
        """Get recent knowledge updates"""
        cursor = self.conn.cursor()
        
        if verified_only:
            cursor.execute("""
                SELECT * FROM knowledge_updates WHERE verified = 1
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
        else:
            cursor.execute("""
                SELECT * FROM knowledge_updates
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_conversation_summary(self, hours: int = 24) -> Dict:
        """Get conversation summary for a time period"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total_conversations,
                   SUM(tokens_used) as total_tokens,
                   COUNT(DISTINCT topic) as unique_topics,
                   AVG(importance_score) as avg_importance
            FROM conversation_memory
            WHERE timestamp > datetime('now', '-' || ? || ' hours')
        """, (hours,))
        
        result = cursor.fetchone()
        return dict(result) if result else {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class DocumentProcessor:
    """Handles document reading and processing"""
    
    @staticmethod
    def read_text_file(file_path: str) -> str:
        """Read text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    @staticmethod
    def read_json_file(file_path: str) -> Dict:
        """Read JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Error reading JSON: {str(e)}"}
    
    @staticmethod
    def list_files(directory: str = ".") -> List[str]:
        """List files in directory"""
        try:
            path = Path(directory)
            files = [str(f) for f in path.glob("*") if f.is_file()]
            return files[:20]  # Limit to 20 files
        except Exception as e:
            return [f"Error listing files: {str(e)}"]


class TaskAutomation:
    """Handles task automation"""
    
    def __init__(self, memory_db: MemoryDatabase):
        self.memory_db = memory_db
    
    def create_automation(self, task_name: str, description: str, priority: str = "normal") -> str:
        """Create task automation"""
        self.memory_db.log_task(task_name, description, automation_type="automated", priority=priority)
        return f"✓ Automation created for: {task_name} (Priority: {priority})"
    
    def get_automation_suggestions(self) -> List[str]:
        """Get automation suggestions based on patterns"""
        pending_tasks = self.memory_db.get_pending_tasks()
        suggestions = []
        
        if len(pending_tasks) > 5:
            suggestions.append("💡 You have many pending tasks. Consider automating repetitive ones.")
        
        if len(pending_tasks) > 0:
            task_types = {}
            for task in pending_tasks:
                task_type = task['automation_type']
                task_types[task_type] = task_types.get(task_type, 0) + 1
            
            for task_type, count in task_types.items():
                if count > 2:
                    suggestions.append(f"💡 {count} {task_type} tasks detected. Could be automated.")
        
        return suggestions


class JarvisAssistant:
    """Main Jarvis AI Assistant with continuous learning"""
    
    def __init__(self):
        self.memory_db = MemoryDatabase()
        self.doc_processor = DocumentProcessor()
        self.task_automation = TaskAutomation(self.memory_db)
        
        self.token_usage = {"input": 0, "output": 0}
        self.start_time = datetime.now()
        self.conversation_history = []
        self.learning_counter = 0
    
    def get_context_from_memory(self, user_input: str) -> str:
        """Get relevant context from memory"""
        memories = self.memory_db.retrieve_relevant_memories(user_input, limit=3)
        if memories:
            context = "\n[RELEVANT MEMORIES]:\n"
            for mem in memories:
                context += f"- User asked: {mem['user_message'][:80]}...\n"
                context += f"  Jarvis responded: {mem['assistant_response'][:80]}...\n"
            return context
        return ""
    
    def get_knowledge_context(self, user_input: str) -> str:
        """Get relevant knowledge base context"""
        docs = self.memory_db.search_knowledge_base(user_input, limit=2)
        if docs:
            context = "\n[KNOWLEDGE BASE REFERENCES]:\n"
            for doc in docs:
                context += f"- From '{doc['document_name']}': {doc['content'][:150]}...\n"
            return context
        return ""
    
    def get_learning_context(self) -> str:
        """Get learning insights context"""
        insights = self.memory_db.get_improvement_suggestions(limit=2)
        if insights:
            context = "\n[LEARNED PATTERNS]:\n"
            for insight in insights:
                context += f"- {insight['content']} (confidence: {insight['confidence_score']:.0%})\n"
            return context
        return ""
    
    def process_commands(self, user_input: str) -> Optional[str]:
        """Process special commands"""
        
        if user_input.lower() == "exit" or user_input.lower() == "quit":
            return "exit"
        
        elif user_input.lower() == "help":
            return self.display_help()
        
        elif user_input.lower().startswith("load "):
            file_path = user_input[5:].strip()
            category = "general"
            if "|" in file_path:
                file_path, category = file_path.split("|", 1)
                file_path = file_path.strip()
                category = category.strip()
            
            content = self.doc_processor.read_text_file(file_path)
            if not content.startswith("Error"):
                self.memory_db.add_document(file_path, content, category)
                return f"✓ Loaded and stored: {file_path} (category: {category})"
            return content
        
        elif user_input.lower().startswith("search knowledge:"):
            query = user_input[16:].strip()
            results = self.memory_db.search_knowledge_base(query)
            if results:
                response = "📚 Knowledge Base Results:\n"
                for doc in results:
                    response += f"- [{doc['category']}] {doc['document_name']}\n"
                    response += f"  {doc['content'][:100]}...\n"
                return response
            return "No documents found in knowledge base"
        
        elif user_input.lower().startswith("automate:"):
            task = user_input[9:].strip()
            priority = "normal"
            if "|" in task:
                task, priority = task.split("|", 1)
                task = task.strip()
                priority = priority.strip().lower()
            return self.task_automation.create_automation(task, f"Automated task: {task}", priority)
        
        elif user_input.lower() == "tasks":
            tasks = self.memory_db.get_pending_tasks()
            if tasks:
                response = "📋 Pending Tasks:\n"
                for task in tasks:
                    response += f"- [{task['priority'].upper()}] {task['task_name']}: {task['description']}\n"
                return response
            return "No pending tasks"
        
        elif user_input.lower().startswith("complete "):
            try:
                task_id = int(user_input[9:].strip())
                self.memory_db.complete_task(task_id)
                return f"✓ Task {task_id} marked as completed"
            except:
                return "Invalid task ID"
        
        elif user_input.lower() == "suggestions":
            suggestions = self.memory_db.get_improvement_suggestions()
            if suggestions:
                response = "💡 Self-Improvement Suggestions:\n"
                for suggestion in suggestions:
                    response += f"- {suggestion['content']}\n"
                    response += f"  (confidence: {suggestion['confidence_score']:.0%})\n"
                return response
            
            # Auto-generate suggestions
            auto_suggestions = self.task_automation.get_automation_suggestions()
            if auto_suggestions:
                return "💡 Auto-Generated Suggestions:\n" + "\n".join(auto_suggestions)
            
            return "No improvement suggestions at this time"
        
        elif user_input.lower() == "memory summary":
            summary = self.memory_db.get_conversation_summary(hours=24)
            response = "📊 24-Hour Memory Summary:\n"
            response += f"  Total conversations: {summary.get('total_conversations', 0)}\n"
            response += f"  Total tokens used: {summary.get('total_tokens', 0)}\n"
            response += f"  Unique topics: {summary.get('unique_topics', 0)}\n"
            response += f"  Average importance: {summary.get('avg_importance', 0):.2f}\n"
            return response
        
        elif user_input.lower() == "stats":
            return self.display_stats()
        
        elif user_input.lower().startswith("set preference:"):
            pref = user_input[14:].strip()
            key, value = pref.split("=", 1) if "=" in pref else (pref, "true")
            self.memory_db.set_preference(key.strip(), value.strip())
            return f"✓ Preference set: {key.strip()} = {value.strip()}"
        
        elif user_input.lower() == "preferences":
            prefs = self.memory_db.get_all_preferences()
            if prefs:
                response = "⚙️ Current Preferences:\n"
                for key, value in prefs.items():
                    response += f"  {key} = {value}\n"
                return response
            return "No preferences set yet"
        
        elif user_input.lower() == "list files":
            files = self.doc_processor.list_files()
            response = "📂 Local Files:\n"
            for f in files[:10]:
                response += f"  {f}\n"
            return response
        
        return None
    
    def display_help(self) -> str:
        """Display help menu"""
        return """
╔════════════════════════════════════════════════════════════╗
║         JARVIS - Advanced Learning Assistant Help          ║
╠════════════════════════════════════════════════════════════╣
║  CONVERSATION MANAGEMENT:                                 ║
║    exit, quit              → End the conversation          ║
║    help                    → Show this help message        ║
║                                                            ║
║  KNOWLEDGE MANAGEMENT:                                    ║
║    load <file> [|category] → Load document to knowledge   ║
║    search knowledge: <q>   → Search knowledge base        ║
║    list files              → List local files             ║
║                                                            ║
║  TASK AUTOMATION:                                         ║
║    automate: <task> [|priority] → Create automation      ║
║    tasks                   → Show pending tasks            ║
║    complete <id>           → Mark task as completed       ║
║                                                            ║
║  LEARNING & IMPROVEMENT:                                  ║
║    suggestions             → Get improvement ideas        ║
║    memory summary          → 24-hour memory stats         ║
║    preferences             → Show all preferences         ║
║    set preference: <k=v>   → Set user preference         ║
║    stats                   → Show conversation stats      ║
╚════════════════════════════════════════════════════════════╝
"""
    
    def display_stats(self) -> str:
        """Display statistics"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        total_tokens = self.token_usage["input"] + self.token_usage["output"]
        
        stats = f"""
📊 Jarvis Statistics:
  Conversation messages: {len(self.conversation_history)}
  Input tokens: {self.token_usage['input']}
  Output tokens: {self.token_usage['output']}
  Total tokens: {total_tokens}
  Time elapsed: {elapsed:.1f}s
  Estimated cost: ${total_tokens * 0.000015:.4f}
  Learning cycles: {self.learning_counter}
"""
        return stats
    
    def update_knowledge_from_response(self, user_input: str, response: str):
        """Extract and store new knowledge from the response"""
        self.learning_counter += 1
        
        # Store every 5 exchanges as a learning opportunity
        if self.learning_counter % 5 == 0:
            # Add insight about user interests
            self.memory_db.add_learning_insight(
                insight_type="user_interest",
                content=f"User shows interest in: {user_input[:60]}",
                confidence=0.7,
                category="user_behavior"
            )
            
            # Add insight about response effectiveness
            self.memory_db.add_learning_insight(
                insight_type="response_quality",
                content=f"Response effectiveness for topic: {user_input[:40]}",
                confidence=0.75,
                category="response_optimization"
            )
    
    def chat(self, user_input: str) -> str:
        """Process user input and generate response"""
        
        # Check for commands
        command_result = self.process_commands(user_input)
        if command_result:
            if command_result == "exit":
                return "exit"
            return command_result
        
        # Build enhanced context from memory and knowledge
        memory_context = self.get_context_from_memory(user_input)
        knowledge_context = self.get_knowledge_context(user_input)
        learning_context = self.get_learning_context()
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Build enriched system prompt with learned context
        enriched_prompt = SYSTEM_PROMPT
        if memory_context:
            enriched_prompt += "\n" + memory_context
        if knowledge_context:
            enriched_prompt += "\n" + knowledge_context
        if learning_context:
            enriched_prompt += "\n" + learning_context
        
        # Prepare messages for API
        messages = [
            {"role": "system", "content": enriched_prompt}
        ]
        messages.extend(self.conversation_history[-20:])  # Last 20 messages
        
        try:
            # Make API call
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            assistant_message = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            # Update token usage
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            self.token_usage["input"] += input_tokens
            self.token_usage["output"] += output_tokens
            
            # Store in memory
            total_tokens = input_tokens + output_tokens
            self.memory_db.store_conversation(
                user_input, 
                assistant_message, 
                total_tokens,
                tags=user_input[:30],
                topic=user_input.split()[0] if user_input.split() else "general"
            )
            
            # Update knowledge from this interaction
            self.update_knowledge_from_response(user_input, assistant_message)
            
            return f"{assistant_message}\n\n[Tokens - In: {input_tokens}, Out: {output_tokens}]"
        
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def run(self):
        """Run the main chatbot loop"""
        print("\n" + "="*65)
        print("        Welcome to Jarvis - Continuously Learning AI")
        print("="*65)
        print("I am Jarvis, your intelligent AI assistant.")
        print("I learn from our conversations and improve over time.")
        print("I maintain a memory database of our interactions.")
        print("Type 'help' for available commands")
        print("="*65 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                response = self.chat(user_input)
                
                if response == "exit":
                    print("\nJarvis: Goodbye! I've stored everything I learned from our conversation.")
                    print("Jarvis: My knowledge base is now more complete.")
                    break
                
                print(f"\nJarvis: {response}\n")
            
            except KeyboardInterrupt:
                print("\n\nJarvis: Session interrupted. All learnings and memories have been saved.")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
        
        self.memory_db.close()


if __name__ == "__main__":
    jarvis = JarvisAssistant()
    jarvis.run()
