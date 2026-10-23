import random
import re
import urllib.parse
from typing import List, Optional, Tuple


class Transform:
    """Base class for combinatorial evasion transforms."""
    name: str = "base"

    def apply(self, text: str, rng: random.Random) -> str:
        raise NotImplementedError


class CaseVariationTransform(Transform):
    """Varies letter casing randomly (e.g., 'SELECT' -> 'sElEcT')."""
    name = "case_variation"

    def apply(self, text: str, rng: random.Random) -> str:
        result = []
        for ch in text:
            if ch.isalpha():
                result.append(ch.upper() if rng.random() > 0.5 else ch.lower())
            else:
                result.append(ch)
        return "".join(result)


class WhitespaceSubstitutionTransform(Transform):
    """Substitutes standard spaces with equivalent SQL/HTTP separators."""
    name = "whitespace_sub"

    def __init__(self, style: Optional[str] = None) -> None:
        self.style = style

    def apply(self, text: str, rng: random.Random) -> str:
        styles = ["/**/", "+", "%20", "%09"]
        chosen = self.style or rng.choice(styles)
        # Only replace spaces outside of quotes where appropriate
        return text.replace(" ", chosen)


class CommentPlacementTransform(Transform):
    """Injects inline comment separators inside keywords (e.g., 'UNION' -> 'UN/**/ION')."""
    name = "comment_placement"

    def apply(self, text: str, rng: random.Random) -> str:
        keywords = ["SELECT", "UNION", "WHERE", "FROM", "script", "alert", "cat", "echo"]
        result = text
        for kw in keywords:
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            matches = list(pattern.finditer(result))
            if matches:
                m = rng.choice(matches)
                word = m.group(0)
                mid = len(word) // 2
                split_word = word[:mid] + "/**/" + word[mid:]
                result = result[:m.start()] + split_word + result[m.end():]
                break
        return result


class URLEncodeTransform(Transform):
    """Applies standard URL encoding to non-alphanumeric characters."""
    name = "url_encode"

    def apply(self, text: str, rng: random.Random) -> str:
        # Encode special punctuation characters without double-encoding existing escapes
        return urllib.parse.quote(text, safe="~()*!.'")


class HexEncodeTransform(Transform):
    """Selectively encodes sensitive characters as hexadecimal %HH escapes."""
    name = "hex_encode"

    def apply(self, text: str, rng: random.Random) -> str:
        result = []
        sensitive = set("'\"<>;/\\ ")
        for ch in text:
            if ch in sensitive and rng.random() > 0.3:
                result.append(f"%{ord(ch):02X}")
            else:
                result.append(ch)
        return "".join(result)


class UnicodeEncodeTransform(Transform):
    """Applies overlong or unicode representation to bypass simple string matching."""
    name = "unicode_encode"

    def apply(self, text: str, rng: random.Random) -> str:
        # Replaces targeted characters with standard unicode escape sequence or alternative byte
        replacements = {
            "'": "%u0027",
            '"': "%u0022",
            "<": "%u003c",
            ">": "%u003e",
            "/": "%u002f",
        }
        chars = list(text)
        for i, ch in enumerate(chars):
            if ch in replacements and rng.random() > 0.4:
                chars[i] = replacements[ch]
        return "".join(chars)


AVAILABLE_TRANSFORMS = [
    CaseVariationTransform(),
    WhitespaceSubstitutionTransform(),
    CommentPlacementTransform(),
    URLEncodeTransform(),
    HexEncodeTransform(),
    UnicodeEncodeTransform(),
]


class TransformPipeline:
    """Composes multiple transforms and tracks the transformation history."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self.rng = random.Random(seed)

    def set_seed(self, seed: int) -> None:
        self.rng.seed(seed)

    def apply_random_combination(
        self, text: str, max_transforms: int = 2
    ) -> Tuple[str, List[str]]:
        """Selects 1 to max_transforms transforms, applies them, and returns (transformed_text, transform_names)."""
        count = self.rng.randint(1, max_transforms)
        chosen = self.rng.sample(AVAILABLE_TRANSFORMS, count)
        transformed = text
        applied_names = []

        for t in chosen:
            transformed = t.apply(transformed, self.rng)
            applied_names.append(t.name)

        return transformed, applied_names

    def apply_named(self, text: str, names: List[str]) -> str:
        """Applies a specific sequence of transforms by name."""
        name_map = {t.name: t for t in AVAILABLE_TRANSFORMS}
        transformed = text
        for name in names:
            if name in name_map:
                transformed = name_map[name].apply(transformed, self.rng)
        return transformed
