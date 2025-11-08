import chromadb
import torch
from transformers import AutoTokenizer, AutoModel
import math
import json
import requests
import uuid
from typing import List, Dict, Optional, Union
import numpy as np
from bs4 import BeautifulSoup
import re


def create_case_embeddings_db(
    cases_data: Union[str, Dict[str, str]],
    collection_name: str = "case_chunks",
    persist_directory: str = "./chroma_db",
):
    """
    Create embeddings for one or multiple case documents and store them in ChromaDB.

    Args:
        cases_data: Either:
            - str: Single case document text
            - Dict[str, str]: Dictionary mapping case_id -> case_text for multiple cases
        collection_name (str): Name for the ChromaDB collection
        persist_directory (str): Directory to persist the ChromaDB data

    Returns:
        dict: Contains collection info and processing statistics
    """
    # --- Configuration ---
    MODEL_NAME = "law-ai/InLegalBERT"
    CHUNK_OVERLAP = 100
    BATCH_SIZE = 8
    # ---------------------

    # Handle both single case and multiple cases input
    if isinstance(cases_data, str):
        cases_dict = {"default_case": cases_data}
        # print(f"Processing single case document with {len(cases_data)} characters")
    else:
        cases_dict = cases_data
        total_chars = sum(len(text) for text in cases_dict.values())
        # print(f"Processing {len(cases_dict)} cases with total {total_chars} characters")
        for case_id, case_text in cases_dict.items():
            print(f"  - {case_id}: {len(case_text)} characters")

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=persist_directory)

    # Create or get collection
    try:
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )
        # print(f"Created new collection: {collection_name}")
    except Exception as e:
        if "already exists" in str(e):
            client.delete_collection(collection_name)
            collection = client.create_collection(
                name=collection_name, metadata={"hnsw:space": "cosine"}
            )
            # print(f"Recreated collection: {collection_name}")
        else:
            raise e

    # Load model and tokenizer
    # print(f"Loading tokenizer: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # print(f"Loading model: {MODEL_NAME}")
    model = AutoModel.from_pretrained(MODEL_NAME)

    # Set up device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # print(f"Using device: {device}")
    model.to(device)
    model.eval()

    def get_chunk_embeddings_and_texts(text: str, case_id: str):
        """Generate embeddings and extract chunk texts for a single case."""
        print(f"  📄 Processing case: {case_id}")

        # Tokenize with chunking
        max_length = tokenizer.model_max_length

        encoded_input = tokenizer(
            text,
            max_length=max_length,
            truncation=True,
            return_overflowing_tokens=True,
            stride=CHUNK_OVERLAP,
            padding="max_length",
            return_tensors="pt",
            return_offsets_mapping=True,
        )

        input_ids = encoded_input["input_ids"]
        attention_mask = encoded_input["attention_mask"]
        offset_mapping = encoded_input["offset_mapping"]

        num_chunks = input_ids.shape[0]
        print(f"  - Split into {num_chunks} chunks")

        # Extract chunk texts
        chunk_texts = []
        for i in range(num_chunks):
            last_non_padding_index = (attention_mask[i] == 1).sum() - 1
            first_real_token_index = 1
            last_real_token_index = last_non_padding_index - 1

            if last_real_token_index >= first_real_token_index:
                start_char = offset_mapping[i][first_real_token_index][0].item()
                end_char = offset_mapping[i][last_real_token_index][1].item()
                chunk_texts.append(text[start_char:end_char])
            else:
                chunk_texts.append("")

        # Process chunks in batches to get embeddings
        all_embeddings = []
        num_batches = math.ceil(num_chunks / BATCH_SIZE)

        for i in range(num_batches):
            start_idx = i * BATCH_SIZE
            end_idx = min((i + 1) * BATCH_SIZE, num_chunks)

            batch_input_ids = input_ids[start_idx:end_idx].to(device)
            batch_attention_mask = attention_mask[start_idx:end_idx].to(device)

            with torch.no_grad():
                output = model(
                    input_ids=batch_input_ids, attention_mask=batch_attention_mask
                )

            cls_embeddings = output.last_hidden_state[:, 0, :]
            all_embeddings.append(cls_embeddings.cpu().numpy())

            if (i + 1) % 10 == 0 or i + 1 == num_batches:
                print(f"    ...Processed batch {i+1}/{num_batches}")

        all_embeddings = np.vstack(all_embeddings)

        return all_embeddings, chunk_texts

    # Process all cases
    all_embeddings = []
    all_documents = []
    all_metadatas = []
    all_ids = []
    total_chunks = 0

    for case_id, case_text in cases_dict.items():
        print(f"\n🔧 Starting embeddings for case: {case_id}")
        embeddings, chunk_texts = get_chunk_embeddings_and_texts(case_text, case_id)

        # Prepare data for this case
        case_ids = [str(uuid.uuid4()) for _ in range(len(chunk_texts))]
        case_metadatas = [
            {
                "case_id": case_id,
                "chunk_index": i,
                "global_chunk_index": total_chunks + i,
                "text_length": len(text),
                "case_total_chunks": len(chunk_texts),
            }
            for i, text in enumerate(chunk_texts)
        ]

        all_embeddings.extend(embeddings.tolist())
        all_documents.extend(chunk_texts)
        all_metadatas.extend(case_metadatas)
        all_ids.extend(case_ids)
        total_chunks += len(chunk_texts)

        print(f"  ✅ Completed case {case_id}: {len(chunk_texts)} chunks created")

    # Add to ChromaDB collection in safe-sized batches to avoid rust/chroma batch limits
    # print(f"\nAdding {len(all_embeddings)} embeddings from {len(cases_dict)} cases to ChromaDB...")
    CHROMA_ADD_BATCH = 5000  # keep safely below observed native max (5461)
    total_to_add = len(all_embeddings)
    if total_to_add == 0:
        print("No embeddings to add to ChromaDB.")
    else:
        print(
            f"\nAdding {total_to_add} embeddings to ChromaDB in batches of {CHROMA_ADD_BATCH}..."
        )
        for start in range(0, total_to_add, CHROMA_ADD_BATCH):
            end = min(start + CHROMA_ADD_BATCH, total_to_add)
            batch_embeddings = all_embeddings[start:end]
            batch_documents = all_documents[start:end]
            batch_metadatas = all_metadatas[start:end]
            batch_ids = all_ids[start:end]

            print(f"  - Adding batch {start}-{end} ({len(batch_embeddings)} items)")
            collection.add(
                embeddings=batch_embeddings,
                documents=batch_documents,
                metadatas=batch_metadatas,
                ids=batch_ids,
            )

    # print(f"✅ Successfully created embeddings database!")
    # print(f"  - Collection: {collection_name}")
    # print(f"  - Total cases: {len(cases_dict)}")
    # print(f"  - Total chunks: {total_chunks}")
    # print(f"  - Embedding dimension: {len(all_embeddings[0])}")
    # print(f"  - Persist directory: {persist_directory}")

    # # print case breakdown
    # print("\n📊 Case Breakdown:")
    case_stats = {}
    for metadata in all_metadatas:
        case_id = metadata["case_id"]
        if case_id not in case_stats:
            case_stats[case_id] = 0
        case_stats[case_id] += 1

    # for case_id, chunk_count in case_stats.items():
    # print(f"  - {case_id}: {chunk_count} chunks")

    return {
        "collection_name": collection_name,
        "num_cases": len(cases_dict),
        "num_chunks": total_chunks,
        "embedding_dim": len(all_embeddings[0]),
        "persist_directory": persist_directory,
        "case_stats": case_stats,
    }


