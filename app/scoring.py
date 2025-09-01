from typing import Dict, Any, List
import re

DIMENSIONS = [
    "Relevância e Originalidade",
    "Rigor Metodológico",
    "Qualidade da Escrita",
    "Fundamentação Teórica",
    "Resultados e Discussão"
]

SECTION_HINTS = {
    "introdução": ["introdução", "contexto", "motivação", "objetivo"],
    "metodologia": ["método", "metodologia", "procedimentos", "amostra", "amostragem", "instrumento"],
    "resultados": ["resultados", "achados", "achado", "experimentos", "análise"],
    "discussão": ["discussão", "implicações", "interpretação", "limitações"],
    "conclusões": ["conclusão", "conclusões", "trabalhos futuros", "futuros"]
}

CITATION_PATTERNS = [
    re.compile(r"\((?:19|20)\d{2}\)"),
    re.compile(r"\[(?:\d{1,3})(?:,\s*\d{1,3})*\]"),
    re.compile(r"[A-Z][a-zA-Z]+,\s*(?:19|20)\d{2}")
]

def count_citations(text: str) -> int:
    total = 0
    for pat in CITATION_PATTERNS:
        total += len(pat.findall(text))
    return total

def section_coverage(text: str) -> Dict[str, int]:
    t = text.lower()
    cov = {}
    for sec, hints in SECTION_HINTS.items():
        hits = sum(1 for h in hints if h in t)
        cov[sec] = hits
    return cov

def readability_signals(text: str) -> Dict[str, Any]:
    # Very rough signals
    words = re.findall(r"\w+", text, flags=re.UNICODE)
    sentences = re.split(r"[.!?]\s+", text.strip())
    avg_len = (sum(len(w) for w in words) / len(words)) if words else 0
    sent_len = (sum(len(s.split()) for s in sentences) / len(sentences)) if sentences else 0
    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_word_len": avg_len,
        "avg_sentence_words": sent_len
    }

def clamp(x: float, lo: float = 1.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, x))

def explain(label: str, details: List[str]) -> str:
    bullet = "; ".join(details)
    return f"{label}: {bullet}." if details else f"{label}: sem evidências claras."

def score(text: str) -> Dict[str, Any]:
    text = text.strip()
    if not text:
        return {
            "scores": {d: 1 for d in DIMENSIONS},
            "explainability": {d: "Texto vazio, atribuído mínimo 1." for d in DIMENSIONS}
        }

    cov = section_coverage(text)
    cites = count_citations(text)
    read = readability_signals(text)

    # Heuristics per dimension
    explanations = {}

    # Relevância e Originalidade
    novelty_signals = sum(1 for k in ["propomos", "apresentamos", "neste trabalho", "contribuição"]
                          if k in text.lower())
    rel_score = 5 + 2 * novelty_signals
    rel_score += 1 if "lacuna" in text.lower() or "gap" in text.lower() else 0
    rel_score = clamp(rel_score)
    explanations["Relevância e Originalidade"] = explain(
        "Base", [
            f"sinais de novidade={novelty_signals}",
            "menciona lacuna" if ("lacuna" in text.lower() or "gap" in text.lower()) else "sem menção explícita a lacuna"
        ]
    )

    # Rigor Metodológico
    meth_hits = cov.get("metodologia", 0)
    rigor_score = 4 + 2 * meth_hits
    # Presence of sample or dataset
    if re.search(r"\b(amostra|amostragem|dataset|base de dados)\b", text.lower()):
        rigor_score += 2
    # Mentions of reprodutibilidade or protocolo
    if re.search(r"\b(reprodutibil|protocolo|pré\-registro|pré registro)\b", text.lower()):
        rigor_score += 1
    rigor_score = clamp(rigor_score)
    explanations["Rigor Metodológico"] = explain(
        "Base", [
            f"sinais de metodologia={meth_hits}",
            "menciona amostra/dataset" if re.search(r"\b(amostra|amostragem|dataset|base de dados)\b", text.lower()) else "sem amostra/dataset",
            "menciona reprodutibilidade/protocolo" if re.search(r"\b(reprodutibil|protocolo|pré\-registro|pré registro)\b", text.lower()) else "sem menção a reprodutibilidade"
        ]
    )

    # Qualidade da Escrita
    qc = 7.0
    if read["avg_sentence_words"] > 35:
        qc -= 1.5
    if read["avg_sentence_words"] < 10:
        qc -= 1.0
    if read["word_count"] < 150:
        qc -= 1.5
    qc = clamp(qc)
    explanations["Qualidade da Escrita"] = explain(
        "Base", [
            f"média palavras por sentença={read['avg_sentence_words']:.1f}",
            f"tamanho do texto={read['word_count']} palavras"
        ]
    )

    # Fundamentação Teórica
    ft = 3 + min(cites, 10) * 0.6
    if cov.get("introdução", 0) > 0:
        ft += 1
    ft = clamp(ft)
    explanations["Fundamentação Teórica"] = explain(
        "Base", [
            f"citações detectadas={cites}",
            "há sinais de introdução" if cov.get("introdução", 0) > 0 else "sem sinais de introdução"
        ]
    )

    # Resultados e Discussão
    rd = 3 + 1.5 * cov.get("resultados", 0) + 1.5 * cov.get("discussão", 0)
    if "limitações" in text.lower() or "limitação" in text.lower():
        rd += 1.5
    rd = clamp(rd)
    explanations["Resultados e Discussão"] = explain(
        "Base", [
            f"sinais de resultados={cov.get('resultados', 0)}",
            f"sinais de discussão={cov.get('discussão', 0)}",
            "menciona limitações" if ("limitações" in text.lower() or "limitação" in text.lower()) else "sem menção a limitações"
        ]
    )

    scores = {
        "Relevância e Originalidade": round(rel_score, 1),
        "Rigor Metodológico": round(rigor_score, 1),
        "Qualidade da Escrita": round(qc, 1),
        "Fundamentação Teórica": round(ft, 1),
        "Resultados e Discussão": round(rd, 1)
    }

    return {
        "scores": scores,
        "explainability": explanations,
        "signals": {
            "section_coverage": cov,
            "citations": cites,
            "readability": read
        }
    }
