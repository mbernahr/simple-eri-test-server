# Simple External RAG Test Server

A minimal **External Retrieval Interface (ERI)** test implementation backed by **ChromaDB**,  
with a small **FastAPI** backend and a **Gradio** helper UI.

Use this repository to:

- spin up a local ERI server,
- protect it with simple `USERNAME_PASSWORD` authentication,
- upload and index PDFs into a vector store (Chroma),
- and test ERI-based retrieval from tools like **OpenWebUI**.

---

## 1. Repository structure

```text
simple-eri-test-server/
├── start.sh               # Convenience script: start backend + frontend
├── README.md              # This file
└── rag-test
    ├── frontend.py        # Gradio helper UI
    ├── requirements.txt
    ├── chroma_db/         # Chroma persistence (runtime, git-ignored)
    ├── gradio_tmp/        # Temporary upload directory (runtime, git-ignored)
    └── src/
        ├── main.py        # FastAPI ERI backend (uvicorn entrypoint)
        ├── api.py         # ERI endpoints (/auth, /retrieval, /embedding, /admin, ...)
        ├── auth.py        # JWT + static token + username/password auth
        ├── config.py      # Server + ERI configuration
        ├── database.py    # Chroma-based vector store manager
        ├── embeddings.py  # Sentence-transformers embeddings (all-MiniLM-L6-v2)
        ├── models.py      # Pydantic models for ERI schema
        ├── security.py    # Request validation, security headers, sanitization
        ├── user_store.py  # Simple JSON-backed user store (users.json)
        ├── users.json     # Created at runtime via /admin/user or the UI
        └── Papers/        # Uploaded PDFs (created at runtime)
```

--- 

## 2. Requirements
- Python 3.10+

---

## 3. Installation
From scratch:
```bash
git clone https://github.com/mbernahr/simple-eri-test-server.git
cd simple-eri-test-server/rag-test

# create and activate virtualenv (example using venv)
python -m venv .venv
# Linux/Mac:
source .venv/bin/activate       
# Windows: 
# .venv\Scripts\activate

pip install -r requirements.txt
```

---

## 4. Running the server
### 4.1 Using `start.sh` (Recommended)
```bash
cd simple-eri-test-server
chmod +x start.sh
./start.sh
```

`start.sh` will:
1. `cd rag-test`
2. start the **External knowledge server** (Backend) in the background:
    ```bash
    python src/main.py &
    ```
3. wait 5 seconds for initialization,
4. start the **Gradio frontend**:
    ```bash
    python frontend.py
    ```

Default ports:
- Backend (FastAPI): `http://127.0.0.1:40304`
- Frontend (Gradio): `http://127.0.0.1:7860`

### 4.2 Starting manually (two terminals)
**Terminal 1**
```bash
cd simple-eri-test-server/rag-test
source .venv/bin/activate
python src/main.py
```

**Terminal 2**
```bash
cd simple-eri-test-server/rag-test
source .venv/bin/activate
python frontend.py
```

---

## 5. Using this helper

Open: `http://localhost:7860`

The UI provides three main functions:

---

### 5.1 User management

- Fields: **Username**, **Password**  
- Button: **Save user**

This calls `POST /admin/user` and stores credentials in `src/users.json`
via a simple JSON-backed user store (`user_store.py`).

You will use these credentials later for `USERNAME_PASSWORD` auth from OpenWebUI.

---

### 5.2 Document upload

- File input: **PDF to index**  
- Button: **Upload & index**

Flow:

1. The frontend sends the PDF to `POST /admin/upload`.
2. The backend saves it under:

   ```text
   rag-test/src/Papers/<filename>.pdf
   ```
3. `VectorStoreManager.add_pdf(...)` then:
    - loads the PDF with `PyPDFLoader`,
    - splits it into chunks via `RecursiveCharacterTextSplitter`,
    - adds those chunks into Chroma at:
        ```text
        rag-test/chroma_db/
        ```

If everything succeeds, the UI shows a green confirmation message with the original
file name.

---

### 5.3 Vector DB maintenance

- Button: Clear vector DB

This calls POST /admin/clear and removes **all entries** from the
Chroma collection.

--

## 6. Connecting from OpenWebUI (ERI Knowledge Server)

You can register this server as an external knowledge backend in **OpenWebUI**.

The Gradio UI shows a short configuration hint; the essential settings are:

- **Host / URL:** `http://<host-ip>`, for example:
  - `http://127.0.0.1` for local access
  - or your LAN IP if you run it on another machine
- **Port:** `40304`
- **Authentication:** `USERNAME_PASSWORD`
- **Username / password:** the ones you created in the Gradio UI
  (e.g. `user1` / `secret123`, or your own values)

Typical flow in OpenWebUI:

1. Add a new “knowledge”:
   - host: `http://<host-ip>`
   - port: `40304`
   - auth method: `USERNAME_PASSWORD`
   - username/password: from the helper
2. Create a Knowledge Base that uses this ERI server.
3. Ask a question in a chat that uses this KB. OpenWebUI will:
   - call `/auth` to obtain a token,
   - call `/retrieval` with your prompt,
   - receive Chroma-based context (`Context` objects),
   - and augment the LLM answer with that context.

---

## 7. Background: External Retrieval Interface (ERI)

This project is a minimal testbed for the **External Retrieval Interface (ERI)** idea.

The ERI is an API pattern (in the spirit of the
[OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification))
that acts as a contract between:

- **Data providers** – who own and serve the data, and  
- **Interaction platforms** – LLM-based systems that call ERI endpoints to augment prompts.

### Key ideas

**Clear separation of roles**

- Data providers implement ERI-compatible servers.
- Interaction platforms:
  - call `/auth`, `/dataSource`, `/retrieval`, …
  - integrate the retrieved context into prompt construction.

**Provider control**

Data providers retain control over:

- which data is exposed,
- how it is retrieved (algorithms, ranking, filtering),
- and which LLM providers / locations / infrastructure are allowed
  to process the retrieved data.

**Unified retrieval interface**

By standardizing endpoints and payloads, different data providers can offer
heterogeneous backends (databases, vector stores, file systems, etc.)
behind a common API.

### Typical logical components of ERI

- **Authentication**
  - `GET /auth/methods` – supported auth methods.
  - `POST /auth` – performs authentication and returns a token.
- **Restrictions / security**
  - endpoints to describe which LLM providers / regions / types are allowed.
- **Data and embedding description**
  - `GET /dataSource` – which data source exists.
  - `GET /embedding/info` – what embedding is used for documents and queries.
- **Retrieval**
  - `GET /retrieval/info` – list of retrieval processes.
  - `POST /retrieval` – core retrieval endpoint returning a list of `Context` objects.

This repository implements a basic version of those ideas, using:

- **ChromaDB** as the vector store,
- **SentenceTransformers** (`all-MiniLM-L6-v2`) for embeddings,
- **FastAPI** for the HTTP API,
- **Gradio** for a small helper UI.

It is intentionally small and focused, so you can:

- understand the ERI pattern end-to-end,
- plug it into OpenWebUI or similar tools,
- and experiment with RAG-style augmentation in a controlled local environment.

