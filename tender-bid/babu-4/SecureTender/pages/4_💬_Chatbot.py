import streamlit as st
import json
from datetime import datetime
from database.db_manager import DatabaseManager
from services.chatbot_service import ChatbotService

# Page configuration
st.set_page_config(
    page_title="Chatbot - ACTMS",
    page_icon="💬",
    layout="wide"
)

# Initialize services
@st.cache_resource
def init_services():
    return DatabaseManager(), ChatbotService()

def main():
    db, chatbot_service = init_services()
    
    st.title("💬 ACTMS AI Assistant")
    st.markdown("Get instant help and guidance for using the Anti-Corruption Tender Management System.")
    
    # Initialize session state for conversation
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "suggested_questions" not in st.session_state:
        st.session_state.suggested_questions = chatbot_service.get_suggested_questions()
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        chat_interface(chatbot_service)
    
    with col2:
        sidebar_content(db, chatbot_service)

def chat_interface(chatbot_service):
    """Main chat interface"""
    st.subheader("💬 Chat with AI Assistant")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        if st.session_state.chat_history:
            for i, message in enumerate(st.session_state.chat_history):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        
                        # Show source and confidence if available
                        if "metadata" in message:
                            metadata = message["metadata"]
                            if metadata.get("source") or metadata.get("confidence"):
                                with st.expander("ℹ️ Response Details"):
                                    if metadata.get("source"):
                                        st.write(f"**Source:** {metadata['source']}")
                                    if metadata.get("confidence"):
                                        st.write(f"**Confidence:** {metadata['confidence']:.1%}")
        else:
            # Welcome message
            with st.chat_message("assistant"):
                st.write("""
                👋 Hello! I'm the ACTMS AI Assistant. I'm here to help you with:
                
                - 📋 Understanding the tender management process
                - 📝 Guidance on bid submission
                - 🔍 Explaining AI analysis results
                - 🤖 System features and navigation
                - ❓ Answering questions about anti-corruption measures
                
                How can I assist you today?
                """)
    
    # Chat input
    if prompt := st.chat_input("Type your question here..."):
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get chatbot response
        with st.spinner("🤔 Thinking..."):
            try:
                # Prepare conversation history for context
                conversation_history = []
                for msg in st.session_state.chat_history[-10:]:  # Last 10 messages
                    conversation_history.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                response_data = chatbot_service.get_response(prompt, conversation_history[:-1])
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_data["response"],
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "source": response_data.get("source"),
                        "confidence": response_data.get("confidence")
                    }
                })
                
                # Rerun to update the interface
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Sorry, I encountered an error: {str(e)}")

def sidebar_content(db, chatbot_service):
    """Sidebar with helpful content"""
    st.subheader("🚀 Quick Actions")
    
    # Quick action buttons
    quick_actions = chatbot_service.get_quick_actions()
    
    for action in quick_actions:
        if st.button(action["title"], key=f"action_{action['title']}", help=action["description"]):
            # Add quick action as a chat message
            user_message = f"Help me with: {action['title']}"
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Get chatbot response immediately
            try:
                # Prepare conversation history for context
                conversation_history = []
                for msg in st.session_state.chat_history[-10:]:  # Last 10 messages
                    conversation_history.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                response_data = chatbot_service.get_response(user_message, conversation_history[:-1])
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_data["response"],
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "source": response_data.get("source"),
                        "confidence": response_data.get("confidence")
                    }
                })
            except Exception as e:
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": f"❌ Sorry, I encountered an error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
            
            st.rerun()
    
    st.markdown("---")
    
    # Suggested questions
    st.subheader("💡 Suggested Questions")
    
    with st.expander("📋 Tender Management"):
        suggested_tender = [
            "How do I upload a new tender?",
            "What information is extracted from tender documents?",
            "How do I set a tender deadline?",
            "Can I edit a tender after submission?"
        ]
        for question in suggested_tender:
            if st.button(question, key=f"tender_{question}"):
                add_suggested_question(question)
    
    with st.expander("📝 Bid Submission"):
        suggested_bid = [
            "How do I submit a bid?",
            "What makes a bid suspicious?",
            "How is my proposal analyzed?",
            "Can I withdraw a submitted bid?"
        ]
        for question in suggested_bid:
            if st.button(question, key=f"bid_{question}"):
                add_suggested_question(question)
    
    with st.expander("🔍 AI Analysis"):
        suggested_ai = [
            "How does the AI detection work?",
            "What is an anomaly score?",
            "How can I improve my bid score?",
            "What triggers a suspicious bid alert?"
        ]
        for question in suggested_ai:
            if st.button(question, key=f"ai_{question}"):
                add_suggested_question(question)
    
    st.markdown("---")
    
    # System status
    st.subheader("📊 System Overview")
    
    try:
        # Get quick stats
        tender_count = db.get_tender_count()
        bid_count = db.get_bid_count()
        alert_count = db.get_alert_count()
        
        st.metric("Active Tenders", tender_count)
        st.metric("Total Bids", bid_count)
        st.metric("Active Alerts", alert_count)
        
        # Show system status
        if alert_count > 0:
            st.warning(f"⚠️ {alert_count} alerts need attention")
        else:
            st.success("✅ All systems normal")
        
    except Exception as e:
        st.error("❌ Unable to load system status")
    
    st.markdown("---")
    
    # Chat controls
    st.subheader("🛠️ Chat Controls")
    
    if st.button("🗑️ Clear Chat History", key="clear_chat"):
        st.session_state.chat_history = []
        st.success("Chat history cleared!")
        st.rerun()
    
    if st.button("💾 Export Chat", key="export_chat"):
        export_chat_history()
    
    # Chat statistics
    if st.session_state.chat_history:
        with st.expander("📈 Chat Statistics"):
            user_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "user"])
            assistant_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "assistant"])
            
            st.write(f"**Your messages:** {user_messages}")
            st.write(f"**Assistant responses:** {assistant_messages}")
            st.write(f"**Total exchanges:** {min(user_messages, assistant_messages)}")

def add_suggested_question(question):
    """Add a suggested question to chat history and get AI response"""
    st.session_state.chat_history.append({
        "role": "user",
        "content": question,
        "timestamp": datetime.now().isoformat()
    })
    
    # Get chatbot response immediately
    try:
        from services.chatbot_service import ChatbotService
        chatbot_service = ChatbotService()
        
        # Prepare conversation history for context
        conversation_history = []
        for msg in st.session_state.chat_history[-10:]:  # Last 10 messages
            conversation_history.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        response_data = chatbot_service.get_response(question, conversation_history[:-1])
        
        # Add assistant response to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response_data["response"],
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "source": response_data.get("source"),
                "confidence": response_data.get("confidence")
            }
        })
    except Exception as e:
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": f"❌ Sorry, I encountered an error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
    
    st.rerun()

def export_chat_history():
    """Export chat history as JSON"""
    if not st.session_state.chat_history:
        st.warning("No chat history to export")
        return
    
    try:
        chat_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_messages": len(st.session_state.chat_history),
            "conversation": st.session_state.chat_history
        }
        
        json_string = json.dumps(chat_data, indent=2)
        
        st.download_button(
            label="📥 Download Chat History",
            data=json_string,
            file_name=f"actms_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
key="download_chat"
        )
        
    except Exception as e:
        st.error(f"❌ Error exporting chat history: {str(e)}")

if __name__ == "__main__":
    main()
