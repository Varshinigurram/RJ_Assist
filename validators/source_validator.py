import re


def normalize(text: str) -> str:
    """Normalize text for consistent keyword checks."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def validate_source_grounding(
    academic_material: str,
    journal: str,
) -> dict:
    """
    Perform deterministic checks for the current BST assignment.

    This is a heuristic validator. It cannot guarantee that every
    sentence is factually supported by the academic source.
    """
    source = normalize(academic_material)
    output = normalize(journal)

    errors = []

    if not source:
        return {
            "valid": False,
            "errors": ["Academic material is empty."],
        }

    if not output:
        return {
            "valid": False,
            "errors": ["Journal is empty."],
        }

    # Check that the journal addresses the supplied topic.
    if "binary search tree" in source:
        if "binary search tree" not in output:
            errors.append(
                "Journal does not mention Binary Search Trees."
            )

    # Check claims that are not supported by the current BST source.
    unsupported_claims = {
        "balanced tree performance": [
            "balanced tree",
            "balanced trees",
            "logarithmic performance",
            "linear time",
            "o log n",
            "o n",
        ],
        "deletion implementation details": [
            "inorder predecessor",
            "inorder successor",
            "predecessor or successor",
        ],
        "tree serialization": [
            "serialize",
            "serialization",
            "rebuild the tree",
        ],
        "unsupported traversal applications": [
            "quick reconstruction",
            "deleting children before parents",
            "safe cleanup",
        ],
    }

    for category, phrases in unsupported_claims.items():
        for phrase in phrases:
            if phrase in output and phrase not in source:
                errors.append(
                    f"Potentially unsupported claim "
                    f"({category}): '{phrase}'."
                )

    # Check for common unrelated topics.
    unrelated_terms = [
        "master theorem",
        "recurrence relation",
        "recursive function",
        "file organizer",
    ]

    for term in unrelated_terms:
        if term in output and term not in source:
            errors.append(
                f"Potentially unsupported topic: '{term}'."
            )

    return {
        "valid": not errors,
        "errors": errors,
    }


if __name__ == "__main__":
    from pathlib import Path

    source = (
        "This week's module covered Binary Search Trees. "
        "Smaller values are placed in the left subtree and "
        "larger values in the right subtree. The module covered "
        "insertion, deletion, searching, and inorder, preorder, "
        "and postorder traversal. Operations depend on tree "
        "structure, and traversals visit nodes in different ways."
    )

    journal_path = Path("outputs/generated_journal.md")

    if not journal_path.exists():
        raise FileNotFoundError(
            f"Journal not found: {journal_path}"
        )

    journal = journal_path.read_text(encoding="utf-8-sig")

    result = validate_source_grounding(source, journal)

    print("Source grounding:", result["valid"])

    for error in result["errors"]:
        print("-", error)