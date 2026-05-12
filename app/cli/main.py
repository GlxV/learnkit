from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.core.models.flashcard import Flashcard
from app.core.models.question import Question
from app.core.prompt.prompt_builder import PromptOptions
from app.core.services.backup_service import BackupService
from app.core.services.block_service import BlockService
from app.core.services.module_service import ModuleService
from app.core.services.study_history_service import StudyHistoryService
from app.core.services.study_service import StudyService, StudySession
from app.core.services.subject_service import SubjectService
from app.core.storage.local_storage import LocalStorage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli.main",
        description="CLI temporaria do LearnKit para testar o core.",
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Diretorio local de armazenamento. Padrao: data",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_subject = subparsers.add_parser("create-subject")
    create_subject.add_argument("name")
    create_subject.add_argument("--description")
    create_subject.set_defaults(handler=handle_create_subject)

    list_subjects = subparsers.add_parser("list-subjects")
    list_subjects.set_defaults(handler=handle_list_subjects)

    create_module = subparsers.add_parser("create-module")
    create_module.add_argument("subject")
    create_module.add_argument("name")
    create_module.add_argument("--description")
    create_module.set_defaults(handler=handle_create_module)

    list_modules = subparsers.add_parser("list-modules")
    list_modules.add_argument("subject")
    list_modules.set_defaults(handler=handle_list_modules)

    add_block = subparsers.add_parser("add-block")
    add_block.add_argument("subject")
    add_block.add_argument("module")
    add_block.add_argument("title")
    add_block.add_argument("files", nargs="*")
    add_block.add_argument("--description")
    add_block.set_defaults(handler=handle_add_block)

    list_blocks = subparsers.add_parser("list-blocks")
    list_blocks.add_argument("subject")
    list_blocks.add_argument("module")
    list_blocks.set_defaults(handler=handle_list_blocks)

    export_text = subparsers.add_parser("export-text")
    export_text.add_argument("subject")
    export_text.add_argument("module")
    export_text.add_argument("block")
    export_text.add_argument("--format", choices=["md", "txt"], default="md")
    export_text.add_argument("--output")
    export_text.set_defaults(handler=handle_export_text)

    generate_prompt = subparsers.add_parser("generate-prompt")
    generate_prompt.add_argument("subject")
    generate_prompt.add_argument("module")
    generate_prompt.add_argument("block")
    generate_prompt.add_argument("--flashcards", type=int, default=10)
    generate_prompt.add_argument("--questions", type=int, default=10)
    generate_prompt.add_argument("--difficulty", default="intermediario")
    generate_prompt.add_argument("--style", default="clara e objetiva")
    generate_prompt.add_argument("--output")
    generate_prompt.set_defaults(handler=handle_generate_prompt)

    import_ai = subparsers.add_parser("import-ai-response")
    import_ai.add_argument("subject")
    import_ai.add_argument("module")
    import_ai.add_argument("block")
    import_ai.add_argument("response_file")
    import_ai.set_defaults(handler=handle_import_ai_response)

    show_summary = subparsers.add_parser("show-summary")
    show_summary.add_argument("subject")
    show_summary.add_argument("module")
    show_summary.add_argument("block")
    show_summary.set_defaults(handler=handle_show_summary)

    list_flashcards = subparsers.add_parser("list-flashcards")
    list_flashcards.add_argument("subject")
    list_flashcards.add_argument("module")
    list_flashcards.add_argument("block")
    list_flashcards.set_defaults(handler=handle_list_flashcards)

    list_questions = subparsers.add_parser("list-questions")
    list_questions.add_argument("subject")
    list_questions.add_argument("module")
    list_questions.add_argument("block")
    list_questions.set_defaults(handler=handle_list_questions)

    module_summaries = subparsers.add_parser("show-module-summaries")
    module_summaries.add_argument("subject")
    module_summaries.add_argument("module")
    module_summaries.set_defaults(handler=handle_show_module_summaries)

    module_flashcards = subparsers.add_parser("list-module-flashcards")
    module_flashcards.add_argument("subject")
    module_flashcards.add_argument("module")
    module_flashcards.set_defaults(handler=handle_list_module_flashcards)

    module_questions = subparsers.add_parser("list-module-questions")
    module_questions.add_argument("subject")
    module_questions.add_argument("module")
    module_questions.set_defaults(handler=handle_list_module_questions)

    subject_summaries = subparsers.add_parser("show-subject-summaries")
    subject_summaries.add_argument("subject")
    subject_summaries.set_defaults(handler=handle_show_subject_summaries)

    subject_flashcards = subparsers.add_parser("list-subject-flashcards")
    subject_flashcards.add_argument("subject")
    subject_flashcards.set_defaults(handler=handle_list_subject_flashcards)

    subject_questions = subparsers.add_parser("list-subject-questions")
    subject_questions.add_argument("subject")
    subject_questions.set_defaults(handler=handle_list_subject_questions)

    study_block = subparsers.add_parser("study-block")
    study_block.add_argument("subject")
    study_block.add_argument("module")
    study_block.add_argument("block")
    study_block.set_defaults(handler=handle_study_block)

    study_module = subparsers.add_parser("study-module")
    study_module.add_argument("subject")
    study_module.add_argument("module")
    study_module.set_defaults(handler=handle_study_module)

    study_subject = subparsers.add_parser("study-subject")
    study_subject.add_argument("subject")
    study_subject.set_defaults(handler=handle_study_subject)

    export_backup = subparsers.add_parser("export-subject-backup")
    export_backup.add_argument("subject")
    export_backup.add_argument("--output-dir", default="backups")
    export_backup.set_defaults(handler=handle_export_subject_backup)

    record_result = subparsers.add_parser("record-study-result")
    record_result.add_argument("block_id")
    record_result.add_argument("item_type", choices=["flashcard", "question", "summary"])
    record_result.add_argument("item_id")
    record_result.add_argument("result", choices=["correct", "incorrect", "skipped", "neutral"])
    record_result.add_argument("--difficulty")
    record_result.add_argument("--duration-seconds", type=int, default=0)
    record_result.set_defaults(handler=handle_record_study_result)

    study_stats = subparsers.add_parser("study-stats")
    study_stats.add_argument("--block-id")
    study_stats.set_defaults(handler=handle_study_stats)

    return parser


