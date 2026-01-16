"""Word Error Rate (WER) and Character Error Rate (CER) calculator.

This is a domain service that calculates error rates for STT evaluation.
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
