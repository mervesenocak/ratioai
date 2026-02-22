import io
import json
import textwrap
import requests
import streamlit as st

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from pypdf import PdfReader


# ---------------------------
# Helpers
# ---------------------------

def extract_text_from_pdf(uploaded_file) -> str:
    """PDF -> text (best effort)."""
    reader = PdfReader(uploaded_file)
    parts = []
    for page in reader.pages:
        t = page.extract_text() or ""
        t = t.strip()
        if t:
            parts.append(t)
    return "\n\n".join(parts).strip()


def make_pdf_bytes(title: str, content: str) -> bytes:
    """Text -> PDF bytes (A4). Uses DejaVuSans if available for Turkish chars."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Try register a font that supports Turkish characters
    # If it fails, fallback to Helvetica (some chars may break)
    font_name = "Helvetica"
    try:
        # Common Windows path; you can adjust if needed
        # You can also place DejaVuSans.ttf inside project and reference relative path
        import os
        candidates = [
            r"C:\Windows\Fonts\DejaVuSans.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
        ]
        for p in candidates:
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont("CustomTR", p))
                font_name = "CustomTR"
                break
    except Exception:
        pass

    margin = 40
    y = height - margin

    c.setFont(font_name, 14)
    c.drawString(margin, y, title)
    y -= 22

    c.setFont(font_name, 10)

    # Wrap lines to fit page width (rough)
    max_chars = 110
    lines = []
    for para in (content or "").splitlines():
        if not para.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=max_chars, break_long_words=False, replace_whitespace=False))

    line_height = 14
    for line in lines:
        if y <= margin:
            c.showPage()
            c.setFont(font_name, 10)
            y = height - margin
        c.drawString(margin, y, line)
        y -= line_height

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def build_payload(dava_turu: str, kisa_karar: str, deliller: list, ceza_puanlari: dict | None):
    payload = {
        "dava_turu": dava_turu,
        "kisa_karar": kisa_karar,
        "deliller": deliller or [],
    }
    if dava_turu == "CEZA":
        payload["ceza_puanlari"] = ceza_puanlari
    return payload


# ---------------------------
# UI
# ---------------------------

st.set_page_config(page_title="RatioAI — Hakim Simülasyonu (Demo)", layout="wide")

st.title("⚖️ RatioAI — Hakim Simülasyonu (Demo)")
st.caption("Kısa karar + deliller → Gerekçeli karar (FastAPI üzerinden).")

with st.sidebar:
    st.header("Ayarlar")

    dava_turu = st.selectbox("Dava Türü", ["OZEL_HUKUK", "CEZA"], index=0)
    endpoint = st.text_input("API Endpoint", value="http://127.0.0.1:8000/generate")

    st.divider()

    st.subheader("Kısa Karar PDF Yükle")
    pdf_file = st.file_uploader("PDF seç", type=["pdf"], accept_multiple_files=False)
    pdf_text = ""
    if pdf_file is not None:
        try:
            pdf_text = extract_text_from_pdf(pdf_file)
            if not pdf_text:
                st.warning("PDF’den metin çıkarılamadı. (PDF tarama olabilir) Metni elle yapıştırman gerekebilir.")
            else:
                st.success("PDF metni çıkarıldı. İstersen aşağıdaki alana otomatik dolacak.")
        except Exception as e:
            st.error(f"PDF okunamadı: {e}")

    st.divider()

    ceza_puanlari = None
    if dava_turu == "CEZA":
        st.subheader("Ceza Puanları (0–10)")
        kast_taksir = st.slider("Kast/Taksir", 0.0, 10.0, 6.0, 0.5)
        gecmis = st.slider("Sanığın geçmişi", 0.0, 10.0, 5.0, 0.5)
        islenis_sekli = st.slider("Suçun işleniş şekli", 0.0, 10.0, 6.0, 0.5)
        magdur_etki = st.slider("Mağdur üzerindeki etki", 0.0, 10.0, 6.0, 0.5)
        toplumsal_zarar = st.slider("Toplumsal zarar", 0.0, 10.0, 5.0, 0.5)

        ceza_puanlari = {
            "kast_taksir": kast_taksir,
            "gecmis": gecmis,
            "islenis_sekli": islenis_sekli,
            "magdur_etki": magdur_etki,
            "toplumsal_zarar": toplumsal_zarar,
        }

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.header("Kısa Karar")
    kisa_karar = st.text_area(
        "Kısa Karar Metni",
        value=pdf_text if pdf_text else "",
        height=220,
        placeholder="Kısa kararı buraya yaz veya PDF yükle.",
    )

    st.subheader("Deliller")
    if "delil_count" not in st.session_state:
        st.session_state.delil_count = 2

    for i in range(st.session_state.delil_count):
        with st.expander(f"Delil {i+1}", expanded=(i == 0)):
            name = st.text_input(f"Ad (Delil {i+1})", key=f"delil_name_{i}", value=f"Delil {i+1}")
            content = st.text_area(f"İçerik (Delil {i+1})", key=f"delil_content_{i}", height=90)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Delil Ekle"):
            st.session_state.delil_count += 1
            st.rerun()
    with c2:
        if st.button("➖ Delil Sil", disabled=(st.session_state.delil_count <= 1)):
            st.session_state.delil_count -= 1
            st.rerun()

with col2:
    st.header("Gerekçeli Karar")
    generate_btn = st.button("🚀 Gerekçeli Karar Üret", type="primary")

    if generate_btn:
        if not kisa_karar.strip():
            st.error("Kısa karar boş olamaz.")
        else:
            deliller = []
            for i in range(st.session_state.delil_count):
                name = st.session_state.get(f"delil_name_{i}", f"Delil {i+1}").strip()
                content = st.session_state.get(f"delil_content_{i}", "").strip()
                if content:
                    deliller.append({"name": name, "content": content})

            payload = build_payload(dava_turu, kisa_karar.strip(), deliller, ceza_puanlari)

            try:
                r = requests.post(endpoint, json=payload, timeout=180)
                if r.status_code != 200:
                    st.error(f"Hata: {r.status_code}")
                    try:
                        st.code(r.json(), language="json")
                    except Exception:
                        st.code(r.text)
                else:
                    data = r.json()
                    st.session_state.generated = data.get("gerekceli_karar", "")
                    st.session_state.generated_meta = data
                    st.success("Karar üretildi ✅")
            except requests.exceptions.RequestException as e:
                st.error(f"API bağlantı hatası: {e}")

    karar = st.session_state.get("generated", "")
    if karar:
        st.text_area("Çıktı", value=karar, height=520)

        # PDF indir
        pdf_bytes = make_pdf_bytes("Gerekçeli Karar (RatioAI Demo)", karar)
        st.download_button(
            "📄 Gerekçeli Kararı PDF İndir",
            data=pdf_bytes,
            file_name="gerekceli_karar_ratioai.pdf",
            mime="application/pdf",
        )

        with st.expander("Kullanılan kaynaklar / uyarılar (debug)"):
            meta = st.session_state.get("generated_meta", {})
            st.code(meta.get("warnings", []), language="json")
            st.write("Kanunlar:", len(meta.get("used_laws", []) or []))
            st.write("İçtihatlar:", len(meta.get("used_precedents", []) or []))
            if meta.get("criminal_scoring"):
                st.code(meta["criminal_scoring"], language="json")