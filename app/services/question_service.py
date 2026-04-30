import json
from app.services.llm_service import LLMService
from app.utils.parser import parse_llm_response
from app.models.question import Question
from app.extensions import db


DIFFICULTY_LABELS = {
    "easy": "Mudah",
    "medium": "Sedang",
    "hard": "Sulit",
}

TYPE_LABELS = {
    "multiple_choice": "pilihan ganda (4 opsi A, B, C, D)",
    "essay": "esai singkat",
    "true_false": "benar/salah",
}

SYSTEM_PROMPT = """Kamu adalah asisten pendidik yang ahli dalam membuat soal latihan berkualitas tinggi.
Selalu kembalikan respons dalam format JSON yang valid.
Jangan tambahkan teks di luar blok JSON."""


def _build_prompt(topic: str, difficulty: str, question_type: str, num_questions: int) -> str:
    diff_label = DIFFICULTY_LABELS.get(difficulty, "Sedang")
    type_label = TYPE_LABELS.get(question_type, "pilihan ganda")

    base = (
        f"Buatlah {num_questions} soal latihan tentang topik: '{topic}'.\n"
        f"Tingkat kesulitan: {diff_label}.\n"
        f"Tipe soal: {type_label}.\n\n"
    )

    if question_type == "multiple_choice":
        format_hint = (
            "Format JSON yang harus dikembalikan (array langsung, tanpa wrapper):\n"
            "[\n"
            "  {\n"
            '    "question": "Teks soal di sini",\n'
            '    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],\n'
            '    "answer": "A",\n'
            '    "explanation": "Penjelasan singkat jawaban"\n'
            "  }\n"
            "]\n"
        )
    elif question_type == "true_false":
        format_hint = (
            "Format JSON yang harus dikembalikan:\n"
            "[\n"
            "  {\n"
            '    "question": "Pernyataan yang harus dinilai Benar/Salah",\n'
            '    "options": ["Benar", "Salah"],\n'
            '    "answer": "Benar",\n'
            '    "explanation": "Penjelasan singkat"\n'
            "  }\n"
            "]\n"
        )
    else:  # essay
        format_hint = (
            "Format JSON yang harus dikembalikan:\n"
            "[\n"
            "  {\n"
            '    "question": "Pertanyaan esai di sini",\n'
            '    "options": [],\n'
            '    "answer": "Kunci jawaban / poin-poin penting",\n'
            '    "explanation": "Penjelasan tambahan jika ada"\n'
            "  }\n"
            "]\n"
        )

    return base + format_hint + "\nHanya kembalikan array JSON, tanpa teks tambahan apapun."


class QuestionService:
    """Service utama untuk logika bisnis pembuatan soal latihan."""

    def __init__(self):
        self.llm = LLMService()

    def generate_questions(
        self,
        topic: str,
        difficulty: str = "medium",
        question_type: str = "multiple_choice",
        num_questions: int = 5,
    ) -> dict:
        """
        Menghasilkan soal latihan menggunakan LLM dan menyimpannya ke database.

        Returns:
            dict berisi 'questions' (list) dan 'record_id' (int).
        """
        # Validasi input
        if not topic or not topic.strip():
            raise ValueError("Topik soal tidak boleh kosong.")
        if difficulty not in DIFFICULTY_LABELS:
            raise ValueError(f"Tingkat kesulitan harus salah satu dari: {list(DIFFICULTY_LABELS.keys())}")
        if question_type not in TYPE_LABELS:
            raise ValueError(f"Tipe soal harus salah satu dari: {list(TYPE_LABELS.keys())}")
        if not (1 <= num_questions <= 20):
            raise ValueError("Jumlah soal harus antara 1 hingga 20.")

        prompt = _build_prompt(topic.strip(), difficulty, question_type, num_questions)
        raw_response = self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=3000)
        questions = parse_llm_response(raw_response)

        # Simpan ke database
        record = Question(
            topic=topic.strip(),
            difficulty=difficulty,
            question_type=question_type,
            num_questions=num_questions,
            questions_json=json.dumps(questions, ensure_ascii=False),
        )
        db.session.add(record)
        db.session.commit()

        return {"questions": questions, "record_id": record.id}

    def get_history(self, limit: int = 20) -> list[dict]:
        """Mengambil riwayat soal yang pernah di-generate."""
        records = (
            Question.query.order_by(Question.created_at.desc()).limit(limit).all()
        )
        result = []
        for r in records:
            data = r.to_dict()
            data["questions"] = json.loads(r.questions_json)
            result.append(data)
        return result

    def get_by_id(self, record_id: int) -> dict | None:
        """Mengambil satu record soal berdasarkan ID."""
        record = Question.query.get(record_id)
        if not record:
            return None
        data = record.to_dict()
        data["questions"] = json.loads(record.questions_json)
        return data
