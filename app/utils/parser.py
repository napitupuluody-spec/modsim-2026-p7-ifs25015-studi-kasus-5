import json
import re


def parse_llm_response(raw_text: str) -> list[dict]:
    """
    Mem-parse respons teks dari LLM menjadi list soal latihan terstruktur.

    Strategi:
    1. Coba parse JSON langsung dari blok ```json ... ```.
    2. Jika gagal, coba parse seluruh teks sebagai JSON.
    3. Jika tetap gagal, kembalikan format fallback.
    """
    # Coba ekstrak blok JSON dari markdown code fence
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_text)
    if json_match:
        candidate = json_match.group(1).strip()
        parsed = _try_parse_json(candidate)
        if parsed is not None:
            return _normalize(parsed)

    # Coba parse seluruh teks sebagai JSON langsung
    parsed = _try_parse_json(raw_text.strip())
    if parsed is not None:
        return _normalize(parsed)

    # Fallback: kembalikan sebagai satu soal teks mentah
    return [
        {
            "question": raw_text.strip(),
            "options": [],
            "answer": "",
            "explanation": "",
        }
    ]


def _try_parse_json(text: str):
    """Mencoba mem-parse string sebagai JSON, mengembalikan None jika gagal."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _normalize(data) -> list[dict]:
    """
    Memastikan hasil parse adalah list of dict dengan field standar:
    question, options, answer, explanation.
    """
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict):
        # Beberapa LLM membungkus dalam {"questions": [...]}
        questions = data.get("questions", [data])
    else:
        return [{"question": str(data), "options": [], "answer": "", "explanation": ""}]

    normalized = []
    for item in questions:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "question": item.get("question", item.get("soal", "")),
                "options": item.get("options", item.get("pilihan", [])),
                "answer": item.get("answer", item.get("jawaban", "")),
                "explanation": item.get("explanation", item.get("penjelasan", "")),
            }
        )
    return normalized if normalized else [{"question": str(data), "options": [], "answer": "", "explanation": ""}]
