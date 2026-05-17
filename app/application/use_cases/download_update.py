from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable
from urllib.request import urlopen

from app.application.dto.update_info import DownloadedUpdateDTO, UpdateInfoDTO
from app.infrastructure.update.download_paths import update_download_dir

ProgressCallback = Callable[[int, int | None, int | None], None]


class DownloadUpdateError(RuntimeError):
    pass


class DownloadUpdateUseCase:
    def __init__(
        self,
        download_root: Path | None = None,
        opener: Callable[..., object] | None = None,
        timeout: int = 30,
        chunk_size: int = 64 * 1024,
    ) -> None:
        self.download_root = download_root
        self.opener = opener or urlopen
        self.timeout = timeout
        self.chunk_size = chunk_size

    def execute(
        self,
        update_info: UpdateInfoDTO,
        progress_callback: ProgressCallback | None = None,
    ) -> DownloadedUpdateDTO:
        self._validate_update_info(update_info)
        target_dir = update_download_dir(update_info.latest_version, self.download_root)
        target_dir.mkdir(parents=True, exist_ok=True)
        final_path = target_dir / update_info.asset_name
        temp_path = final_path.with_suffix(final_path.suffix + ".download")
        if temp_path.exists():
            temp_path.unlink()
        if final_path.exists():
            final_path.unlink()

        digest = hashlib.sha256()
        downloaded = 0
        total = None
        try:
            with self.opener(update_info.asset_url, timeout=self.timeout) as response:
                total = self._content_length(response)
                self._emit(progress_callback, 0, total)
                with temp_path.open("wb") as output:
                    while True:
                        chunk = response.read(self.chunk_size)
                        if not chunk:
                            break
                        output.write(chunk)
                        digest.update(chunk)
                        downloaded += len(chunk)
                        self._emit(progress_callback, downloaded, total)
        except Exception as exc:  # noqa: BLE001
            temp_path.unlink(missing_ok=True)
            raise DownloadUpdateError(f"Could not download update: {exc}") from exc

        actual_hash = digest.hexdigest()
        if actual_hash.lower() != update_info.sha256.lower():
            temp_path.unlink(missing_ok=True)
            raise DownloadUpdateError(
                f"SHA-256 mismatch. Expected {update_info.sha256}, got {actual_hash}."
            )

        temp_path.replace(final_path)
        self._emit(progress_callback, downloaded, total)
        return DownloadedUpdateDTO(
            version=update_info.latest_version,
            package_path=final_path,
            asset_name=update_info.asset_name,
            sha256=actual_hash,
            size_bytes=downloaded,
        )

    def _validate_update_info(self, update_info: UpdateInfoDTO) -> None:
        if not update_info.can_auto_update:
            raise DownloadUpdateError("Update is not installable.")
        if not update_info.asset_url:
            raise DownloadUpdateError("Update does not include an asset URL.")
        if not update_info.asset_name:
            raise DownloadUpdateError("Update does not include an asset name.")
        if not update_info.sha256:
            raise DownloadUpdateError("Update does not include SHA-256.")

    def _content_length(self, response: object) -> int | None:
        headers = getattr(response, "headers", None)
        if headers is None:
            return None
        value = headers.get("Content-Length") if hasattr(headers, "get") else None
        try:
            return int(value) if value else None
        except (TypeError, ValueError):
            return None

    def _emit(self, callback: ProgressCallback | None, downloaded: int, total: int | None) -> None:
        if callback is None:
            return
        percent = int(downloaded * 100 / total) if total else None
        callback(downloaded, total, percent)
