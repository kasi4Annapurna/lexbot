import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
from openai import OpenAI
import tempfile
import os

# ---- SETUP ----
# Key comes from Streamlit Cloud Secrets (safe - not hardcoded!)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

chroma_client = chromadb.EphemeralClient()
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# ---- FUNCTIONS ----

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def split_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

def load_pdf_to_db(text, collection_name="lexbot"):
    try:
        chroma_client.delete_collection(collection_name)
    except:
        pass
    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=embed_fn
    )
    chunks = split_text(text)
    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )
    return collection, len(chunks)

def search_db(query, collection):
    results = collection.query(query_texts=[query], n_results=3)
    return results["documents"][0]

def ask_groq(question, context_chunks):
    context = "\n\n---\n\n".join(context_chunks)
    prompt = f"""You are a helpful assistant. Answer the question using ONLY the context below.
Always mention which part of the document your answer comes from.

Context:
{context}

Question: {question}

Answer:"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# ---- UI ----

st.title("📄 LexBot — Ask Your PDF Anything!")
st.write("Upload a PDF, then ask questions about it.")

uploaded_file = st.file_uploader("Upload your PDF here", type="pdf")

if uploaded_file:
    with st.spinner("Reading your PDF... please wait ⏳"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        text = read_pdf(tmp_path)
        collection, num_chunks = load_pdf_to_db(text)

    st.success(f"✅ PDF loaded! Created {num_chunks} searchable chunks.")

    question = st.text_input("Ask a question about your PDF:")

    if question:
        with st.spinner("Thinking... 🤔"):
            relevant_chunks = search_db(question, collection)
            answer = ask_groq(question, relevant_chunks)

        st.subheader("💬 Answer:")
        st.write(answer)

        with st.expander("📚 Source chunks used (click to see)"):
            for i, chunk in enumerate(relevant_chunks):
                st.write(f"**Chunk {i+1}:** {chunk[:300]}...")
