from validators.source_validator import validate_source_grounding
from pathlib import Path

from crewai import Task
from crewai.project import load_crew

from validators.journal_revision import (
    build_revision_instructions,
)
from validators.journal_validator import validate_journal


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
DRAFT_FILE = OUTPUTS / "draft_journal.md"
FINAL_FILE = OUTPUTS / "generated_journal.md"
REPORT_FILE = OUTPUTS / "validation_report.md"

MAX_REVISION_ATTEMPTS = 2


def output_text(value):
    """Extract readable text from CrewAI task results."""
    return str(getattr(value, "raw", value) or "").strip()


def main():
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    # Remove any old draft so a failed run cannot reuse it.
    if DRAFT_FILE.exists():
        DRAFT_FILE.unlink()
        
        crew, inputs = load_crew(ROOT / "crew.jsonc")

    print("Running the existing RJ Assist crew...")
    crew.kickoff(inputs=inputs)

    if not DRAFT_FILE.exists():
        raise FileNotFoundError(
            f"Writer draft was not created: {DRAFT_FILE}"
        )

    journal = DRAFT_FILE.read_text(encoding="utf-8-sig").strip()

    writer = next(
        agent
        for agent in crew.agents
        if agent.role == "Reflective Journal Writer"
    )
    
    analyst_output = output_text(crew.tasks[0].output)

    reviewer = next(
        agent
        for agent in crew.agents
        if agent.role == "Journal Quality Reviewer"
    )

    reviewer_output = output_text(crew.tasks[2].output)

    for attempt in range(MAX_REVISION_ATTEMPTS + 1):
        structure = validate_journal(journal)
        grounding = validate_source_grounding(
            inputs.get("academic_material", ""),
            journal,
        )

        errors = list(structure["errors"])
        errors.extend(grounding["errors"])

        reviewer_passed = reviewer_output.startswith(
            "VERDICT: PASS"
        )

        print(
            f"\nValidation attempt {attempt}: "
            f"{structure['total_words']} words"
        )
        print("Structural validation:", structure["valid"])
        print("Source grounding:", grounding["valid"])
        print("Reviewer verdict:", reviewer_output.splitlines()[0]
              if reviewer_output else "Missing verdict")

        if (
            structure["valid"]
            and grounding["valid"]
            and reviewer_passed
        ):
            FINAL_FILE.write_text(
                journal + "\n",
                encoding="utf-8",
            )
            REPORT_FILE.write_text(
                "VERDICT: PASS\n"
                f"Total words: {structure['total_words']}\n"
                "Structural validation: PASS\n"
                "Source grounding: PASS\n"
                f"Revision attempts: {attempt}\n\n"
                f"Reviewer report:\n{reviewer_output}\n",
                encoding="utf-8",
            )
            print(f"\nFinal journal saved: {FINAL_FILE}")
            print(f"Validation report saved: {REPORT_FILE}")
            return

        if attempt == MAX_REVISION_ATTEMPTS:
            break

        # Give the Writer every deterministic validation error.
        feedback_result = {
            **structure,
            "errors": errors or [
                "The quality reviewer did not approve the journal."
            ],
        }
        feedback = build_revision_instructions(
            journal,
            feedback_result,
        )

        if reviewer_output:
            feedback += (
                "\n\nReviewer findings:\n"
                + reviewer_output
            )

        revision_task = Task(
            description=(
                "Revise the journal to correct every reported issue.\n"
                "Treat the supplied academic material as the source "
                "of truth. Do not add unsupported topics or invent "
                "personal experiences.\n\n"
                f"Subject: {inputs.get('subject', '')}\n"
                f"Week: {inputs.get('week', '')}\n\n"
                f"Academic material:\n"
                f"{inputs.get('academic_material', '')}\n\n"
                f"Analyst evidence:\n{analyst_output}\n\n"
                f"Student reflection:\n"
                f"{inputs.get('student_reflection', '')}\n\n"
                f"Revision instructions:\n{feedback}\n\n"
                "Return only the complete revised journal."
            ),
            expected_output=(
                "A complete five-section journal, 200–400 words "
                "total, with at least 50 words per section, grounded "
                "in the supplied academic material."
            ),
            agent=writer,
        )

        print(f"Requesting Writer revision {attempt + 1}...")
        revised_output = writer.execute_task(revision_task)
        journal = output_text(revised_output)

        if not journal:
            print("Writer returned empty text; stopping revisions.")
            break

        # Ask the existing Reviewer to assess the revised version.
        review_task = Task(
            description=(
                "Review this revised journal against the source.\n"
                "Check topic alignment, unsupported academic claims, "
                "fabricated personal experiences, all five required "
                "sections, section word counts, total word count, "
                "conceptual learning, and practical application.\n"
                "Return VERDICT: PASS only if the journal meets "
                "the requirements. Otherwise return VERDICT: FAIL "
                "and concise reasons.\n\n"
                f"Subject: {inputs.get('subject', '')}\n"
                f"Week: {inputs.get('week', '')}\n"
                f"Academic source:\n"
                f"{inputs.get('academic_material', '')}\n\n"
                f"Student reflection:\n"
                f"{inputs.get('student_reflection', '')}\n\n"
                f"Revised journal:\n{journal}"
            ),
            expected_output=(
                "First line exactly VERDICT: PASS or VERDICT: FAIL, "
                "followed by concise reasons."
            ),
            agent=reviewer,
        )

        reviewer_output = output_text(
            reviewer.execute_task(review_task)
        )


    final_result = validate_journal(journal)

    REPORT_FILE.write_text(
        "VERDICT: FAIL\n"
        "The journal did not pass all required checks.\n"
        f"Total words: {final_result['total_words']}\n"
        f"Errors: {final_result['errors']}\n"
        f"Revision attempts: {MAX_REVISION_ATTEMPTS}\n",
        encoding="utf-8",
    )

    # Keep the rejected output separate; do not replace the final journal.
    (OUTPUTS / "journal_needing_revision.md").write_text(
        journal + "\n",
        encoding="utf-8",
    )

    print("\nThe journal still needs revision.")
    print("See outputs/validation_report.md for the errors.")
    print("The rejected draft is saved separately.")


if __name__ == "__main__":
    main()
