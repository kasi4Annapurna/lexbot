import streamlit as st
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from pypdf import PdfReader
from openai import OpenAI
import tempfile
import os
from dotenv import load_dotenv

# ---- SETUP ----
load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

client = OpenAI(
    api_key=GROQ_API_KEY or "dummy",
    base_url="https://api.groq.com/openai/v1"
)

# Use PersistentClient instead of EphemeralClient (fixes the crash)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embed_fn = DefaultEmbeddingFunction()

# ---- FUNCTIONS ----

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()

def split_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

def load_pdf_to_db(text, collection_name="lexbot"):
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass
    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=embed_fn
    )
    chunks = split_text(text)
    if not chunks:
        raise ValueError("No text could be extracted from the PDF.")
    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )
    return collection, len(chunks)

def search_db(query, collection, n_results=3):
    results = collection.query(query_texts=[query], n_results=n_results)
    return results["documents"][0]

def ask_groq(question, context_chunks):
    if not GROQ_API_KEY:
        return "⚠️ **GROQ_API_KEY is not set.** Please check your `.env` file."
    
    context = "\n\n---\n\n".join(context_chunks)
    prompt = f"""You are a helpful assistant. Answer the question using ONLY the context below.
Always mention which part of the document your answer comes from.

Context:
{context}

Question: {question}

Answer:"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error calling Groq API: {str(e)}"

# ---- UI ----

st.set_page_config(page_title="LexBot", page_icon="📄", layout="centered")
st.title("📄 LexBot — Ask Your PDF Anything!")
st.write("Upload a PDF, then ask questions about it.")

if not GROQ_API_KEY:
    st.warning("⚠️ No GROQ_API_KEY found. Check your `.env` file.")

uploaded_file = st.file_uploader("Upload your PDF here", type="pdf")

if uploaded_file:
    with st.spinner("Reading your PDF... please wait ⏳"):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            text = read_pdf(tmp_path)
            os.unlink(tmp_path)
            if not text:
                st.error("Could not extract any text from this PDF.")
                st.stop()
            collection, num_chunks = load_pdf_to_db(text)
            st.session_state["collection"] = collection
            st.session_state["num_chunks"] = num_chunks
            st.session_state["pdf_name"] = uploaded_file.name
        except Exception as e:
            st.error(f"Failed to process PDF: {e}")
            st.stop()

    st.success(f"✅ **{st.session_state.get('pdf_name', 'PDF')}** loaded! Created **{st.session_state['num_chunks']}** searchable chunks.")

    question = st.text_input("Ask a question about your PDF:")

    if question:
        with st.spinner("Thinking... 🤔"):
            relevant_chunks = search_db(question, st.session_state["collection"])
            answer = ask_groq(question, relevant_chunks)

        st.subheader("💬 Answer:")
        st.markdown(answer)

        with st.expander("📚 Source chunks used (click to see)"):
            for i, chunk in enumerate(relevant_chunks):
                st.markdown(f"**Chunk {i+1}:**")
                st.write(chunk[:500] + ("..." if len(chunk) > 500 else ""))
else:
    st.info("👆 Upload a PDF to get started.")
