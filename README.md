# DocuMind AI 🧠

An intelligent, full-stack **Document Q&A Assistant** powered by **RAG (Retrieval Augmented Generation)** with multi-LLM support, study tools, and a professional React interface.

![DocuMind AI](https://img.shields.io/badge/DocuMind-AI-6366f1?style=for-the-badge&logo=brain&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=flat-square&logo=mongodb)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991?style=flat-square&logo=openai)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?style=flat-square&logo=google)

---

## ✨ Features

### 📄 Document Intelligence
- **Upload PDFs, TXT, code files** (Python, JS, Java, C++, Markdown, CSV)
- Automatic text extraction and smart chunking
- Vector embeddings with **FAISS** for fast similarity search

### 💬 RAG-Powered Chat
- Ask questions about your uploaded documents
- AI retrieves relevant context and generates accurate answers
- **Source citations** with relevance scores
- Full conversation history stored in **MongoDB**

### 🔄 Multi-LLM Support
- Switch between **GPT-4o Mini** (OpenAI) and **Gemini 1.5 Flash** (Google)
- Seamless model switching mid-conversation

### 🎓 Study Tools
- **Quiz Generator** — Auto-generate MCQ quizzes from documents
- **Flashcards** — Create study flashcards for quick revision
- **Smart Summary** — Get concise summaries with key points

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, React Markdown, Axios |
| **Backend** | Python, FastAPI, Uvicorn |
| **Database** | MongoDB Atlas (Motor async driver) |
| **Vector Store** | FAISS (Facebook AI Similarity Search) |
| **AI / LLM** | OpenAI GPT-4o Mini, Google Gemini 1.5 Flash |
| **Embeddings** | OpenAI text-embedding-3-small |
| **PDF Parsing** | PyPDF2 |

---

## 📁 Project Structure

```
DocuMind-AI/
├── client/                    # React Frontend (Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx    # RAG chat interface
│   │   │   ├── DocumentUpload.jsx # File upload & management
│   │   │   ├── Header.jsx        # Navigation & model selector
│   │   │   ├── Sidebar.jsx       # Conversation history
│   │   │   └── StudyTools.jsx    # Quiz, flashcards, summary
│   │   ├── services/
│   │   │   └── api.js            # Axios API service
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── server/                    # FastAPI Backend
│   ├── main.py                # App entry point
│   ├── config.py              # Environment configuration
│   ├── database.py            # MongoDB connection
│   ├── models.py              # Pydantic schemas
│   ├── routes/
│   │   ├── chat.py            # Chat & conversation endpoints
│   │   ├── documents.py       # Upload & document management
│   │   └── study.py           # Quiz, flashcards, summary
│   ├── services/
│   │   ├── llm_service.py     # OpenAI & Gemini integration
│   │   ├── rag_service.py     # FAISS vector search & RAG
│   │   └── document_service.py # File parsing & chunking
│   ├── requirements.txt
│   └── .env.example
│
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** 18+
- **Python** 3.10+
- **MongoDB Atlas** account (free tier works)
- **OpenAI API key** (for GPT-4 & embeddings)
- **Google Gemini API key** (optional, for Gemini model)

### 1. Clone the Repository
```bash
git clone https://github.com/harsh0707005-web/DocuMind-AI.git
cd DocuMind-AI
```

### 2. Backend Setup
```bash
cd server

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env         # Windows
# cp .env.example .env         # Mac/Linux

# Edit .env with your API keys:
# MONGODB_URI=mongodb+srv://...
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=...

# Start the server
python main.py
```
Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd client

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend runs at: `http://localhost:5173`

---

## 🔑 API Keys Setup

### MongoDB Atlas (Free)
1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Create a free cluster
3. Get connection string → paste in `.env`

### OpenAI API
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an API key → paste in `.env`

### Google Gemini API (Free)
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create an API key → paste in `.env`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/` | Send message with RAG context |
| GET | `/api/chat/conversations` | List all conversations |
| GET | `/api/chat/conversations/:id/messages` | Get conversation messages |
| DELETE | `/api/chat/conversations/:id` | Delete a conversation |
| POST | `/api/documents/upload` | Upload a document |
| GET | `/api/documents/` | List all documents |
| DELETE | `/api/documents/:id` | Delete a document |
| POST | `/api/study/quiz` | Generate quiz questions |
| POST | `/api/study/flashcards` | Generate flashcards |
| POST | `/api/study/summarize` | Summarize documents |
| GET | `/api/health` | Health check |

---

## 🖼️ Screenshots

### Chat Interface
Professional dark-theme chat with RAG-powered responses and source citations.

### Document Manager
Upload, manage, and track your indexed documents with chunk statistics.

### Study Tools
AI-generated quizzes with instant feedback, interactive flashcards, and smart summaries.

---

## 🛠️ How RAG Works

```
1. Upload Document → Extract Text → Split into Chunks
2. Generate Embeddings (OpenAI text-embedding-3-small)
3. Store in FAISS Vector Index
4. User Asks Question → Embed Query → Search FAISS
5. Retrieve Top-K Relevant Chunks
6. Send Context + Query to LLM (GPT-4 / Gemini)
7. Return Answer with Source Citations
```

---

## 👨‍💻 Author

**Harsh Vijay Rathod**
- Portfolio: [harsh-rathod.netlify.app](https://harsh-rathod.netlify.app)
- GitHub: [@harsh0707005-web](https://github.com/harsh0707005-web)
- LinkedIn: [Harsh Rathod](https://www.linkedin.com/in/harsh-rathod-921890291/)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
