from __future__ import annotations

import asyncio
import hashlib
import re
import shutil
import tempfile
from pathlib import Path
from typing import Protocol


class SupportsOcr(Protocol):
    available: bool

    def extract_image_bytes(self, image_bytes: bytes, suffix: str = ".png") -> str:
        ...

    def extract_image_file(self, image_path: str | Path) -> str:
        ...


class OcrExtractor:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.backend_name = ""
        self.unavailable_reason = ""
        self._available: bool | None = None
        self._cache: dict[str, str] = {}

    @property
    def available(self) -> bool:
        if self._available is None:
            self._available = self._detect_backend()
        return self._available

    def extract_image_bytes(self, image_bytes: bytes, suffix: str = ".png") -> str:
        if not self.available:
            return ""
        digest = hashlib.sha256(image_bytes).hexdigest()
        if digest in self._cache:
            return self._cache[digest]
        suffix = suffix if suffix.startswith(".") else f".{suffix}"
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / f"image{suffix}"
            image_path.write_bytes(image_bytes)
            text = self.extract_image_file(image_path)
        self._cache[digest] = text
        return text

    def extract_image_file(self, image_path: str | Path) -> str:
        if not self.available:
            return ""
        prepared_path: Path | None = None
        try:
            prepared_path = self._prepare_image(Path(image_path))
            if self.backend_name == "windows":
                return self._clean_ocr_text(self._run_async(self._windows_ocr(prepared_path))).strip()
            if self.backend_name == "tesseract":
                return self._clean_ocr_text(self._tesseract_ocr(prepared_path)).strip()
        except Exception as exc:
            self.unavailable_reason = f"OCR falhou: {exc}"
            return ""
        finally:
            if prepared_path and prepared_path.exists() and prepared_path.parent.name.startswith("learnkit_ocr_"):
                shutil.rmtree(prepared_path.parent, ignore_errors=True)
        return ""

    def _clean_ocr_text(self, text: str) -> str:
        text = text.replace("\x00", "")
        text = re.sub(r"q[äaå][o0qQ]\b", "ção", text, flags=re.IGNORECASE)
        text = re.sub(r"[Gg][äaå][o0]\b", "ção", text)
        text = re.sub(r"q[öoõ][eE]s\b", "ções", text, flags=re.IGNORECASE)
        text = re.sub(r"#[o0]\b", "ção", text, flags=re.IGNORECASE)
        text = re.sub(r"ä[o0]\b", "ão", text, flags=re.IGNORECASE)
        text = re.sub(r"öes\b", "ões", text, flags=re.IGNORECASE)
        text = text.replace("å", "á").replace("Å", "Á")
        text = text.replace("Ä", "A")
        text = re.sub(r"\bn[äáö6]s\b", "nós", text, flags=re.IGNORECASE)
        text = text.replace("NÖ", "NÓ").replace("Nö", "Nó")
        text = text.replace("diferenqa", "diferença").replace("Diferenqa", "Diferença")
        text = text.replace("informa;äo", "informação")
        text = text.replace("p.ßgrama", "programa").replace("pßgrama", "programa")
        text = text.replace("ucgrama", "programa").replace("uograma", "programa")
        text = text.replace("upgrama", "programa")
        text = re.sub(r"\b[UuLl]nguagem\b", "linguagem", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _detect_backend(self) -> bool:
        if not self.enabled:
            self.unavailable_reason = "OCR desativado."
            return False

        try:
            from winrt.windows.media.ocr import OcrEngine

            engine = OcrEngine.try_create_from_user_profile_languages()
            if engine is None:
                languages = OcrEngine.available_recognizer_languages
                if len(languages):
                    engine = OcrEngine.try_create_from_language(languages[0])
            if engine is not None:
                self.backend_name = "windows"
                return True
        except Exception as exc:
            self.unavailable_reason = f"OCR local do Windows indisponivel: {exc}"

        try:
            import pytesseract  # type: ignore[import-not-found]

            if shutil.which("tesseract"):
                _ = pytesseract
                self.backend_name = "tesseract"
                return True
            self.unavailable_reason = "Tesseract nao encontrado no PATH."
        except Exception as exc:
            if not self.unavailable_reason:
                self.unavailable_reason = f"OCR indisponivel: {exc}"

        return False

    async def _windows_ocr(self, image_path: Path) -> str:
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.storage import FileAccessMode, StorageFile

        file = await StorageFile.get_file_from_path_async(str(image_path.resolve()))
        stream = await file.open_async(FileAccessMode.READ)
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            languages = OcrEngine.available_recognizer_languages
            if len(languages):
                engine = OcrEngine.try_create_from_language(languages[0])
        if engine is None:
            raise RuntimeError("Nenhum idioma OCR local disponivel.")
        result = await engine.recognize_async(bitmap)
        return result.text or ""

    def _tesseract_ocr(self, image_path: Path) -> str:
        import pytesseract  # type: ignore[import-not-found]

        return str(pytesseract.image_to_string(str(image_path), lang="por+eng"))

    def _prepare_image(self, image_path: Path) -> Path:
        from PIL import Image, ImageEnhance, ImageOps

        image = Image.open(image_path).convert("RGB")
        image = ImageOps.grayscale(image)
        image = ImageEnhance.Contrast(image).enhance(1.55)

        width, height = image.size
        max_side = max(width, height)
        scale = 1.0
        if max_side < 1400:
            scale = min(3.0, 1400 / max_side)
        elif max_side > 2600:
            scale = 2600 / max_side
        if scale != 1.0:
            image = image.resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                Image.Resampling.LANCZOS,
            )

        tmp_dir = Path(tempfile.mkdtemp(prefix="learnkit_ocr_"))
        output = tmp_dir / "prepared.png"
        image.save(output)
        return output

    def _run_async(self, coroutine) -> str:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return str(asyncio.run(coroutine))

        result: dict[str, str] = {}
        error: dict[str, BaseException] = {}

        def runner() -> None:
            try:
                result["text"] = str(asyncio.run(coroutine))
            except BaseException as exc:
                error["error"] = exc

        import threading

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()
        thread.join()
        if error:
            raise error["error"]
        return result.get("text", "")
