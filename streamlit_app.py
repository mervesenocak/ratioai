import streamlit as st
import requests

st.set_page_config(page_title="RatioAI Hakim Simülasyonu", layout="wide")
st.title("⚖️ RatioAI — Hâkim Simülasyonu (Ollama + RAG)")

api_url = st.sidebar.text_input("API URL", "http://127.0.0.1:8000")

dava_turu = st.selectbox("Davanın Türü", ["OZEL_HUKUK", "CEZA"])
kisa_karar = st.text_area("Kısa Karar", height=220, placeholder="Kısa karar metnini buraya yapıştır...")

ceza_puanlari = None
if dava_turu == "CEZA":
    st.subheader("Ceza Takdir Puanları (0–10)")
    c1, c2, c3, c4, c5 = st.columns(5)
    kast_taksir = c1.number_input("Kast/Taksir", 0, 10, 5)
    gecmis = c2.number_input("Geçmiş", 0, 10, 5)
    islenis = c3.number_input("İşleniş", 0, 10, 5)
    magdur = c4.number_input("Mağdur Etki", 0, 10, 5)
    toplum = c5.number_input("Toplumsal Zarar", 0, 10, 5)
    ceza_puanlari = {
        "kast_taksir": int(kast_taksir),
        "gecmis": int(gecmis),
        "islenis_sekli": int(islenis),
        "magdur_etki": int(magdur),
        "toplumsal_zarar": int(toplum),
    }

st.subheader("Deliller (opsiyonel)")
delil_sayisi = st.number_input("Delil sayısı", min_value=0, max_value=20, value=0, step=1)

deliller = []
for i in range(int(delil_sayisi)):
    c1, c2 = st.columns([1, 3])
    name = c1.text_input(f"Delil {i+1} adı", key=f"name_{i}")
    content = c2.text_input(f"Delil {i+1} içeriği", key=f"content_{i}")
    if name and content:
        deliller.append({"name": name, "content": content})

if st.button("Gerekçeli Kararı Üret"):
    payload = {
        "kisa_karar": kisa_karar,
        "dava_turu": dava_turu,
        "deliller": deliller or None,
        "ceza_puanlari": ceza_puanlari,
    }
    r = requests.post(f"{api_url}/generate", json=payload, timeout=180)
    if r.status_code != 200:
        st.error(f"Hata: {r.status_code}\n{r.text}")
    else:
        data = r.json()

        st.subheader("📄 Gerekçeli Karar")
        st.text_area("Çıktı", data["gerekceli_karar"], height=420)

        st.subheader("🔎 Kullanılan Kaynaklar")
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**Kanun Maddeleri**")
            for d in data["used_laws"]:
                demo = " (DEMO)" if d["meta"].get("demo") else ""
                st.markdown(f"- **{d['id']}**{demo}: {d['title']}")
        with colB:
            st.markdown("**İçtihatlar**")
            for d in data["used_precedents"]:
                demo = " (DEMO)" if d["meta"].get("demo") else ""
                st.markdown(f"- **{d['id']}**{demo}: {d['title']}")

        if data.get("warnings"):
            st.warning("Uyarılar:\n- " + "\n- ".join(data["warnings"]))