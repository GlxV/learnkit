from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.study_package import StudyPackageDTO


@dataclass(frozen=True, slots=True)
class ValidationIssueDTO:
    severity: str
    message: str


@dataclass(slots=True)
class StudyPackageValidationDTO:
    package: StudyPackageDTO
    usable_package: StudyPackageDTO
    summary_found: bool
    visual_valid: bool
    flashcards_total: int
    flashcards_valid: int
    questions_total: int
    questions_valid: int
    issues: list[ValidationIssueDTO]

    @property
    def fatal_issues(self) -> list[ValidationIssueDTO]:
        return [issue for issue in self.issues if issue.severity == "fatal"]

    @property
    def warning_issues(self) -> list[ValidationIssueDTO]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def info_issues(self) -> list[ValidationIssueDTO]:
        return [issue for issue in self.issues if issue.severity == "info"]

    @property
    def can_save(self) -> bool:
        return not self.fatal_issues
