
import os
import time
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from huggingface_hub import InferenceClient

# 1. Load Environment Variables
load_dotenv()

# 2. Configurations
QDRANT_CLIENT = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

GROQ_LLM = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

HF_TOKEN = os.getenv("HF_TOKEN")
HF_CLIENT = InferenceClient(token=HF_TOKEN)
COLLECTION_NAME = "medilex_encyclopedia"


# ---------------------------------------------------------------------------
# EMBEDDING & SPARSE VECTOR
# ---------------------------------------------------------------------------

def get_cloud_embedding(text):
    """Dense Vector Generation via HF Inference API"""
    try:
        res = HF_CLIENT.feature_extraction(text, model="BAAI/bge-large-en-v1.5")
        return res.tolist()
    except Exception as e:
        print(f"[ERROR] Embedding Error: {str(e)}")
        raise


def get_sparse_vector(text):
    """Simple BM25-style Sparse Vector for Hybrid Search"""
    words = text.lower().split()
    sparse_data = {}
    for word in words:
        if len(word) > 3:
            idx = hash(word) % 10000
            sparse_data[idx] = sparse_data.get(idx, 0.0) + 1.0
    return list(sparse_data.keys()), list(sparse_data.values())


# ---------------------------------------------------------------------------
# PROMPT TEMPLATES  (one per intent)
# ---------------------------------------------------------------------------

DISEASE_INFO_PROMPT = ChatPromptTemplate.from_template("""
You are MediLex AI, a professional medical assistant.
You have access to the Gale Encyclopedia of Medicine.

GOLDEN RULE: Read the user's question carefully. Your FIRST priority is to directly answer exactly what was asked.
If the provided context does not contain the answer, DO NOT say you cannot find it. Instead, use your own internal medical knowledge to answer comprehensively, and add a note at the end stating: "*Note: This information is provided from general medical knowledge.*"

FORMAT RULES:
1. Start with 1-2 warm, conversational sentences acknowledging the topic — like a doctor speaking to a patient.
   Make it feel human and reassuring, not a textbook definition.
2. Then provide only the structured sections that are relevant to the question AND have info in the context.
3. Use exact markdown headings (##) for each section. Skip empty sections entirely.

Sections to use (include only relevant ones):
## Description
## Demographics
## Causes and Symptoms
## Diagnosis
## Treatment
## Prognosis
## Prevention
## When to Call the Doctor
## Resources

---
Context from Gale Encyclopedia:
{context}

User Query: {question}
---
Note: If you used your own knowledge, remember to state that clearly at the end.
""")

DRUG_QUERY_PROMPT = ChatPromptTemplate.from_template("""
You are MediLex AI, a professional pharmacological assistant.
You have access to the Gale Encyclopedia of Medicine.

GOLDEN RULE: Read the user's question carefully. Your FIRST priority is to directly answer exactly what was asked.
If the provided context does not contain the drug or answer, DO NOT say you cannot find it. Instead, use your own internal pharmacological knowledge to answer comprehensively, and add a note at the end stating: "*Note: This information is provided from general medical knowledge.*"

FORMAT RULES:
1. Start with 1-2 warm, conversational sentences about the drug — like a pharmacist speaking to a patient.
   Make it feel approachable, not a textbook entry.
2. Then provide only relevant structured sections that have info in the context.
3. Use exact markdown headings (##). Skip empty sections entirely.

Sections to use:
## Drug Overview
## Drug Class / Category
## Recommended Dosage
## Precautions
## Side Effects
## Interactions
## Description
## When NOT to Use
## Resources

---
Context from Gale Encyclopedia:
{context}

User Query: {question}
---
Note: This is encyclopedia information only — always advise the user to consult a doctor before taking any medication.
""")