def query_case_embeddings_db(
    query: str,
    collection_name: str = "case_chunks",
    persist_directory: str = "./chroma_db",
    top_k: int = 3,
    filter_case_ids: Optional[List[str]] = None,
):
    """
    Query the ChromaDB collection to find relevant chunks and generate an answer with source tracking.

    Args:
        query (str): The question to ask about the case(s)
        collection_name (str): Name of the ChromaDB collection
        persist_directory (str): Directory where ChromaDB data is persisted
        top_k (int): Number of relevant chunks to retrieve
        filter_case_ids (List[str], optional): Only search within specific case IDs

    Returns:
        dict: Contains the query results, generated answer, and source information
    """
    MODEL_NAME = "law-ai/InLegalBERT"

    # print(f"🔍 Querying embeddings database for: '{query}'")
    # if filter_case_ids:
    # print(f"   Filtering to cases: {filter_case_ids}")

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=persist_directory)

    try:
        collection = client.get_collection(collection_name)
        # print(f"✅ Found collection: {collection_name}")
    except Exception as e:
        raise RuntimeError(
            f"Collection '{collection_name}' not found. Please create embeddings first. Error: {e}"
        )

    # Load model and tokenizer for query embedding
    # print(f"Loading model for query embedding: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    # Generate query embedding
    # print("Generating query embedding...")
    encoded_input = tokenizer(
        query,
        max_length=tokenizer.model_max_length,
        truncation=True,
        padding="max_length",
        return_tensors="pt",
    )

    input_ids = encoded_input["input_ids"].to(device)
    attention_mask = encoded_input["attention_mask"].to(device)

    with torch.no_grad():
        output = model(input_ids=input_ids, attention_mask=attention_mask)

    query_embedding = output.last_hidden_state[:, 0, :].cpu().numpy()

    # Prepare where clause for filtering
    where_clause = None
    if filter_case_ids:
        where_clause = {"case_id": {"$in": filter_case_ids}}

    # Query ChromaDB for similar chunks
    # # print(f"Searching for top {top_k} similar chunks...")
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
        where=where_clause,
    )

    # Process results with source tracking
    relevant_chunks = []
    sources_summary = {}

    for i in range(len(results["documents"][0])):
        metadata = results["metadatas"][0][i]
        case_id = metadata["case_id"]

        chunk_data = {
            "text": results["documents"][0][i],
            "metadata": metadata,
            "distance": results["distances"][0][i],
            "similarity_score": 1
            - results["distances"][0][i],  # Convert distance to similarity
            "source": {
                "case_id": case_id,
                "chunk_index": metadata["chunk_index"],
                "global_chunk_index": metadata["global_chunk_index"],
            },
        }
        relevant_chunks.append(chunk_data)

        # Track sources
        if case_id not in sources_summary:
            sources_summary[case_id] = []
        sources_summary[case_id].append(metadata["chunk_index"])

    # # print(f"Found {len(relevant_chunks)} relevant chunks from {len(sources_summary)} cases")

    # Display results with sources
    # print("\n" + "="*60)
    # print(f"📋 QUERY: '{query}'")
    # print("="*60)

    # print("\n📚 SOURCES FOUND:")
    # for case_id, chunk_indices in sources_summary.items():
    # print(f"  • {case_id}: chunks {sorted(chunk_indices)}")

    # print(f"\n🔍 TOP {top_k} RELEVANT CHUNKS:")
    # for i, chunk in enumerate(relevant_chunks):
    # source = chunk['source']
    # print(f"\n--- Result {i+1} ---")
    # print(f"📄 Source: {source['case_id']} (chunk {source['chunk_index']})")
    # print(f"🎯 Similarity: {chunk['similarity_score']:.4f}")
    # print(f"📝 Text: {chunk['text'][:400]}{'...' if len(chunk['text']) > 400 else ''}")
    # print("-" * 50)

    # Generate answer using Gemini API with source citations
    def generate_answer_with_sources(query: str, chunks: List[Dict], sources: Dict):
        """Generate answer using Gemini API with retrieved context and source citations."""
        # print("\n" + "="*60)
        # print("🤖 GENERATING ANSWER WITH LLM (GEMINI)")
        # print("="*60)

        # Prepare context with source annotations
        context_parts = []
        for i, chunk in enumerate(chunks):
            source = chunk["source"]
            annotated_text = f"[Source: {source['case_id']}, Chunk {source['chunk_index']}]\n{chunk['text']}"
            context_parts.append(annotated_text)

        context = "\n\n---\n\n".join(context_parts)

        system_prompt = (
            "You are a helpful legal assistant. Based on the context provided from legal cases, "
            "answer the user's question concisely and accurately. "
            "IMPORTANT: Always cite your sources by mentioning the case ID and chunk number "
            "when referencing specific information (e.g., 'According to Case_A, chunk 5...'). "
            "If information comes from multiple sources, mention all relevant sources."
        )

        user_prompt = f"""
            **Context from Legal Cases:**
            {context}

            **Question:**
            {query}

            Please provide a comprehensive answer and cite the specific sources (case ID and chunk numbers) for each piece of information you reference.
        """

        api_key = "AIzaSyAZK12mvMhMrOoDQytcwU3DfTjxAYLtENI"
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not found.")

        payload = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
        }

        model_name = "gemini-2.5-flash-preview-09-2025"
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        # print("📡 Calling Gemini API...")
        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)

        try:
            resp.raise_for_status()
            result = resp.json()
            answer = result["candidates"][0]["content"]["parts"][0]["text"]

            # print("\n" + "="*60)
            # print("🎯 GEMINI ANSWER WITH SOURCES")
            # print("="*60)
            # print(answer)

            # print(f"\n📚 SOURCES REFERENCED:")
            # for case_id, chunks in sources.items():
            # print(f"  • {case_id}: chunks {sorted(chunks)}")

            return answer
        except Exception as e:
            # print(f"❌ Error generating answer: {e}")
            return None

    # Generate answer with sources
    answer = generate_answer_with_sources(query, relevant_chunks, sources_summary)

    return {
        "query": query,
        "relevant_chunks": relevant_chunks,
        "sources_summary": sources_summary,
        "answer": answer,
        "collection_stats": {
            "name": collection_name,
            "total_chunks": collection.count(),
        },
    }


