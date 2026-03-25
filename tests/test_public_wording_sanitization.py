from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def blocked_phrases() -> list[str]:
    company_token = "".join(
        chr(code)
        for code in [
            72,
            89,
            79,
            83,
            85,
            78,
            71,
            45,
            73,
            84,
            88,
            45,
            65,
            73,
            45,
            66,
            117,
            115,
            105,
            110,
            101,
            115,
            115,
            45,
            68,
            101,
            112,
            97,
            114,
            116,
            109,
            101,
            110,
            116,
        ]
    )
    source_repo_token = "".join(
        chr(code)
        for code in [
            108,
            108,
            109,
            45,
            103,
            97,
            116,
            101,
            119,
            97,
            121,
            45,
            99,
            111,
            110,
            115,
            111,
            108,
            101,
        ]
    )
    return [
        company_token,
        source_repo_token,
        "query-topic-modeling",
        "query_topic_modeling",
    ]


def candidate_files() -> list[Path]:
    patterns = ["**/*.md", "**/*.toml", "**/*.py", "**/*.yml", "**/*.yaml"]
    excluded_prefixes = (
        ".git",
        ".venv",
        ".venv-smoke-cli",
        "dist",
        "build",
        "__pycache__",
    )
    excluded_exact = {
        Path("tests/test_public_wording_sanitization.py"),
    }

    files: set[Path] = set()
    for pattern in patterns:
        for path in REPO_ROOT.glob(pattern):
            rel = path.relative_to(REPO_ROOT)
            if rel in excluded_exact:
                continue
            if any(part in excluded_prefixes for part in rel.parts):
                continue
            files.add(path)
    return sorted(files)


def test_blocked_source_identity_phrases_absent() -> None:
    blocked = blocked_phrases()
    offenders: list[str] = []

    for path in candidate_files():
        text = path.read_text(encoding="utf-8")
        for phrase in blocked:
            if phrase in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {phrase}")

    assert offenders == []