def services(args: argparse.Namespace) -> tuple[SubjectService, ModuleService, BlockService, StudyService]:
    storage = LocalStorage(args.data_dir)
    return (
        SubjectService(storage),
        ModuleService(storage),
        BlockService(storage),
        StudyService(storage),
    )


def handle_create_subject(args: argparse.Namespace) -> None:
    subject_service, _, _, _ = services(args)
    subject = subject_service.create_subject(args.name, args.description)
    print(f"Materia criada: {subject.name} ({subject.slug})")


def handle_list_subjects(args: argparse.Namespace) -> None:
    subject_service, _, _, _ = services(args)
    subjects = subject_service.list_subjects()
    if not subjects:
        print("Nenhuma materia cadastrada.")
        return
    for subject in subjects:
        print(f"- {subject.name} ({subject.slug})")


def handle_create_module(args: argparse.Namespace) -> None:
    _, module_service, _, _ = services(args)
    module = module_service.create_module(args.subject, args.name, args.description)
    print(f"Modulo criado: {module.name} ({module.slug})")


def handle_list_modules(args: argparse.Namespace) -> None:
    _, module_service, _, _ = services(args)
    modules = module_service.list_modules(args.subject)
    if not modules:
        print("Nenhum modulo cadastrado.")
        return
    for module in modules:
        print(f"- {module.name} ({module.slug})")


def handle_add_block(args: argparse.Namespace) -> None:
    _, _, block_service, _ = services(args)
    block = block_service.create_block(
        args.subject,
        args.module,
        args.title,
        file_paths=args.files,
        description=args.description,
    )
    failures = [item for item in block.imported_files if item.extraction_status == "failed"]
    print(f"Bloco criado: {block.title} ({block.slug})")
    print(f"Arquivos importados: {len(block.imported_files)}")
    print(f"Caracteres extraidos: {block.extracted_content.character_count}")
    if failures:
        print("Avisos de extracao:")
        for item in failures:
            print(f"- {item.file_name}: {item.error_message}")


def handle_list_blocks(args: argparse.Namespace) -> None:
    _, _, block_service, _ = services(args)
    blocks = block_service.list_blocks(args.subject, args.module)
    if not blocks:
        print("Nenhum bloco cadastrado.")
        return
    for block in blocks:
        print(f"- {block.title} ({block.slug})")


def handle_export_text(args: argparse.Namespace) -> None:
    _, _, block_service, _ = services(args)
    path = block_service.export_text(
        args.subject,
        args.module,
        args.block,
        output_path=args.output,
        file_format=args.format,
    )
    print(f"Texto exportado em: {path}")


def handle_generate_prompt(args: argparse.Namespace) -> None:
    _, _, block_service, _ = services(args)
    prompt = block_service.generate_prompt(
        args.subject,
        args.module,
        args.block,
        options=PromptOptions(
            flashcard_count=args.flashcards,
            question_count=args.questions,
            difficulty=args.difficulty,
            language_style=args.style,
        ),
    )
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(prompt, encoding="utf-8")
        print(f"Prompt salvo em: {path}")
    else:
        print(prompt)


def handle_import_ai_response(args: argparse.Namespace) -> None:
    _, _, block_service, _ = services(args)
    block = block_service.import_ai_response_file(
        args.subject,
        args.module,
        args.block,
        args.response_file,
    )
    warnings = block.ai_response.parser_warnings if block.ai_response else []
    print(f"Resposta importada para o bloco: {block.title}")
    print(f"Resumo: {'sim' if block.summary else 'nao'}")
    print(f"Flashcards: {len(block.flashcards)}")
    print(f"Perguntas: {len(block.questions)}")
    if warnings:
        print("Avisos do parser:")
        for warning in warnings:
            print(f"- {warning}")


