import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LAW_DIR = DATA_DIR / "laws"
PREC_DIR = DATA_DIR / "precedents"
LAW_DIR.mkdir(parents=True, exist_ok=True)
PREC_DIR.mkdir(parents=True, exist_ok=True)

laws = [
    ("HMK-24", "HMK m.24 (Tasarruf ilkesi)", "Hâkim, tarafların talep sonuçlarıyla bağlıdır; ondan fazlasına veya başka bir şeye karar veremez.", "HMK"),
    ("HMK-25", "HMK m.25 (Taraflarca getirilme ilkesi)", "Hâkim, tarafların ileri sürmediği vakıaları kendiliğinden dikkate alamaz.", "HMK"),
    ("HMK-27", "HMK m.27 (Hukuki dinlenilme hakkı)", "Taraflar, yargılama boyunca bilgi sahibi olma, açıklama ve ispat hakkına sahiptir.", "HMK"),
    ("HMK-31", "HMK m.31 (Hâkimin davayı aydınlatma ödevi)", "Hâkim, uyuşmazlığın aydınlatılması için gerekli gördüğü açıklamayı taraflardan isteyebilir.", "HMK"),
    ("HMK-33", "HMK m.33 (Hâkimin hukuku uygulaması)", "Hâkim, Türk hukukunu resen uygular.", "HMK"),
    ("HMK-119", "HMK m.119 (Dava dilekçesinin içeriği)", "Dava dilekçesinde taraflar, talepler, vakıalar ve deliller yer alır.", "HMK"),
    ("HMK-190", "HMK m.190 (İspat yükü)", "Kanunda aksine hüküm bulunmadıkça, iddia edilen vakıaya bağlanan hukuki sonuçtan kendi lehine hak çıkaran taraf ispatla yükümlüdür.", "HMK"),
    ("HMK-266", "HMK m.266 (Bilirkişi)", "Çözümü özel veya teknik bilgiyi gerektiren hallerde bilirkişiye başvurulur.", "HMK"),
    ("HMK-281", "HMK m.281 (Bilirkişi raporuna itiraz)", "Taraflar rapora itiraz edebilir; hâkim gerekli görürse ek rapor alabilir.", "HMK"),
    ("HMK-297", "HMK m.297 (Hükmün kapsamı)", "Hüküm sonucu, gerekçe ve yargılama giderleri gibi unsurları içerir.", "HMK"),

    ("TBK-49", "TBK m.49 (Haksız fiil sorumluluğu)", "Kusurlu ve hukuka aykırı fiille başkasına zarar veren, bu zararı gidermekle yükümlüdür.", "TBK"),
    ("TBK-50", "TBK m.50 (İspat)", "Zarar gören, zararı ve zarar verenin kusurunu ispatla yükümlüdür.", "TBK"),
    ("TBK-51", "TBK m.51 (Tazminatın belirlenmesi)", "Hâkim, tazminatın kapsamını ve ödenme biçimini durumun gereklerine göre belirler.", "TBK"),
    ("TBK-52", "TBK m.52 (İndirim sebepleri)", "Zarar görenin rızası, birlikte kusur veya diğer sebepler tazminatı azaltabilir.", "TBK"),
    ("TBK-56", "TBK m.56 (Manevi tazminat)", "Hâkim, olayın özelliklerini göz önüne alarak manevi tazminata hükmedebilir.", "TBK"),
    ("TBK-97", "TBK m.97 (Ödemezlik def’i)", "Karşılıklı borçlarda ifa sırasına göre ödemezlik def’i ileri sürülebilir.", "TBK"),
    ("TBK-112", "TBK m.112 (Borçlunun sorumluluğu)", "Borçlu, borcun hiç/eksik ifasından doğan zararı gidermekle yükümlü olabilir.", "TBK"),
    ("TBK-117", "TBK m.117 (Temerrüt)", "Borçlu, alacaklının ihtarıyla temerrüde düşer; kanunda sayılan hallerde ihtar gerekmez.", "TBK"),
    ("TBK-138", "TBK m.138 (Aşırı ifa güçlüğü)", "Koşulları varsa sözleşmenin uyarlanması veya feshi talep edilebilir.", "TBK"),

    ("TMK-2", "TMK m.2 (Dürüstlük kuralı)", "Herkes haklarını kullanırken ve borçlarını yerine getirirken dürüstlük kurallarına uymak zorundadır.", "TMK"),
    ("TMK-3", "TMK m.3 (İyi niyet)", "Kanunun iyiniyete hukuki sonuç bağladığı durumlarda asıl olan iyiniyetin varlığıdır.", "TMK"),
    ("TMK-6", "TMK m.6 (İspat yükü)", "Kanunda aksine hüküm bulunmadıkça taraflardan her biri iddiasını ispatla yükümlüdür.", "TMK"),
    ("TMK-24", "TMK m.24 (Kişilik haklarının korunması)", "Kişilik hakkı saldırıya uğrayan, hâkimden korunma isteyebilir.", "TMK"),
    ("TMK-25", "TMK m.25 (Dava hakları)", "Durdurma, önleme, tespit vb. talepler ileri sürülebilir.", "TMK"),
    ("TMK-683", "TMK m.683 (Mülkiyet hakkı)", "Malik, malını kullanma, yararlanma ve tasarruf etme yetkilerine sahiptir.", "TMK"),

    ("TTK-4", "TTK m.4 (Ticari davalar)", "Bazı uyuşmazlıklar ticari dava sayılır ve ticari hükümler uygulanır.", "TTK"),
    ("TTK-18", "TTK m.18 (Tacir gibi davranma)", "Tacir, tüm faaliyetlerinde basiretli bir iş insanı gibi hareket etmek zorundadır.", "TTK"),

    ("IİK-67", "İİK m.67 (İtirazın iptali)", "Şartları varsa itirazın iptali ve icra inkâr tazminatına hükmedilebilir.", "IİK"),
    ("IİK-72", "İİK m.72 (Menfi tespit/istirdat)", "Borçlu olmadığını iddia eden, menfi tespit davası açabilir; şartları varsa istirdat talep edebilir.", "IİK"),

    ("TCK-21", "TCK m.21 (Kast)", "Suçun oluşması kastın varlığına bağlıdır; kastın kapsamı değerlendirilir.", "TCK"),
    ("TCK-22", "TCK m.22 (Taksir)", "Taksirle işlenen fiillerde dikkat ve özen yükümlülüğüne aykırılık aranır.", "TCK"),
    ("TCK-61", "TCK m.61 (Cezanın belirlenmesi)", "Temel ceza belirlenirken işleniş biçimi, failin kastı, zarar/tehlikenin ağırlığı vb. dikkate alınır.", "TCK"),
    ("TCK-62", "TCK m.62 (Takdiri indirim)", "Şartları varsa takdiri indirim uygulanabilir.", "TCK"),
    ("CMK-223", "CMK m.223 (Hüküm)", "Beraat/mahkûmiyet/düşme vb. hüküm türleri düzenlenmiştir.", "CMK"),
]


