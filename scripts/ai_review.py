import json
import os
import subprocess
import sys

import requests


MODEL = os.getenv(
    "REVIEW_MODEL",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def run(command):
    result = subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout


def get_diff():
    return run(
        "git diff "
        f"{os.environ['PR_HEAD_SHA']}^ "
        f"{os.environ['PR_HEAD_SHA']} "
    )


def load_rules():
    with open(".ai_review/rules.md", "r", encoding="utf-8") as f:
        return f.read()


def call_model(prompt):
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

    response.raise_for_status()

    data = response.json()

    if "choices" not in data:
        print(f"Unexpected API response: {json.dumps(data, indent=2)}")
        raise ValueError("API response missing 'choices' field")

    return data["choices"][0]["message"]["content"]


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


def parse_response(text):
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


def main():
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

    print("Running AI review...")
    raw = call_model(prompt)

    try:
        review = parse_response(raw)
    except json.JSONDecodeError:
        print("Model returned invalid JSON:")
        print(raw)
        sys.exit(1)

    validate_review(review)

    print(json.dumps(review, indent=2))

    post_review(review)


def validate_review(review):
    if not isinstance(review, dict):
        raise ValueError("Review must be an object")

    if "findings" not in review:
        raise ValueError("Missing findings")

    allowed_severity = {
        "critical",
        "high",
        "medium",
        "low",
    }

    for finding in review["findings"]:
        if finding["severity"] not in allowed_severity:
            raise ValueError("Invalid severity")

        confidence = finding.get("confidence")

        if not isinstance(confidence, (float, int)):
            raise ValueError("Invalid confidence")

        if not 0 <= confidence <= 1:
            raise ValueError("Confidence outside [0, 1]")


def post_review(review):
    comments = []

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
        print("No sufficiently confident findings.")
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

    print("Review posted.")


if __name__ == "__main__":
    main()