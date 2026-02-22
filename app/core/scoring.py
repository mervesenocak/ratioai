from typing import Dict, Any


def clamp_0_10(x: int) -> int:
    return max(0, min(10, int(x)))


def score_criminal(
    *,
    kast_taksir: int,
    gecmis: int,
    islenis_sekli: int,
    magdur_etki: int,
    toplumsal_zarar: int,
) -> Dict[str, Any]:
    scores = {
        "kast_taksir": clamp_0_10(kast_taksir),
        "gecmis": clamp_0_10(gecmis),
        "islenis_sekli": clamp_0_10(islenis_sekli),
        "magdur_etki": clamp_0_10(magdur_etki),
        "toplumsal_zarar": clamp_0_10(toplumsal_zarar),
    }
    total = sum(scores.values())

    if total <= 15:
        band = "ALT"
        takdir = "Lehe takdir ağırlıklı; alt hadden uzaklaşmama eğilimi."
    elif total <= 30:
        band = "ORTA"
        takdir = "Dengeli takdir; temel ceza orta bantta belirlenebilir."
    else:
        band = "UST"
        takdir = "Aleyhe takdir ağırlıklı; üst hadden belirleme ve indirim/erteleme değerlendirmesinde daha sıkı yaklaşım."

    return {
        "scores": scores,
        "total": total,
        "band": band,
        "takdir_aciklama": takdir,
    }