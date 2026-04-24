from collections import Counter, defaultdict

import pandas as pd

START = "(start)"
CONVERSION = "(conversion)"
NULL = "(null)"


def journey_paths(events: pd.DataFrame) -> list[tuple[list[str], bool]]:
    paths: list[tuple[list[str], bool]] = []
    for _, group in events.groupby("journey_id", sort=False):
        ordered = group.sort_values(["timestamp", "event_id"])
        channels = ordered.loc[ordered["event_type"].isin(["impression", "click"]), "channel"].tolist()
        collapsed = [channel for index, channel in enumerate(channels) if index == 0 or channel != channels[index - 1]]
        converted = bool((ordered["event_type"] == "conversion").any())
        paths.append((collapsed, converted))
    return paths


def transition_probabilities(paths: list[tuple[list[str], bool]]) -> dict[str, dict[str, float]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for channels, converted in paths:
        sequence = [START, *channels, CONVERSION if converted else NULL]
        for source, target in zip(sequence, sequence[1:], strict=False):
            counts[source][target] += 1
    return {
        source: {target: value / sum(targets.values()) for target, value in targets.items()}
        for source, targets in counts.items()
    }


def _conversion_probability(transitions: dict[str, dict[str, float]], steps: int = 100) -> float:
    state = {START: 1.0}
    converted = 0.0
    for _ in range(steps):
        next_state: dict[str, float] = defaultdict(float)
        for source, probability in state.items():
            for target, transition in transitions.get(source, {NULL: 1.0}).items():
                mass = probability * transition
                if target == CONVERSION:
                    converted += mass
                elif target != NULL:
                    next_state[target] += mass
        state = next_state
        if sum(state.values()) < 1e-12:
            break
    return min(converted, 1.0)


def removal_effects(events: pd.DataFrame) -> pd.DataFrame:
    """Estimate normalized Markov removal effects per channel."""
    paths = journey_paths(events)
    baseline = _conversion_probability(transition_probabilities(paths))
    channels = sorted({channel for path, _ in paths for channel in path})
    effects: list[dict[str, float | str]] = []
    for channel in channels:
        removed = [([item for item in path if item != channel], converted) for path, converted in paths]
        probability = _conversion_probability(transition_probabilities(removed))
        effect = max(0.0, (baseline - probability) / baseline) if baseline else 0.0
        effects.append({"channel": channel, "removal_effect": effect})
    report = pd.DataFrame(effects)
    total = report["removal_effect"].sum() if not report.empty else 0.0
    report["attribution_share"] = report["removal_effect"] / total if total else 0.0
    return report.sort_values("attribution_share", ascending=False).reset_index(drop=True)
