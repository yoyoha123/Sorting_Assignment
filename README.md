# Sorting_Assignment

## Student Name
- **Yoav Hamburger**

## Selected Algorithms
This submission implements and compares (course IDs **3**, **4**, **5**):
- **3** – Insertion Sort  
- **4** – Merge Sort  
- **5** – Quick Sort  

IDs **1** (Bubble) and **2** (Selection) are listed in the assignment table but are **not implemented**; if you include them in `-a`, the program prints a warning and continues with the remaining algorithms.

---

## Quick Start

```bash
python run_experiments.py -a 3 4 5 -e 1 -r 10
```

On Windows, if `python` is not on your PATH, use `py` instead:

```bash
py run_experiments.py -a 3 4 5 -e 1 -r 10
```

**Omit `-s`** to use the built-in default size list from **n = 100** through **n = 1,000,000** (log-spaced steps). That default is tuned so curves show both small-`n` behavior and large-scale growth without typing a long size list.

Other useful flags:
- **`-s`** – explicit sizes (overrides the default)
- **`-e 1`** – nearly sorted experiment with **5%** of indices perturbed; **`-e 2`** – **20%**
- **`-r`** – repetitions per size (more repetitions → smoother mean/std)

---

## Engineering: insertion cap (safety valve)

**Insertion Sort** is **not executed for n > 20,000**. The program prints a warning, records a skipped measurement, and still plots **Merge** and **Quick** at larger sizes.

This is a deliberate **engineering trade-off**: insertion is **O(n²)**; at **n = 1,000,000** a single run could take hours or appear to hang, while **O(n log n)** algorithms remain practical. The cap keeps batch experiments reliable and reproducible on a typical laptop while still showing the quadratic-vs-log-linear gap up to **n = 20,000** for insertion.

---

## Plots: logarithmic X-axis

**`result1.png`** and **`result2.png`** use a **logarithmic scale on the X-axis** (array size **n**).

Sizes span orders of magnitude (from **100** to **1,000,000** in the default configuration). On a linear axis, points at small **n** would collapse near the origin and the **O(n²)** vs **O(n log n)** growth shapes would be hard to read. A log-scaled **n** spreads those points and makes the **different asymptotic growth rates** visible on one figure.

---

## Result 1 – Random arrays
![Random arrays comparison](result1.png)

On **random** data, **Insertion Sort** exhibits **quadratic** growth in practice: many element **shifts** per insert. **Merge Sort** and **Quick Sort** scale as **O(n log n)** in typical cases, so their runtimes grow much more slowly as **n** increases. The plot (log **n**, linear time) highlights that structural gap.

---

## Result 2 – Nearly sorted arrays
![Nearly sorted comparison](result2.png)

**Nearly sorted** inputs are built from a sorted array with a controlled fraction of positions perturbed (experiment types **1** / **2**).

**Insertion Sort** improves **dramatically** here because its inner loop does almost no work when each new key is already close to its final position: in the **best case** (fully sorted input) insertion is **O(n)**; with **small noise** the behavior stays close to that—far fewer **shifts** than on random data.

**Merge Sort** is **O(n log n)** **regardless of input order**: it always performs the same divide-and-merge work, so it does **not** get the same asymptotic “boost” as insertion on nearly sorted data.

Because insertion moves toward **linear-time** behavior while merge (and typical quicksort on this implementation) stay **n log n**, the **performance gap between insertion and the divide-and-conquer sorts closes** compared to **result1**, even though merge remains asymptotically the same class as before.

---

## Outputs
- **`result1.png`** – random arrays  
- **`result2.png`** – nearly sorted arrays (noise level set by **`-e`**)
