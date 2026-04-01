from __future__ import annotations

import argparse
import math
import statistics
import time
from dataclasses import dataclass
from random import Random
from typing import Callable

import matplotlib.pyplot as plt


NOISE_LEVEL_BY_EXPERIMENT = {1: 0.05, 2: 0.20}
ALGORITHM_NAMES = {3: "Insertion Sort", 4: "Merge Sort", 5: "Quick Sort"}
DEFAULT_RANDOM_SEED = 42
DEFAULT_SIZES = [
    5_000,
    10_000,
    20_000,
    50_000,
    100_000,
    250_000,
    500_000,
    1_000_000,
]


@dataclass(frozen=True)
class AlgorithmConfig:
    algorithm_id: int
    name: str
    sort_fn: Callable[[list[int]], list[int]]


@dataclass(frozen=True)
class Measurement:
    size: int
    mean_seconds: float
    std_seconds: float


def insertion_sort(values: list[int]) -> list[int]:
    arr = values.copy()
    for i in range(1, len(arr)):
        current = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > current:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = current
    return arr


def _merge(left: list[int], right: list[int]) -> list[int]:
    merged: list[int] = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    if i < len(left):
        merged.extend(left[i:])
    if j < len(right):
        merged.extend(right[j:])
    return merged


def merge_sort(values: list[int]) -> list[int]:
    if len(values) <= 1:
        return values.copy()
    midpoint = len(values) // 2
    left_sorted = merge_sort(values[:midpoint])
    right_sorted = merge_sort(values[midpoint:])
    return _merge(left_sorted, right_sorted)


def _partition(arr: list[int], low: int, high: int) -> int:
    midpoint = (low + high) // 2
    pivot = arr[midpoint]
    i = low - 1
    j = high + 1
    while True:
        i += 1
        while arr[i] < pivot:
            i += 1
        j -= 1
        while arr[j] > pivot:
            j -= 1
        if i >= j:
            return j
        arr[i], arr[j] = arr[j], arr[i]


def quick_sort(values: list[int]) -> list[int]:
    arr = values.copy()
    if len(arr) <= 1:
        return arr
    stack: list[tuple[int, int]] = [(0, len(arr) - 1)]
    while stack:
        low, high = stack.pop()
        if low >= high:
            continue
        pivot_idx = _partition(arr, low, high)
        left_size = pivot_idx - low
        right_size = high - (pivot_idx + 1)
        if left_size > right_size:
            stack.append((low, pivot_idx))
            stack.append((pivot_idx + 1, high))
        else:
            stack.append((pivot_idx + 1, high))
            stack.append((low, pivot_idx))
    return arr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run sorting algorithm experiments and create required plots.",
        epilog=(
            "Course algorithm IDs: 1=Bubble, 2=Selection, 3=Insertion, 4=Merge, 5=Quick. "
            "This file implements 3, 4, 5 only; use e.g. -a 3 4 5."
        ),
    )
    parser.add_argument(
        "-a",
        "--algorithms",
        nargs="+",
        type=int,
        required=True,
        help="Exactly three algorithm IDs for this submission: 3=Insertion, 4=Merge, 5=Quick (course table 1-5; see README).",
    )
    parser.add_argument(
        "-s",
        "--sizes",
        nargs="*",
        type=int,
        default=None,
        help=f"Array sizes (default: {DEFAULT_SIZES}).",
    )
    parser.add_argument(
        "-e",
        "--experiment",
        type=int,
        choices=sorted(NOISE_LEVEL_BY_EXPERIMENT),
        default=1,
        help="Nearly sorted experiment type: 1=5%% noise, 2=20%% noise.",
    )
    parser.add_argument("-r", "--repetitions", type=int, default=10, help="Number of repetitions per array size.")
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED, help="Random seed for reproducibility.")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if len(args.algorithms) != 3:
        raise ValueError("Please provide exactly 3 algorithms using -a.")
    invalid_algorithms = [algorithm_id for algorithm_id in args.algorithms if algorithm_id not in ALGORITHM_NAMES]
    if invalid_algorithms:
        raise ValueError(f"Invalid algorithm IDs: {invalid_algorithms}. Allowed IDs are 3, 4, 5.")
    if len(set(args.algorithms)) != len(args.algorithms):
        raise ValueError("Algorithm IDs must be unique.")
    sizes = args.sizes if args.sizes else DEFAULT_SIZES
    if not sizes:
        raise ValueError("Array sizes list is empty.")
    if any(size <= 0 for size in sizes):
        raise ValueError("All array sizes must be positive integers.")
    if args.repetitions <= 0:
        raise ValueError("Repetitions must be a positive integer.")


def resolve_algorithms(algorithm_ids: list[int]) -> list[AlgorithmConfig]:
    available: dict[int, Callable[[list[int]], list[int]]] = {
        3: insertion_sort,
        4: merge_sort,
        5: quick_sort,
    }
    missing = [algorithm_id for algorithm_id in algorithm_ids if algorithm_id not in available]
    if missing:
        unsupported_names = [ALGORITHM_NAMES.get(algorithm_id, str(algorithm_id)) for algorithm_id in missing]
        raise ValueError(f"Unsupported selections: {unsupported_names}. Use IDs 3, 4, 5.")
    return [
        AlgorithmConfig(algorithm_id=algorithm_id, name=ALGORITHM_NAMES[algorithm_id], sort_fn=available[algorithm_id])
        for algorithm_id in algorithm_ids
    ]


