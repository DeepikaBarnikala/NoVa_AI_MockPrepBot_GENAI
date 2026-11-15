# ✨ NOVA AI – Mock Interview Coach

**Prepare smarter. Practice confidently. Get hired.**

NOVA AI is a Generative AI-powered mock interview coach designed to help students prepare for technical interviews, HR interviews, aptitude questions, resume-based interviews, and other interview topics. It uses Google's Gemini API to generate responses, provide feedback, and support interactive interview practice.

## 📌 Project Overview

Preparing for interviews requires practice, personalized feedback, and access to relevant learning resources. NOVA AI brings these capabilities together in one application.

The project combines Large Language Models (LLMs), prompt engineering, document processing, Retrieval-Augmented Generation (RAG), image analysis, and conversation management to create an interactive interview preparation experience.

## 🎯 Objectives

- Provide an interactive AI-powered mock interview experience.
- Generate questions based on interview category, topic, and difficulty.
- Analyze resumes and suggest personalized interview questions.
- Analyze uploaded images and screenshots.
- Use a knowledge base to support relevant answers through RAG.
- Maintain conversation context for follow-up questions.
- Save chat history for future reference.
- Explore practical applications of Generative AI.

## 🚀 Features

### 1. AI Mock Interview
- Supports different interview categories, including Technical, HR, Aptitude, and resume-based preparation where configured.
- Allows topic and difficulty selection.
- Generates interview questions and evaluates user responses.
- Provides explanations, corrections, and suggestions for improvement.
- Supports interactive, question-by-question practice.

### 2. Resume Analysis
- Accepts PDF resume uploads.
- Extracts resume text using PyPDF.
- Generates a summary of skills, experience, strengths, and improvement areas.
- Suggests personalized interview questions based on resume content.

### 3. Image Question Analyzer
- Accepts supported image formats such as PNG, JPG, JPEG, and WebP.
- Analyzes uploaded screenshots, questions, and other relevant images.
- Supports follow-up questions about uploaded image content when the conversation feature is enabled.

### 4. Retrieval-Augmented Generation (RAG)
- Uses a knowledge base to retrieve relevant information for answering questions.
- Uses retrieved context to help ground generated responses.
- Supports the integration of document retrieval and LLM-based answer generation.
- Can be extended with additional documents and learning resources.

### 5. Conversation Continuity
- Maintains previous messages during a conversation.
- Uses conversation context to answer follow-up questions.
- Helps users continue asking questions without replacing earlier messages.

### 6. Chat History
- Uses local SQLite by default or MySQL when configured.
- Organizes chat-history functionality in a separate Python module.
- Can be extended with conversation search, deletion, and history management.

### 7. AI Response Generation
- Integrates with the Google Gemini API.
- Uses prompt engineering to guide response quality and structure.
- Supports configurable generation settings, including temperature and output-token limits where implemented.
- Includes retry handling for supported temporary API failures.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| Streamlit | Interactive web interface |
| Google Gemini API | AI response generation |
| Google Gen AI SDK | Python integration with Gemini |
| python-dotenv | Loading local environment variables |
| PyPDF | Extracting text from PDF resumes |
| ChromaDB | Vector storage and retrieval for the RAG pipeline |
| MySQL Connector/Python | Optional hosted MySQL chat-history storage |
| SQLite | Local conversation-history storage |
| Git and GitHub | Version control and source-code hosting |

## 🧠 Generative AI Concepts Used

- **Large Language Models (LLMs):** Generate interview questions, explanations, and feedback.
- **Prompt Engineering:** Defines the AI's role, response format, and evaluation instructions.
- **Retrieval-Augmented Generation (RAG):** Supplies relevant retrieved knowledge to the language model.
- **Chunking:** Divides documents into smaller sections for retrieval, where implemented.
- **Embeddings and Vector Search:** Support semantic document retrieval when configured in the RAG pipeline.
- **Context Window:** Determines how much conversation and supporting information the model can process.
- **Temperature:** Controls the variability of generated responses.
- **Conversation Memory:** Uses previous messages to support follow-up questions.
- **Hallucination Reduction:** Uses relevant context and explicit instructions to encourage grounded answers.
- **Response Evaluation:** Can assess answers for relevance, correctness, clarity, and support from available context.

## 📂 Project Structure

The following is the intended high-level structure. Adjust the filenames to match the actual files in your GitHub repository.

