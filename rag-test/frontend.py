import os
import socket
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------
# Gradio Temp-Dir Configuration (MUST BE BEFORE IMPORTING GRADIO)
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
GRADIO_TEMP_PATH = BASE_DIR / "gradio_tmp"
GRADIO_TEMP_PATH.mkdir(parents=True, exist_ok=True)
os.environ["GRADIO_TEMP_DIR"] = str(GRADIO_TEMP_PATH)
os.environ["GRADIO_LANGUAGE"] = "en"
os.environ["GRADIO_LOCALE"] = "en"

import gradio as gr  # noqa: E402
import requests  # noqa: E402
from src.config import PORT  # noqa: E402

# ---------------------------------------------------
# Basic config
# ---------------------------------------------------
BASE_URL = f"http://localhost:{PORT}"
BACKEND_MAIN = BASE_DIR / "src" / "main.py"


# ---------------------------------------------------
# Helpers
# ---------------------------------------------------
def get_external_ip() -> str:
    """
    Try to determine a non-loopback IPv4 address of this machine,
    which can be used from other hosts to reach the ERI server.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def ensure_backend_running() -> str:
    """
    Check if the ERI backend is reachable on /health.
    If not, start it in a separate process via `python src/main.py`.
    """
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=1.0)
        if resp.ok:
            return "Backend is already running."
    except requests.RequestException:
        pass

    # Backend seems down → start it
    try:
        subprocess.Popen(
            [sys.executable, str(BACKEND_MAIN)],
            cwd=str(BACKEND_MAIN.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Give the server a brief moment to come up
        time.sleep(2)
        return "Backend was not running and has been started."
    except Exception as exc:
        return f"Failed to start backend: {exc}"


# ---------------------------------------------------
# Backend calls used by the UI
# ---------------------------------------------------
def create_user(username: str, password: str) -> str:
    """
    Call /admin/user to create or update a username/password pair
    for USERNAME_PASSWORD authentication.
    """
    if not username or not password:
        return "<span class='msg-warn'>Please enter username and password.</span>"

    resp = requests.post(
        f"{BASE_URL}/admin/user",
        json={"username": username, "password": password},
    )

    if resp.ok:
        data = resp.json()
        return (
            "<span class='msg-ok'>User "
            f"'<strong>{data['username']}</strong>' created/updated.<br>"
            "You can now use this account for ERI authentication.</span>"
        )

    return (
        "<span class='msg-error'>Error creating user:"
        f" {resp.status_code} {resp.text}</span>"
    )


def upload_pdf(file) -> str:
    """
    Upload a PDF file to /admin/upload and index it into the vector DB.

    The backend:
    - saves it under src/Papers/
    - runs VectorStoreManager.add_pdf(...)
    - persists it into the Chroma vector DB
    """
    if file is None:
        return "<span class='msg-warn'>Please select a PDF file.</span>"

    clean_filename = Path(file.name).name

    with open(file.name, "rb") as f:
        files = {"file": (clean_filename, f, "application/pdf")}
        resp = requests.post(f"{BASE_URL}/admin/upload", files=files)

    if resp.ok:
        data = resp.json()
        display_name = data.get("filename", file.name)
        return (
            "<span class='msg-ok'>"
            f"File '<strong>{display_name}</strong>' has been uploaded and indexed.<br>"
            "Ready for external retrieval.</span>"
        )

    return (
        "<span class='msg-error'>Error uploading/indexing PDF:"
        f" {resp.status_code} {resp.text}</span>"
    )


def clear_vector_db() -> str:
    """
    Call /admin/clear to wipe the Chroma vector DB.
    PDFs in the Papers directory are not removed, only the vector index.
    """
    resp = requests.post(f"{BASE_URL}/admin/clear")
    if resp.ok:
        return (
            "<span class='msg-ok'>Vector DB has been cleared. "
            "You can now upload and re-index new documents.</span>"
        )
    return (
        "<span class='msg-error'>Error clearing DB:"
        f" {resp.status_code} {resp.text}</span>"
    )


def get_server_info_markdown() -> str:
    """
    Render a clear hint how to configure this ERI server in OpenWebUI.
    """
    ip = get_external_ip()
    port = PORT
    host_url = f"http://{ip}"

    return (
        "#### Configuration for this external knowledge server in OpenWebUI\n\n"
        f"- **Server host name:** `{host_url}`\n"
        f"- **Port:** `{port}`\n"
        "- **Authentication:** `USERNAME_PASSWORD`\n\n"
        "For your username/password, use one of the users you created above in the UI."
    )


# ---------------------------------------------------
# Gradio UI
# ---------------------------------------------------
CUSTOM_CSS = """
<style>
/* Layout & background */
body, #root {
    padding: 0 !important;
    margin: 0 !important;
}
.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
}