# Example usage:
"""
# Step 1: Create embeddings database
db_info = create_case_embeddings_db(scase, "my_case_collection")

# Step 2: Query the database
result = query_case_embeddings_db("Who won the case?", "my_case_collection", top_k=3)
# print("Answer:", result['answer'])
"""

cases = {
    "smith_v_jones_2023": "Full text of Smith v Jones case...",
    "doe_v_company_2024": "Full text of Doe v Company case...",
    "precedent_case_2020": "Full text of precedent case...",
}

# Step 1: Create embeddings database for multiple cases
db_info = create_case_embeddings_db(cases, "multi_case_collection")

# Step 2: Query across all cases
result = query_case_embeddings_db(
    "What are the damages awarded?", "multi_case_collection", top_k=5
)
print(result)
# Step 3: Query specific cases only
result2 = query_case_embeddings_db(
    "Who won the case?",
    "multi_case_collection",
)
print(result2)


# =============================================================================
# NEW LEGAL CASE ANALYSIS FUNCTIONS
# =============================================================================


def clean_html_content(html_content: str) -> str:
    """Clean HTML content and extract text."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Extract text
    text = soup.get_text()

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = " ".join(chunk for chunk in chunks if chunk)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def load_cases_from_json(json_file_path: str) -> Dict[str, Dict]:
    """Load cases from the JSON file."""
    print(f"Loading cases from: {json_file_path}")

    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cases = {}
    research_materials = data.get("research_materials", {})
    cases_list = research_materials.get("cases", [])

    print(f"Found {len(cases_list)} cases in the JSON file")

    # Limit to 5 cases for now
    CASE_LIMIT = 10
    if len(cases_list) > CASE_LIMIT:
        print(f"⚠️  Limiting to first {CASE_LIMIT} cases for testing")
        cases_list = cases_list[:CASE_LIMIT]

    for case in cases_list:
        doc_id = str(case.get("docid"))
        case_title = case.get("title", "")
        court = case.get("court", "")
        date = case.get("date", "")

        # Extract the HTML doc content
        doc_data = case.get("doc_data", {})
        html_doc = doc_data.get("doc", "")

        if html_doc:
            # Check if doc content is too large (>300k characters)
            if len(html_doc) > 750000:
                print(
                    f"  - Case {doc_id}: {case_title[:60]}... SKIPPED (doc too large: {len(html_doc)} chars)"
                )
                continue

            # Clean the HTML content
            clean_text = clean_html_content(html_doc)

            cases[doc_id] = {
                "doc_id": doc_id,
                "title": case_title,
                "court": court,
                "date": date,
                "original_case_data": case,
                "clean_text": clean_text,
            }

            print(f"  - Case {doc_id}: {case_title[:60]}... ({len(clean_text)} chars)")

    return cases


def create_legal_case_embeddings(
    cases: Dict[str, Dict], collection_name: str = "case_chunks"
):
    """Create embeddings for legal cases with doc_id metadata."""
    print(f"\n🔧 Creating embeddings for {len(cases)} legal cases...")

    # Prepare cases data for embedding
    cases_for_embedding = {}
    case_metadata = {}

    for doc_id, case_data in cases.items():
        cases_for_embedding[doc_id] = case_data["clean_text"]
        case_metadata[doc_id] = {
            "title": case_data["title"],
            "court": case_data["court"],
            "date": case_data["date"],
        }

    # Use existing function but with custom metadata
    return create_case_embeddings_db(cases_for_embedding, collection_name)


def find_relevant_cases(
    user_query: str, collection_name: str = "case_chunks", top_k: int = 10
) -> List[str]:
    """Find top relevant case doc_ids using similarity search."""
    print(f"\n🔍 Finding relevant cases for: '{user_query}'")

    # Query embeddings to get relevant chunks
    results = query_case_embeddings_db(user_query, collection_name, top_k=top_k * 3)

    # Extract unique doc_ids from results
    doc_ids_seen = set()
    relevant_doc_ids = []

    for chunk in results.get("relevant_chunks", []):
        # Handle both case_id (new) and legacy metadata structures
        case_id = chunk["metadata"].get("case_id") or chunk["metadata"].get("doc_id")
        if case_id and case_id not in doc_ids_seen:
            doc_ids_seen.add(case_id)
            relevant_doc_ids.append(case_id)
            if len(relevant_doc_ids) >= top_k:
                break

    print(f"Found {len(relevant_doc_ids)} relevant cases")
    return relevant_doc_ids


def analyze_case_verdict(
    doc_id: str, collection_name: str = "case_chunks", user_context: str = ""
) -> dict:
    """Analyze who won a specific case from user's perspective."""
    print(f"\n⚖️ Analyzing verdict for case {doc_id}...")

    # Step 1: Find chunks related to case outcome and parties
    pattern_query = """
    case outcome judgment verdict ruling decision plaintiff defendant appellant 
    respondent petitioner relief granted denied dismissed allowed rejected won lost
    """

    print("  🔍 Finding outcome-related chunks...")
    pattern_results = query_case_embeddings_db(
        pattern_query, collection_name, top_k=5, filter_case_ids=[doc_id]
    )

    if not pattern_results.get("relevant_chunks"):
        print("  ❌ No relevant chunks found for verdict analysis")
        return {
            "doc_id": doc_id,
            "verdict": "UNCLEAR",
            "analysis": "No relevant chunks found",
        }

    # Step 2: Extract the chunks text
    relevant_chunks = pattern_results["relevant_chunks"]
    chunks_text = []
    for chunk in relevant_chunks:
        chunks_text.append(chunk["text"])

    combined_context = "\n\n---CHUNK---\n\n".join(chunks_text)

    # Step 3: Let LLM identify user's party position and determine win/loss
    print("  🤖 Analyzing verdict with user context...")
    verdict_analysis = analyze_verdict_with_llm(combined_context, user_context, doc_id)

    return {
        "doc_id": doc_id,
        "verdict": verdict_analysis.get("verdict", "UNCLEAR"),
        "analysis": verdict_analysis.get("full_analysis", ""),
        "user_party_identified": verdict_analysis.get("user_party", "Unknown"),
        "reasoning": verdict_analysis.get("reasoning", ""),
    }


