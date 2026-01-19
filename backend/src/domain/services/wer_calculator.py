"""Word Error Rate (WER) and Character Error Rate (CER) calculator.

This is a domain service that calculates error rates for STT evaluation.
Feature: 003-stt-testing-module
"""


def _levenshtein_distance(ref: list[str], hyp: list[str]) -> int:
    """Calculate Levenshtein distance between two sequences.

    Args:
        ref: Reference sequence
        hyp: Hypothesis sequence

    Returns:
        Edit distance (number of insertions, deletions, substitutions)
    """
    m, n = len(ref), len(hyp)

    # Create distance matrix
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Initialize first row and column
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Fill the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,  # Deletion
                    dp[i][j - 1] + 1,  # Insertion
                    dp[i - 1][j - 1] + 1,  # Substitution
                )

    return dp[m][n]


def calculate_wer(reference: str, hypothesis: str) -> float:
    """Calculate Word Error Rate (WER).

    WER = (S + D + I) / N
    where:
    - S = number of substitutions
    - D = number of deletions
    - I = number of insertions
    - N = number of words in reference

    Args:
        reference: Ground truth text
        hypothesis: Recognized text

    Returns:
        Word error rate as a float between 0.0 and 1.0+
        (can be > 1.0 if insertions exceed reference length)
    """
    if not reference:
        return 0.0 if not hypothesis else 1.0

    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    distance = _levenshtein_distance(ref_words, hyp_words)
    return distance / len(ref_words)


def calculate_cer(reference: str, hypothesis: str) -> float:
    """Calculate Character Error Rate (CER).

    CER is similar to WER but operates on characters instead of words.
    This is more suitable for languages without clear word boundaries (e.g., Chinese).

    Args:
        reference: Ground truth text
        hypothesis: Recognized text

    Returns:
        Character error rate as a float between 0.0 and 1.0+
    """
    if not reference:
        return 0.0 if not hypothesis else 1.0

    # Remove whitespace for character-level comparison
    ref_chars = list(reference.replace(" ", ""))
    hyp_chars = list(hypothesis.replace(" ", ""))

    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0

    distance = _levenshtein_distance(ref_chars, hyp_chars)
    return distance / len(ref_chars)


def calculate_error_rate(reference: str, hypothesis: str, language: str) -> tuple[float, str]:
    """Calculate error rate based on language.

    Auto-selects WER for English, CER for CJK languages.

    Args:
        reference: Ground truth text
        hypothesis: Recognized text
        language: Language code (e.g., 'zh-TW', 'en-US')

    Returns:
        Tuple of (error_rate, error_type) where error_type is 'WER' or 'CER'
    """
    cjk_languages = {"zh-TW", "zh-CN", "ja-JP", "ko-KR"}
    if language in cjk_languages:
        return calculate_cer(reference, hypothesis), "CER"
    return calculate_wer(reference, hypothesis), "WER"


def calculate_alignment(
    ref: list[str], hyp: list[str]
) -> tuple[list[tuple[str | None, str | None, str]], int, int, int]:
    """Calculate alignment between reference and hypothesis with edit operations.

    Uses dynamic programming to find the optimal alignment and track operations.

    Args:
        ref: Reference sequence (words or characters)
        hyp: Hypothesis sequence (words or characters)

    Returns:
        Tuple of:
        - alignment: List of (ref_token, hyp_token, operation) tuples
        - insertions: Number of insertions
        - deletions: Number of deletions
        - substitutions: Number of substitutions
    """
    m, n = len(ref), len(hyp)

    # Create distance matrix with backtracking info
    # Each cell stores (distance, operation)
    # Operations: 'match', 'substitute', 'insert', 'delete'
    dp = [[(0, "") for _ in range(n + 1)] for _ in range(m + 1)]

    # Initialize first row and column
    for i in range(m + 1):
        dp[i][0] = (i, "delete")
    for j in range(n + 1):
        dp[0][j] = (j, "insert")
    dp[0][0] = (0, "")

    # Fill the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = (dp[i - 1][j - 1][0], "match")
            else:
                delete_cost = dp[i - 1][j][0] + 1
                insert_cost = dp[i][j - 1][0] + 1
                substitute_cost = dp[i - 1][j - 1][0] + 1

                min_cost = min(delete_cost, insert_cost, substitute_cost)

                if min_cost == substitute_cost:
                    dp[i][j] = (min_cost, "substitute")
                elif min_cost == delete_cost:
                    dp[i][j] = (min_cost, "delete")
                else:
                    dp[i][j] = (min_cost, "insert")

    # Backtrack to get alignment
    alignment = []
    i, j = m, n
    insertions, deletions, substitutions = 0, 0, 0

    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j][1] == "match":
            alignment.append((ref[i - 1], hyp[j - 1], "match"))
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j][1] == "substitute":
            alignment.append((ref[i - 1], hyp[j - 1], "substitute"))
            substitutions += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j][1] == "delete":
            alignment.append((ref[i - 1], None, "delete"))
            deletions += 1
            i -= 1
        elif j > 0:  # insert
            alignment.append((None, hyp[j - 1], "insert"))
            insertions += 1
            j -= 1

    alignment.reverse()
    return alignment, insertions, deletions, substitutions
