from dataclasses import dataclass
from typing import Callable, Iterable

from .indicators import FRAMEWORK_INDICATORS


@dataclass(frozen=True)
class IndicatorMatch:
    passage_id: str
    document_id: str
    filename: str
    framework: str
    indicator: str
    passage_text: str
    page_number: int | None
    section_title: str | None
    similarity: float

    def as_dict(self) -> dict:
        return {
            "passage_id": self.passage_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "framework": self.framework,
            "indicator": self.indicator,
            "passage_text": self.passage_text,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "similarity": self.similarity,
        }


def retrieve_matches(
    passages: Iterable,
    top_k: int = 5,
    model=None,
    indicator_catalog: dict | None = None,
    cosine_similarity: Callable | None = None,
) -> list[IndicatorMatch]:
    passages = list(passages)
    catalog = indicator_catalog or FRAMEWORK_INDICATORS
    if not passages or not catalog:
        return []
    if model is None:
        raise RuntimeError("Semantic retrieval model is unavailable.")
    indicator_items = [
        (framework, indicator, description)
        for framework, indicators in catalog.items()
        for indicator, description in indicators.items()
    ]
    encode = model.encode
    passage_vectors = encode([passage.text for passage in passages], convert_to_tensor=True)
    indicator_vectors = encode([description for _, _, description in indicator_items], convert_to_tensor=True)
    if cosine_similarity is None:
        from sentence_transformers import util
        cosine_similarity = util.cos_sim
    scores = cosine_similarity(passage_vectors, indicator_vectors)
    matches = []
    for indicator_index, (framework, indicator, _) in enumerate(indicator_items):
        ranked = sorted(
            enumerate(passages),
            key=lambda pair: float(scores[pair[0]][indicator_index]),
            reverse=True,
        )[:top_k]
        for passage_index, passage in ranked:
            matches.append(IndicatorMatch(
                passage_id=passage.passage_id,
                document_id=passage.document_id,
                filename=passage.filename,
                framework=framework,
                indicator=indicator,
                passage_text=passage.text,
                page_number=passage.page_number,
                section_title=passage.section_title,
                similarity=round(float(scores[passage_index][indicator_index]), 6),
            ))
    return matches
