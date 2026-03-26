# lexbot
# 📄 LexBot — Ask Your PDF Anything!

A RAG (Retrieval Augmented Generation) chatbot that lets you upload any PDF and ask questions about it. Answers are cited directly from the document — no hallucination!

## 🛠️ Tech Stack
- **Streamlit** — Web UI
- **ChromaDB** — Local vector database
- **Sentence Transformers** — Text embeddings
- **Groq LLM** — Free AI answer generation
- **LangChain** — Framework glue
- **PyPDF** — PDF reading

## 💡 What is RAG?
RAG = Retrieval Augmented Generation:
1. **Chunk** — PDF is split into small pieces
2. **Embed** — Each chunk is converted to vectors
3. **Search** — Your question finds the most relevant chunks
4. **Answer** — AI answers ONLY from those chunks (no hallucination!)

## ⚙️ How to Run Locally

1. Clone this repo:
```
git clone https://github.com/yourusername/lexbot.git
cd lexbot
```

2. Install requirements:
```
pip install -r requirements.txt
```

3. Create a `.env` file and add your Groq API key:
```
GROQ_API_KEY=your-groq-key-here
```
Get a free key at: https://console.groq.com

4. Run the app:
```
streamlit run app.py
```

## 🔑 Environment Variables
| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your free Groq API key from console.groq.com |

## 📌 Features
- Upload any PDF
- Ask questions in plain English
- Get cited answers from the document
- See exact source chunks used
- 100% private — runs on your laptop

## 🤝 Built By
Rasam — as a one-day RAG chatbot project
