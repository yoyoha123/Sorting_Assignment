from __future__ import annotations

import argparse
import math
import statistics
import sys
import time
from dataclasses import dataclass
from random import Random
from typing import Callable

import matplotlib.pyplot as plt


NOISE_LEVEL_BY_EXPERIMENT = {1: 0.05, 2: 0.20}
ALGORITHM_NAMES = {
    1: "Bubble Sort",
    2: "Selection Sort",
    3: "Insertion Sort",
    4: "Merge Sort",
    5: "Quick Sort",
}
INSERTION_SORT_ID = 3
MAX_INSERTION_SORT_SIZE = 20_000
NOT_IMPLEMENTED_IDS = frozenset({1, 2})
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
    skipped: bool = False


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
        epilog="Algorithm IDs: 1=Bubble, 2=Selection, 3=Insertion, 4=Merge, 5=Quick. IDs 1-2 are not implemented (warning only).",
    )
    parser.add_argument(
        "-a",
        "--algorithms",
        nargs="+",
        type=int,
        required=True,
        help="Exactly three algorithm IDs from 1–5 (see epilog). IDs 1–2 print Not implemented.",
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
        raise ValueError(f"Invalid algorithm IDs: {invalid_algorithms}. Allowed IDs are 1–5.")
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
    implemented: dict[int, Callable[[list[int]], list[int]]] = {
        3: insertion_sort,
        4: merge_sort,
        5: quick_sort,
    }
    configs: list[AlgorithmConfig] = []
    for algorithm_id in algorithm_ids:
        name = ALGORITHM_NAMES[algorithm_id]
        if algorithm_id in NOT_IMPLEMENTED_IDS:
            print(f"Warning: {name} (ID {algorithm_id}): Not implemented - skipping.")
            continue
        sort_fn = implemented.get(algorithm_id)
        if sort_fn is None:
            print(f"Warning: {name} (ID {algorithm_id}): Not implemented - skipping.")
            continue
        configs.append(AlgorithmConfig(algorithm_id=algorithm_id, name=name, sort_fn=sort_fn))
    if not configs:
        raise ValueError("No implemented algorithms left after resolving -a; use at least one of IDs 3, 4, 5.")
    return configs


def generate_random_array(size: int, rng: Random) -> list[int]:
    return [rng.randint(0, 1_000_000) for _ in range(size)]


def generate_nearly_sorted_array(size: int, noise_fraction: float, rng: Random) -> list[int]:
    arr = list(range(size))
    if size == 0:
        return arr
    k = max(1, min(size, round(size * noise_fraction)))
    indices = rng.sample(range(size), k)
    block = [arr[i] for i in indices]
    rng.shuffle(block)
    for idx, value in zip(indices, block, strict=True):
        arr[idx] = value
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
            if algorithm.algorithm_id == INSERTION_SORT_ID and size > MAX_INSERTION_SORT_SIZE:
                print(
                    f"Warning: Skipping Insertion Sort for n={size} (cap {MAX_INSERTION_SORT_SIZE}) to avoid long runtimes."
                )
                metrics[algorithm.name].append(
                    Measurement(size=size, mean_seconds=math.nan, std_seconds=math.nan, skipped=True)
                )
                continue
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
        active = [m for m in measurements if not m.skipped and not math.isnan(m.mean_seconds)]
        if not active:
            continue
        color = prop_cycle[idx % len(prop_cycle)]
        x = [m.size for m in active]
        all_sizes.extend(x)
        y = [m.mean_seconds for m in active]
        yerr = [0.0 if math.isnan(m.std_seconds) else m.std_seconds for m in active]
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
            if measurement.skipped:
                print(f"  n={measurement.size:<8} skipped (Insertion Sort > {MAX_INSERTION_SORT_SIZE})")
                continue
            print(f"  n={measurement.size:<8} {measurement.mean_seconds:.6f} +/- {measurement.std_seconds:.6f}")


def main() -> None:
    args = parse_args()
    validate_args(args)
    sizes = sorted(args.sizes if args.sizes else DEFAULT_SIZES)
    max_n = max(sizes) if sizes else 1
    merge_depth_budget = max(5000, (max_n.bit_length() + 8) * 200)
    sys.setrecursionlimit(min(1_000_000, max(sys.getrecursionlimit(), merge_depth_budget)))
    algorithms = resolve_algorithms(args.algorithms)
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