def analyze_verdict_with_llm(case_chunks: str, user_context: str, doc_id: str) -> dict:
    """Use LLM to analyze verdict considering user's position."""

    system_prompt = """
    You are a legal expert analyzing court cases. Your task is to:
    1. Identify which party the user most likely represents based on their situation
    2. Determine the case outcome (who won/lost)  
    3. Decide whether this outcome is WIN or LOSS from the user's perspective
    
    Be clear and analytical in your reasoning.
    """

    user_prompt = f"""
    **CASE CONTEXT (Case ID: {doc_id}):**
    {case_chunks}
    
    **USER'S SITUATION:**
    {user_context}
    
    **ANALYSIS REQUIRED:**
    
    1. **Identify User's Party Position:** Based on the user's situation, which party in this case does the user most likely represent? (plaintiff/defendant/appellant/respondent/petitioner/etc.)
    
    2. **Case Outcome:** What was the actual outcome of this case? Who won and who lost?
    
    3. **User's Result:** Given the user's likely party position and the actual case outcome, would this be a WIN or LOSS for someone in the user's situation?
    
    4. **Reasoning:** Explain your analysis clearly.
    
    **PROVIDE YOUR ANSWER IN THIS FORMAT:**
    USER_PARTY: [which party the user represents]
    CASE_OUTCOME: [who won the actual case]  
    USER_RESULT: [WIN or LOSS for the user]
    REASONING: [your detailed explanation]
    """

    try:
        api_key = "AIzaSyAZK12mvMhMrOoDQytcwU3DfTjxAYLtENI"
        payload = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
        }

        model_name = "gemini-2.5-flash-preview-09-2025"
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        analysis_text = result["candidates"][0]["content"]["parts"][0]["text"]

        # Parse the structured response
        parsed_result = parse_llm_verdict_response(analysis_text)
        parsed_result["full_analysis"] = analysis_text

        return parsed_result

    except Exception as e:
        print(f"  ❌ Error in LLM analysis: {e}")
        return {
            "verdict": "UNCLEAR",
            "user_party": "Unknown",
            "reasoning": f"Analysis failed: {str(e)}",
            "full_analysis": f"Error occurred during analysis: {str(e)}",
        }