SYMPTOM_TO_DRUG_PROMPT = ChatPromptTemplate.from_template("""
You are MediLex AI, a professional medical assistant.
The user has described a symptom or condition AND is asking about a specific drug.

If the provided context does not contain the answer, use your own internal medical knowledge to answer comprehensively, and add a note at the end stating: "*Note: This information is provided from general medical knowledge.*"

FORMAT RULES:
1. Start with 1-2 warm, empathetic conversational sentences that acknowledge the user's symptom
   AND briefly explain why the drug they asked about is commonly used for it.
   Example: "Fever can really make you feel drained — Paracetamol is one of the most trusted medicines
   for bringing it down and easing that discomfort."
   Make it feel like a caring doctor is speaking, not a textbook.
2. Then provide the structured drug information from the encyclopedia.
3. Include ONLY sections that have information in the context. Skip empty sections.
4. Use exact markdown headings (##).
5. End with a clear disclaimer to consult a doctor.

Sections to use:
## Why This Drug May Help
## Drug Overview
## Recommended Dosage
## Precautions
## Side Effects
## Interactions
## When NOT to Use
## Resources

---
Context from Gale Encyclopedia:
{context}

User Query: {question}
---
""")

SYMPTOM_ONLY_PROMPT = ChatPromptTemplate.from_template("""
You are MediLex AI, a professional medical assistant.
The user is describing symptoms and wants to understand what condition they may relate to and what treatments exist.

If the provided context does not contain the answer, use your own internal medical knowledge to answer comprehensively, and add a note at the end stating: "*Note: This information is provided from general medical knowledge.*"

GOLDEN RULE: Read the user's question carefully. Your FIRST priority is to directly answer exactly what was asked.
If they said "I have fever", focus on fever. If they asked about remedies, lead with remedies.

FORMAT RULES:
1. Start with 1-2 warm, empathetic conversational sentences acknowledging the specific symptom the user mentioned.
   Match the tone to what they said — if it sounds serious, be reassuring; if mild, be calm and helpful.
2. Then provide only relevant structured sections that have info in the context.
3. Use exact markdown headings (##). Skip empty sections entirely.
4. Under "## Possible Conditions", list ONLY conditions directly related to the user's symptom.
5. Under "## Recommended Medications", list drugs mentioned in the encyclopedia for this specific symptom.
6. End with a disclaimer to see a doctor for actual diagnosis.

Sections to use:
## Possible Conditions
## Causes and Symptoms
## Diagnosis
## Treatment
## Recommended Medications
## Home Remedies
## When to Call the Doctor
## Prevention
## Resources

---
Context from Gale Encyclopedia:
{context}

User Query: {question}
---
""")

MEDICINE_LIST_PROMPT = ChatPromptTemplate.from_template("""
You are MediLex AI, a professional medical assistant.
The user is asking about what medicines or drugs are available for a specific condition or symptom.

If the provided context does not contain the answer, use your own internal medical knowledge to answer comprehensively, and add a note at the end stating: "*Note: This information is provided from general medical knowledge.*"

GOLDEN RULE: Directly answer the user's question FIRST — list the medicines.

FORMAT RULES:
1. Start with 1-2 warm conversational sentences that directly address the question.
   Example: "For stomach pain, the Gale Encyclopedia mentions several medications depending on the underlying cause — here's what's covered."
2. Then directly list all medicines/drugs found in the context for this condition.
3. After the list, include only the supporting sections that are relevant.
4. Use exact markdown headings (##). Skip empty sections.
5. End with a disclaimer to consult a doctor before taking any medication.

Sections to use:
## Medicines / Drugs Available
## How Each Medicine Works
## Recommended Dosage
## Precautions
## When to Call the Doctor
## Resources

---
Context from Gale Encyclopedia:
{context}

User Query: {question}
---
""")

DRUG_COMPARISON_PROMPT = ChatPromptTemplate.from_template("""
You are MediLex AI, a professional medical assistant.
The user wants to compare two drugs or medicines.

If the provided context does not contain the answer, use your own internal medical knowledge to answer comprehensively, and add a note at the end stating: "*Note: This information is provided from general medical knowledge.*"

GOLDEN RULE: Directly compare the two drugs side by side. Do NOT treat them separately.

FORMAT RULES:
1. Start with 1-2 warm conversational sentences acknowledging the comparison being made.
   Example: "Both Ibuprofen and Paracetamol are common pain relievers, but they work quite differently — here's how they compare."
2. Present a clear side-by-side comparison using the sections below.
3. Use exact markdown headings (##). Skip sections where context has no info.
4. Be balanced — cover both drugs equally in each section.
5. End with a recommendation note to consult a doctor for personal choice.

Sections to use:
## Overview Comparison
## Drug Class
## How Each Works
## Recommended Dosage
## Side Effects
## Precautions
## Interactions
## When to Prefer One Over the Other
## Resources

---
Context from Gale Encyclopedia:
{context}

User Query: {question}
---
""")

