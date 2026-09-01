"""
Helps the chatbot answer questions using product documents.
Reads uploaded files, saves them in pieces, and finds answers when customers ask.
"""
import math
import os

from dotenv import load_dotenv

load_dotenv()

# Only plain-text uploads are supported for now (.txt, .csv, .md).
ALLOWED_TEXT_EXTENSIONS = {'.txt', '.csv', '.md'}
EMBED_MODEL = 'text-embedding-3-small'
CHAT_MODEL = 'gpt-4o-mini'
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 5
EMBED_BATCH_SIZE = 64


def normalize_product_type(product_type):
    """The shop calls it accessory but the database stores it as tool. This fixes the name."""
    pt = (product_type or '').strip().lower()
    if pt == 'accessory':
        return 'tool'
    return pt


def _openai_client():
    """Gets the OpenAI key from .env and connects. Shows an error if the key is missing."""
    from openai import OpenAI
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY is not configured.')
    return OpenAI(api_key=api_key)


def extract_text(blob, filename):
    """Reads text from an uploaded file. Returns nothing if the file type is wrong or we cannot read it."""
    if not blob:
        return None
    ext = os.path.splitext((filename or '').lower())[1]
    if ext not in ALLOWED_TEXT_EXTENSIONS:
        return None
    for encoding in ('utf-8', 'utf-8-sig', 'latin-1'):
        try:
            return blob.decode(encoding)
        except (UnicodeDecodeError, AttributeError):
            continue
    return None


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Cuts a long text into smaller pieces. Some text repeats at the edges so nothing gets lost."""
    text = (text or '').strip()
    if not text:
        return []
    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        # Step back a little so neighbouring chunks share some text.
        start = max(end - overlap, start + 1)
    return chunks


def embed_texts(texts):
    """Sends text to OpenAI and gets back number lists the computer can search with. Does it in batches for big files."""
    if not texts:
        return []
    client = _openai_client()
    vectors = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i:i + EMBED_BATCH_SIZE]
        response = client.embeddings.create(model=EMBED_MODEL, input=batch)
        vectors.extend(item.embedding for item in response.data)
    return vectors


def cosine_similarity(a, b):
    """Checks how close two number lists are. Higher score means they match better."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def index_product(product_type, product_id):
    """Reads all files for one product, splits them into pieces, and saves them so the chatbot can search later."""
    from models import (
        delete_rag_chunks_for_product,
        get_product_files_with_data,
        insert_rag_chunks,
    )

    product_type = normalize_product_type(product_type)
    if product_type not in ('plant', 'tool', 'food'):
        return None, 'Invalid product type.'
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return None, 'Invalid product id.'

    files = get_product_files_with_data(product_type, product_id)
    if not files:
        return None, 'No documents found for this product. Upload text files and save first.'

    pending = []
    for file_row in files:
        text = extract_text(file_row.get('file_data'), file_row.get('file_name'))
        if not text:
            continue
        for idx, content in enumerate(chunk_text(text)):
            pending.append({
                'product_type': product_type,
                'product_id': product_id,
                'file_id': file_row['id'],
                'chunk_index': idx,
                'content': content,
            })

    if not pending:
        return None, 'No readable text content found in the uploaded files.'

    try:
        embeddings = embed_texts([row['content'] for row in pending])
    except Exception as exc:
        return None, f'Embedding failed: {exc}'

    for row, embedding in zip(pending, embeddings):
        row['embedding'] = embedding

    # Start over each time instead of trying to update old pieces one by one.
    delete_rag_chunks_for_product(product_type, product_id)
    inserted = insert_rag_chunks(pending)
    if inserted != len(pending):
        return None, 'Failed to save indexed chunks to the database.'

    return inserted, None


def search_chunks(product_type, product_id, query, top_k=TOP_K):
    """Finds the text pieces that best match a customer question for one product."""
    from models import get_rag_chunks_for_product

    product_type = normalize_product_type(product_type)
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return []

    chunks = get_rag_chunks_for_product(product_type, product_id)
    if not chunks:
        return []

    try:
        query_vec = embed_texts([query.strip()])[0]
    except Exception:
        return []

    scored = []
    for chunk in chunks:
        emb = chunk.get('embedding') or []
        if not emb:
            continue
        scored.append((cosine_similarity(query_vec, emb), chunk['content']))

    scored.sort(key=lambda item: item[0], reverse=True)
    # Skip pieces that do not really match the question.
    return [content for score, content in scored[:top_k] if score > 0]


def answer_question(product_type, product_id, product_name, question):
    """Uses the product documents to answer a question. Sends the best matching text to GPT and returns the reply."""
    question = (question or '').strip()
    if not question:
        return None, 'Please enter a question.'

    product_type = normalize_product_type(product_type)
    passages = search_chunks(product_type, product_id, question)
    if not passages:
        return (
            'No indexed documents are available for this product yet, '
            'so I cannot answer from product documentation. '
            'Please check the product description or contact the store.',
            None,
        )

    context = '\n\n---\n\n'.join(passages)
    name = (product_name or 'this product').strip()
    system_prompt = (
        f'You are a helpful assistant for an aquarium store. '
        f'Answer questions about "{name}" using ONLY the context below. '
        f'If the answer is not in the context, say you do not have that information '
        f'in the product documents. Keep answers concise and friendly.'
    )
    user_prompt = f'Context:\n{context}\n\nQuestion: {question}'

    try:
        client = _openai_client()
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0.2,
        )
        answer = (response.choices[0].message.content or '').strip()
        if not answer:
            return None, 'No answer was generated.'
        return answer, None
    except Exception as exc:
        return None, f'Could not generate an answer: {exc}'