def parse_llm_verdict_response(analysis_text: str) -> dict:
    """Parse structured LLM response to extract verdict components."""

    result = {"verdict": "UNCLEAR", "user_party": "Unknown", "reasoning": ""}

    lines = analysis_text.split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("USER_PARTY:"):
            result["user_party"] = line.replace("USER_PARTY:", "").strip()
        elif line.startswith("USER_RESULT:"):
            user_result = line.replace("USER_RESULT:", "").strip().upper()
            if "WIN" in user_result:
                result["verdict"] = "WIN"
            elif "LOSS" in user_result:
                result["verdict"] = "LOSS"
            else:
                result["verdict"] = "UNCLEAR"
        elif line.startswith("REASONING:"):
            result["reasoning"] = line.replace("REASONING:", "").strip()

    # If reasoning spans multiple lines, capture it all
    if "REASONING:" in analysis_text:
        reasoning_start = analysis_text.find("REASONING:") + len("REASONING:")
        result["reasoning"] = analysis_text[reasoning_start:].strip()

    return result


def extract_simple_verdict(analysis_text: str) -> str:
    """Extract generic outcome from LLM analysis - let LLM determine what this means for the user."""
    if not analysis_text:
        return "UNCLEAR"

    analysis_lower = analysis_text.lower()

    print(f"🔍 Analyzing verdict text: {analysis_lower[:200]}...")

    # Generic positive outcome indicators (someone succeeded/won)
    positive_patterns = [
        "won",
        "successful",
        "succeeded",
        "prevailed",
        "granted",
        "allowed",
        "favorable",
        "in favor",
        "relief",
        "vindicated",
        "upheld",
        "sustained",
        "appeal allowed",
        "petition allowed",
        "claim allowed",
        "suit decreed",
        "judgment in favor",
        "order in favor",
        "decree in favor",
    ]

    # Generic negative outcome indicators (someone failed/lost)
    negative_patterns = [
        "dismissed",
        "rejected",
        "failed",
        "unsuccessful",
        "denied",
        "not granted",
        "unfavorable",
        "against",
        "lost",
        "defeated",
        "appeal dismissed",
        "petition dismissed",
        "claim rejected",
        "suit dismissed",
    ]

    # Count occurrences
    positive_count = sum(
        1 for pattern in positive_patterns if pattern in analysis_lower
    )
    negative_count = sum(
        1 for pattern in negative_patterns if pattern in analysis_lower
    )

    print(
        f"📊 Positive indicators: {positive_count}, Negative indicators: {negative_count}"
    )

    # Determine generic outcome
    if positive_count > negative_count and positive_count > 0:
        print("✅ Overall POSITIVE outcome detected")
        return "POSITIVE_OUTCOME"
    elif negative_count > positive_count and negative_count > 0:
        print("❌ Overall NEGATIVE outcome detected")
        return "NEGATIVE_OUTCOME"
    else:
        print("❓ Outcome unclear")
        return "UNCLEAR"


