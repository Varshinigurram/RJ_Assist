
import re

REQUIRED_SECTIONS = [
    "Experience",
    "Feelings",
    "Learning",
    "Application",
    "Conclusion",
]

MIN_SECTION_WORDS = 50
MIN_TOTAL_WORDS = 200
MAX_TOTAL_WORDS = 400

# Accepts headings such as:
# Experience
# 1. Experience (Class Content)
# Experience (Class Content):

HEADING_PATTERN = re.compile(
    r"^\s*(?:\*\*|__)?\s*(?:\d+\.\s*)?"
    r"(Experience|Feelings|Learning|Application|Conclusion)"
    r"(?:\s*\([^)]*\))?\s*:?\s*(?:\*\*|__)?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

WORD_PATTERN = re.compile(
    r"\b[\w$]+(?:[’'-][\w$]+)*\b",
    re.UNICODE,
)


def count_words(text):
    """Count words consistently for validation."""
    return len(WORD_PATTERN.findall(text))


def extract_sections(journal):
    """Extract section bodies and preserve heading order."""
    matches = list(HEADING_PATTERN.finditer(journal))
    sections = {}
    ordered_sections = []
    duplicates = []

    for index, match in enumerate(matches):
        name = match.group(1).capitalize()
        start = match.end()

        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(journal)
        )

        content = journal[start:end].strip()
        ordered_sections.append(name)

        if name in sections:
            duplicates.append(name)
        else:
            sections[name] = content

    return sections, ordered_sections, duplicates


def validate_journal(journal):
    errors = []

    sections, ordered_sections, duplicates = extract_sections(journal)

    # Check missing sections.
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            errors.append(f"Missing section: {name}")

    # Check duplicate sections.
    for name in sorted(set(duplicates)):
        errors.append(f"Duplicate section: {name}")

    # Check exact section order and count.
    if ordered_sections != REQUIRED_SECTIONS:
        errors.append(
            "Sections must appear exactly once in this order: "
            + ", ".join(REQUIRED_SECTIONS)
            + "."
        )

    # Check each section's word count.
    section_results = {}

    for name in REQUIRED_SECTIONS:
        if name not in sections:
            section_results[name] = {
                "present": False,
                "word_count": 0,
                "valid": False,
            }
            continue

        words = count_words(sections[name])
        valid = words >= MIN_SECTION_WORDS

        section_results[name] = {
            "present": True,
            "word_count": words,
            "valid": valid,
        }

        if not valid:
            errors.append(
                f"{name} has {words} words; "
                f"minimum is {MIN_SECTION_WORDS}."
            )

    # Check the complete journal.
    total_words = count_words(journal)

    if total_words < MIN_TOTAL_WORDS:
        errors.append(
            f"Journal has {total_words} words; "
            f"minimum is {MIN_TOTAL_WORDS}."
        )

    if total_words > MAX_TOTAL_WORDS:
        errors.append(
            f"Journal has {total_words} words; "
            f"maximum is {MAX_TOTAL_WORDS}."
        )

    return {
        "valid": not errors,
        "total_words": total_words,
        "sections": section_results,
        "errors": errors,
    }


if __name__ == "__main__":
    from pathlib import Path

    journal_path = Path("outputs/generated_journal.md")

    if not journal_path.exists():
        print(f"Journal not found: {journal_path}")
    else:
        journal = journal_path.read_text(encoding="utf-8")
        result = validate_journal(journal)

        print("\n=== RJ ASSIST JOURNAL VALIDATION ===")
        print(f"Valid: {result['valid']}")
        print(f"Total words: {result['total_words']}")

        print("\nSection Results:")
        for name, data in result["sections"].items():
            status = "PASS" if data["valid"] else "FAIL"
            print(
                f"- {name}: {data['word_count']} words ({status})"
            )

        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"- {error}")
        else:
            print("\nAll validation checks passed.")
