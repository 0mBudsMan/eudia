import torch
from transformers import AutoTokenizer, AutoModel
import math
from case import scase
# --- Configuration ---
MODEL_NAME = "law-ai/InLegalBERT"
# This is the number of tokens that will overlap between chunks.
# A larger overlap (e.g., 100-150) can be better but is slower.
CHUNK_OVERLAP = 100
# Process this many chunks at a time. Adjust based on your GPU/CPU memory.
BATCH_SIZE = 8
# ---------------------

def get_document_embedding(text: str, tokenizer, model, device):
    """
    Generates a single embedding for a large text document by chunking,
    processing in batches, and averaging the [CLS] token embeddings.
    """
    print(f"Starting embedding generation for a document with {len(text)} characters.")

    # 1. Get Model's Max Length
    # We subtract 2 to account for the [CLS] and [SEP] tokens.
    max_length = tokenizer.model_max_length
    
    # 2. Tokenize the entire text with chunking
    # The tokenizer will automatically handle creating overlapping chunks.
    # - `return_overflowing_tokens=True`: This is the key. It tells the
    #   tokenizer to return a list of chunked inputs.
    # - `stride`: This is the number of tokens to overlap between chunks.
    # - `padding="max_length"`: Ensures all chunks are padded to 512 tokens.
    print(f"Tokenizing and chunking the text with max_length={max_length} and overlap={CHUNK_OVERLAP}...")
    encoded_input = tokenizer(
        text,
        max_length=max_length,
        truncation=True,
        return_overflowing_tokens=True,
        stride=CHUNK_OVERLAP,
        padding="max_length",
        return_tensors="pt"  # Return PyTorch tensors
    )

    input_ids = encoded_input['input_ids']
    attention_mask = encoded_input['attention_mask']
    
    num_chunks = input_ids.shape[0]
    print(f"Text was split into {num_chunks} overlapping chunks.")

    # 3. Process chunks in batches
    all_cls_embeddings = []
    num_batches = math.ceil(num_chunks / BATCH_SIZE)
    
    print(f"Processing {num_chunks} chunks in {num_batches} batches of size {BATCH_SIZE}...")
    
    for i in range(num_batches):
        start_index = i * BATCH_SIZE
        end_index = min((i + 1) * BATCH_SIZE, num_chunks)
        
        # Slice the batch
        batch_input_ids = input_ids[start_index:end_index].to(device)
        batch_attention_mask = attention_mask[start_index:end_index].to(device)
        
        # Process the batch
        with torch.no_grad():
            output = model(
                input_ids=batch_input_ids,
                attention_mask=batch_attention_mask
            )
        
        # Get the last hidden state
        last_hidden_state = output.last_hidden_state
        
        # Get the embedding for the [CLS] token (the first token)
        # Shape: (batch_size, 768)
        cls_embeddings = last_hidden_state[:, 0, :]
        
        # Store the embeddings (move to CPU to save GPU memory)
        all_cls_embeddings.append(cls_embeddings.cpu())
        
        print(f"  ...Processed batch {i+1}/{num_batches}")

    # 4. Aggregate Embeddings
    # Concatenate all batch results into one big tensor
    all_cls_embeddings_tensor = torch.cat(all_cls_embeddings, dim=0)
    
    print(f"Aggregating {all_cls_embeddings_tensor.shape[0]} chunk embeddings.")
    
    # Calculate the mean embedding across all chunks
    # This gives you a single vector (shape: 768) for the entire document.
    document_embedding = torch.mean(all_cls_embeddings_tensor, dim=0)
    
    return document_embedding

# --- Main execution ---
if __name__ == "__main__":
    
    # 1. Load Model and Tokenizer
    print(f"Loading tokenizer: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    
    print(f"Loading model: {MODEL_NAME}")
    model = AutoModel.from_pretrained(MODEL_NAME)
    
    # 2. Set up device (GPU if available, otherwise CPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    model.to(device)
    model.eval()  # Set model to evaluation mode

    # 3. Create dummy text (simulating your 150-page document)
    # A 150-page document is ~75,000 words.
    # This paragraph is ~50 words. We'll repeat it 1500 times.
    sample_paragraph = scase
    
    print("Generating large dummy text...")
    # This will be approx 75,000 words
    large_legal_text = sample_paragraph * 1500 

    # 4. Generate the embedding
    try:
        doc_embedding = get_document_embedding(large_legal_text, tokenizer, model, device)
        
        print("\n--- Success! ---")
        print(f"Generated document embedding of shape: {doc_embedding.shape}")
        print("First 5 dimensions of the final embedding:")
        print(doc_embedding[:5])

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        if "out of memory" in str(e).lower():
            print(">>> HINT: Try reducing the BATCH_SIZE at the top of the script.")