from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    genai = None
    HAS_GEMINI = False
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

app = FastAPI(title="Healthcare Knowledge Navigator API")

# Allow CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "faiss_db"
# Initialize embeddings model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ── Gemini LLM Setup ──────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY and HAS_GEMINI:
    genai.configure(api_key=GEMINI_API_KEY)

def get_gemini_model():
    """Returns a Gemini model instance if the API key is configured."""
    if GEMINI_API_KEY and HAS_GEMINI:
        return genai.GenerativeModel("gemini-2.0-flash")
    return None

# ── Intent Detection ──────────────────────────────────────────────────
import re

GREETING_KEYWORDS = {
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "howdy", "what's up", "sup", "yo", "greetings", "hola", "hi there",
    "hey there", "hello there"
}

CONVERSATIONAL_KEYWORDS = {
    "who are you", "what are you", "what can you do", "help",
    "how are you", "what is your name", "tell me about yourself",
    "what are you trained on", "thank you", "thanks", "bye",
    "goodbye", "see you", "ok", "okay", "cool", "great", "nice",
    "what do you do", "how do you work", "what kind of questions",
    "what type of questions", "what questions can", "what can i ask",
    "what should i ask", "how to use", "how does this work",
    "what is this", "tell me about you", "introduce yourself",
    "who made you", "who built you", "who created you",
    "what topics", "what areas", "what subjects", "capabilities",
    "your purpose", "your function", "what are your features",
    "how can you help", "what help", "assist me", "can you help",
    "good job", "well done", "awesome", "amazing", "wonderful",
    "not helpful", "wrong answer", "that's wrong", "incorrect",
    "are you ai", "are you a bot", "are you human", "are you real",
    "what model", "which model", "what llm", "what language model"
}

# Regex patterns for conversational queries (must be specific to avoid matching medical queries)
CONVERSATIONAL_PATTERNS = [
    r"what\s+(kind|type|sort)\s+of\s+(question|quer|thing)",
    r"what\s+(can|should)\s+i\s+ask\s+(you|about)",
    r"how\s+(do|can|should)\s+i\s+use\s+(you|this|the\s+app|the\s+system)",
    r"tell\s+me\s+(about|more\s+about)\s+(you|yourself|this\s+(app|system|tool|bot))",
    r"(thanks|thank\s+you|thx|ty)\s*(so\s+much|a\s+lot)?$",
    r"^(yes|no|yep|nope|yea|nah|sure|definitely|absolutely)$",
    r"^(good|nice|great|cool|awesome|amazing|ok|okay|fine|alright)$",
]

def classify_intent(query: str) -> str:
    """
    Classifies query intent into: 'greeting', 'conversational', or 'medical'.
    Uses keyword matching first, regex patterns second, then LLM classification.
    """
    q = query.strip().lower().rstrip("?!.")
    
    # Quick keyword match for greetings
    if q in GREETING_KEYWORDS:
        return "greeting"
    
    # Keyword substring match for conversational
    for kw in CONVERSATIONAL_KEYWORDS:
        if kw in q:
            return "conversational"
    
    # Regex pattern match for conversational
    for pattern in CONVERSATIONAL_PATTERNS:
        if re.search(pattern, q):
            return "conversational"
    
    # If we have Gemini, use it for smarter classification
    model = get_gemini_model()
    if model:
        try:
            classification_prompt = f"""Classify the following user message into exactly one category.
Reply with ONLY the category name, nothing else.

Categories:
- greeting: casual greetings like hi, hello, hey, good morning
- conversational: general questions about the system, small talk, non-medical topics, questions about capabilities, thanks, feedback, meta-questions like "what can you do" or "what type of questions can i ask"
- medical: any question specifically about health, medicine, drugs, diseases, treatments, clinical guidelines, symptoms, diagnoses, or patient care

User message: "{query}"

Category:"""
            resp = model.generate_content(classification_prompt)
            category = resp.text.strip().lower().strip('"').strip("'")
            if category in ("greeting", "conversational", "medical"):
                return category
        except Exception:
            pass
    
    # Default: assume medical so the RAG pipeline handles it
    return "medical"