def handle_show_summary(args: argparse.Namespace) -> None:
    _, _, block_service, _ = services(args)
    summary = block_service.show_summary(args.subject, args.module, args.block)
    print(summary.content if summary else "Este bloco ainda nao possui resumo.")


def handle_list_flashcards(args: argparse.Namespace) -> None:
    _, _, block_service, _ = services(args)
    print_flashcards(block_service.list_flashcards(args.subject, args.module, args.block))


def handle_list_questions(args: argparse.Namespace) -> None:
    _, _, block_service, _ = services(args)
    print_questions(block_service.list_questions(args.subject, args.module, args.block))


def handle_show_module_summaries(args: argparse.Namespace) -> None:
    _, _, _, study_service = services(args)
    summaries = study_service.list_module_summaries(args.subject, args.module)
    print_summaries(summaries)


def handle_list_module_flashcards(args: argparse.Namespace) -> None:
    _, _, _, study_service = services(args)
    print_flashcards(study_service.list_module_flashcards(args.subject, args.module))


def handle_list_module_questions(args: argparse.Namespace) -> None:
    _, _, _, study_service = services(args)
    print_questions(study_service.list_module_questions(args.subject, args.module))


def handle_show_subject_summaries(args: argparse.Namespace) -> None:
    _, _, _, study_service = services(args)
    print_summaries(study_service.list_subject_summaries(args.subject))


def handle_list_subject_flashcards(args: argparse.Namespace) -> None:
    _, _, _, study_service = services(args)
    print_flashcards(study_service.list_subject_flashcards(args.subject))


def handle_list_subject_questions(args: argparse.Namespace) -> None:
    _, _, _, study_service = services(args)
    print_questions(study_service.list_subject_questions(args.subject))


def handle_study_block(args: argparse.Namespace) -> None:
    _, _, _, study_service = services(args)
    print_study_session(study_service.study_block(args.subject, args.module, args.block))


def handle_study_module(args: argparse.Namespace) -> None:
    _, _, _, study_service = services(args)
    print_study_session(study_service.study_module(args.subject, args.module))


def handle_study_subject(args: argparse.Namespace) -> None:
    _, _, _, study_service = services(args)
    print_study_session(study_service.study_subject(args.subject))


def handle_export_subject_backup(args: argparse.Namespace) -> None:
    storage = LocalStorage(args.data_dir)
    path = BackupService(storage).export_subject(args.subject, args.output_dir)
    print(f"Backup exportado em: {path}")


def handle_record_study_result(args: argparse.Namespace) -> None:
    storage = LocalStorage(args.data_dir)
    record = StudyHistoryService(storage).record_result(
        block_id=args.block_id,
        item_type=args.item_type,
        item_id=args.item_id,
        result=args.result,
        difficulty=args.difficulty,
        duration_seconds=args.duration_seconds,
    )
    print(f"Resultado registrado: {record.result} ({record.item_type}:{record.item_id})")


def handle_study_stats(args: argparse.Namespace) -> None:
    storage = LocalStorage(args.data_dir)
    stats = StudyHistoryService(storage).get_stats(args.block_id)
    print(f"Revisoes: {stats.total_reviews}")
    print(f"Acertos: {stats.correct}")
    print(f"Erros: {stats.incorrect}")
    print(f"Pulados: {stats.skipped}")
    print(f"Precisao: {stats.accuracy:.0%}")
    print(f"Tempo total: {stats.total_duration_seconds}s")


def print_summaries(summaries: list[object]) -> None:
    if not summaries:
        print("Nenhum resumo encontrado.")
        return
    for index, summary in enumerate(summaries, start=1):
        print(f"\n# Resumo {index}\n")
        print(summary.content)


def print_flashcards(flashcards: list[Flashcard]) -> None:
    if not flashcards:
        print("Nenhum flashcard encontrado.")
        return
    for index, card in enumerate(flashcards, start=1):
        print(f"\nCard {index}")
        print(f"Pergunta: {card.question}")
        print(f"Resposta: {card.answer}")


def print_questions(questions: list[Question]) -> None:
    if not questions:
        print("Nenhuma pergunta encontrada.")
        return
    for index, question in enumerate(questions, start=1):
        print(f"\nPergunta {index}")
        print(f"Enunciado: {question.statement}")
        for letter in ("A", "B", "C", "D"):
            if letter in question.alternatives:
                print(f"{letter}) {question.alternatives[letter]}")
        print(f"Gabarito: {question.correct_answer}")
        if question.explanation:
            print(f"Explicacao: {question.explanation}")


def print_study_session(session: StudySession) -> None:
    print(f"# Estudo: {session.title}")
    print(f"Escopo: {session.scope}")
    print_summaries(session.summaries)
    print("\n# Flashcards")
    print_flashcards(session.flashcards)
    print("\n# Perguntas")
    print_questions(session.questions)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.handler(args)
        return 0
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
