from datetime import datetime
from app.extensions import db


class Question(db.Model):
    """Model untuk menyimpan soal latihan yang di-generate."""

    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    topic = db.Column(db.String(255), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False, default="medium")
    question_type = db.Column(db.String(50), nullable=False, default="multiple_choice")
    num_questions = db.Column(db.Integer, nullable=False, default=5)
    questions_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "question_type": self.question_type,
            "num_questions": self.num_questions,
            "questions_json": self.questions_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Question id={self.id} topic={self.topic!r}>"
