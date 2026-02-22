from pathlib import Path
import os
import json
import urllib.request
import urllib.error
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from app.schemas import GenerateRequest, GenerateResponse, RetrievedDoc
from app.core.retrieval import Retriever, load_jsonl
from app.core.prompting import build_prompt, format_gerekceli_karar
from app.core.scoring import score_criminal
from app.core.validators import validate_has_sections, warn_demo_sources

load_dotenv()

app = FastAPI(title="RatioAI Hakim Simülasyonu API", version="0.2.0")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LAW_PATH = DATA_DIR / "laws" / "laws.jsonl"
PREC_PATH = DATA_DIR / "precedents" / "precedents.jsonl"

# Render / prod ortamında dosyalar yoksa uygulama açılır ama generate çalışmaz.
# Bu yüzden güvenli şekilde yükleyelim.
law_docs = []
prec_docs = []

try:
    if LAW_PATH.exists():
        law_docs = load_jsonl(LAW_PATH, kind="law")
    else:
        print(f"[WARN] LAW_PATH not found: {LAW_PATH}")

    if PREC_PATH.exists():
        prec_docs = load_jsonl(PREC_PATH, kind="precedent")
    else:
        print(f"[WARN] PREC_PATH not found: {PREC_PATH}")
except Exception as e:
    print(f"[WARN] Failed loading data files: {e}")

retriever = Retriever(law_docs, prec_docs)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

# ✅ Mock modu (Render'da LLM yoksa bile /generate çalışsın)
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "0") == "1"


def llm_generate(prompt: str) -> str:
    """
    Ollama /api/generate çağrısı.
    Render'da localhost ollama yoksa bu çağrı başarısız olur.
    """
    url = f"{OLLAMA_URL.rstrip('/')}/api/generate"
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
            body = resp.read().decode("utf-8", errors="ignore")
            obj = json.loads(body)
            return (obj.get("response") or "").strip()

    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Ollama HTTPError: {e.code} {e.reason} | {detail}")

    except urllib.error.URLError as e:
        # Ollama'ya erişememe (en sık Render'da olur)
        raise RuntimeError(
            f"Ollama URL error: {e}. OLLAMA_URL={OLLAMA_URL}. "
            "Render'da local ollama çalışmaz; dış erişilebilir bir Ollama endpoint'i vermelisin."
        )

    except Exception as e:
        raise RuntimeError(f"Ollama request failed: {e}")


def to_schema_docs(docs) -> List[RetrievedDoc]:
    return [RetrievedDoc(id=d.id, title=d.title, text=d.text, meta=d.meta) for d in docs]


def mock_generate_decision(
    req: GenerateRequest,
    laws,
    precedents,
    criminal_scoring,
) -> str:
    """
    LLM yokken demo için stabil "gerekçeli karar" üretir.
    Retrieval sonuçlarını (ilk 5) ve ceza skorunu (varsa) raporlar.
    """
    law_titles = "\n".join([f"- {d.title}" for d in (laws or [])[:5]]) or "- (bulunamadı)"
    prec_titles = "\n".join([f"- {d.title}" for d in (precedents or [])[:5]]) or "- (bulunamadı)"

    score_text = ""
    if req.dava_turu == "CEZA" and criminal_scoring is not None:
        score_text = f"\n\nCEZA PUANLAMASI (DEMO):\n{criminal_scoring}"

    evid_text = "\n".join([f"- {e.name}: {e.content}" for e in (req.deliller or [])]) or "- (sunulmadı)"

    text = f"""
MAHKEMESİ: RatioAI Sanal Mahkeme (DEMO)
DOSYA TÜRÜ: {req.dava_turu}

OLAY / TALEP:
{req.kisa_karar}

DELİLLER:
{evid_text}

HUKUKİ DEĞERLENDİRME:
Bu karar demo (mock) modunda oluşturulmuştur. Sistem, olay anlatımı ve delillere göre
ilgili mevzuat ve emsal dokümanları eşleştirir ve gerekçeli karar taslağı üretir.

KULLANILAN MEVZUAT (İlk 5):
{law_titles}

KULLANILAN EMSALLER (İlk 5):
{prec_titles}
{score_text}

HÜKÜM (DEMO):
Tarafların beyanları ve dosya kapsamı birlikte değerlendirilmiş olup, bu metin yalnızca
sistemin işleyişini göstermek amacıyla üretilmiştir; nihai yargısal karar yerine geçmez.
"""
    return format_gerekceli_karar(text.strip(), req.dava_turu)


@app.get("/", response_class=HTMLResponse)
def home():
    mock_badge = "AÇIK ✅" if USE_MOCK_LLM else "KAPALI ❌"
    return f"""
    <h2>RatioAI Hakim Simülasyonu API ✅</h2>
    <ul>
      <li><a href="/docs">/docs</a> (Swagger UI)</li>
      <li><a href="/healthz">/healthz</a> (health check)</li>
    </ul>
    <p><b>Mock mode:</b> {mock_badge}</p>
    <p>Not: /generate endpoint'i için LLM (Ollama) erişimi gerekir. LLM yoksa mock moda düşebilir.</p>
    """


@app.get("/healthz")
def healthz():
    return {"ok": True, "version": "0.2.0", "mock_mode": USE_MOCK_LLM}


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    # Veri dosyaları yüklenmemişse anlamlı hata
    if not law_docs or not prec_docs:
        raise HTTPException(
            status_code=500,
            detail=(
                "Data files are not loaded. Ensure data/laws/laws.jsonl and "
                "data/precedents/precedents.jsonl exist in the deployed environment."
            ),
        )

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

    # ✅ Mock mode açık ise direkt demo üret
    if USE_MOCK_LLM:
        karar = mock_generate_decision(req, laws, precedents, criminal_scoring)
    else:
        # ✅ Mock mode kapalı ama LLM çökerse otomatik demo moda düş
        try:
            karar = llm_generate(prompt)
            karar = format_gerekceli_karar(karar, req.dava_turu)
        except RuntimeError:
            karar = mock_generate_decision(req, laws, precedents, criminal_scoring)

    warnings: List[str] = []
    warnings += validate_has_sections(karar)
    warnings += warn_demo_sources(laws, precedents)

    return GenerateResponse(
        gerekceli_karar=karar,
        used_laws=to_schema_docs(laws),
        used_precedents=to_schema_docs(precedents),
        criminal_scoring=criminal_scoring,
        warnings=warnings,
    )