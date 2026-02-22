import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Doc:
    id: str
    title: str
    text: str
    meta: Dict[str, Any]


def load_jsonl(path: Path, kind: str) -> List[Doc]:
    docs: List[Doc] = []
    if not path.exists():
        return docs

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)

            if kind == "law":
                docs.append(
                    Doc(
                        id=obj["id"],
                        title=obj.get("title", obj["id"]),
                        text=obj["text"],
                        meta={"source": obj.get("source", "UNKNOWN"), "demo": obj.get("demo", False)},
                    )
                )
            else:
                docs.append(
                    Doc(
                        id=obj["id"],
                        title=obj.get("title", obj["id"]),
                        text=obj["text"],
                        meta={
                            "chamber": obj.get("chamber"),
                            "date": obj.get("date"),
                            "ek": obj.get("ek"),
                            "kk": obj.get("kk"),
                            "tags": obj.get("tags", []),
                            "demo": obj.get("demo", False),
                        },
                    )
                )
    return docs


class Retriever:
    def __init__(self, law_docs: List[Doc], precedent_docs: List[Doc]):
        self.law_docs = law_docs
        self.prec_docs = precedent_docs

        self.law_vec = TfidfVectorizer(ngram_range=(1, 2), max_features=60000)
        self.prec_vec = TfidfVectorizer(ngram_range=(1, 2), max_features=80000)

        self._law_matrix = self.law_vec.fit_transform([d.text for d in law_docs]) if law_docs else None
        self._prec_matrix = self.prec_vec.fit_transform([d.text for d in precedent_docs]) if precedent_docs else None

    def search(self, query: str, topk_laws: int = 8, topk_precedents: int = 8) -> Tuple[List[Doc], List[Doc]]:
        laws: List[Doc] = []
        precs: List[Doc] = []

        if self._law_matrix is not None and self.law_docs:
            qv = self.law_vec.transform([query])
            sims = cosine_similarity(qv, self._law_matrix)[0]
            idxs = sims.argsort()[::-1][:topk_laws]
            laws = [self.law_docs[i] for i in idxs if sims[i] > 0.04]

        if self._prec_matrix is not None and self.prec_docs:
            qv = self.prec_vec.transform([query])
            sims = cosine_similarity(qv, self._prec_matrix)[0]
            idxs = sims.argsort()[::-1][:topk_precedents]
            precs = [self.prec_docs[i] for i in idxs if sims[i] > 0.04]

        return laws, precs