DRUG_INTERACTION_PROMPT = ChatPromptTemplate.from_template("""
You are MediLex AI, a professional medical assistant.
The user is asking whether two specific drugs can be taken together (drug interaction).

If the provided context does not contain the answer, use your own internal medical knowledge to answer comprehensively, and add a note at the end stating: "*Note: This information is provided from general medical knowledge.*"

GOLDEN RULE: This is a safety-critical query. Directly address whether these drugs interact.

FORMAT RULES:
1. Start with a calm but clear 1-2 sentence opener that takes the question seriously.
   Example: "Combining Aspirin and Warfarin requires caution — let me share what the encyclopedia says about this."
2. Directly state whether an interaction is known based on the context.
3. Use exact markdown headings (##). Skip sections with no context info.
4. End with a STRONG disclaimer: always consult a doctor or pharmacist before combining medications.

Sections to use:
## Known Interaction
## What Happens When Combined
## Risk Level
## Precautions
## Safe Alternatives
## When to Call the Doctor
## Resources

---
Context from Gale Encyclopedia:
{context}

User Query: {question}
---
⚠️ Always end with: "This is for informational purposes only. Please consult your doctor or pharmacist before combining any medications."
""")

MEDICAL_PROCEDURE_PROMPT = ChatPromptTemplate.from_template("""
You are MediLex AI, a professional medical assistant.
The user is asking about a medical test, procedure, or diagnostic process.

If the provided context does not contain the answer, use your own internal medical knowledge to answer comprehensively, and add a note at the end stating: "*Note: This information is provided from general medical knowledge.*"

GOLDEN RULE: Explain the procedure clearly step by step. Focus on what the patient needs to know.

FORMAT RULES:
1. Start with 1-2 warm conversational sentences explaining what this procedure is for.
   Example: "An MRI is one of the most detailed imaging tools doctors use — it's non-invasive and gives a clear picture of internal structures."
2. Then provide structured information using the sections below.
3. Use exact markdown headings (##). Skip sections with no context info.
4. Use simple, patient-friendly language alongside medical terms.

Sections to use:
## What Is This Procedure?
## Why Is It Done?
## How To Prepare
## How It Is Performed
## Risks and Side Effects
## Normal Results
## Abnormal Results
## When to Call the Doctor
## Resources

---
Context from Gale Encyclopedia:
{context}

User Query: {question}
---
""")

EMERGENCY_QUERY_PROMPT = ChatPromptTemplate.from_template("""
You are MediLex AI, a professional medical assistant.
The user is asking about an emergency medical situation or first aid.

If the provided context does not contain the answer, use your own internal medical knowledge to answer comprehensively, and add a note at the end stating: "*Note: This information is provided from general medical knowledge.*"

🚨 GOLDEN RULE: This is an emergency query. Prioritize safety above all else.
- Your FIRST line must be a clear, urgent warning to call emergency services if the situation is life-threatening.
- Then provide first aid steps from the context.
- Do NOT delay with long introductions.

FORMAT RULES:
1. Begin immediately with a 🚨 emergency notice if the situation is life-threatening.
   Example: "🚨 If someone is experiencing a heart attack, call emergency services (911/112) IMMEDIATELY before doing anything else."
2. Then provide clear, numbered first-aid steps.
3. Use exact markdown headings (##). Skip sections with no context info.
4. Keep language simple and action-oriented — no lengthy medical explanations.
5. End with a reminder to always seek professional emergency care.

Sections to use:
## 🚨 Emergency Notice
## Immediate First Aid Steps
## Warning Signs to Watch For
## What NOT To Do
## When To Call the Doctor / 911
## Recovery and Follow-up
## Resources

---
Context from Gale Encyclopedia:
{context}

User Query: {question}
---
""")

