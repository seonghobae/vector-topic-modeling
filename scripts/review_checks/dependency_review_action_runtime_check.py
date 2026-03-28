"""Monitor upstream runtime metadata for dependency-review action pin."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import re
import urllib.error
import urllib.request
from urllib.parse import urlparse

MONITORED_ACTION_REF = "actions/dependency-review-action@v4"
MONITORED_ACTION_YAML_URL = (
    "https://raw.githubusercontent.com/actions/dependency-review-action/v4/action.yml"
)


@dataclass(frozen=True)
class RuntimeStatus:
    """Result payload for dependency-review action runtime monitoring."""

    action_ref: str
    expected_runtime: str
    actual_runtime: str
    is_expected: bool
    status: str


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for runtime monitoring checks."""

    parser = argparse.ArgumentParser(
        description=(
            "Check actions/dependency-review-action runtime metadata and "
            "report whether it matches an expected Node runtime."
        )
    )
    parser.add_argument(
        "--action-ref",
        default=MONITORED_ACTION_REF,
        help="Action reference used by repository workflow.",
    )
    parser.add_argument(
        "--action-yaml-url",
        default=MONITORED_ACTION_YAML_URL,
        help="Raw action.yml URL to inspect.",
    )
    parser.add_argument(
        "--expected-runtime",
        default="node24",
        help="Expected value for runs.using in action metadata.",
    )
    return parser.parse_args()


def fetch_action_yaml(*, action_yaml_url: str) -> str:
    """Fetch action metadata YAML from the upstream raw URL."""

    parsed = urlparse(action_yaml_url)
    if parsed.scheme != "https" or parsed.netloc != "raw.githubusercontent.com":
        raise RuntimeError("action_yaml_url must use https://raw.githubusercontent.com")
    path_segments = [segment for segment in parsed.path.split("/") if segment]
    if (
        len(path_segments) < 4
        or path_segments[0] != "actions"
        or path_segments[1] != "dependency-review-action"
        or path_segments[-1] != "action.yml"
    ):
        raise RuntimeError(
            "action_yaml_url must target /actions/dependency-review-action/<ref>/action.yml"
        )

    request = urllib.request.Request(
        action_yaml_url,
        headers={"User-Agent": "vector-topic-modeling-runtime-monitor"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError as err:
        raise RuntimeError(
            f"failed to fetch action metadata url={action_yaml_url}: {err}"
        ) from err


def parse_runs_using(action_yaml: str) -> str | None:
    """Extract the `runs.using` runtime token from action.yml content."""

    in_runs = False
    runs_indent: int | None = None
    runs_child_indent: int | None = None
    block_scalar_indent: int | None = None

    for raw_line in action_yaml.splitlines():
        line_without_comment = raw_line.split("#", 1)[0].rstrip()
        if not line_without_comment:
            continue

        indent = len(raw_line) - len(raw_line.lstrip())

        if not in_runs:
            if re.match(r"^\s*runs\s*:\s*$", line_without_comment):
                in_runs = True
                runs_indent = indent
                runs_child_indent = None
            continue

        if indent <= (runs_indent or 0):
            in_runs = False
            runs_indent = None
            runs_child_indent = None
            block_scalar_indent = None
            if re.match(r"^\s*runs\s*:\s*$", line_without_comment):
                in_runs = True
                runs_indent = indent
                runs_child_indent = None
            continue

        if block_scalar_indent is not None:
            if indent > block_scalar_indent:
                continue
            block_scalar_indent = None

        if re.match(r"^\s*[A-Za-z0-9_-]+\s*:\s*[|>][-+0-9]*\s*$", line_without_comment):
            block_scalar_indent = indent
            continue

        if runs_child_indent is None:
            runs_child_indent = indent
        if indent != runs_child_indent:
            continue

        match = re.match(
            r"^\s*using\s*:\s*(['\"]?)([A-Za-z0-9_.-]+)\1\s*$",
            line_without_comment,
        )
        if match is not None:
            return match.group(2)

    return None


def evaluate_runtime_status(
    *, action_ref: str, expected_runtime: str, actual_runtime: str
) -> RuntimeStatus:
    """Classify runtime metadata as ready (expected) or monitoring (mismatch)."""

    is_expected = actual_runtime == expected_runtime
    status = "ready" if is_expected else "monitoring"
    return RuntimeStatus(
        action_ref=action_ref,
        expected_runtime=expected_runtime,
        actual_runtime=actual_runtime,
        is_expected=is_expected,
        status=status,
    )


def _print_payload(payload: dict[str, object]) -> None:
    """Emit a stable JSON payload for workflow and local parsers."""

    print(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def main() -> int:
    """Run the runtime monitor and return status code for workflow gating."""

    args = parse_args()
    try:
        action_yaml = fetch_action_yaml(action_yaml_url=args.action_yaml_url)
    except Exception as err:
        _print_payload(
            {
                "action_ref": args.action_ref,
                "action_yaml_url": args.action_yaml_url,
                "message": str(err),
                "status": "fetch-error",
            }
        )
        return 2

    actual_runtime = parse_runs_using(action_yaml)
    if actual_runtime is None:
        _print_payload(
            {
                "action_ref": args.action_ref,
                "action_yaml_url": args.action_yaml_url,
                "message": "runs.using runtime not found in action metadata",
                "status": "parse-error",
            }
        )
        return 2

    try:
        result = evaluate_runtime_status(
            action_ref=args.action_ref,
            expected_runtime=args.expected_runtime,
            actual_runtime=actual_runtime,
        )
    except Exception as err:  # pragma: no cover - defensive boundary
        _print_payload(
            {
                "action_ref": args.action_ref,
                "action_yaml_url": args.action_yaml_url,
                "message": f"unexpected runtime monitor error: {err}",
                "status": "unexpected-error",
            }
        )
        return 2
    _print_payload(asdict(result))
    return 1 if result.is_expected else 0


if __name__ == "__main__":
    raise SystemExit(main())
