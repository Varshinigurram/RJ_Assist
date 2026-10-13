
from pathlib import Path

from validators.journal_validator import validate_journal


MAX_REVISION_ATTEMPTS = 2


def build_revision_instructions(journal, validation_result):
    """Build precise revision instructions from Python validation errors."""
    errors = validation_result["errors"]

    instructions = [
        "Revise the journal below to satisfy the validation requirements.",
        "Preserve the five required sections in this exact order:",
        "Experience, Feelings, Learning, Application, Conclusion.",
        "Keep at least 50 words in every section and 200–400 words overall.",
        "Preserve source-supported academic content and module-specific applications.",
        "Do not invent student emotions or personal experiences.",
        "Return only the complete revised journal.",
        "",
        "Validation errors:",
    ]

    instructions.extend(f"- {error}" for error in errors)
    instructions.extend(["", "Current journal:", journal])

    return "\n".join(instructions)


def validate_with_revision(
    journal,
    revision_function,
    max_attempts=MAX_REVISION_ATTEMPTS,
):
    """
    Validate a journal and request bounded revisions when necessary.

    revision_function receives the current journal and validation feedback.
    It must return the revised journal as a string.
    """
    current_journal = journal

    for attempt in range(max_attempts + 1):
        result = validate_journal(current_journal)

        if result["valid"]:
            return {
                "valid": True,
                "journal": current_journal,
                "validation": result,
                "revision_attempts": attempt,
            }

        if attempt == max_attempts:
            break

        feedback = build_revision_instructions(
            current_journal,
            result,
        )

        revised = revision_function(current_journal, feedback)

        if not isinstance(revised, str) or not revised.strip():
            return {
                "valid": False,
                "journal": current_journal,
                "validation": result,
                "revision_attempts": attempt + 1,
                "error": "Revision function returned empty or invalid text.",
            }

        current_journal = revised.strip()

    final_result = validate_journal(current_journal)

    return {
        "valid": final_result["valid"],
        "journal": current_journal,
        "validation": final_result,
        "revision_attempts": max_attempts,
    }


if __name__ == "__main__":
    journal_path = Path("outputs/generated_journal.md")

    if not journal_path.exists():
        raise FileNotFoundError(
            f"Journal not found: {journal_path}"
        )

    journal = journal_path.read_text(encoding="utf-8")
    result = validate_journal(journal)

    print("Initial validation:", result)

    if result["valid"]:
        print("The journal already satisfies the hard constraints.")
    else:
        print(
            "Revision is required. The revision function must be "
            "connected to the Writer before automatic revision can run."
        )
