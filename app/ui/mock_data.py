from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from app.core.services.progress_service import ProgressService
from app.core.storage.local_storage import LocalStorage
from app.ui.icon_catalog import subject_icon_for_name


@dataclass(slots=True)
class UIBlock:
    title: str
    progress: int
    flashcards: int
    questions: int
    summary: str
    id: str | None = None
    subject_name: str = ""
    module_name: str = ""


@dataclass(slots=True)
class UIModule:
    name: str
    progress: int
    blocks: list[UIBlock] = field(default_factory=list)
    id: str | None = None
    slug: str = ""


@dataclass(slots=True)
class UISubject:
    name: str
    description: str
    progress: int
    color: str
    icon: str
    modules: list[UIModule] = field(default_factory=list)
    id: str | None = None
    slug: str = ""


def demo_subjects() -> list[UISubject]:
    math_blocks = [
        UIBlock("Funcoes do 1o grau", 68, 24, 36, "Relacoes lineares, coeficientes e graficos."),
        UIBlock("Funcoes do 2o grau", 42, 18, 28, "Parabolas, raizes e vertice."),
        UIBlock("Logaritmos", 31, 15, 24, "Definicao, propriedades e aplicacoes."),
        UIBlock("Trigonometria", 55, 21, 32, "Seno, cosseno, tangente e ciclo trigonometrico."),
        UIBlock("Estatistica", 74, 20, 30, "Media, mediana, moda e interpretacao de dados."),
        UIBlock("Sistemas Lineares", 48, 16, 26, "Metodos de resolucao e interpretacao."),
        UIBlock("Equacoes e Inequacoes", 63, 19, 31, "Manipulacao algebrica e intervalos."),
    ]
    return [
        UISubject(
            "Matematica",
            "Modulos personalizados para provas, trimestres e revisao.",
            62,
            "#3B82F6",
            "calculator",
            [
                UIModule("1o Trimestre", 61, math_blocks[:5]),
                UIModule("2o Trimestre", 28, math_blocks[5:]),
                UIModule("Prova 1", 72, math_blocks[:3]),
                UIModule("Recuperacao", 35, math_blocks[2:5]),
                UIModule("Extras", 18, math_blocks[4:]),
            ],
        ),
        UISubject("Fisica", "Cinematica, dinamica e energia.", 44, "#2563EB", "atom", []),
        UISubject("Quimica", "Estequiometria, ligacoes e solucoes.", 38, "#16A34A", "flask", []),
        UISubject("Historia", "Linha do tempo, eventos e revisoes.", 57, "#D97706", "landmark", []),
        UISubject("Biologia", "Citologia, genetica e ecologia.", 49, "#8B5CF6", "dna", []),
        UISubject("Lingua Portuguesa", "Literatura, gramatica e interpretacao.", 53, "#EF4444", "book", []),
    ]


class UIDataProvider:
    """Adapts core storage data for the PySide UI.

    Demo data is available only when LEARNKIT_DEMO=1. In normal runs, an empty
    workspace stays empty so the UI does not invent progress or content.
    """

    def __init__(self, storage: LocalStorage | None = None) -> None:
        self.storage = storage or LocalStorage("data")
        self.meta_path = self.storage.base_path / "ui_subject_meta.json"

    def subjects(self) -> list[UISubject]:
        real_subjects = self.storage.list_subjects()
        if not real_subjects:
            return demo_subjects() if os.getenv("LEARNKIT_DEMO") == "1" else []

        metadata = self._load_metadata()
        progress_service = ProgressService(self.storage)
        palette = ["#3B82F6", "#7C3AED", "#22C55E", "#F59E0B", "#8B5CF6", "#EF4444"]
        mapped: list[UISubject] = []

        for index, subject in enumerate(real_subjects):
            meta = metadata.get(subject.slug, {})
            modules: list[UIModule] = []
            subject_work_total = 0
            subject_work_done = 0

            for module in self.storage.list_modules(subject.slug):
                mapped_blocks: list[UIBlock] = []
                module_work_total = 0
                module_work_done = 0

                for block in self.storage.list_blocks(subject.slug, module.slug):
                    progress = progress_service.get_block_progress(block.id)
                    work_total = progress.flashcards_total + progress.questions_total
                    work_done = progress.flashcards_reviewed + progress.questions_answered
                    percent = int((work_done / work_total) * 100) if work_total else 0
                    module_work_total += work_total
                    module_work_done += work_done
                    mapped_blocks.append(
                        UIBlock(
                            title=block.title,
                            progress=percent,
                            flashcards=len(block.flashcards),
                            questions=len(block.questions),
                            summary=(
                                block.summary.content.strip().splitlines()[0][:120]
                                if block.summary and block.summary.content.strip()
                                else "Resumo ainda nao importado."
                            ),
                            id=block.id,
                            subject_name=subject.name,
                            module_name=module.name,
                        )
                    )

                subject_work_total += module_work_total
                subject_work_done += module_work_done
                module_percent = int((module_work_done / module_work_total) * 100) if module_work_total else 0
                modules.append(UIModule(module.name, module_percent, mapped_blocks, id=module.id, slug=module.slug))

            subject_percent = int((subject_work_done / subject_work_total) * 100) if subject_work_total else 0
            mapped.append(
                UISubject(
                    name=subject.name,
                    description=subject.description or "Organize seus estudos em modulos e blocos personalizados.",
                    progress=subject_percent,
                    color=str(subject.color or meta.get("color", palette[index % len(palette)])),
                    icon=subject_icon_for_name(
                        subject.name,
                        str(subject.icon or meta.get("icon", "")),
                    ),
                    modules=modules,
                    id=subject.id,
                    slug=subject.slug,
                )
            )
        return mapped

    def all_blocks(self) -> list[UIBlock]:
        return [block for subject in self.subjects() for module in subject.modules for block in module.blocks]

    def global_stats(self):
        return ProgressService(self.storage).get_global_stats()

    def create_subject(
        self,
        name: str,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
        initial_modules: list[str] | None = None,
    ) -> None:
        from app.core.services.module_service import ModuleService
        from app.core.services.subject_service import SubjectService

        subject = SubjectService(self.storage).create_subject(name, description, icon=icon, color=color)
        if color or icon:
            metadata = self._load_metadata()
            metadata[subject.slug] = {
                "color": color or "#3B82F6",
                "icon": icon or "book",
            }
            self._save_metadata(metadata)
        module_service = ModuleService(self.storage)
        for module_name in initial_modules or []:
            module_service.create_module(subject.slug, module_name)

    def update_subject(
        self,
        subject_ref: str,
        name: str,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
    ) -> None:
        from app.core.services.subject_service import SubjectService

        subject = SubjectService(self.storage).update_subject(
            subject_ref,
            name,
            description,
            icon=icon,
            color=color,
        )
        metadata = self._load_metadata()
        metadata[subject.slug] = {
            "color": color or subject.color or "#3B82F6",
            "icon": icon or subject.icon or "book",
        }
        self._save_metadata(metadata)

    def create_module(self, subject_name: str, module_name: str, description: str | None = None) -> None:
        from app.core.services.module_service import ModuleService
        from app.core.services.subject_service import SubjectService

        try:
            self.storage.get_subject(subject_name)
        except ValueError:
            SubjectService(self.storage).create_subject(subject_name)
        ModuleService(self.storage).create_module(subject_name, module_name, description)

    def _load_metadata(self) -> dict[str, dict[str, str]]:
        if not self.meta_path.exists():
            return {}
        data = json.loads(self.meta_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

    def _save_metadata(self, metadata: dict[str, dict[str, str]]) -> None:
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
