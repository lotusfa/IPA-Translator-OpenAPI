
# 🕒 IPA‑Translator‑OpenAPI  

**A RESTful API for converting words, phrases, or sentences into their precise International Phonetic Alphabet (IPA) representation.**  

---  

## 📖 Overview  

This repository implements a FastAPI server that exposes endpoints for translating text into IPA for multiple languages.  

---  

## 🚀 Quickstart (Local Python)

```bash
git clone https://github.com/lotusfa/IPA-Translator-OpenAPI.git
cd openapi-servers/servers/ipa-translator
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --reload
```
---  

## 🚀 Quickstart (Docker)

If you prefer containerised deployment, you can build and run the service with Docker Compose from the project root:

```bash
# Build the Docker images
docker compose build

# Start the containers in detached mode
docker compose up -d
```

The API will be reachable at `http://localhost:8000` (or the port you expose in `docker-compose.yml`).  

---  

## 🔗 Open WebUI Integration

If you want to let AI use the IPA translator. you can point the server to open webui. See the official tutorial : https://docs.openwebui.com/openapi-servers/open-webui


openapi.example.json also attached for your reference :)
http://localhost:8000/openapi.json

(Tips: You can toggle 'Function Calling' to 'native' in Chat Controls. )

---  

## 🔗 IPA Translator in Open WebUI

Please take a look to the demo folder:

demo/demo_en.jpg
demo/demo_yue.jpg

---  

## 🔗 Related Projects  

- **IPA‑Translator (JS/HTML only)** – A client‑side web tool that performs the same IPA conversion directly in the browser. See the repository for the original UI implementation: https://github.com/lotusfa/IPA-Translator  

- **Data Source** – The IPA dictionaries used by the API are derived from the open‑source linguistic data hosted at: https://open-dict-data.github.io/  

---  

## 🙏 Acknowledgements  

- The FastAPI framework for making rapid API development straightforward.  
- The open‑dict‑data project for providing high‑quality lexical resources.  

---  