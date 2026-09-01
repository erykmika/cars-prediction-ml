import json
import logging
import os
import subprocess
import sys
import time
from typing import Any

import requests


MODEL = os.getenv(
    "REVIEW_MODEL",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MAX_RETRIES = 5
BASE_DELAY = 1.0
MAX_DELAY = 60.0


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)


logger.info(f"Using model: {MODEL}")
logger.info(f"Using OpenRouter URL: {OPENROUTER_URL}")

def run(command: list[str]) -> str:
    logger.info(f"Running command: {' '.join(command)}")
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=True,
    )
    logger.info(f"Command output: {result.stdout}")
    return result.stdout


def get_diff() -> str:
    return run(
        [
            "git",
            "diff",
            f"{os.environ['PR_HEAD_SHA']}^",
            os.environ['PR_HEAD_SHA'],
        ]
    )


def load_rules() -> str:
    with open(".ai_review/rules.md", "r", encoding="utf-8") as f:
        logger.info("Loading review rules...")
        return f.read()


def call_model(prompt: str) -> str:
    delay = BASE_DELAY

    for attempt in range(MAX_RETRIES):
        logger.info(f"Calling model (attempt {attempt + 1}/{MAX_RETRIES})...")
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": (
                    f"Bearer {os.environ['OPENROUTER_API_KEY']}"
                ),
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            },
            timeout=300,
        )

        if response.status_code == 429 or 500 <= response.status_code < 600:
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    f"API returned {response.status_code}, retrying in "
                    f"{delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
                )
                time.sleep(delay)
                delay = min(delay * 2, MAX_DELAY)
                continue
            response.raise_for_status()

        response.raise_for_status()

        data = response.json()

        if "choices" not in data:
            logger.error(f"Unexpected API response: {json.dumps(data, indent=2)}")
            raise ValueError("API response missing 'choices' field")

        return data["choices"][0]["message"]["content"]

    raise RuntimeError("Max retries exceeded")


SYSTEM_PROMPT = """
You are a senior software engineer performing an automated
pull request review.

You are NOT a general code style reviewer.

Only report concrete, actionable problems.

Never invent files, lines, APIs, or behavior.

Only report problems that can be supported by the supplied
diff and repository context.

Return ONLY valid JSON.

Schema:

{
  "summary": "short summary",
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "path": "relative/path/to/file",
      "line": 123,
      "title": "short title",
      "body": "explanation and suggested fix",
      "confidence": 0.95
    }
  ]
}
"""


def parse_response(text: str) -> dict[str, Any]:
    text = text.strip()

    # Handle accidental markdown fences.
    if text.startswith("```"):
        lines = text.splitlines()

        if lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines)

    return json.loads(text)


def main() -> None:
    diff = get_diff()
    rules = load_rules()

    prompt = f"""
Repository review rules:

{rules}

Pull request diff:

{diff}

Review this pull request.

Remember:

- Only report issues in changed code.
- Prefer no finding over a speculative finding.
- Include the exact changed line where possible.
- Confidence must represent your confidence that this is
  a genuine issue.
"""

    logger.info("Running AI review...")
    raw = call_model(prompt)

    try:
        review = parse_response(raw)
    except json.JSONDecodeError:
        logger.error("Model returned invalid JSON:")
        logger.error(raw)
        sys.exit(1)

    validate_review(review)

    logger.info(f"AI review completed: {json.dumps(review, indent=2)}")

    post_review(review)


def validate_review(review: dict[str, Any]) -> None:
    if not isinstance(review, dict):
        raise ValueError("Review must be an object")

    if "findings" not in review:
        raise ValueError("Missing findings")

    if not isinstance(review["findings"], list):
        raise ValueError("Findings must be a list")

    allowed_severity = {
        "critical",
        "high",
        "medium",
        "low",
    }

    required_fields = {"path", "line", "title", "body", "severity", "confidence"}

    for i, finding in enumerate(review["findings"]):
        if not isinstance(finding, dict):
            raise ValueError(f"Finding {i} must be an object")

        missing = required_fields - finding.keys()
        if missing:
            raise ValueError(f"Finding {i} missing required fields: {missing}")

        if finding["severity"] not in allowed_severity:
            raise ValueError(f"Finding {i}: invalid severity")

        if not isinstance(finding["path"], str) or not finding["path"]:
            raise ValueError(f"Finding {i}: path must be a non-empty string")

        if not isinstance(finding["line"], int) or finding["line"] < 1:
            raise ValueError(f"Finding {i}: line must be a positive integer")

        if not isinstance(finding["title"], str) or not finding["title"]:
            raise ValueError(f"Finding {i}: title must be a non-empty string")

        if not isinstance(finding["body"], str) or not finding["body"]:
            raise ValueError(f"Finding {i}: body must be a non-empty string")

        confidence = finding.get("confidence")

        if not isinstance(confidence, (float, int)):
            raise ValueError(f"Finding {i}: invalid confidence")

        if not 0 <= confidence <= 1:
            raise ValueError(f"Finding {i}: confidence outside [0, 1]")


def post_review(review: dict[str, Any]) -> None:
    comments: list[dict[str, Any]] = []

    logger.info(f"All findings: {json.dumps(review['findings'], indent=2)}")

    for finding in review["findings"]:
        # Don't post low-confidence findings.
        if finding["confidence"] < 0.85:
            continue

        comments.append(
            {
                "path": finding["path"],
                "line": finding["line"],
                "side": "RIGHT",
                "body": (
                    f"**{finding['severity'].upper()}: "
                    f"{finding['title']}**\n\n"
                    f"{finding['body']}\n\n"
                    f"_AI confidence: "
                    f"{finding['confidence']:.0%}_"
                ),
            }
        )

    if not comments:
        logger.info("No sufficiently confident findings.")
        return

    repository = os.environ["GITHUB_REPOSITORY"]
    owner, repo = repository.split("/")

    pr_number = os.environ["PR_NUMBER"]

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/pulls/{pr_number}/reviews"
    )

    payload = {
        "commit_id": os.environ["PR_HEAD_SHA"],
        "body": review.get(
            "summary",
            "AI code review completed.",
        ),
        "event": "COMMENT",
        "comments": comments,
    }

    response = requests.post(
        url,
        headers={
            "Authorization": (
                f"Bearer {os.environ['GITHUB_TOKEN']}"
            ),
            "Accept": "application/vnd.github+json",
        },
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    logger.info("Review posted.")


if __name__ == "__main__":
    main()