PROMPT_MAP = {
    "DISEASE_INFO":      DISEASE_INFO_PROMPT,
    "DRUG_QUERY":        DRUG_QUERY_PROMPT,
    "SYMPTOM_TO_DRUG":   SYMPTOM_TO_DRUG_PROMPT,
    "SYMPTOM_ONLY":      SYMPTOM_ONLY_PROMPT,
    "MEDICINE_LIST":     MEDICINE_LIST_PROMPT,
    "DRUG_COMPARISON":   DRUG_COMPARISON_PROMPT,
    "DRUG_INTERACTION":  DRUG_INTERACTION_PROMPT,
    "MEDICAL_PROCEDURE": MEDICAL_PROCEDURE_PROMPT,
    "EMERGENCY_QUERY":   EMERGENCY_QUERY_PROMPT,
}


# ---------------------------------------------------------------------------
# SEARCH QUERY REWRITING  (improves retrieval for mixed queries)
# ---------------------------------------------------------------------------

def build_search_query(query, intent):
    """
    Rewrites the search query to maximise Qdrant retrieval quality per intent.
    """
    if intent in ("DRUG_QUERY", "SYMPTOM_TO_DRUG"):
        extract_prompt = f"""
        From this query: "{query}"
        Extract ONLY the drug/medicine name. Return just the name, nothing else.
        """
        try:
            drug_name = GROQ_LLM.invoke(extract_prompt).content.strip()
            print(f"[RAG] Extracted drug name for search: '{drug_name}'")
            return drug_name
        except:
            return query

    if intent in ("DISEASE_INFO", "SYMPTOM_ONLY", "MEDICINE_LIST"):
        extract_prompt = f"""
        From this query: "{query}"
        Extract the main medical condition or symptom keywords. Return just the keywords, nothing else.
        """
        try:
            keywords = GROQ_LLM.invoke(extract_prompt).content.strip()
            print(f"[RAG] Extracted keywords for search: '{keywords}'")
            return keywords
        except:
            return query

    if intent in ("DRUG_COMPARISON", "DRUG_INTERACTION"):
        # Extract both drug names and search for each separately, then combine
        extract_prompt = f"""
        From this query: "{query}"
        Extract the names of the two drugs being mentioned. Return them comma-separated, nothing else.
        Example output: "Aspirin, Warfarin"
        """
        try:
            drugs = GROQ_LLM.invoke(extract_prompt).content.strip()
            print(f"[RAG] Extracted drug pair for search: '{drugs}'")
            return drugs  # e.g. "Aspirin Warfarin" — both hit Qdrant
        except:
            return query

    if intent == "MEDICAL_PROCEDURE":
        extract_prompt = f"""
        From this query: "{query}"
        Extract only the medical procedure or test name. Return just the name, nothing else.
        """
        try:
            procedure = GROQ_LLM.invoke(extract_prompt).content.strip()
            print(f"[RAG] Extracted procedure name for search: '{procedure}'")
            return procedure
        except:
            return query

    if intent == "EMERGENCY_QUERY":
        extract_prompt = f"""
        From this query: "{query}"
        Extract the main medical emergency or condition keyword. Return just the keywords, nothing else.
        """
        try:
            emergency_kw = GROQ_LLM.invoke(extract_prompt).content.strip()
            print(f"[RAG] Extracted emergency keywords for search: '{emergency_kw}'")
            return emergency_kw
        except:
            return query

    return query


# ---------------------------------------------------------------------------
# MAIN RAG FUNCTION
# ---------------------------------------------------------------------------

