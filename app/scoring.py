from typing import Dict, Any, List
import re
# Importação conceitual. Para implementar, você precisaria instalar e configurar uma biblioteca de PLN como spacy ou nltk.
# import spacy 
# nlp = spacy.load("pt_core_news_sm")

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

# Regex para citar padrões como (Autor, Ano), [1], [1, 2], [1-3]
CITATION_PATTERNS = [
    re.compile(r"\((?:[A-Z][a-zA-Z]+(?:,?\s*&?\s*[A-Z][a-zA-Z]+)*,\s*(?:19|20)\d{2})\)"),
    re.compile(r"\[(?:\d{1,3})(?:,?\s*\d{1,3}|-\d{1,3})*\]")
]

def count_citations(text: str) -> int:
    """
    Conta citações usando padrões de regex mais abrangentes.
    """
    total = 0
    for pat in CITATION_PATTERNS:
        total += len(pat.findall(text))
    # Adicionar contagem de citações com nome e ano, ex: 'Silva (2020)'
    total += len(re.findall(r'[A-Z][a-zA-Z]+\s*\((?:19|20)\d{2}\)', text))
    return total

def section_coverage(text: str) -> Dict[str, int]:
    """
    Usa um método mais robusto para detectar seções.
    Poderia ser expandido para usar PLN para identificar a estrutura do documento.
    """
    t = text.lower()
    cov = {}
    for sec, hints in SECTION_HINTS.items():
        hits = sum(1 for h in hints if h in t)
        cov[sec] = hits
    return cov

def readability_signals(text: str) -> Dict[str, Any]:
    """
    Sinais de legibilidade melhorados.
    """
    words = re.findall(r"\w+", text, flags=re.UNICODE)
    sentences = re.split(r"[.!?]\s+", text.strip())
    
    word_count = len(words)
    sentence_count = len(sentences)
    
    avg_word_len = (sum(len(w) for w in words) / word_count) if word_count > 0 else 0
    avg_sentence_words = (sum(len(s.split()) for s in sentences) / sentence_count) if sentence_count > 0 else 0

    # Exemplo de uma métrica de legibilidade: Índice de Legibilidade de Flesch-Kincaid
    # F-K = 0.39 * (palavras / frases) + 11.8 * (sílabas / palavras) - 15.59
    # Para simplificar sem contar sílabas, podemos usar uma aproximação ou a fórmula original:
    # A fórmula original é difícil de implementar sem um contador de sílabas. A proposta a seguir é uma aproximação.
    flesch_kincaid = 0
    if word_count > 0 and sentence_count > 0:
        flesch_kincaid = 0.39 * avg_sentence_words + 11.8 * avg_word_len # Esta é uma simplificação
    
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_word_len": avg_word_len,
        "avg_sentence_words": avg_sentence_words,
        "flesch_kincaid": flesch_kincaid
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
    
    explanations = {}

    # Relevância e Originalidade (Melhorado)
    # A presença de "apresentamos" ou "propomos" não significa necessariamente originalidade.
    # O ideal seria usar PLN para identificar verbos no presente do indicativo que sugerem uma ação de pesquisa.
    novelty_signals = sum(1 for k in ["propomos", "apresentamos", "neste trabalho", "contribuição", "novel", "novo", "inédito"]
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

    # Rigor Metodológico (Melhorado)
    meth_hits = cov.get("metodologia", 0)
    rigor_score = 4 + 2 * meth_hits
    if re.search(r"\b(amostra|amostragem|dataset|base de dados)\b", text.lower()):
        rigor_score += 2
    if re.search(r"\b(reprodutibil|protocolo|pré\-registro|pré registro)\b", text.lower()):
        rigor_score += 1
    # Adicionando um sinal para a menção de dados quantitativos ou qualitativos
    if re.search(r"\b(quantitativ|qualitativ)\b", text.lower()):
        rigor_score += 1.5
    rigor_score = clamp(rigor_score)
    explanations["Rigor Metodológico"] = explain(
        "Base", [
            f"sinais de metodologia={meth_hits}",
            "menciona amostra/dataset" if re.search(r"\b(amostra|amostragem|dataset|base de dados)\b", text.lower()) else "sem amostra/dataset",
            "menciona reprodutibilidade/protocolo" if re.search(r"\b(reprodutibil|protocolo|pré\-registro|pré registro)\b", text.lower()) else "sem menção a reprodutibilidade",
            "menciona abordagem quantitativa/qualitativa" if re.search(r"\b(quantitativ|qualitativ)\b", text.lower()) else "sem menção a tipo de dado"
        ]
    )

    # Qualidade da Escrita (Melhorado)
    # A nota passa a ser mais influenciada pela métrica de legibilidade
    qc = 7.0
    # Reduz a pontuação se a legibilidade for muito baixa ou alta (indica texto muito simples)
    if read["flesch_kincaid"] < 20 or read["flesch_kincaid"] > 70:
         qc -= 1.0
    if read["word_count"] < 150:
        qc -= 1.5
    if read["avg_sentence_words"] > 35:
        qc -= 1.5
    qc = clamp(qc)
    explanations["Qualidade da Escrita"] = explain(
        "Base", [
            f"média palavras por sentença={read['avg_sentence_words']:.1f}",
            f"tamanho do texto={read['word_count']} palavras",
            f"Índice Flesch-Kincaid (simplificado)={read['flesch_kincaid']:.1f}"
        ]
    )

    # Fundamentação Teórica (Melhorado)
    # A nota passa a ser mais influenciada pela contagem de citações
    ft = 3 + min(cites, 10) * 0.6
    if cov.get("introdução", 0) > 0:
        ft += 1
    # Adicionando um bônus se o texto menciona "literatura" ou "referências"
    if re.search(r"\b(literatura|referênci)\b", text.lower()):
        ft += 1.0
    ft = clamp(ft)
    explanations["Fundamentação Teórica"] = explain(
        "Base", [
            f"citações detectadas={cites}",
            "há sinais de introdução" if cov.get("introdução", 0) > 0 else "sem sinais de introdução",
            "menciona literatura/referências" if re.search(r"\b(literatura|referênci)\b", text.lower()) else "sem menção à literatura"
        ]
    )

    # Resultados e Discussão (Melhorado)
    rd = 3 + 1.5 * cov.get("resultados", 0) + 1.5 * cov.get("discussão", 0)
    if "limitações" in text.lower() or "limitação" in text.lower():
        rd += 1.5
    # Bônus se houver menção a "conclusões" ou "trabalhos futuros"
    if cov.get("conclusões", 0) > 0:
        rd += 1.0
    rd = clamp(rd)
    explanations["Resultados e Discussão"] = explain(
        "Base", [
            f"sinais de resultados={cov.get('resultados', 0)}",
            f"sinais de discussão={cov.get('discussão', 0)}",
            "menciona limitações" if ("limitações" in text.lower() or "limitação" in text.lower()) else "sem menção a limitações",
            "menciona conclusões/trabalhos futuros" if cov.get("conclusões", 0) > 0 else "sem menção a conclusões"
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
