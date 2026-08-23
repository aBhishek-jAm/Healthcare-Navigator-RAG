"""
PubMed Data Scraper for Healthcare Knowledge Navigator.
Fetches real medical abstracts from PubMed's free E-utilities API.
No API key required for basic usage.
"""
import requests
import time
import os
import xml.etree.ElementTree as ET

BASE_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
BASE_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
DATA_DIR = "data"

DISEASES = [
    "type 2 diabetes treatment guidelines",
    "hypertension management clinical",
    "asthma treatment protocol",
    "chronic kidney disease management",
    "heart failure treatment guidelines",
    "stroke prevention guidelines",
    "COPD treatment protocol",
    "breast cancer treatment guidelines",
    "lung cancer screening guidelines",
    "colorectal cancer screening",
    "rheumatoid arthritis treatment",
    "osteoporosis management guidelines",
    "depression treatment clinical guidelines",
    "anxiety disorder treatment protocol",
    "alzheimer disease management",
    "parkinson disease treatment",
    "epilepsy treatment guidelines",
    "HIV treatment antiretroviral",
    "tuberculosis treatment protocol",
    "hepatitis B treatment guidelines",
    "hepatitis C treatment guidelines",
    "chronic liver disease management",
    "inflammatory bowel disease treatment",
    "celiac disease management guidelines",
    "thyroid disorder treatment",
    "hyperlipidemia management guidelines",
    "obesity management clinical guidelines",
    "pneumonia treatment protocol",
    "urinary tract infection treatment",
    "sepsis management guidelines",
    "anemia treatment guidelines",
    "deep vein thrombosis treatment",
    "atrial fibrillation management",
    "migraine treatment guidelines",
    "chronic pain management protocol",
    "osteoarthritis treatment guidelines",
    "gout treatment clinical guidelines",
    "psoriasis treatment protocol",
    "eczema dermatitis management",
    "glaucoma treatment guidelines",
    "diabetic retinopathy screening",
    "chronic obstructive pulmonary disease",
    "sleep apnea treatment guidelines",
    "iron deficiency treatment protocol",
    "vitamin D deficiency management",
    "prostate cancer screening guidelines",
    "cervical cancer screening protocol",
    "pancreatitis management guidelines",
    "gallstone disease treatment",
    "peptic ulcer treatment protocol",
]

def search_pubmed(query, max_results=5):
    """Search PubMed and return list of PMIDs."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    }
    try:
        r = requests.get(BASE_SEARCH, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"  Search error: {e}")
        return []

def fetch_abstracts(pmids):
    """Fetch abstracts for a list of PMIDs."""
    if not pmids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "xml",
    }
    try:
        r = requests.get(BASE_FETCH, params=params, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        articles = []
        for article in root.findall(".//PubmedArticle"):
            title_el = article.find(".//ArticleTitle")
            title = title_el.text if title_el is not None and title_el.text else "Untitled"
            abstract_el = article.find(".//AbstractText")
            abstract = abstract_el.text if abstract_el is not None and abstract_el.text else ""
            journal_el = article.find(".//Journal/Title")
            journal = journal_el.text if journal_el is not None else "Unknown Journal"
            year_el = article.find(".//PubDate/Year")
            year = year_el.text if year_el is not None else "N/A"
            if abstract and len(abstract) > 100:
                articles.append({
                    "title": title,
                    "abstract": abstract,
                    "journal": journal,
                    "year": year,
                })
        return articles
    except Exception as e:
        print(f"  Fetch error: {e}")
        return []

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    total = 0
    for i, query in enumerate(DISEASES):
        safe_name = query.replace(" ", "_")[:40]
        print(f"[{i+1}/{len(DISEASES)}] Searching: {query}")
        pmids = search_pubmed(query, max_results=5)
        if not pmids:
            print("  No results found.")
            time.sleep(0.5)
            continue
        articles = fetch_abstracts(pmids)
        if not articles:
            print("  No abstracts retrieved.")
            time.sleep(0.5)
            continue
        filepath = os.path.join(DATA_DIR, f"{safe_name}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Clinical Topic: {query.title()}\n")
            f.write("=" * 60 + "\n\n")
            for j, art in enumerate(articles):
                f.write(f"Section {j+1}: {art['title']}\n")
                f.write(f"Source: {art['journal']} ({art['year']})\n")
                f.write("-" * 40 + "\n")
                f.write(art["abstract"] + "\n\n")
        total += len(articles)
        print(f"  Saved {len(articles)} abstracts to {filepath}")
        time.sleep(0.4)  # Rate limit courtesy
    print(f"\nDone! Total abstracts collected: {total}")
    print(f"Files saved to: {os.path.abspath(DATA_DIR)}")

if __name__ == "__main__":
    main()
