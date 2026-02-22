from typing import List, Optional, Dict, Any
from .retrieval import Doc


def format_laws(laws: List[Doc]) -> str:
    if not laws:
        return "KANUN BULUNAMADI (dataset boş veya eşleşme yok)."
    out = []
    for d in laws:
        demo = " [DEMO]" if d.meta.get("demo") else ""
        out.append(f"- [{d.id}]{demo} {d.title}: {d.text}")
    return "\n".join(out)


def format_precedents(precs: List[Doc]) -> str:
    if not precs:
        return "YARGITAY İÇTİHADI BULUNAMADI (dataset boş veya eşleşme yok)."
    out = []
    for d in precs:
        m = d.meta or {}
        demo = " [DEMO]" if m.get("demo") else ""
        out.append(
            f"- [{d.id}]{demo} {m.get('chamber','Yargıtay')} "
            f"({m.get('date','Tarih yok')}) {m.get('ek','E. yok')} {m.get('kk','K. yok')}\n"
            f"  Metin/Özet: {d.text}"
        )
    return "\n".join(out)


def format_evidence(evidences: Optional[List[dict]]) -> str:
    if not evidences:
        return "DELİL SUNULMADI."
    out = []
    for i, ev in enumerate(evidences, 1):
        out.append(f"{i}) {ev['name']}: {ev['content']}")
    return "\n".join(out)


def build_prompt(
    *,
    kisa_karar: str,
    dava_turu: str,
    evidences: Optional[List[dict]],
    laws: List[Doc],
    precedents: List[Doc],
    criminal_scoring: Optional[Dict[str, Any]] = None,
) -> str:
    scoring_block = ""
    if dava_turu == "CEZA" and criminal_scoring:
        s = criminal_scoring["scores"]
        scoring_block = f"""
CEZA TAKDİR PUANLARI (0–10):
- Kast/Taksir: {s['kast_taksir']}
- Sanığın geçmişi: {s['gecmis']}
- Suçun işleniş şekli: {s['islenis_sekli']}
- Mağdur üzerindeki etki: {s['magdur_etki']}
- Toplumsal zarar: {s['toplumsal_zarar']}
TOPLAM: {criminal_scoring['total']}  |  Bant: {criminal_scoring['band']}
Takdir açıklaması: {criminal_scoring['takdir_aciklama']}
"""

    format_block = f"""
ÇIKTI FORMAT ZORUNLULUĞU (UYGULANACAK):
- Çıktı tek parça metin olmalı, aşağıdaki başlıkları AYNI sırayla içermelidir.
- Her başlık ROMEN rakamıyla başlamalıdır (I, II, III...).
- Başlıklar BÜYÜK HARF olmalıdır.
- Her başlık altında kısa ama somut değerlendirme olmalı; varsayım yapılmamalı.
- Kanun maddeleri madde madde yazılmalı.
- Yargıtay içtihatları varsa “Daire / Tarih / Esas-Karar” formatında listelenmeli; yoksa
  “Dosyada emsal içtihat bulunmadığından yer verilmemiştir.” denmelidir.
- Son bölüm mutlaka “VII. SONUÇ VE HÜKÜM” olmalı ve 1), 2), 3) şeklinde numaralı olmalıdır.

KULLANILACAK ŞABLON:
T.C.
RATIOAI HUKUKİ KARAR DESTEK SİSTEMİ
(Akademik Prototip)

DOSYA TÜRÜ: {dava_turu}
--------------------------------------------------

I. TARAF BEYANLARI
- Davacı: ...
- Davalı: ...

II. UYUŞMAZLIĞIN HUKUKİ NİTELİĞİ
...

III. DELİLLERİN DEĞERLENDİRİLMESİ
1. ...
2. ...

IV. UYGULANAN HUKUK KURALLARI
- ...
- ...

V. YARGITAY İÇTİHATLARI
- ...
(veya: Dosyada emsal içtihat bulunmadığından yer verilmemiştir.)

VI. HUKUKİ DEĞERLENDİRME
...

VII. SONUÇ VE HÜKÜM
1) ...
2) ...
3) ...
"""

    return f"""
ROL:
Sen Türk Hukuku alanında uzman, Yargıtay içtihatlarını esas alan ileri seviye bir HÂKİM SİMÜLASYONUSUN.
Görevin: Kullanıcının verdiği KISA KARAR metnini; kanun maddeleri, Yargıtay yerleşik içtihatları,
deliller ve hukuki değerlendirme ilkeleri çerçevesinde usule/esasa uygun TAM GEREKÇELİ KARARA dönüştürmek.

KATI KURALLAR:
1) Dava türü: {dava_turu}
- ÖZEL HUKUK ise: Yargıtay içtihatlarına aykırı hüküm kuramazsın. Aykırı görüş varsa açıkça belirt ve gerekçelendir.
- CEZA ise: Takdir yetkisini aşağıdaki puanlara göre açıkla ve gerekçelendir.

2) Varsayım yapma: Dosyada/delillerde bulunmayan olgular için "ispatlanamadı" / "dosya kapsamından anlaşılamadı" de.

3) Atıf zorunluluğu:
- Özel hukukta: kullandığın Yargıtay kararlarını daire/tarih/E./K. bilgisiyle an.
- Kanun maddelerini madde numarasıyla yaz.
- Retrieval’da yoksa uydurma madde/karar/atıf üretme.
- DEMO etiketli içerikler yalnızca örnek amaçlıdır; gerçek karar gibi sunma.

4) ÇIKTI TEK PARÇA METİN olacak ve aşağıdaki FORMAT ZORUNLULUĞUNA birebir uyacaktır.

{format_block}

GİRDİ:
KISA KARAR:
\"\"\"{kisa_karar}\"\"\"

DELİLLER:
{format_evidence(evidences)}

İLGİLİ KANUN MADDELERİ (RETRIEVAL):
{format_laws(laws)}

İLGİLİ YARGITAY İÇTİHATLARI (RETRIEVAL):
{format_precedents(precedents)}

{scoring_block}

ÜRETİM:
- Resmi gerekçeli karar diliyle yaz.
- Deliller ile sonuç arasında illiyet bağını açıkla.
"""
def format_gerekceli_karar(raw: str, dava_turu: str) -> str:
    """
    Model çıktısını daha 'mahkeme kararı' görünümüne zorlayan hafif post-process.
    Varsayım üretmez, sadece biçim düzeltir.
    """
    text = (raw or "").strip()

    # Üst başlık yoksa ekle
    header = (
        "T.C.\n"
        "RATIOAI HUKUKİ KARAR DESTEK SİSTEMİ\n"
        "(Akademik Prototip)\n\n"
        f"DOSYA TÜRÜ: {dava_turu}\n"
        "--------------------------------------------------\n\n"
    )
    if "RATIOAI HUKUKİ KARAR DESTEK SİSTEMİ" not in text:
        text = header + text

    # Başlıkları normalize et (farklı yazılmışsa)
    def normalize_section(s: str) -> str:
        s2 = s.upper().replace("İ", "İ").replace("İ", "İ")
        return re.sub(r"\s+", " ", s2).strip()

    normalized = text
    # Eğer hiç bölüm başlığı yoksa, metni bölümlere kaba şekilde yerleştir
    has_any = any(sec in normalize_section(normalized) for sec in REQUIRED_SECTIONS)
    if not has_any:
        normalized = (
            header
            + "I. TARAF BEYANLARI\n"
            + "(Kısa karardan anlaşılan beyanlar özetlenmiştir.)\n\n"
            + "II. UYUŞMAZLIĞIN HUKUKİ NİTELİĞİ\n\n"
            + "III. DELİLLERİN DEĞERLENDİRİLMESİ\n\n"
            + "IV. UYGULANAN HUKUK KURALLARI\n\n"
            + "V. YARGITAY İÇTİHATLARI\n\n"
            + "VI. HUKUKİ DEĞERLENDİRME\n\n"
            + "VII. SONUÇ VE HÜKÜM\n"
            + text
        )
        return normalized

    # Eksik başlık varsa en sona ekle (boş bile olsa format tutarlı dursun)
    up = normalize_section(normalized)
    for sec in REQUIRED_SECTIONS:
        if sec not in up:
            normalized += f"\n\n{sec}\n(İşbu başlık altında dosya kapsamına göre ayrıca değerlendirme yapılır.)\n"
            up = normalize_section(normalized)

    # Ayırıcı çizgileri güzelleştir
    normalized = re.sub(r"\n-{10,}\n", "\n--------------------------------------------------\n", normalized)

    # "VII. SONUÇ VE HÜKÜM" içinde numara yoksa 1) ile başlatmayı dene
    if "VII. SONUÇ VE HÜKÜM" in normalized:
        part = normalized.split("VII. SONUÇ VE HÜKÜM", 1)[1]
        if not re.search(r"\n\s*1\)", part):
            normalized = normalized.replace(
                "VII. SONUÇ VE HÜKÜM",
                "VII. SONUÇ VE HÜKÜM\n1) (Hüküm fıkrası burada numaralı şekilde yazılır.)",
                1
            )

    return normalized.strip()

