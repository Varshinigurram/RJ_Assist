import re


REQUIRED_SECTIONS = [
    "Experience",
    "Feelings",
    "Learning",
    "Application",
    "Conclusion",
]

MIN_SECTION_WORDS = 50
MIN_TOTAL_WORDS = 280
MAX_TOTAL_WORDS = 400


def count_words(text):
    return len(re.findall(r"\b[\w$]+\b", text))


def extract_sections(journal):
    sections = {}

    pattern = re.compile(
        r"(?:\d+\.\s*)?"
        r"(Experience|Feelings|Learning|Application|Conclusion)"
        r"(?:\s*\([^)]*\))?"
        r"\s*:?\s*"
        r"(.*?)(?="
        r"(?:\n\s*(?:\d+\.\s*)?(?:Experience|Feelings|Learning|Application|Conclusion)"
        r"(?:\s*\([^)]*\))?"
        r"\s*:?)"
        r"|$)",
        re.IGNORECASE | re.DOTALL,
    )

    matches = pattern.findall(journal)

    for section_name, content in matches:
        sections[section_name.capitalize()] = content.strip()

    return sections


def validate_journal(journal):
    errors = []
    section_results = {}

    sections = extract_sections(journal)

    # Check exact section presence
    for section in REQUIRED_SECTIONS:
        if section not in sections:
            errors.append(f"Missing section: {section}")
            section_results[section] = {
                "present": False,
                "word_count": 0,
                "valid": False,
            }
            continue

        word_count = count_words(sections[section])

        valid = word_count >= MIN_SECTION_WORDS

        section_results[section] = {
            "present": True,
            "word_count": word_count,
            "valid": valid,
        }

        if not valid:
            errors.append(
                f"{section} has only {word_count} words "
                f"(minimum {MIN_SECTION_WORDS})."
            )

    # Count total words
    total_words = count_words(journal)

    if total_words < MIN_TOTAL_WORDS:
        errors.append(
            f"Total word count is {total_words} "
            f"(minimum {MIN_TOTAL_WORDS})."
        )

    if total_words > MAX_TOTAL_WORDS:
        errors.append(
            f"Total word count is {total_words} "
            f"(maximum {MAX_TOTAL_WORDS})."
        )

    # Check section order
    positions = []

    for section in REQUIRED_SECTIONS:
        if section in sections:
            positions.append(
                journal.lower().find(section.lower())
            )

    if positions != sorted(positions):
        errors.append("Sections are not in the required order.")

    return {
        "valid": len(errors) == 0,
        "total_words": total_words,
        "sections": section_results,
        "errors": errors,
    }


if __name__ == "__main__":
    test_journal = """
1. Experience (Class Content)

This week's module focused on Binary Search Trees. I learned how values are organized
with smaller values placed on the left and larger values on the right. We covered
searching, insertion, deletion, and different traversal methods. The examples helped
me understand how the structure changes when nodes are added or removed.

2. Feelings (Emotional Reactions)

I found the topic interesting because the ordering rule made searching easier to
understand. I initially had to think carefully about deletion when a node had two
children. Working through the different cases helped me understand why the inorder
successor is useful in that situation.

3. Learning (Key Analysis)

I understood that the efficiency of a BST depends on its shape. A balanced tree can
make searching efficient, while a badly shaped tree can behave more like a linear
structure. I also understood that inorder traversal produces values in sorted order,
while preorder and postorder provide different ways to visit the nodes.

4. Application (Practical Use)

I could use BST concepts when maintaining data that needs to remain ordered while
supporting searching and insertion. For example, scores could be stored in a BST and
an inorder traversal could display them in ascending order. The ordering rule and
traversal methods from this module directly support this type of application.

5. Conclusion

Overall, this module helped me understand that the usefulness of a BST depends on how
the data is organized. I also learned that choosing the right traversal depends on
what information needs to be obtained from the tree. As a next step, I would like to
learn about self-balancing trees such as AVL trees and understand how they improve
performance when the tree becomes unbalanced.
"""

    result = validate_journal(test_journal)

    print("\n=== RJ ASSIST JOURNAL VALIDATION ===")
    print(f"Valid: {result['valid']}")
    print(f"Total words: {result['total_words']}")

    print("\nSection Results:")

    for section, data in result["sections"].items():
        print(
            f"- {section}: "
            f"{data['word_count']} words "
            f"({'PASS' if data['valid'] else 'FAIL'})"
        )

    if result["errors"]:
        print("\nErrors:")

        for error in result["errors"]:
            print(f"- {error}")
    else:
        print("\nAll validation checks passed.")