from typing import List


def validate_has_sections(text: str) -> List[str]:
    required = [
        "Tarafların iddia ve savunmaları",
        "Uyuşmazlığın hukuki niteliği",
        "Delillerin değerlendirilmesi",
        "Uygulanan kanun maddeleri",
        "Yargıtay içtihatlarına atıf",
        "Hukuki değerlendirme",
        "Sonuç ve hüküm",
    ]
    warnings = []
    low = text.lower()
    for h in required:
        if h.lower() not in low:
            warnings.append(f"Eksik başlık: {h}")
    return warnings


def warn_demo_sources(used_laws, used_precedents) -> List[str]:
    w = []
    if any(d.meta.get("demo") for d in used_laws):
        w.append("Kullanılan kanun maddeleri içinde DEMO içerik var. Akademik kullanım için gerçek metinlerle değiştir.")
    if any(d.meta.get("demo") for d in used_precedents):
        w.append("Kullanılan içtihatlar içinde DEMO içerik var. Akademik kullanım için gerçek Yargıtay kararlarıyla değiştir.")
    return w