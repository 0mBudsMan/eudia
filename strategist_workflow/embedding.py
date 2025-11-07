import chromadb
import torch
from transformers import AutoTokenizer, AutoModel
import math
import json
import requests
import uuid
from typing import List, Dict, Optional, Union
import numpy as np

def create_case_embeddings_db(cases_data: Union[str, Dict[str, str]], collection_name: str = "case_chunks", 
                            persist_directory: str = "./chroma_db"):
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
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        # print(f"Created new collection: {collection_name}")
    except Exception as e:
        if "already exists" in str(e):
            client.delete_collection(collection_name)
            collection = client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
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
        # print(f"Processing case: {case_id}")
        
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
            return_offsets_mapping=True
        )
        
        input_ids = encoded_input['input_ids']
        attention_mask = encoded_input['attention_mask']
        offset_mapping = encoded_input['offset_mapping']
        
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
                    input_ids=batch_input_ids,
                    attention_mask=batch_attention_mask
                )
            
            cls_embeddings = output.last_hidden_state[:, 0, :]
            all_embeddings.append(cls_embeddings.cpu().numpy())
            
            if (i+1) % 10 == 0 or i+1 == num_batches:
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
        embeddings, chunk_texts = get_chunk_embeddings_and_texts(case_text, case_id)
        
        # Prepare data for this case
        case_ids = [str(uuid.uuid4()) for _ in range(len(chunk_texts))]
        case_metadatas = [
            {
                "case_id": case_id,
                "chunk_index": i,
                "global_chunk_index": total_chunks + i,
                "text_length": len(text),
                "case_total_chunks": len(chunk_texts)
            } 
            for i, text in enumerate(chunk_texts)
        ]
        
        all_embeddings.extend(embeddings.tolist())
        all_documents.extend(chunk_texts)
        all_metadatas.extend(case_metadatas)
        all_ids.extend(case_ids)
        total_chunks += len(chunk_texts)
    
    # Add to ChromaDB collection
    # print(f"\nAdding {len(all_embeddings)} embeddings from {len(cases_dict)} cases to ChromaDB...")
    collection.add(
        embeddings=all_embeddings,
        documents=all_documents,
        metadatas=all_metadatas,
        ids=all_ids
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
        'collection_name': collection_name,
        'num_cases': len(cases_dict),
        'num_chunks': total_chunks,
        'embedding_dim': len(all_embeddings[0]),
        'persist_directory': persist_directory,
        'case_stats': case_stats
    }


def query_case_embeddings_db(query: str, collection_name: str = "case_chunks", 
                           persist_directory: str = "./chroma_db", top_k: int = 3,
                           filter_case_ids: Optional[List[str]] = None):
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
        raise RuntimeError(f"Collection '{collection_name}' not found. Please create embeddings first. Error: {e}")
    
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
        return_tensors="pt"
    )
    
    input_ids = encoded_input['input_ids'].to(device)
    attention_mask = encoded_input['attention_mask'].to(device)
    
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
        include=['documents', 'metadatas', 'distances'],
        where=where_clause
    )
    
    # Process results with source tracking
    relevant_chunks = []
    sources_summary = {}
    
    for i in range(len(results['documents'][0])):
        metadata = results['metadatas'][0][i]
        case_id = metadata['case_id']
        
        chunk_data = {
            'text': results['documents'][0][i],
            'metadata': metadata,
            'distance': results['distances'][0][i],
            'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
            'source': {
                'case_id': case_id,
                'chunk_index': metadata['chunk_index'],
                'global_chunk_index': metadata['global_chunk_index']
            }
        }
        relevant_chunks.append(chunk_data)
        
        # Track sources
        if case_id not in sources_summary:
            sources_summary[case_id] = []
        sources_summary[case_id].append(metadata['chunk_index'])
    
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
            source = chunk['source']
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
            answer = result['candidates'][0]['content']['parts'][0]['text']
            
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
        'query': query,
        'relevant_chunks': relevant_chunks,
        'sources_summary': sources_summary,
        'answer': answer,
        'collection_stats': {
            'name': collection_name,
            'total_chunks': collection.count()
        }
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
    "precedent_case_2020": "Full text of precedent case..."
}

# Step 1: Create embeddings database for multiple cases
db_info = create_case_embeddings_db(cases, "multi_case_collection")

# Step 2: Query across all cases  
result = query_case_embeddings_db("What are the damages awarded?", "multi_case_collection", top_k=5)
print(result)
# Step 3: Query specific cases only
result2 = query_case_embeddings_db(
    "Who won the case?", 
    "multi_case_collection",
)
print(result2)