def generate_conversational_response(query: str) -> str:
    """Generate a friendly conversational response using Gemini or a fallback."""
    model = get_gemini_model()
    if model:
        try:
            prompt = f"""You are the Healthcare Knowledge Navigator, a specialized medical RAG assistant.
You help healthcare professionals find evidence-based answers from clinical guidelines,
research papers, and treatment protocols.

When responding to general/conversational queries:
- Be warm, professional, and concise.
- Introduce yourself and explain your capabilities.
- Guide the user toward asking medical questions you can help with.
- Never make up medical information for casual queries.

User message: "{query}"

Your response:"""
            resp = model.generate_content(prompt)
            return resp.text.strip()
        except Exception:
            pass
    
    # Fallback responses if Gemini is not available
    q = query.strip().lower()
    if any(kw in q for kw in GREETING_KEYWORDS):
        return ("Hello! 👋 I'm the Healthcare Knowledge Navigator — a specialized medical assistant. "
                "I can help you find evidence-based answers from clinical guidelines like the ADA Standards of Care. "
                "Try asking me something like: *\"What is the first-line treatment for Type 2 diabetes?\"*")
    
    if "who are you" in q or "what are you" in q or "trained" in q:
        return ("I'm a **Retrieval-Augmented Generation (RAG)** medical assistant. "
                "I search through indexed clinical guidelines and research papers to find relevant information, "
                "then synthesize it into clear answers with citations and confidence scores.\n\n"
                "Currently, I have the **ADA 2025 Clinical Guidelines** indexed in my knowledge base. "
                "Ask me anything about diabetes management, cardiovascular risk, or chronic kidney disease!")
    
    if "thank" in q:
        return "You're welcome! Feel free to ask any other medical questions. I'm here to help. 🩺"
    
    if "bye" in q or "goodbye" in q:
        return "Goodbye! Stay healthy. Feel free to come back anytime you need clinical guidance. 👋"
    
    return ("I'm the Healthcare Knowledge Navigator. I specialize in answering medical questions "
            "using indexed clinical guidelines. How can I help you today?")


def generate_rag_response(query: str, docs_with_scores: list) -> tuple[str, int]:
    """
    Use Gemini to synthesize a proper answer from retrieved chunks.
    Falls back to raw chunk display if Gemini is unavailable.
    """
    # Build context from retrieved docs
    context_parts = []
    for i, (doc, score) in enumerate(docs_with_scores):
        source = os.path.basename(doc.metadata.get("source", "Unknown"))
        context_parts.append(f"[Source {i+1}: {source}]\n{doc.page_content.strip()}")
    
    context = "\n\n".join(context_parts)
    
    # Calculate confidence from similarity scores
    confidence_vals = []
    for doc, score in docs_with_scores:
        confidence_vals.append(max(10, min(99, int(100 - (score * 50)))))
    avg_confidence = sum(confidence_vals) // len(confidence_vals)
    
    model = get_gemini_model()
    if model:
        try:
            rag_prompt = f"""You are a medical assistant. Answer the user's question using ONLY the context provided below.
Rules:
1. Be clear, concise, and clinically accurate.
2. Use inline citation references like [1], [2] to indicate which source supports each claim.
3. If the context does not contain enough information to answer, clearly state: "The available guidelines do not contain sufficient information to answer this question."
4. Never fabricate information not present in the context.
5. Use bullet points or short paragraphs for readability.

Context:
{context}

User Question: {query}

Answer:"""
            resp = model.generate_content(rag_prompt)
            return resp.text.strip(), avg_confidence
        except Exception:
            pass
    
    # Fallback: format raw chunks (original behavior)
    answer_text = "Based on the retrieved clinical literature:\n\n"
    for i, (doc, score) in enumerate(docs_with_scores):
        answer_text += f"**Finding {i+1}:** {doc.page_content.strip()}\n\n"
    
    return answer_text.strip(), avg_confidence


# ── Vector DB Helper ──────────────────────────────────────────────────
def get_vector_db():
    if os.path.exists(DB_PATH):
        return FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
    return None


# ── API Models ────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str

class Citation(BaseModel):
    id: int
    source: str
    snippet: str

class QueryResponse(BaseModel):
    answer: str
    confidence: int
    citations: list[Citation]


# ── Main Endpoint ─────────────────────────────────────────────────────
@app.post("/api/query", response_model=QueryResponse)
def query_knowledge(req: QueryRequest):
    # Step 1: Classify intent
    intent = classify_intent(req.query)
    
    # Step 2: Handle non-medical queries conversationally
    if intent in ("greeting", "conversational"):
        return QueryResponse(
            answer=generate_conversational_response(req.query),
            confidence=100,
            citations=[]
        )
    
    # Step 3: Medical query → use RAG pipeline
    vector_db = get_vector_db()
    if not vector_db:
        return QueryResponse(
            answer="Vector database not found. Please run `python ingest.py` to process clinical documents first.",
            confidence=0,
            citations=[]
        )
    
    # Retrieve top 3 relevant chunks
    docs = vector_db.similarity_search_with_score(req.query, k=3)
    
    if not docs:
        return QueryResponse(
            answer="No relevant information found in the indexed guidelines for this query.",
            confidence=0,
            citations=[]
        )
    
    # Generate synthesized answer
    answer_text, final_confidence = generate_rag_response(req.query, docs)
    
    # Build citations
    citations = []
    for i, (doc, score) in enumerate(docs):
        source_name = doc.metadata.get("source", "Unknown")
        citations.append(Citation(
            id=i + 1,
            source=os.path.basename(source_name),
            snippet=doc.page_content[:80].replace('\n', ' ') + "..."
        ))
    
    return QueryResponse(
        answer=answer_text,
        confidence=final_confidence,
        citations=citations
    )
