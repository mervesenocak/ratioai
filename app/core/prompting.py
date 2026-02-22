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
        scoring_block = f'''
CEZA TAKDİR PUANLARI (0–10):
- Kast/Taksir: {s['kast_taksir']}
- Sanığın geçmişi: {s['gecmis']}
- Suçun işleniş şekli: {s['islenis_sekli']}
- Mağdur üzerindeki etki: {s['magdur_etki']}
- Toplumsal zarar: {s['toplumsal_zarar']}
TOPLAM: {criminal_scoring['total']}  |  Bant: {criminal_scoring['band']}
Takdir açıklaması: {criminal_scoring['takdir_aciklama']}
'''

    return f'''
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
- DEMO etiketli içerikler yalnızca örnek amaçlıdır; gerçek karar gibi sunma.

4) ÇIKTI TEK PARÇA METİN olacak ve şu başlıkları içerecek:
- Tarafların iddia ve savunmaları
- Uyuşmazlığın hukuki niteliği
- Delillerin değerlendirilmesi
- Uygulanan kanun maddeleri
- Yargıtay içtihatlarına atıf
- Hukuki değerlendirme
- Sonuç ve hüküm

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
- Retrieval’da yoksa uydurma madde/karar/atıf üretme.
- Deliller ile sonuç arasında illiyet bağını açıkla.
'''