def get_medical_answer(query, intent="DISEASE_INFO"):
    """
    Main RAG pipeline. Uses intent to pick the right prompt and search strategy.
    """
    try:
        # A. REWRITE SEARCH QUERY BASED ON INTENT
        search_query = build_search_query(query, intent)

        # 1. Exact Text Match for Keywords (Solves drug queries like "cetirizine" inside a sentence)
        text_match_results = []
        # Ensure we use the extracted keyword (which should be short), not a massive sentence.
        # But if the user typed a massive sentence, the LLM extraction above will have shortened it!
        try:
            from qdrant_client.http import models
            text_match_results = QDRANT_CLIENT.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=models.Filter(
                    should=[
                        # Split keywords so that if it's "Aspirin, Warfarin", it searches both
                        models.FieldCondition(key="content", match=models.MatchText(text=w.strip(','))) 
                        for w in search_query.split() if len(w.strip(',')) >= 2
                    ]
                ),
                limit=5,
                with_payload=True
            )[0]
        except Exception as e:
            print(f"[WARNING] Text match search failed: {e}")

        # 2. Dense Vector Search
        dense_vector = get_cloud_embedding(search_query)
        search_results = QDRANT_CLIENT.query_points(
            collection_name=COLLECTION_NAME,
            query=dense_vector,
            using="default",
            limit=15,
            with_payload=True
        ).points

        if not search_results and not text_match_results:
            return {
                "answer": "I couldn't find specific records for your query in the Gale Encyclopedia of Medicine.",
                "pages": [],
                "image": None,
                "intent": intent
            }

        # 3. Combine & Deduplicate Results
        all_candidates = {}
        for res in text_match_results:
            all_candidates[res.id] = {"score": 1.5, "payload": res.payload}
            
        for res in search_results:
            if res.id not in all_candidates:
                all_candidates[res.id] = {"score": res.score, "payload": res.payload}

        # C. LOGICAL RERANKING
        scored_results = []
        for res_id, data in all_candidates.items():
            score = data["score"]
            content = data["payload"].get('content', '').lower()

            if intent in ("DISEASE_INFO", "SYMPTOM_ONLY"):
                for header in ["definition", "treatment", "diagnosis", "symptoms", "prevention", "causes"]:
                    if header in content:
                        score += 0.05

            if intent in ("DRUG_QUERY", "SYMPTOM_TO_DRUG", "MEDICINE_LIST"):
                for header in ["dosage", "side effects", "precautions", "interactions", "drug", "medication"]:
                    if header in content:
                        score += 0.06

            if intent == "DRUG_COMPARISON":
                for header in ["dosage", "side effects", "drug class", "precautions", "interactions", "mechanism"]:
                    if header in content:
                        score += 0.06

            if intent == "DRUG_INTERACTION":
                for header in ["interaction", "contraindication", "warning", "precaution", "avoid", "risk"]:
                    if header in content:
                        score += 0.08  # Higher boost — safety critical

            if intent == "MEDICAL_PROCEDURE":
                for header in ["procedure", "test", "preparation", "results", "normal", "abnormal", "performed", "diagnosis"]:
                    if header in content:
                        score += 0.06

            if intent == "EMERGENCY_QUERY":
                for header in ["emergency", "first aid", "immediate", "call", "symptoms", "warning", "urgent"]:
                    if header in content:
                        score += 0.08  # Higher boost — safety critical

            scored_results.append((score, data))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_results = [item[1] for item in scored_results[:6]]

        # D. CONTEXT ASSEMBLY
        context_text = ""
        source_pages = set()
        found_image = None

        for res in top_results:
            payload = res.get("payload", {})
            context_text += f"\n---\n{payload.get('content', '')}"
            if 'page' in payload:
                source_pages.add(payload['page'])
            if not found_image and payload.get('image_path'):
                found_image = payload['image_path']

        # E. SELECT PROMPT TEMPLATE BASED ON INTENT
        prompt_template = PROMPT_MAP.get(intent, DISEASE_INFO_PROMPT)
        chain = prompt_template | GROQ_LLM
        response = chain.invoke({"context": context_text, "question": query})

        return {
            "answer": response.content,
            "pages": sorted(list(source_pages)),
            "image": found_image,
            "intent": intent
        }

    except Exception as e:
        print(f"[ERROR] Error in get_medical_answer: {str(e)}")
        return {"answer": f"System Error: {str(e)}", "pages": [], "image": None, "intent": intent}


if __name__ == "__main__":
    print("Testing MediLex RAG Engine...")
    test_query = "I have a fever, tell me about paracetamol"
    res = get_medical_answer(test_query, intent="SYMPTOM_TO_DRUG")
    print(f"\n--- FINAL ANSWER ---\n{res['answer']}")
    print(f"\nSources: Pages {res['pages']}")
    print(f"Intent used: {res['intent']}")