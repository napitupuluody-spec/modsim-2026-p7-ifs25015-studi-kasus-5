import json
import time
from flask import Blueprint, request, jsonify
from app.services.question_service import QuestionService
from app.models.request_log import RequestLog
from app.extensions import db

question_bp = Blueprint("questions", __name__, url_prefix="/api")
_service = None


def get_service() -> QuestionService:
    """Lazy-init service agar tidak gagal saat import sebelum app context."""
    global _service
    if _service is None:
        _service = QuestionService()
    return _service


def _log_request(endpoint: str, method: str, payload: str, status_code: int,
                 response_time_ms: float, error_message: str = None):
    """Menyimpan log permintaan ke database."""
    log = RequestLog(
        endpoint=endpoint,
        method=method,
        payload=payload,
        status_code=status_code,
        response_time_ms=response_time_ms,
        error_message=error_message,
    )
    db.session.add(log)
    db.session.commit()


@question_bp.route("/generate", methods=["POST"])
def generate():
    """
    POST /api/generate
    Body JSON:
    {
        "topic": "Rekursif dalam Python",
        "difficulty": "medium",       // easy | medium | hard
        "question_type": "multiple_choice",  // multiple_choice | essay | true_false
        "num_questions": 5
    }
    """
    start = time.time()
    payload_str = request.get_data(as_text=True)
    error_msg = None
    status = 200

    try:
        data = request.get_json(force=True, silent=True) or {}
        topic = data.get("topic", "").strip()
        difficulty = data.get("difficulty", "medium")
        question_type = data.get("question_type", "multiple_choice")
        num_questions = int(data.get("num_questions", 5))

        result = get_service().generate_questions(
            topic=topic,
            difficulty=difficulty,
            question_type=question_type,
            num_questions=num_questions,
        )
        response = jsonify({
            "success": True,
            "record_id": result["record_id"],
            "topic": topic,
            "difficulty": difficulty,
            "question_type": question_type,
            "num_questions": num_questions,
            "questions": result["questions"],
        })

    except ValueError as e:
        status = 400
        error_msg = str(e)
        response = jsonify({"success": False, "error": error_msg})
        response.status_code = status

    except Exception as e:
        status = 500
        error_msg = str(e)
        response = jsonify({"success": False, "error": "Terjadi kesalahan internal server."})
        response.status_code = status

    elapsed = round((time.time() - start) * 1000, 2)
    _log_request("/api/generate", "POST", payload_str, status, elapsed, error_msg)
    return response


@question_bp.route("/history", methods=["GET"])
def history():
    """
    GET /api/history?limit=20
    Mengambil riwayat soal yang pernah di-generate.
    """
    start = time.time()
    error_msg = None
    status = 200

    try:
        limit = min(int(request.args.get("limit", 20)), 100)
        records = get_service().get_history(limit=limit)
        response = jsonify({"success": True, "total": len(records), "data": records})

    except Exception as e:
        status = 500
        error_msg = str(e)
        response = jsonify({"success": False, "error": "Gagal mengambil riwayat."})
        response.status_code = status

    elapsed = round((time.time() - start) * 1000, 2)
    _log_request("/api/history", "GET", "", status, elapsed, error_msg)
    return response


@question_bp.route("/history/<int:record_id>", methods=["GET"])
def history_detail(record_id: int):
    """
    GET /api/history/<id>
    Mengambil detail satu record soal berdasarkan ID.
    """
    start = time.time()
    error_msg = None
    status = 200

    try:
        record = get_service().get_by_id(record_id)
        if record is None:
            status = 404
            response = jsonify({"success": False, "error": f"Record dengan ID {record_id} tidak ditemukan."})
            response.status_code = status
        else:
            response = jsonify({"success": True, "data": record})

    except Exception as e:
        status = 500
        error_msg = str(e)
        response = jsonify({"success": False, "error": "Gagal mengambil detail record."})
        response.status_code = status

    elapsed = round((time.time() - start) * 1000, 2)
    _log_request(f"/api/history/{record_id}", "GET", "", status, elapsed, error_msg)
    return response


@question_bp.route("/logs", methods=["GET"])
def logs():
    """
    GET /api/logs?limit=50
    Mengambil log permintaan terakhir.
    """
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        records = RequestLog.query.order_by(RequestLog.created_at.desc()).limit(limit).all()
        return jsonify({"success": True, "total": len(records), "data": [r.to_dict() for r in records]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@question_bp.route("/health", methods=["GET"])
def health():
    """GET /api/health - Health check endpoint."""
    return jsonify({"success": True, "status": "ok", "message": "Generator Soal Latihan API berjalan normal."})
