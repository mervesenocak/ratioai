from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

CaseType = Literal["OZEL_HUKUK", "CEZA"]


class EvidenceItem(BaseModel):
    name: str
    content: str


class CriminalScores(BaseModel):
    kast_taksir: int = Field(ge=0, le=10)
    gecmis: int = Field(ge=0, le=10)
    islenis_sekli: int = Field(ge=0, le=10)
    magdur_etki: int = Field(ge=0, le=10)
    toplumsal_zarar: int = Field(ge=0, le=10)


class GenerateRequest(BaseModel):
    kisa_karar: str = Field(..., min_length=20)
    dava_turu: CaseType
    deliller: Optional[List[EvidenceItem]] = None
    ceza_puanlari: Optional[CriminalScores] = None


class RetrievedDoc(BaseModel):
    id: str
    title: str
    text: str
    meta: Dict[str, Any]


class GenerateResponse(BaseModel):
    gerekceli_karar: str
    used_laws: List[RetrievedDoc]
    used_precedents: List[RetrievedDoc]
    criminal_scoring: Optional[dict] = None
    warnings: List[str] = []