def make_demo_precedents():
    precs = []
    chambers = [
        "Yargıtay 3. Hukuk Dairesi",
        "Yargıtay 4. Hukuk Dairesi",
        "Yargıtay 9. Hukuk Dairesi",
        "Yargıtay 11. Hukuk Dairesi",
        "Yargıtay 13. Hukuk Dairesi",
        "Yargıtay 15. Hukuk Dairesi",
        "Yargıtay Ceza Genel Kurulu",
        "Yargıtay 8. Ceza Dairesi",
        "Yargıtay 12. Ceza Dairesi",
    ]
    tags_pool = [
        ["ispat", "HMK-190"],
        ["manevi tazminat", "TBK-56"],
        ["haksız fiil", "TBK-49"],
        ["bilirkişi", "HMK-266"],
        ["itirazın iptali", "IİK-67"],
        ["menfi tespit", "IİK-72"],
        ["dürüstlük", "TMK-2"],
        ["tacir", "TTK-18"],
        ["temerrüt", "TBK-117"],
        ["taksir", "TCK-22"],
        ["kast", "TCK-21"],
        ["cezanın belirlenmesi", "TCK-61"],
    ]

    for i in range(1, 51):
        chamber = chambers[i % len(chambers)]
        y = 2018 + (i % 7)
        m = (i % 12) + 1
        d = (i % 28) + 1
        ek = f"{y}/{1000+i} E."
        kk = f"{y}/{2000+i} K."
        tags = tags_pool[i % len(tags_pool)]

        precs.append({
            "id": f"DEMO-{i:03d}",
            "title": f"{chamber} {ek} {kk}",
            "chamber": chamber,
            "date": f"{y:04d}-{m:02d}-{d:02d}",
            "ek": ek,
            "kk": kk,
            "tags": tags,
            "demo": True,
            "text": (
                "DEMO ÖZET: Uyuşmazlıkta ispat yükü, delillerin tartışılması ve gerekçenin denetlenebilir olması ilkeleri vurgulanmıştır. "
                "Hâkimin, taraf iddia-savunmaları ile delilleri birlikte değerlendirip, hangi delile neden üstünlük tanıdığını gerekçede göstermesi gerektiği belirtilmiştir."
            ),
        })
    return precs


precedents = make_demo_precedents()

laws_path = LAW_DIR / "laws.jsonl"
precs_path = PREC_DIR / "precedents.jsonl"

with laws_path.open("w", encoding="utf-8") as f:
    for (id_, title, text, source) in laws[:30]:
        f.write(json.dumps({"id": id_, "title": title, "text": text, "source": source, "demo": True}, ensure_ascii=False) + "\n")

with precs_path.open("w", encoding="utf-8") as f:
    for p in precedents:
        f.write(json.dumps(p, ensure_ascii=False) + "\n")

print("OK:")
print(f"- {laws_path} yazıldı (30 DEMO kanun maddesi)")
print(f"- {precs_path} yazıldı (50 DEMO içtihat)")