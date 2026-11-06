import re

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

# Matches "VERDICT: PASS" as an isolated token at the very start of the text,
# regardless of leading whitespace, Markdown bold markers (**), or trailing
# punctuation.  Does NOT match "VERDICT: PASS WITH CONDITIONS" or similar.
_VERDICT_PASS_RE = re.compile(
    r"^\s*(?:\*{1,2})?\s*VERDICT:\s*PASS\s*(?:\*{1,2})?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Phrases that indicate a moderation or error response rather than a journal.
_MODERATION_PHRASES = (
    "user safety:",
    "content policy",
    "cannot assist",
    "i'm unable",
    "i am unable",
    "as an ai",
)


def is_verdict_pass(text: str) -> bool:
    """Return True only when the first non-empty line is an unambiguous VERDICT: PASS."""
    if not text:
        return False
    first_line = next(
        (ln for ln in text.splitlines() if ln.strip()), ""
    )
    return bool(_VERDICT_PASS_RE.match(first_line))


def is_valid_journal_text(text: str) -> bool:
    """Return False for empty, moderation, or error responses."""
    if not text or not text.strip():
        return False
    lower = text.lower()
    if any(phrase in lower for phrase in _MODERATION_PHRASES):
        return False
    # Require the text to contain at least one of the five section names.
    section_names = ("experience", "feelings", "learning", "application", "conclusion")
    return any(name in lower for name in section_names)


def output_text(value):
    """Extract readable text from CrewAI task results."""
    return str(getattr(value, "raw", value) or "").strip()


def main():
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    # Clear outputs from any previous run so stale files cannot be mistaken
    # for results produced by this run.
    for stale in (DRAFT_FILE, FINAL_FILE, REPORT_FILE):
        if stale.exists():
            stale.unlink()

    crew, inputs = load_crew(ROOT / "crew.jsonc")

    print("Running the existing RJ Assist crew...")
    crew.kickoff(inputs=inputs)

    # Try the on-disk draft first; fall back to the in-memory task output.
    if DRAFT_FILE.exists():
        journal = DRAFT_FILE.read_text(encoding="utf-8-sig").strip()
    else:
        # crew.tasks[1] is the Writer task.  .output is a TaskOutput object;
        # output_text() safely extracts .raw from it.
        in_memory = output_text(crew.tasks[1].output)
        if in_memory:
            journal = in_memory
            print("Note: draft_journal.md not flushed to disk; using in-memory Writer output.")
        else:
            raise FileNotFoundError(
                f"Writer produced no output and {DRAFT_FILE} was not created. "
                "Check the OpenRouter API key and model availability."
            )

    if not is_valid_journal_text(journal):
        raise ValueError(
            f"Writer output looks like a moderation or error response, not a journal.\n"
            f"First 200 chars: {journal[:200]!r}"
        )

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

        reviewer_passed = is_verdict_pass(reviewer_output)

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
                "Treat the supplied academic material as the sole source "
                "of truth. Do not add unsupported topics, Big-O notation, "
                "balanced-tree details, or invent personal experiences.\n\n"
                f"Subject: {inputs.get('subject', '')}\n"
                f"Week: {inputs.get('week', '')}\n\n"
                f"College instructions:\n"
                f"{inputs.get('college_instructions', '')}\n\n"
                f"Journal template:\n"
                f"{inputs.get('journal_template', '')}\n\n"
                f"Academic material:\n"
                f"{inputs.get('academic_material', '')}\n\n"
                f"Analyst evidence:\n{analyst_output}\n\n"
                f"Student reflection:\n"
                f"{inputs.get('student_reflection', '')}\n\n"
                f"Revision instructions:\n{feedback}\n\n"
                "Return only the complete revised journal."
            ),
            expected_output=(
                "A complete five-section journal (Experience, Feelings, "
                "Learning, Application, Conclusion), 200–400 words total "
                "(aiming for approximately 300–320 words), with at least "
                "50 words per section, grounded in the supplied academic material."
            ),
            agent=writer,
        )

        print(f"Requesting Writer revision {attempt + 1}...")
        revised_output = writer.execute_task(revision_task)
        journal = output_text(revised_output)

        if not is_valid_journal_text(journal):
            print(
                "Writer returned empty or invalid text (possibly a moderation "
                "response); stopping revisions."
            )
            # Preserve whatever was returned for debugging.
            if journal:
                (OUTPUTS / "journal_needing_revision.md").write_text(
                    journal + "\n", encoding="utf-8"
                )
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


    # Validate the final journal, including when a revision exits early.
    final_result = validate_journal(journal)

    final_grounding = validate_source_grounding(
        inputs.get("academic_material", ""),
        journal,
    )

    final_reviewer_passed = is_verdict_pass(reviewer_output)

    final_errors = (
        list(final_result["errors"])
        + list(final_grounding["errors"])
    )

    if not final_reviewer_passed:
        final_errors.append(
            "The quality reviewer did not return VERDICT: PASS."
        )

    final_passed = (
        final_result["valid"]
        and final_grounding["valid"]
        and final_reviewer_passed
    )

    if final_passed:
        FINAL_FILE.write_text(
            journal + "\n",
            encoding="utf-8",
        )

        REPORT_FILE.write_text(
            "VERDICT: PASS\n"
            f"Total words: {final_result['total_words']}\n"
            "Structural validation: PASS\n"
            "Source grounding: PASS\n"
            "Reviewer verdict: PASS\n"
            f"Revision attempts: {attempt}\n\n"
            f"Reviewer report:\n{reviewer_output}\n",
            encoding="utf-8",
        )

        print(f"\nFinal journal saved: {FINAL_FILE}")
        print(f"Validation report saved: {REPORT_FILE}")
        return

    REPORT_FILE.write_text(
        "VERDICT: FAIL\n"
        "The journal did not pass all required checks.\n"
        f"Total words: {final_result['total_words']}\n"
        f"Structural validation: {final_result['valid']}\n"
        f"Source grounding: {final_grounding['valid']}\n"
        f"Reviewer verdict: "
        f"{reviewer_output.splitlines()[0] if reviewer_output else 'Missing verdict'}\n"
        f"Revision attempts: {attempt}\n"
        f"Errors: {final_errors}\n\n"
        f"Reviewer report:\n{reviewer_output}\n",
        encoding="utf-8",
    )

    # Keep rejected content separate from the accepted journal.
    (OUTPUTS / "journal_needing_revision.md").write_text(
        journal + "\n",
        encoding="utf-8",
    )

    print("\nThe journal still needs revision.")
    print(f"Validation report saved: {REPORT_FILE}")
    print("The rejected draft is saved separately.")


if __name__ == "__main__":
    main()
