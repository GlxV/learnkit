from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.core.storage.local_storage import LocalStorage


class BackupService:
    def __init__(self, storage: LocalStorage) -> None:
        self.storage = storage

    def export_subject(self, subject_ref: str, output_dir: str | Path) -> Path:
        subject = self.storage.get_subject(subject_ref)
        source_dir = self.storage.subject_path(subject.slug)
        destination_dir = Path(output_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        archive_path = destination_dir / f"{subject.slug}_backup.zip"

        with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
            for file_path in sorted(source_dir.rglob("*")):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(source_dir.parent))

        return archive_path

    def export_all_data(self, output_dir: str | Path) -> Path:
        destination_dir = Path(output_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        archive_path = destination_dir / "learnkit_data_backup.zip"

        with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
            for file_path in sorted(self.storage.base_path.rglob("*")):
                if file_path.is_file() and file_path != archive_path:
                    archive.write(file_path, file_path.relative_to(self.storage.base_path))

        return archive_path
