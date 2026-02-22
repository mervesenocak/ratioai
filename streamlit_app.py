import json
import requests
import streamlit as st

st.set_page_config(page_title="RatioAI Demo", page_icon="⚖️", layout="wide")

st.title("⚖️ RatioAI — Hakim Simülasyonu (Demo)")
st.caption("Kısa karar + deliller → Gerekçeli karar")

API_BASE = "http://127.0.0.1:8000"
endpoint = f"{API_BASE}/generate"

st.sidebar.header("Ayarlar")
dava_turu = st.sidebar.selectbox("Dava Türü", ["OZEL_HUKUK", "CEZA"])

st.markdown("## Kısa Karar")
kisa_karar = st.text_area(
    "Kısa Karar Metni",
    height=200,
    placeholder="Davacı, davalının kira bedelini ödemediğini ileri sürerek tahliye talep etmiştir..."
)

st.markdown("## Deliller")

if "deliller" not in st.session_state:
    st.session_state.deliller = [
        {"name": "Kira Sözleşmesi", "content": "Taraflar arasında 01.01.2022 tarihli kira sözleşmesi"},
        {"name": "Banka Kaydı", "content": "Ödenmeyen aylara ilişkin banka hesap dökümü"},
    ]

for i, d in enumerate(st.session_state.deliller):
    with st.expander(f"Delil {i+1}"):
        d["name"] = st.text_input("Delil Adı", d["name"], key=f"name_{i}")
        d["content"] = st.text_area("Delil İçeriği", d["content"], key=f"content_{i}")

if st.button("➕ Delil Ekle"):
    st.session_state.deliller.append({"name": "", "content": ""})
    st.experimental_rerun()

st.markdown("---")

if st.button("🚀 Gerekçeli Karar Üret"):
    if not kisa_karar.strip():
        st.error("Kısa karar boş olamaz.")
    else:
        payload = {
            "dava_turu": dava_turu,
            "kisa_karar": kisa_karar,
            "deliller": [
                {"name": d["name"], "content": d["content"]}
                for d in st.session_state.deliller
                if d["name"] and d["content"]
            ]
        }

        with st.spinner("Karar üretiliyor..."):
            r = requests.post(endpoint, json=payload)

        if r.status_code != 200:
            st.error(f"Hata: {r.status_code}")
            st.code(r.text)
        else:
            data = r.json()
            st.success("Karar üretildi")

            st.markdown("## Gerekçeli Karar")
            st.text_area("", data.get("gerekceli_karar", ""), height=400)

            st.markdown("### Kullanılan Kanunlar")
            for k in data.get("used_laws", []):
                st.write(f"- {k.get('title','')}")

            st.markdown("### Kullanılan İçtihatlar")
            for i in data.get("used_precedents", []):
                st.write(f"- {i.get('title','')}")

            if data.get("warnings"):
                st.markdown("### Uyarılar")
                for w in data["warnings"]:
                    st.warning(w)