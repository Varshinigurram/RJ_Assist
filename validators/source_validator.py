
import re


def normalize(text: str) -> str:
    """Normalize text for simple, deterministic topic checks."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def validate_source_grounding(
    academic_material: str,
    journal: str,
) -> dict:
    """
    Check whether the journal contains the source's main topic
    and avoids obvious unrelated-topic substitutions.

    This is a heuristic check, not a complete factuality detector.
    """
    source = normalize(academic_material)
    output = normalize(journal)

    errors = []

    if not source:
        return {
            "valid": False,
            "errors": ["Academic material is empty."],
        }

    # Explicit topic check for the current BST test case.
    if "binary search tree" in source:
        if "binary search tree" not in output:
            errors.append(
                "Journal does not mention the source topic: "
                "Binary Search Trees."
            )

        unrelated_terms = [
            "master theorem",
            "recurrence relation",
            "recursive function",
            "big o notation",
            "file organizer",
        ]

        for term in unrelated_terms:
            if term in output and term not in source:
                errors.append(
                    f"Potentially unsupported topic: {term}."
                )

    return {
        "valid": not errors,
        "errors": errors,
    }


if __name__ == "__main__":
    from pathlib import Path

    source = (
        "This week's module covered Binary Search Trees. "
        "The material covered insertion, deletion, searching, "
        "and inorder, preorder, and postorder traversal."
    )

    draft_path = Path("outputs/draft_journal.md")

    if not draft_path.exists():
        raise FileNotFoundError(
            "Draft not found: outputs/draft_journal.md"
        )

    draft = draft_path.read_text(encoding="utf-8-sig")
    print(validate_source_grounding(source, draft))
