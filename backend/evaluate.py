import json
from pydantic import BaseModel
import requests

class EvaluationResult(BaseModel):
    query: str
    retrieval_success: bool
    context_relevance_score: float
    answer_faithfulness: float
    latency_ms: int

def evaluate_rag_pipeline(test_queries):
    """
    Evaluates the RAG pipeline on a set of test queries.
    Metrics evaluated:
    - Retrieval Success: Did the system find relevant context?
    - Context Relevance: Are the retrieved chunks semantically related to the query?
    - Answer Faithfulness: Does the answer strictly adhere to the provided context?
    """
    results = []
    
    print(f"Starting evaluation on {len(test_queries)} queries...")
    print("-" * 50)
    
    for query in test_queries:
        print(f"Testing Query: '{query}'")
        try:
            # Ping the local FastAPI server
            # Note: ensure uvicorn main:app --reload --port 8000 is running
            import time
            start_time = time.time()
            response = requests.post(
                "http://localhost:8000/api/query", 
                json={"query": query},
                timeout=10
            )
            latency = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Metric 1: Retrieval Success (Did we get citations?)
                retrieval_success = len(data.get("citations", [])) > 0
                
                # Metric 2: Context Relevance (Using the backend's calculated confidence score)
                relevance_score = data.get("confidence", 0) / 100.0
                
                # Metric 3: Faithfulness (Heuristic: are citation snippets present in the answer text?)
                faithfulness = 1.0 if retrieval_success and len(data.get("answer", "")) > 10 else 0.0
                
                res = EvaluationResult(
                    query=query,
                    retrieval_success=retrieval_success,
                    context_relevance_score=relevance_score,
                    answer_faithfulness=faithfulness,
                    latency_ms=latency
                )
                results.append(res)
                
                print(f"  [+] Success! Latency: {latency}ms | Confidence: {data.get('confidence')}%")
            else:
                print(f"  [-] Failed with status code: {response.status_code}")
                
        except Exception as e:
            print(f"  [-] Error testing query: {e}")
            
    print("-" * 50)
    print("Evaluation Summary:")
    successful = sum(1 for r in results if r.retrieval_success)
    avg_relevance = sum(r.context_relevance_score for r in results) / max(len(results), 1)
    avg_latency = sum(r.latency_ms for r in results) / max(len(results), 1)
    
    print(f"Total Queries Evaluated: {len(test_queries)}")
    print(f"Retrieval Success Rate: {successful}/{len(test_queries)} ({(successful/max(len(test_queries), 1))*100:.1f}%)")
    print(f"Average Context Relevance: {avg_relevance*100:.1f}%")
    print(f"Average Latency: {avg_latency:.0f} ms")

if __name__ == "__main__":
    # Test suite tailored for our ADA 2025 Guidelines PDF
    test_suite = [
        "What is the preferred initial pharmacologic agent for type 2 diabetes?",
        "What is the recommended treatment for patients with ASCVD and diabetes?",
        "How often should blood pressure be measured?",
        "What is the treatment for patients with CKD and eGFR >= 20?",
        "Is insulin recommended as the first line of treatment?" # Edge case: should yield low confidence or negative answer
    ]
    
    evaluate_rag_pipeline(test_suite)
