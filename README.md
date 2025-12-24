# 🛡️ SafeNet - AI-Powered Network Interception System

**SafeNet** is an advanced network security solution designed to filter internet traffic in real-time using Artificial Intelligence.
Unlike traditional firewalls that rely solely on static blacklists, SafeNet acts as an **Interception Proxy**, inspecting the actual content of web pages and classifying them using a Machine Learning model to block inappropriate or malicious content dynamically.

---

## ⚡ Key Capabilities

### 🧠 AI-Driven Content Analysis
* **Context Awareness:** Instead of just blocking URL strings, the system analyzes the textual content of the webpage.
* **Machine Learning Model:** Utilizes a Python-based NLP (Natural Language Processing) engine to calculate the probability of unsafe content in real-time.
* **Zero-Day Protection:** Capable of blocking new, unknown malicious sites that haven't been blacklisted yet, based on their content patterns.

### 🕵️‍♂️ Interception Proxy Architecture
* **Man-in-the-Middle (MitM):** The system sits between the user and the internet, capturing HTTP/HTTPS packets.
* **Traffic Inspection:** Decodes and analyzes headers and body content before delivering it to the browser.
* **Transparent Filtering:** Blocks are applied seamlessly without requiring complex client-side configuration.

### 💻 Full-Stack Dashboard
* **Modern UI:** A responsive **React** application to visualize network activity.
* **Live Monitoring:** Watch traffic logs, blocked attempts, and system performance in real-time.
* **Admin Control:** Manage whitelists/blacklists and adjust AI sensitivity thresholds.

---

## 🛠️ Tech Stack & Architecture

This project demonstrates a complex **Client-Server** architecture:

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Core Engine** | **Python** | Raw socket handling, Proxy logic, Multi-threading. |
| **Analysis** | **AI / ML** | Text classification algorithm (Scikit-learn / Custom logic). |
| **Frontend** | **React.js** | Admin dashboard, State management, API communication. |
| **Communication**| **REST / Sockets** | Data flow between the interception engine and the UI. |

---

## 🚀 How It Works (Under the Hood)

1.  **The Interception:** The Python server starts a socket listener on a specific port.
2.  **The Handshake:** When the user browses the web, the request is routed through SafeNet.
3.  **The Analysis:**
    * The proxy fetches the requested page.
    * The content is passed to the **AI Module**.
    * The model scores the content (e.g., `Safe: 98%`, `Unsafe: 2%`).
4.  ** The Verdict:**
    * If **Safe**: The page is sent back to the client.
    * If **Unsafe**: The connection is dropped, and a "Blocked" page is returned.

---

## 📥 Installation & Run

### Prerequisites
* Python 3.8+
* Node.js & npm

### 1. Start the Server (The Brain)
```bash
cd Server
pip install -r requirements.txt
python app.py
