# AI Repository Intelligence Platform

This project uses a FastAPI-based "parser" service (in `parser-workflow`) and a Flask-based main app (in `repo-ai`). Both services need to be running in parallel during development.

## 🚀 Quick Start & Local Run Instructions

### 1. Set Up Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies:

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

Install the required packages for both the backend parser and the frontend app.

```bash
# Install parser workflow requirements
cd parser-workflow
pip install -r requirements.txt
cd ..

# Install repo-ai requirements
cd repo-ai
pip install -r requirements.txt
cd ..
```

### 3. Configure LLM API Key

The application requires an LLM provider to answer questions about your codebase. It supports Groq, Gemini, OpenRouter, and others.

1. Navigate to the `repo-ai` folder.
2. Create a file named `.env` (you can copy `.env.example`).
3. Add your provider and API key. For example, for Groq:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### 4. Start the Servers

You need to run both the FastAPI parser backend and the Flask web interface at the same time. Open two terminals, and make sure your virtual environment is activated in both.

**Terminal 1 - Parser Backend:**
```bash
cd parser-workflow
python start_backend.py
```
*(This starts the parser on `http://127.0.0.1:8001`)*

**Terminal 2 - Main Web App:**
```bash
cd repo-ai
python app.py
```
*(This starts the UI on `http://127.0.0.1:5000`)*

### 5. Access the Interface

Open your browser and navigate to **[http://localhost:5000](http://localhost:5000)**. 
Upload a repository zip file and start chatting with your codebase!

---

## Important Notes
- **Python Version**: Ensure you are using Python 3.10 or higher.
- **Troubleshooting**: If the `repo-ai` app complains that the parser is unavailable, ensure `start_backend.py` is running and accessible on port `8001`. If the port is in use, the script will pick a random one; update `repo-ai/.env` with the new `PARSER_API_URL`.
