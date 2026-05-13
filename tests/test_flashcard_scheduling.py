from pathlib import Path

from app.core.database import SQLiteStorage
from app.core.models.flashcard import Flashcard
from app.core.services.progress_service import ProgressService


def _create_block_with_cards(tmp_path: Path):
    storage = SQLiteStorage(tmp_path / "learnkit.db")
    subject = storage.create_subject("Matemática")
    module = storage.create_module(subject.slug, "Revisão")
    block = storage.create_block(subject.slug, module.slug, "Funções")
    block.flashcards = [
        Flashcard("Novo card", "Resposta"),
        Flashcard("Card dominado", "Resposta"),
        Flashcard("Card para repetir", "Resposta"),
    ]
    storage.save_block(subject, module, block)
    return storage, block


def test_flashcard_rating_creates_anki_like_review_state(tmp_path: Path) -> None:
    storage, block = _create_block_with_cards(tmp_path)
    service = ProgressService(storage)
    card = block.flashcards[1]

    progress = service.record_flashcard(block.id, card.id, "easy")
    review = progress.flashcard_reviews[card.id]

    assert progress.reviewed_flashcards[card.id] == "easy"
    assert review["status"] == "easy"
    assert review["times_reviewed"] == 1
    assert review["interval_days"] >= 4
    assert review["ease_factor"] > 2.5
    assert review["due_at"] > review["last_reviewed_at"]


def test_flashcard_schedule_persists_in_sqlite(tmp_path: Path) -> None:
    storage, block = _create_block_with_cards(tmp_path)
    service = ProgressService(storage)
    card = block.flashcards[2]

    service.record_flashcard(block.id, card.id, "again")
    reopened = SQLiteStorage(tmp_path / "learnkit.db")
    progress = ProgressService(reopened).get_block_progress(block.id)

    assert progress.flashcard_reviews[card.id]["status"] == "again"
    assert progress.flashcard_reviews[card.id]["interval_days"] == 0
    assert progress.flashcards_again == 1


def test_flashcard_queue_orders_due_new_and_future_cards(tmp_path: Path) -> None:
    storage, block = _create_block_with_cards(tmp_path)
    service = ProgressService(storage)
    new_card, future_card, due_card = block.flashcards

    service.record_flashcard(block.id, future_card.id, "easy")
    service.record_flashcard(block.id, due_card.id, "again")

    queue = service.get_flashcard_queue(block.id)

    assert [item["card_id"] for item in queue] == [due_card.id, new_card.id, future_card.id]
    assert queue[0]["state"] == "due"
    assert queue[1]["state"] == "new"
    assert queue[2]["state"] == "future"