def generate_random_array(size: int, rng: Random) -> list[int]:
    return [rng.randint(0, 1_000_000) for _ in range(size)]


def generate_nearly_sorted_array(size: int, noise_fraction: float, rng: Random) -> list[int]:
    arr = list(range(size))
    swap_count = max(1, round(size * noise_fraction))
    for _ in range(swap_count):
        i = rng.randrange(size)
        j = rng.randrange(size)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def run_experiment(
    algorithms: list[AlgorithmConfig],
    sizes: list[int],
    repetitions: int,
    base_array_builder: Callable[[int, Random], list[int]],
    seed: int,
) -> dict[str, list[Measurement]]:
    metrics: dict[str, list[Measurement]] = {algorithm.name: [] for algorithm in algorithms}
    for size in sizes:
        for algorithm in algorithms:
            runs: list[float] = []
            for rep_idx in range(repetitions):
                rng = Random(seed + (size * 10_000) + rep_idx)
                base_array = base_array_builder(size, rng)
                start = time.perf_counter()
                algorithm.sort_fn(base_array)
                elapsed = time.perf_counter() - start
                runs.append(elapsed)
            mean_seconds = statistics.fmean(runs)
            std_seconds = statistics.stdev(runs) if len(runs) > 1 else 0.0
            metrics[algorithm.name].append(Measurement(size=size, mean_seconds=mean_seconds, std_seconds=std_seconds))
    return metrics


def plot_results(metrics: dict[str, list[Measurement]], output_path: str, title: str) -> None:
    plt.figure(figsize=(10, 6))
    prop_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", ["#1f77b4", "#ff7f0e", "#2ca02c"])
    all_sizes: list[int] = []
    for idx, (name, measurements) in enumerate(metrics.items()):
        if not measurements:
            continue
        color = prop_cycle[idx % len(prop_cycle)]
        x = [m.size for m in measurements]
        all_sizes.extend(x)
        y = [m.mean_seconds for m in measurements]
        yerr = [0.0 if math.isnan(m.std_seconds) else m.std_seconds for m in measurements]
        lower = [max(0.0, yi - ei) for yi, ei in zip(y, yerr)]
        upper = [yi + ei for yi, ei in zip(y, yerr)]
        plt.fill_between(x, lower, upper, alpha=0.25, color=color)
        plt.plot(x, y, marker="o", markersize=8, label=name, color=color)
        if any(e > 0 for e in yerr):
            plt.errorbar(x, y, yerr=yerr, fmt="none", capsize=3, alpha=0.65, linewidth=1, color=color, ecolor=color)
    if all_sizes:
        lo, hi = min(all_sizes), max(all_sizes)
        if lo > 0 and hi / lo >= 2:
            plt.xscale("log")
            plt.xlim(lo * 0.85, hi * 1.15)
        else:
            plt.xlim(0.0, hi * 1.05 if hi > 0 else 1.0)
    plt.xlabel("Array Size (n)")
    plt.ylabel("Running Time (seconds)")
    plt.title(title)
    plt.legend()
    plt.grid(True, which="both", alpha=0.25)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def print_summary(metrics: dict[str, list[Measurement]]) -> None:
    print("\nResults (mean +/- std in seconds):")
    for name, measurements in metrics.items():
        print(f"\n{name}")
        for measurement in measurements:
            print(f"  n={measurement.size:<8} {measurement.mean_seconds:.6f} +/- {measurement.std_seconds:.6f}")


def main() -> None:
    args = parse_args()
    validate_args(args)
    algorithms = resolve_algorithms(args.algorithms)
    sizes = sorted(args.sizes if args.sizes else DEFAULT_SIZES)
    noise_fraction = NOISE_LEVEL_BY_EXPERIMENT[args.experiment]

    random_metrics = run_experiment(
        algorithms=algorithms,
        sizes=sizes,
        repetitions=args.repetitions,
        base_array_builder=generate_random_array,
        seed=args.seed,
    )
    plot_results(
        metrics=random_metrics,
        output_path="result1.png",
        title="Sorting Performance on Random Arrays",
    )
    print_summary(random_metrics)

    nearly_sorted_metrics = run_experiment(
        algorithms=algorithms,
        sizes=sizes,
        repetitions=args.repetitions,
        base_array_builder=lambda size, rng: generate_nearly_sorted_array(size, noise_fraction, rng),
        seed=args.seed + 99,
    )
    noise_percent = int(noise_fraction * 100)
    plot_results(
        metrics=nearly_sorted_metrics,
        output_path="result2.png",
        title=f"Sorting Performance on Nearly Sorted Arrays ({noise_percent}% noise)",
    )
    print_summary(nearly_sorted_metrics)

    print("\nSaved: result1.png and result2.png")


if __name__ == "__main__":
    main()