```text
NOVA-AI/
│
├── app.py                  # Main Streamlit application
├── chat_history.py         # Conversation history and SQLite
├── image_analyzer.py       # Image analysis functionality
├── requirements.txt        # Python dependencies
├── .env                    # Local API key (never commit)
├── .gitignore              # Excluded files and secrets
├── README.md               # Project documentation
│
├── nova_chats.db           # Local SQLite database, if generated
├── nova_uploads/           # Uploaded image files, if generated
│
└── RAG files/modules        # Knowledge base and retrieval components,
                            # using the actual filenames in the project
```

**Note:** The actual project structure may vary. Include additional modules, knowledge-base folders, and configuration files that exist in your implementation.

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.12 (the version used to validate the pinned dependencies).
- Git installed on your computer.
- A Google Gemini API key.
- A GitHub account for source-code hosting.

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd NOVA-AI
```

Replace the repository URL and folder name with your actual values.

If you already have the project on your computer, open Git Bash or a terminal in the existing project folder instead.

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows Command Prompt:

```bash
venv\Scripts\activate
```

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure the Gemini API key

Copy `.env.example` to `.env` in the project root and set your Gemini API key:

```env
GEMINI_API_KEY=your_actual_api_key
```

Local chat history uses SQLite by default. To use MySQL locally, fill in
`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, and
`MYSQL_PASSWORD` in `.env`. Leave the MySQL settings blank to keep using
SQLite. If using MySQL, create the database and a dedicated application user
before starting NOVA.

For a local MySQL server, create a database and a separate app user in the
MySQL client (replace the sample password with a unique one):

```sql
CREATE DATABASE nova_ai CHARACTER SET utf8mb4;
CREATE USER 'nova_app'@'localhost' IDENTIFIED BY 'use-a-unique-password';
GRANT ALL PRIVILEGES ON nova_ai.* TO 'nova_app'@'localhost';
```

Then set `MYSQL_HOST=127.0.0.1`, `MYSQL_PORT=3306`,
`MYSQL_DATABASE=nova_ai`, `MYSQL_USER=nova_app`, and the password in `.env`.
Use the port and host that your local MySQL installation is configured for.

**Security:** Never upload `.env` or expose API keys, database passwords, or
connection strings in source code, screenshots, README files, or public
commits. `.env` is ignored by Git.

### Step 5: Run the application locally

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal, usually:

```text
http://localhost:8501
```

## 📦 Python Dependencies

The project uses the following packages where applicable:

| Package | Installation name | Usage |
|---|---|---|
| Streamlit | `streamlit` | Web application interface |
| Google Gen AI SDK | `google-genai` | Gemini model access |
| python-dotenv | `python-dotenv` | Environment configuration |
| PyPDF | `pypdf` | PDF text extraction |
| ChromaDB | `chromadb` | Vector database for RAG |
| MySQL Connector/Python | `mysql-connector-python` | Optional hosted chat-history database |

Python standard-library modules may also be used:

- `os` — environment variables and file paths.
- `hashlib` — content hashing.
- `io.BytesIO` — handling in-memory binary data.
- `sqlite3` — SQLite database access.
- `time` — retry delays where implemented.
- `mimetypes` — identifying file types.

Standard-library modules do not need to be installed separately.

The definitive dependency list should be generated from the actual imports in the project. Keep `requirements.txt` synchronized with the packages the application needs.

## 🔄 Application Workflow

1. The user opens the NOVA Streamlit interface.
2. The user selects an interview category, topic, and difficulty.
3. The application builds a prompt using the selected settings and relevant conversation context.
4. If RAG is enabled for that feature, relevant information is retrieved from the knowledge base.
5. The Gemini API generates a response.
6. The application displays the question, explanation, or feedback.
7. Previous messages are retained for follow-up questions where conversation continuity is enabled.
8. The chat-history module stores conversation data in local SQLite by default or MySQL when configured.
9. Resume and image-analysis features process uploaded content and generate relevant responses.

## 🔐 Configuration and Security

- Store API credentials in environment variables.
- Exclude `.env`, virtual environments, local databases, and private uploaded files from Git where appropriate.
- Use Streamlit secrets for credentials in a Streamlit Cloud deployment.
- Avoid logging API keys or sensitive user-uploaded information.
- Validate file types and upload sizes.
- Handle API errors and missing configuration gracefully.

