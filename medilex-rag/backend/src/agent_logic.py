from langchain_groq import ChatGroq
from rag_engine import get_medical_answer

class MediLexAgent:
    def __init__(self):
        # Temperature 0 rakhenge taaki classification hamesha accurate rahe
        self.llm = ChatGroq(
            temperature=0, 
            model_name="llama-3.3-70b-versatile"
        )

    def route_query(self, query):
        """
        Faisla karta hai ki query kis category ki hai.
        """
        prompt = f"""
        Analyze the following user query: "{query}"
        
        Classify it into exactly one of these categories:
        1. GREETING: General greetings like 'Hi', 'Hello', 'Who are you?', 'Good morning'.
        2. INVALID: Gibberish, offensive, or completely non-medical unrelated topics.
        3. DRUG_INTERACTION: Asking if two drugs can be taken together or interact.
        4. DRUG_COMPARISON: Comparing two drugs or medicines.
        5. SYMPTOM_TO_DRUG: Mentioning a symptom and asking for medicine.
        6. MEDICINE_LIST: Asking for a list of medicines for a specific condition.
        7. DRUG_QUERY: Asking about a specific drug, medication, or pill.
        8. MEDICAL_PROCEDURE: Asking about a medical test, surgery, or procedure.
        9. EMERGENCY_QUERY: Asking about an emergency, first aid, or life-threatening situation.
        10. SYMPTOM_ONLY: Describing symptoms to find a condition.
        11. DISEASE_INFO: Asking about a disease, condition, or general medical topic.
        
        Return ONLY the category name in uppercase.
        """
        try:
            response = self.llm.invoke(prompt).content.strip().upper()
            valid_intents = ["GREETING", "INVALID", "DRUG_INTERACTION", "DRUG_COMPARISON", "SYMPTOM_TO_DRUG", "MEDICINE_LIST", "DRUG_QUERY", "MEDICAL_PROCEDURE", "EMERGENCY_QUERY", "SYMPTOM_ONLY", "DISEASE_INFO"]
            for intent in valid_intents:
                if intent in response:
                    return intent
            return "DISEASE_INFO"
        except:
            return "DISEASE_INFO" # Fallback to general RAG if LLM fails

    def execute(self, query):
        """
        Main function jo decide karta hai ki kya response dena hai.
        """
        category = self.route_query(query)
        print(f"DEBUG: Query Category -> {category}") # Terminal par check karne ke liye

        if category == "GREETING":
            # Generate a dynamic greeting using the LLM
            greeting_prompt = f"""
            You are MediLex AI, a specialist medical assistant for the Gale Encyclopedia of Medicine.
            The user just greeted you with: "{query}"
            
            Respond warmly to their specific greeting. Then briefly introduce yourself and state that you can provide structured information on diseases, symptoms, diagnosis, and treatments.
            Keep it concise and conversational.
            """
            try:
                dynamic_answer = self.llm.invoke(greeting_prompt).content.strip()
            except:
                dynamic_answer = "Hello! I am MediLex AI, your specialist assistant for the Gale Encyclopedia of Medicine. How can I help you today?"
                
            return {
                "answer": dynamic_answer,
                "pages": [],
                "image": None
            }
        
        if category not in ["INVALID", "GREETING"]:
            # category is a medical intent, pass it to RAG Engine
            return get_medical_answer(query, intent=category)
        
        # Default fallback for INVALID or anything else
        return {
            "answer": "I am specialized in medical information from the Gale Encyclopedia. I'm afraid I can't help with that specific request. Please ask a medical or health-related question.",
            "pages": [],
            "image": None
        }

def run_agentic_rag(query):
    """
    Function called by main.py
    """
    agent = MediLexAgent()
    return agent.execute(query)