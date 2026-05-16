# LearnKit Architecture

This document describes the incremental architecture split introduced after the MVP.

## Layers

- `app/ui`: PySide screens, widgets, navigation, visual feedback and user events.
- `app/application`: use cases, read/query services and DTOs used by the UI.
- `app/domain`: pure LearnKit rules with no storage or UI dependency.
- `app/infrastructure`: SQLite connection, migrations, query helpers and repository foundations.
- `app/core`: existing models and compatibility services kept while the migration is incremental.

## Application Layer

Use cases now wrap the main workflows that were previously called directly from the UI:

- `GeneratePromptUseCase`: builds prompts from extracted content and prompt options.
- `ParseAIResponseUseCase`: parses Markdown responses into a versioned `StudyPackageDTO`; it also accepts the future JSON package shape.
- `ImportStudyPackageUseCase`: creates or updates study packages, including subject/module/block creation, summaries, flashcards, questions and progress sync.
- `ReviewFlashcardUseCase`: records flashcard review actions.
- `AnswerQuestionUseCase`: records question answers.
- `ManageSubjectCatalogUseCase`: owns subject/module/block catalog mutations used by the subjects screen.
- `ManageStudySummaryUseCase`: owns summary text/visual updates and preferred summary mode changes.

Query services provide read models for the UI:

- `UIDataProvider`: maps storage data into `UISubject`, `UIModule` and `UIBlock`.
- `SearchQueryService`: owns global search traversal.
- `ProgressQueryService`: owns progress reads, flashcard queues, question queues, aggregate stats and review dashboard composition.
- `DashboardQueryService`: exposes dashboard and aggregate progress reads.
- `StudySessionQueryService`: exposes block context, summary/session reads, flashcard queues and question queues for study screens.

`UIDataProvider` is intentionally read-oriented. Subject/module/block mutations should go through application use cases, not the provider.

`app/ui/mock_data.py` is now a demo-data compatibility entry point only. New code should import read models from `app.application.query_services.ui_data_provider`.

## Domain Rules

`ReviewScheduler` lives in `app/domain/services/review_scheduler.py`.

It is pure: it receives the current review state plus a rating and returns the next state with status, review count, ease factor, interval and due date. `ProgressService` delegates scheduling to it while keeping persistence command compatibility.

Progress read calculations shared by legacy services and application query services live in `app/core/services/progress_reader.py`. This keeps `app/core` from depending on `app/application` while the compatibility boundary still exists.

## SQLite Infrastructure

`SQLiteStorage` remains the public facade to avoid breaking the current app and tests.

The pieces moved out so far are:

- connection creation: `app/infrastructure/sqlite/connection.py`
- schema and migration runner: `app/infrastructure/sqlite/migrations.py`
- SQLite bootstrap and legacy JSON migration orchestration: `app/infrastructure/sqlite/bootstrap.py`
- dashboard/recent queries: `app/infrastructure/sqlite/queries/dashboard_queries.py`
- search query foundation: `app/infrastructure/sqlite/queries/search_queries.py`
- repositories for subject, module, block and progress SQL plus row-to-domain hydration.
- row-to-domain mapping helpers: `app/infrastructure/sqlite/row_mappers.py`

The database now creates `schema_migrations(version, name, applied_at)` and has a runner that applies migrations in order once.
`SQLiteBootstrap` owns schema creation and one-time JSON-to-SQLite migration orchestration. Legacy progress JSON review columns are applied through versioned migration `1:add_progress_review_json_columns`.

## AI Response Contract

Prompt generation is JSON-first by default. `PromptBuilder` asks for `learnkit.study_package.v1` with `summary_text`, `summary_visual`, `flashcards` and `questions`. Markdown remains supported by setting `PromptOptions(response_format="markdown")`, and `ParseAIResponseUseCase` still accepts the old Markdown section format.

`StudyPackageDTO` is the application contract for parsed packages. Progress query DTOs in `app/application/dto/progress.py` provide typed read models for queues and review dashboards while existing dict-returning methods remain for UI compatibility.

## Current Compatibility Boundaries

- `BlockService` and `ProgressService` still exist for older callers and tests. `ProgressService` now keeps progress writes and delegates legacy read methods to `ProgressReader`.
- `SQLiteStorage` remains the compatibility facade and coordinates repositories plus bootstrap.
- `SQLiteStorage` no longer hydrates subject/module/block/progress rows itself; repositories now expose domain-returning methods while keeping row methods for lower-level tests and future query work.
- UI pages still use provider read models for navigation/filter state, but direct block/session storage reads have moved behind query services.
- Import/review/answer/catalog/summary writes are behind use cases.

## Remaining Follow-Ups

- Convert more UI callers from dict compatibility methods to typed query DTOs.
- Move dashboard/search traversal into optimized infrastructure SQL where dataset size starts to matter.
- Consider splitting slug/path helpers out of `SQLiteStorage` after the facade is no longer needed by legacy callers.
