import json
import os
from google import genai
from google.genai import types

class ChatbotService:
    def __init__(self):
        # Initialize Gemini client (using python_gemini integration)
        # the newest Gemini model is "gemini-2.5-flash" which is recommended
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash"
        
        # Load FAQ data
        self.faqs = self.load_faqs()
        
        # System prompt for the chatbot
        self.system_prompt = """You are an AI assistant for the Anti-Corruption Tender Management System (ACTMS). 
        You help users understand the tender process, bid submission, and system features.
        
        Your key responsibilities:
        1. Answer questions about tender management and bidding processes
        2. Explain system features and how to use them
        3. Provide guidance on anti-corruption best practices
        4. Help with technical issues and system navigation
        5. Explain AI analysis results and alerts
        
        Always be helpful, professional, and focused on transparency and anti-corruption measures.
        If you don't know something specific about the system, suggest they contact support or check the documentation.
        """
    
    def load_faqs(self):
        """Load FAQ data from JSON file"""
        try:
            with open('data/faqs.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_faqs()
    
    def get_default_faqs(self):
        """Default FAQ data if file not found"""
        return {
            "general": [
                {
                    "question": "What is ACTMS?",
                    "answer": "ACTMS (Anti-Corruption Tender Management System) is a comprehensive platform designed to ensure transparency and prevent corruption in government and organizational tender processes. It uses AI-powered detection to identify suspicious activities and maintain audit trails."
                },
                {
                    "question": "How do I submit a tender?",
                    "answer": "To submit a tender, go to the Tender Management page, click 'Upload New Tender', fill in the required details including title, description, department, estimated value, and deadline. You can also upload supporting documents which will be automatically analyzed for key information."
                },
                {
                    "question": "How does the AI analysis work?",
                    "answer": "Our AI system uses machine learning algorithms including Isolation Forest for anomaly detection. It analyzes bid patterns, submission timing, proposal content, and other factors to identify potentially suspicious activities. The system provides anomaly scores and explanations for its findings."
                }
            ],
            "bidding": [
                {
                    "question": "How do I submit a bid?",
                    "answer": "To submit a bid, go to the Bid Submission page, select the tender you want to bid on, enter your company information, bid amount, and detailed proposal. The system will automatically validate your submission and run AI analysis to ensure compliance."
                },
                {
                    "question": "What makes a bid suspicious?",
                    "answer": "Bids may be flagged as suspicious for various reasons including: unusual bid amounts compared to estimated values, very short or generic proposals, submissions outside normal business hours, patterns that deviate from typical bidding behavior, or missing required information."
                }
            ],
            "technical": [
                {
                    "question": "What file formats are supported for tender documents?",
                    "answer": "The system supports common document formats including PDF, DOC, DOCX, and TXT files. Documents are automatically processed using NLP to extract key information such as requirements, dates, contact information, and technical specifications."
                },
                {
                    "question": "How is data security ensured?",
                    "answer": "ACTMS implements multiple security measures including encrypted data storage, audit logging of all activities, user authentication, and secure file handling. All actions are tracked and logged for transparency and accountability."
                }
            ]
        }
    
    def get_response(self, user_message, conversation_history=None):
        """Get chatbot response using Gemini API"""
        try:
            # Check if the question matches any FAQ first
            faq_response = self.check_faqs(user_message)
            if faq_response:
                return {
                    "response": faq_response,
                    "source": "FAQ",
                    "confidence": 0.9
                }
            
            # Prepare conversation context
            conversation_text = ""
            if conversation_history:
                for msg in conversation_history[-5:]:  # Keep last 5 messages
                    role = "User" if msg["role"] == "user" else "Assistant"
                    conversation_text += f"{role}: {msg['content']}\n"
            
            # Create the prompt with system instructions and conversation context
            full_prompt = f"{self.system_prompt}\n\n"
            if conversation_text:
                full_prompt += f"Previous conversation:\n{conversation_text}\n"
            full_prompt += f"User: {user_message}\nAssistant:"
            
            # Get response from Gemini
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            
            return {
                "response": response.text if response.text else "I'm sorry, I couldn't generate a response.",
                "source": "AI",
                "confidence": 0.8
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, but I'm experiencing technical difficulties. Please try again later or contact support. Error: {str(e)}",
                "source": "Error",
                "confidence": 0.0
            }
    
    def check_faqs(self, user_message):
        """Check if user message matches any FAQ"""
        user_message_lower = user_message.lower()
        
        # Simple keyword matching for FAQs
        for category in self.faqs.values():
            for faq in category:
                question_words = faq["question"].lower().split()
                # Check if most question words are in user message
                matches = sum(1 for word in question_words if word in user_message_lower)
                if matches >= len(question_words) * 0.6:  # 60% match threshold
                    return faq["answer"]
        
        return None
    
    def get_suggested_questions(self):
        """Get list of suggested questions"""
        suggestions = []
        for category, faqs in self.faqs.items():
            for faq in faqs[:2]:  # Get first 2 from each category
                suggestions.append(faq["question"])
        return suggestions
    
    def analyze_user_intent(self, message):
        """Analyze user intent for better responses"""
        message_lower = message.lower()
        
        intents = {
            "tender_submission": ["submit tender", "upload tender", "create tender", "new tender"],
            "bid_submission": ["submit bid", "place bid", "bid on", "bidding"],
            "ai_analysis": ["ai analysis", "anomaly", "suspicious", "detection", "alert"],
            "system_help": ["how to", "help", "guide", "tutorial", "instructions"],
            "technical_support": ["error", "problem", "issue", "not working", "bug"],
            "general_info": ["what is", "about", "explain", "information"]
        }
        
        detected_intents = []
        for intent, keywords in intents.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected_intents.append(intent)
                    break
        
        return detected_intents if detected_intents else ["general_info"]
    
    def get_context_specific_response(self, message, context=None):
        """Get response based on specific context (e.g., current page)"""
        base_response = self.get_response(message)
        
        # Add context-specific information
        if context == "tender_management":
            if "how" in message.lower() and "tender" in message.lower():
                base_response["response"] += "\n\nSince you're on the Tender Management page, you can use the 'Upload New Tender' button to get started immediately."
        
        elif context == "bid_submission":
            if "bid" in message.lower():
                base_response["response"] += "\n\nYou can select a tender from the dropdown above and start filling out your bid information."
        
        elif context == "ai_analysis":
            if "suspicious" in message.lower() or "anomaly" in message.lower():
                base_response["response"] += "\n\nYou can view detailed AI analysis results and explanations in the current dashboard."
        
        return base_response
    
    def get_quick_actions(self):
        """Get quick action suggestions based on common user needs"""
        return [
            {
                "title": "Submit New Tender",
                "description": "Upload and create a new tender",
                "action": "Go to Tender Management"
            },
            {
                "title": "Place a Bid",
                "description": "Submit a bid on an active tender",
                "action": "Go to Bid Submission"
            },
            {
                "title": "View AI Analysis",
                "description": "Check for suspicious activities and alerts",
                "action": "Go to AI Analysis"
            },
            {
                "title": "System Documentation",
                "description": "Learn how to use ACTMS effectively",
                "action": "View Help Documentation"
            }
        ]
