"""Rule-based horoscope. No machine learning here, on purpose: not every tool needs a model."""

import random
from datetime import date

# (sign, first day of the NEXT sign). Ordered by month.
_SIGN_STARTS = [
    ("Capricorn", (1, 20)),
    ("Aquarius", (2, 19)),
    ("Pisces", (3, 21)),
    ("Aries", (4, 20)),
    ("Taurus", (5, 21)),
    ("Gemini", (6, 21)),
    ("Cancer", (7, 23)),
    ("Leo", (8, 23)),
    ("Virgo", (9, 23)),
    ("Libra", (10, 23)),
    ("Scorpio", (11, 22)),
    ("Sagittarius", (12, 22)),
]

MESSAGES: dict[str, list[str]] = {
    "Aries": [
        "A bold Friday deploy will go better than it deserves to. Do not make it a habit.",
        "Your impatience with slow CI is justified. Your fix for it will be legendary.",
        "You will argue with a linter today. The linter is right.",
    ],
    "Taurus": [
        "Stability is your gift. Your pinned dependency versions will save a teammate.",
        "A stubborn bug yields to persistence. Stay in the debugger one more hour.",
        "Resist the shiny new framework. Your boring stack is quietly winning.",
    ],
    "Gemini": [
        "Two branches diverge. You will merge them with grace and only one conflict.",
        "A conversation in a code review changes your mind. Let it.",
        "Your context switching is a superpower today, and a curse tomorrow.",
    ],
    "Cancer": [
        "Protect your uptime like you protect your feelings: with good alerts.",
        "An old notebook holds the answer. Open it before writing new code.",
        "Someone needs mentoring. Your patience will be repaid in pull requests.",
    ],
    "Leo": [
        "Your demo will be flawless. The applause is real this time.",
        "Take credit for the model, share credit for the pipeline.",
        "A dashboard you built will be screenshotted by an executive.",
    ],
    "Virgo": [
        "Your tests catch a bug nobody else would have seen. Nobody will thank you. It counts.",
        "Clean up one config file and the whole system feels lighter.",
        "Precision beats speed today. Read the error message twice.",
    ],
    "Libra": [
        "You will balance cost against latency and, for once, both sides are happy.",
        "A disagreement about naming ends in harmony and a style guide.",
        "Fairness in code review returns to you as fewer 3 a.m. pages.",
    ],
    "Scorpio": [
        "A hidden dependency reveals itself. Root it out without mercy.",
        "Your secrets are safe in the secret manager. Your .env file is another story.",
        "Trust the data, not the person describing it.",
    ],
    "Sagittarius": [
        "An adventurous migration to a new cloud region succeeds, mostly.",
        "Your curiosity leads you to a log line that explains everything.",
        "Aim high with the roadmap. Land the first milestone by Friday.",
    ],
    "Capricorn": [
        "Discipline pays off: the retraining pipeline you automated runs while you sleep.",
        "A long-term investment in monitoring quietly prevents a disaster.",
        "Climb one abstraction level. The view is better and the bugs are fewer.",
    ],
    "Aquarius": [
        "Your unconventional architecture diagram will confuse, then inspire.",
        "A tool you built for yourself becomes the team's favorite.",
        "Think about the humans on the other side of the API today.",
    ],
    "Pisces": [
        "Intuition guides your hyperparameter search better than grid search would.",
        "Go with the flow of the data pipeline. Do not fight the schema.",
        "A dream about Kubernetes is not a sign. Rest anyway.",
    ],
}


def zodiac_sign(d: date) -> str:
    for sign, (month, day) in _SIGN_STARTS:
        if (d.month, d.day) < (month, day):
            return sign
    return "Capricorn"


def horoscope_for(birthday: date, today: date | None = None) -> tuple[str, str]:
    """Return (sign, message). The message is stable for a given sign and calendar day."""
    today = today or date.today()
    sign = zodiac_sign(birthday)
    rng = random.Random(f"{sign}:{today.isoformat()}")
    return sign, rng.choice(MESSAGES[sign])
