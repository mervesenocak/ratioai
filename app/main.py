from pathlib import Path
import os
import json
import urllib.request
import urllib.error

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from app.schemas import GenerateRequest, GenerateResponse, RetrievedDoc
from app.core.retrieval import Retriever, load_jsonl
from app.core.prompting import build_prompt
from app.core.scoring import score_criminal
from app.core.validators import validate_has_sections, warn_demo_sources

load_dotenv()

app = FastAPI(title="RatioAI Hakim Simülasyonu API", version="0.2.0")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LAW_PATH = DATA_DIR / "laws" / "laws.jsonl"
PREC_PATH = DATA_DIR / "precedents" / "precedents.jsonl"

law_docs = load_jsonl(LAW_PATH, kind="law")
prec_docs = load_jsonl(PREC_PATH, kind="precedent")
retriever = Retriever(law_docs, prec_docs)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")


def llm_generate(prompt: str) -> str:
    url = f"{OLLAMA_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_ctx": 8192,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read().decode("utf-8")
            obj = json.loads(body)
            return obj.get("response", "").strip()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Ollama HTTPError: {e.code} {e.reason} | {detail}")
    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}")


def to_schema_docs(docs):
    return [RetrievedDoc(id=d.id, title=d.title, text=d.text, meta=d.meta) for d in docs]


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    ev_text = ""
    if req.deliller:
        ev_text = "\n".join([f"{e.name}: {e.content}" for e in req.deliller])

    query = f"{req.kisa_karar}\n{ev_text}".strip()
    laws, precedents = retriever.search(query, topk_laws=10, topk_precedents=10)

    criminal_scoring = None
    if req.dava_turu == "CEZA":
        if req.ceza_puanlari is None:
            raise HTTPException(
                status_code=400,
                detail="CEZA davalarında ceza_puanlari zorunlu (0-10 arası).",
            )
        criminal_scoring = score_criminal(
            kast_taksir=req.ceza_puanlari.kast_taksir,
            gecmis=req.ceza_puanlari.gecmis,
            islenis_sekli=req.ceza_puanlari.islenis_sekli,
            magdur_etki=req.ceza_puanlari.magdur_etki,
            toplumsal_zarar=req.ceza_puanlari.toplumsal_zarar,
        )

    prompt = build_prompt(
        kisa_karar=req.kisa_karar,
        dava_turu=req.dava_turu,
        evidences=[e.model_dump() for e in (req.deliller or [])] or None,
        laws=laws,
        precedents=precedents,
        criminal_scoring=criminal_scoring,
    )

    karar = llm_generate(prompt)

    warnings = []
    warnings += validate_has_sections(karar)
    warnings += warn_demo_sources(laws, precedents)

    return GenerateResponse(
        gerekceli_karar=karar,
        used_laws=to_schema_docs(laws),
        used_precedents=to_schema_docs(precedents),
        criminal_scoring=criminal_scoring,
        warnings=warnings,
    )