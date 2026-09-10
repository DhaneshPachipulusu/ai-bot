"""How the candidate delivered their answers, as distinct from what they knew.

Kept deliberately separate from the competency score. Delivery is coachable and
worth telling a student about - looking away for most of an interview is real,
actionable feedback - but it is not evidence of engineering ability, and folding
it into one number does two bad things: it lets a confident bluffer outscore a
nervous engineer, and it puts accent, nerves and microphone quality into a
figure that gets used to rank people.

Everything here is measured. The previous "pace" and "confidence" scores were
derived from answer word count, so they were a second reading of answer length
wearing different names, and came out identical for every candidate tested.
"""

from typing import Optional

# Conversational speech sits around 110-150 wpm. Outside this band is worth
# mentioning to a candidate; inside it is not worth commenting on.
COMFORTABLE_WPM = (110, 150)

# Below this many camera samples the eye-contact figure is noise, usually
# because the candidate had the camera off for most of the answer.
MIN_EYE_SAMPLES = 8

FILLERS = ("um", "uh", "like", "basically", "actually", "so yeah", "you know",
           "i mean", "sort of", "kind of")


def _fmt_pct(x: float) -> str:
    return "%d%%" % round(x * 100)


def summarise_delivery(conversation: list) -> Optional[dict]:
    """Aggregate per-answer delivery signals across an interview.

    Returns None when nothing was measured, so a text-only interview reports no
    delivery section at all rather than a section full of zeroes.
    """
    words = 0
    seconds = 0
    looking = 0
    eye_samples = 0
    longest_pause = 0.0
    fillers = 0
    answers = 0

    for turn in conversation:
        if turn.get("role") != "candidate":
            continue
        text = (turn.get("text") or "").strip()
        if not text:
            continue
        answers += 1
        low = text.lower()
        words += len(text.split())
        fillers += sum(low.count(f) for f in FILLERS)

        d = turn.get("delivery") or {}
        dur = d.get("duration_seconds") or turn.get("duration_seconds")
        if isinstance(dur, (int, float)) and dur > 0:
            seconds += dur
        samples = d.get("eye_contact_samples") or 0
        ratio = d.get("eye_contact_ratio")
        if isinstance(samples, int) and samples > 0 and ratio is not None:
            eye_samples += samples
            looking += ratio * samples
        pause = d.get("longest_pause_seconds")
        if isinstance(pause, (int, float)):
            longest_pause = max(longest_pause, float(pause))

    if not answers:
        return None

    out = {"answers": answers, "observations": [], "measured": []}

    if seconds > 0:
        wpm = words / (seconds / 60.0)
        out["words_per_minute"] = round(wpm)
        out["speaking_seconds"] = int(seconds)
        out["measured"].append("pace")
        lo, hi = COMFORTABLE_WPM
        if wpm < lo:
            out["observations"].append(
                "You spoke at about %d words a minute, which is on the slow "
                "side. Some of that is thinking time and that is fine, but in a "
                "30-minute screen it limits how much ground you cover."
                % round(wpm))
        elif wpm > hi:
            out["observations"].append(
                "You spoke at about %d words a minute, which is fast. "
                "Interviewers taking notes will miss things - slowing down on "
                "the technical parts specifically will help."
                % round(wpm))
        else:
            out["observations"].append(
                "Your speaking pace was comfortable, around %d words a minute."
                % round(wpm))

    if eye_samples >= MIN_EYE_SAMPLES:
        ratio = looking / eye_samples
        out["eye_contact_ratio"] = round(ratio, 2)
        out["eye_contact_samples"] = eye_samples
        out["measured"].append("eye contact")
        if ratio < 0.4:
            out["observations"].append(
                "You were looking at the camera %s of the time. In a video "
                "interview that reads as low engagement even when the answer is "
                "good. Try putting the camera at eye level and looking at the "
                "lens rather than your own image." % _fmt_pct(ratio))
        elif ratio < 0.65:
            out["observations"].append(
                "You held eye contact %s of the time - workable, and worth "
                "pushing higher on the answers that matter most."
                % _fmt_pct(ratio))
        else:
            out["observations"].append(
                "You held eye contact %s of the time, which is strong."
                % _fmt_pct(ratio))
    elif eye_samples:
        out["observations"].append(
            "Not enough camera data to judge eye contact - the camera was off "
            "for most of the interview.")

    # Only meaningful for a spoken answer. Counting "um" in text a
    # candidate typed says nothing about how they present.
    if words and seconds > 0:
        per_100 = fillers / (words / 100.0)
        out["fillers_per_100_words"] = round(per_100, 1)
        out["measured"].append("filler words")
        if per_100 > 6:
            out["observations"].append(
                "Filler words came in at about %.0f per 100 words. A short "
                "pause reads better than \"um\" - it sounds considered rather "
                "than uncertain." % per_100)

    if longest_pause >= 8:
        out["longest_pause_seconds"] = round(longest_pause)
        out["measured"].append("pauses")
        out["observations"].append(
            "Your longest mid-answer silence was about %d seconds. Saying "
            "\"let me think about that for a second\" keeps the interviewer "
            "with you." % round(longest_pause))

    if not out["measured"]:
        return None
    return out