def analyze_legal_cases(
    json_file_path: str, user_query: str, user_context: str = "", top_k: int = 10
) -> dict:
    """
    Complete workflow: Analyze legal cases from JSON file.

    Args:
        json_file_path: Path to JSON file with cases
        user_query: User's legal problem/query
        user_context: Additional context about user's situation
        top_k: Number of top cases to analyze

    Returns:
        dict: Complete analysis results
    """
    print("=" * 80)
    print("🏛️  LEGAL CASE ANALYSIS PIPELINE")
    print("=" * 80)

    # Step 1: Load cases from JSON
    cases = load_cases_from_json(json_file_path)

    # Step 2: Create embeddings
    embedding_stats = create_legal_case_embeddings(cases)

    # Step 3: Find relevant cases
    relevant_doc_ids = find_relevant_cases(user_query, top_k=top_k)

    # Step 4: Initialize results structure
    final_results = []

    # Initialize incremental results file with basic info
    incremental_results = {
        "user_query": user_query,
        "user_context": user_context,
        "total_cases_to_analyze": len(relevant_doc_ids),
        "analysis_status": "in_progress",
        "cases_completed": 0,
        "verdict_summary": {
            "wins": 0,
            "losses": 0,
            "unclear": 0,
        },
        "cases": [],
        "embedding_stats": embedding_stats,
    }

    # Write initial results file
    output_file = "legal_analysis_results.json"
    print(f"📝 Writing incremental results to: {output_file}")
    save_analysis_results(incremental_results, output_file, quiet=True)

    print(f"\n📊 Analyzing verdicts for {len(relevant_doc_ids)} cases...")

    # Step 5: Analyze verdicts for each case and update results incrementally
    for i, doc_id in enumerate(relevant_doc_ids):
        print(f"\nAnalyzing case {i+1}/{len(relevant_doc_ids)}: {doc_id}")

        # Get case details
        case_detail = cases[doc_id]

        # Analyze verdict
        verdict_analysis = analyze_case_verdict(doc_id, user_context=user_context)

        result = {
            "rank": i + 1,
            "doc_id": doc_id,
            "title": case_detail["title"],
            "court": case_detail["court"],
            "date": case_detail["date"],
            "verdict": verdict_analysis["verdict"],
            "analysis_summary": (
                verdict_analysis["analysis"][:500] + "..."
                if len(verdict_analysis["analysis"]) > 500
                else verdict_analysis["analysis"]
            ),
            "user_party_identified": verdict_analysis.get(
                "user_party_identified", "Unknown"
            ),
            "reasoning": verdict_analysis.get("reasoning", ""),
        }

        final_results.append(result)
        print(f"  Verdict: {verdict_analysis['verdict']}")

        # Update incremental results after each case
        incremental_results["cases"].append(result)
        incremental_results["cases_completed"] = i + 1

        # Update verdict counts
        win_count = sum(1 for r in final_results if r["verdict"] == "WIN")
        loss_count = sum(1 for r in final_results if r["verdict"] == "LOSS")
        unclear_count = sum(1 for r in final_results if r["verdict"] == "UNCLEAR")

        incremental_results["verdict_summary"] = {
            "wins": win_count,
            "losses": loss_count,
            "unclear": unclear_count,
        }

        # Write updated results after each case
        print(f"  📝 Updated results file (completed: {i+1}/{len(relevant_doc_ids)})")
        save_analysis_results(incremental_results, output_file, quiet=True)

    # Step 6: Finalize results
    incremental_results["analysis_status"] = "completed"
    incremental_results["total_cases_analyzed"] = len(final_results)

    # Final save with completion status
    save_analysis_results(incremental_results, output_file)

    print(f"\n🎯 ANALYSIS COMPLETE!")
    print(f"  Total cases analyzed: {len(final_results)}")
    print(f"  Wins: {win_count}, Losses: {loss_count}, Unclear: {unclear_count}")

    return incremental_results


def save_analysis_results(
    results: dict, output_file: str = "legal_analysis_results.json", quiet: bool = False
):
    """Save analysis results to JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    if not quiet:
        print(f"\n💾 Results saved to: {output_file}")
    # For incremental saves, just write without verbose logging


# Example usage for the complete legal case analysis:
"""
# Run complete legal case analysis
results = analyze_legal_cases(
    json_file_path="output.json",
    user_query="breach of contract for delayed delivery causing financial losses",
    user_context="I am a buyer who suffered losses due to delayed delivery of critical equipment",
    top_k=10
)

# Save results
save_analysis_results(results, "legal_analysis_results.json")

# Print summary
print(f"Analysis complete! Found {results['total_cases_analyzed']} relevant cases")
print(f"Verdict summary: {results['verdict_summary']}")
"""