/* Header bar */
.eri-header-row {
    background: #005b8f;
    color: white;
    padding: 18px 24px;
    border-radius: 16px;
    margin-bottom: 24px;
}
.eri-title {
    font-size: 28px;
    font-weight: 600;
    color: #ffffff !important;
    margin-bottom: 4px;
}
.eri-subtitle {
    font-size: 14px;
    color: #ffffff !important;
}

/* Cards */
.eri-card {
    background: #f9fafb;
    border-radius: 16px;
    padding: 18px 18px 20px 18px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    border: 1px solid #e5e7eb;
    margin-bottom: 18px;
}

/* Buttons */
.eri-primary-btn,
.eri-primary-btn button {
    background: #005b8f !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 9999px !important;
    padding: 8px 16px !important;
    border: none !important;
    box-shadow: 0 4px 10px rgba(0,91,143,0.35) !important;
}
.eri-primary-btn button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(0,91,143,0.45) !important;
}
.eri-danger-btn,
.eri-danger-btn button {
    background: #b91c1c !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 9999px !important;
    padding: 8px 16px !important;
    border: none !important;
}

/* Backend status pill */
.eri-status-pill {
    margin-top: 8px;
    margin-bottom: 20px;
    padding: 8px 12px;
    border-radius: 9999px;
    background: #e0f2fe;
    color: #0369a1;
    font-size: 14px;
    display: inline-block;
}

/* Messages */
.msg-ok   { color: #16a34a; }
.msg-warn { color: #b45309; }
.msg-error{ color: #dc2626; }

/* Hide Gradio footer */
footer {
    display: none !important;
}
[data-testid="footer"] {
    display: none !important;
}
</style>
"""


def main():
    with gr.Blocks(title="ERI RAG Test UI") as demo:
        # Custom CSS
        gr.HTML(CUSTOM_CSS)

        # Header
        with gr.Row(elem_classes="eri-header-row"):
            with gr.Column(scale=8):
                gr.HTML(
                    """
                    <div class="eri-title">
                        ERI Demo Helper – Vector DB Setup
                    </div>
                    <div class="eri-subtitle">
                        Small helper UI to create users and upload documents
                        for an ERI-based demo server.
                    </div>
                    """
                )

        # Backend status
        backend_status = ensure_backend_running()
        gr.HTML(
            f"<div class='eri-status-pill'><strong>Backend status:</strong> "
            f"{backend_status}</div>"
        )

        with gr.Row():
            # Left column: actions
            with gr.Column(scale=3):
                # User card
                with gr.Group(elem_classes="eri-card"):
                    gr.Markdown("### 👤 User management")
                    gr.Markdown(
                        "Create or update a username/password pair that can be used "
                        "from OpenWebUI with `USERNAME_PASSWORD` authentication."
                    )
                    username = gr.Textbox(label="Username", value="user1")
                    password = gr.Textbox(
                        label="Password",
                        type="password",
                        value="secret123",
                    )
                    create_user_btn = gr.Button(
                        "Save user", elem_classes="eri-primary-btn"
                    )
                    create_user_out = gr.HTML("")

                # Document card
                with gr.Group(elem_classes="eri-card"):
                    gr.Markdown("### 📄 Document upload")
                    gr.Markdown(
                        "Upload a PDF that will be stored under `src/Papers/` and "
                        "indexed into the Chroma vector database."
                    )
                    pdf_file = gr.File(
                        label="PDF to index",
                        file_types=[".pdf"],
                        type="filepath",
                    )
                    upload_btn = gr.Button(
                        "Upload & index", elem_classes="eri-primary-btn"
                    )
                    upload_out = gr.HTML("")

                # Clear DB card
                with gr.Group(elem_classes="eri-card"):
                    gr.Markdown("### 🧹 Vector DB maintenance")
                    gr.Markdown(
                        "Clear all entries from the vector index. The PDF files on disk are not deleted."
                    )
                    clear_btn = gr.Button(
                        "Clear vector DB", elem_classes="eri-primary-btn"
                    )
                    clear_out = gr.HTML("")

            # Right column: server info
            with gr.Column(scale=2):
                with gr.Group(elem_classes="eri-card"):
                    gr.Markdown("### 🔗 Connect from OpenWebUI")
                    gr.Markdown(get_server_info_markdown())

        # Wire buttons
        create_user_btn.click(
            fn=create_user,
            inputs=[username, password],
            outputs=[create_user_out],
        )

        upload_btn.click(
            fn=upload_pdf,
            inputs=[pdf_file],
            outputs=[upload_out],
        )

        clear_btn.click(
            fn=clear_vector_db,
            inputs=None,
            outputs=[clear_out],
        )

    return demo


if __name__ == "__main__":
    demo = main()
    demo.launch(
        server_name="localhost",
        server_port=7860,
        show_api=False,
    )
