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
    
    if DRAFT_FILE.exists():
        DRAFT_FILE.unlink()

# Load the existing three-agent crew and its configured inputs.
    # Load the existing three-agent crew and its configured inputs.
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

    
    reviewer_output = output_text(crew.tasks[2].output)

    for attempt in range(MAX_REVISION_ATTEMPTS + 1):
        resulanalyst_output = output_text(crew.tasks[0].output) = validate_journal(journal)

        reviewer_text = reviewer_output.strip().upper()
        reviewer_passed = reviewer_text.startswith("VERDICT: PASS")
        reviewer_failed = not reviewer_passed

        print(
            f"\nValidation attempt {attempt}: "
            f"{result['total_words']} words"
        )

        if result["valid"] and not reviewer_failed:
            FINAL_FILE.write_text(
                journal + "\n",
                encoding="utf-8",
            )
            REPORT_FILE.write_text(
                "VERDICT: PASS\n"
                f"Total words: {result['total_words']}\n"
                "Structural validation passed.\n"
                f"Revision attempts: {attempt}\n"
                f"Reviewer report:\n{reviewer_output}\n",
                encoding="utf-8",
            )
            print(f"\nFinal journal saved: {FINAL_FILE}")
            print(f"Validation report saved: {REPORT_FILE}")
            return

        if attempt == MAX_REVISION_ATTEMPTS:
            break

        feedback = build_revision_instructions(
            journal,
            result,
        )

        if reviewer_failed:
            feedback += (
                "\n\nReviewer findings to address:\n"
                + reviewer_output
            )

        revision_task = Task(
            description=(
                "Revise the supplied RJ Assist journal.\n\n"
                f"Subject: {inputs.get('subject', '')}\n"
                f"Week: {inputs.get('week', '')}\n"
                "Original academic material:\n"
                f"{inputs.get('academic_material', '')}\n\n"
                "Academic analyst evidence:\n"
                f"{analyst_output}\n\n"
                "College instructions:\n"
                f"{inputs.get('college_instructions', '')}\n\n"
                "Student reflection (may be empty):\n"
                f"{inputs.get('student_reflection', '')}\n\n"
                f"{feedback}\n\n"
                "Do not invent personal experiences or unsupported "
                "academic claims. Return only the revised journal."
            ),
            expected_output=(
                "The complete five-section reflective journal, "
                "with 200–400 words total and at least 50 words "
                "in each section. Return only the journal."
            ),
            agent=writer,
        )

        print(f"Requesting revision {attempt + 1}...")
        revised_output = writer.execute_task(revision_task)

        journal = output_text(revised_output)

        if not journal:
            print("Writer returned empty text; stopping revisions.")
            break

        # Recheck the latest revision rather than trusting the model.
        reviewer_output = ""

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