import re

REQUIRED_SECTIONS = [
    "I. TARAF BEYANLARI",
    "II. UYUŞMAZLIĞIN HUKUKİ NİTELİĞİ",
    "III. DELİLLERİN DEĞERLENDİRİLMESİ",
    "IV. UYGULANAN HUKUK KURALLARI",
    "V. YARGITAY İÇTİHATLARI",
    "VI. HUKUKİ DEĞERLENDİRME",
    "VII. SONUÇ VE HÜKÜM",
]

def format_gerekceli_karar(raw: str, dava_turu: str) -> str:
    text = (raw or "").strip()

    header = (
        "T.C.\n"
        "RATIOAI HUKUKİ KARAR DESTEK SİSTEMİ\n"
        "(Akademik Prototip)\n\n"
        f"DOSYA TÜRÜ: {dava_turu}\n"
        "--------------------------------------------------\n\n"
    )
    if "RATIOAI HUKUKİ KARAR DESTEK SİSTEMİ" not in text:
        text = header + text

    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").upper()).strip()

    up = norm(text)
    for sec in REQUIRED_SECTIONS:
        if sec not in up:
            text += f"\n\n{sec}\n(İşbu başlık altında dosya kapsamına göre ayrıca değerlendirme yapılır.)\n"
            up = norm(text)

    text = re.sub(r"\n-{10,}\n", "\n--------------------------------------------------\n", text)

    # Hüküm fıkrası numaralandırma kontrolü
    if "VII. SONUÇ VE HÜKÜM" in text:
        after = text.split("VII. SONUÇ VE HÜKÜM", 1)[1]
        if not re.search(r"\n\s*1\)", after):
            text = text.replace("VII. SONUÇ VE HÜKÜM", "VII. SONUÇ VE HÜKÜM\n1) ", 1)

    return text.strip()