## ☁️ Deploy to Streamlit Community Cloud

### Prepare the database

The MySQL server installed on your computer is available only to your
computer. `localhost` in Streamlit Community Cloud refers to the cloud app's
container, not your computer. For cloud-persistent conversations, create a
hosted MySQL database with a provider that permits connections from the
Streamlit app. Use its host, port, database name, and a dedicated database
user; do not use your MySQL root account.

The first app start creates the `conversations` and `messages` tables. No
local SQLite history is copied automatically; it stays in the ignored
`nova_chats.db` file on your computer.

### Push the project to GitHub

From PowerShell in the project folder, check that the secret file is not
staged, then commit and push the deployment files:

```powershell
git status
git check-ignore .env
git add app.py chat_history.py requirements.txt .env.example README.md test_chat_history.py
git commit -m "Prepare NOVA for Streamlit deployment"
git push origin main
```

If Git reports that your local branch is behind, first run:

```powershell
git pull --rebase origin main
```

Resolve any conflicts, then push again. Never force-push.

### Create the Streamlit app

1. Sign in to Streamlit Community Cloud using the GitHub account that can
   access this repository.
2. Select **Create app**, choose
   `DeepikaBarnikala/NoVa_AI_MockPrepBot_GENAI`, branch `main`, and
   `app.py` as the main file.
3. In the app's advanced settings, select Python 3.12 to match the tested
   environment, then deploy.
4. Open the app's **Settings → Secrets** and add the following TOML,
   replacing every placeholder with values from Gemini and your hosted
   MySQL provider:

   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"

   [mysql]
   host = "your-hosted-mysql-host"
   port = 3306
   database = "your-database-name"
   user = "your-dedicated-database-user"
   password = "your-database-password"
   ```

5. Save secrets and reboot/redeploy the app. Keep secrets in Streamlit's
   settings; never put the actual values in GitHub or `.env.example`.
6. Check the deployment logs if installation or startup fails. The direct
   dependencies are pinned in `requirements.txt`, and the database adapter
   supports local SQLite and configured MySQL.
7. Test a new General Chat conversation, an interview answer, RAG PDF upload
   and question, resume/image analysis, and PDF/PPTX downloads.

### Storage limitations

- MySQL stores conversations. It does not store RAG document vectors.
- RAG currently uses a local ChromaDB directory, so the cloud knowledge
  base starts empty and uploaded documents may be lost after a cloud
  restart or redeploy. Upload PDFs again when needed; durable RAG requires
  a separately hosted vector store.
- Uploaded images and generated files are also written to local app storage.
  Download generated documents during the session; local files should not
  be treated as permanent cloud storage.

## 🧪 Testing Checklist

- [ ] The Streamlit application starts successfully.
- [ ] Gemini API credentials are configured correctly.
- [ ] Interview categories and difficulty settings work.
- [ ] Questions and answer feedback are generated.
- [ ] PDF resume upload and analysis work.
- [ ] Image uploads and image questions work.
- [ ] Follow-up questions retain the relevant context.
- [ ] Chat history is saved and can be retrieved where implemented.
- [ ] Hosted MySQL credentials work in Streamlit secrets.
- [ ] RAG retrieves relevant information from the configured knowledge base.
- [ ] API failures and invalid uploads are handled appropriately.
- [ ] The deployed application works using cloud configuration.

## 🔮 Future Enhancements

- Improve conversation continuity and long-session context handling.
- Add better chat-history browsing, renaming, and deletion.
- Improve RAG retrieval quality and document-source attribution.
- Add structured scoring for interview answers.
- Provide progress reports and performance analytics.
- Add more interview categories and programming languages.
- Improve error handling, automated tests, and deployment reliability.
- Introduce persistent cloud storage for user sessions and uploaded files.
- Improve accessibility and mobile responsiveness.

## 🎓 Learning Outcomes

This project provides practical experience with Python application development, Streamlit, API integration, LLM prompting, document processing, vector retrieval, conversation management, and Git-based collaboration.

## 👩‍💻 Project Status

NOVA AI is an ongoing Generative AI project. The current version demonstrates the core functionality developed so far, while selected improvements and production-readiness work remain in progress.

## 📄 License

Add a license if you intend to distribute or open-source the project. Do not claim a license until you have selected and added one.

---

**NOVA AI — Prepare smarter. Practice confidently. Get hired.**
