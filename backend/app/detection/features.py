import math
import re
from typing import List, Dict
import numpy as np


class FeatureExtractor:
    """Extracts statistical, lexical, and structural numerical features from test inputs."""

    FEATURE_NAMES = [
        "input_length",
        "shannon_entropy",
        "special_char_ratio",
        "digit_ratio",
        "uppercase_ratio",
        "url_escape_count",
        "comment_token_count",
        "whitespace_count",
        "sql_keyword_score",
        "xss_tag_score",
        "cmd_token_score",
        "traversal_seq_count",
        "null_byte_flag",
        "max_consecutive_special",
    ]

    def __init__(self) -> None:
        self.sql_keywords = re.compile(r"\b(select|union|where|or|and|like|from|insert|drop)\b", re.I)
        self.xss_keywords = re.compile(r"(<script|<img|<svg|onload|onerror|javascript:|alert|prompt)", re.I)
        self.cmd_keywords = re.compile(r"(&&|\|\||;|`|\$\(|echo|cat|id|whoami|uname)", re.I)
        self.traversal_keywords = re.compile(r"(\.\./|\.\.\\|\.\.%2f|/etc/|windows/)", re.I)
        self.special_chars = set("'\"<>;/\\$%&|=()#*+-")

    def extract_dict(self, text: str) -> Dict[str, float]:
        """Extracts named feature map for interpretability."""
        n = len(text)
        if n == 0:
            return {name: 0.0 for name in self.FEATURE_NAMES}

        # 1. Length
        length = float(n)

        # 2. Shannon Entropy
        counts: Dict[str, int] = {}
        for ch in text:
            counts[ch] = counts.get(ch, 0) + 1
        entropy = -sum((c / n) * math.log2(c / n) for c in counts.values())

        # 3. Special char ratio
        special_count = sum(1 for ch in text if ch in self.special_chars)
        special_ratio = special_count / n

        # 4. Digit ratio
        digit_count = sum(1 for ch in text if ch.isdigit())
        digit_ratio = digit_count / n

        # 5. Uppercase ratio
        upper_count = sum(1 for ch in text if ch.isupper())
        upper_ratio = upper_count / n

        # 6. URL escape count (%xx)
        url_escapes = len(re.findall(r"%[0-9a-fA-F]{2}", text))

        # 7. Comment tokens (/*, */, #, --)
        comment_tokens = len(re.findall(r"(/\*|\*/|#|--)", text))

        # 8. Whitespace count
        whitespace_count = float(sum(1 for ch in text if ch.isspace() or ch == "+"))

        # 9. SQL keywords score
        sql_score = float(len(self.sql_keywords.findall(text)))

        # 10. XSS keywords score
        xss_score = float(len(self.xss_keywords.findall(text)))

        # 11. Command injection keywords score
        cmd_score = float(len(self.cmd_keywords.findall(text)))

        # 12. Traversal sequence count
        traversal_count = float(len(self.traversal_keywords.findall(text)))

        # 13. Null byte flag
        null_byte = 1.0 if ("%00" in text or "\x00" in text) else 0.0

        # 14. Max consecutive special characters
        max_consec = 0
        current_consec = 0
        for ch in text:
            if ch in self.special_chars:
                current_consec += 1
                if current_consec > max_consec:
                    max_consec = current_consec
            else:
                current_consec = 0

        return {
            "input_length": length,
            "shannon_entropy": round(entropy, 3),
            "special_char_ratio": round(special_ratio, 3),
            "digit_ratio": round(digit_ratio, 3),
            "uppercase_ratio": round(upper_ratio, 3),
            "url_escape_count": float(url_escapes),
            "comment_token_count": float(comment_tokens),
            "whitespace_count": whitespace_count,
            "sql_keyword_score": sql_score,
            "xss_tag_score": xss_score,
            "cmd_token_score": cmd_score,
            "traversal_seq_count": traversal_count,
            "null_byte_flag": null_byte,
            "max_consecutive_special": float(max_consec),
        }

    def extract_vector(self, text: str) -> np.ndarray:
        """Extracts feature vector as a 1D numpy array."""
        feat_dict = self.extract_dict(text)
        return np.array([feat_dict[k] for k in self.FEATURE_NAMES], dtype=np.float32)

    def extract_batch(self, texts: List[str]) -> np.ndarray:
        """Extracts 2D feature matrix (samples, features)."""
        return np.array([self.extract_vector(t) for t in texts], dtype=np.float32)
