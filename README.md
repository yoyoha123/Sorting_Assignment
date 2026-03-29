# Sorting_Assignment

## Student Name:
- Yoav Hamburger

## Selected Algorithms
- 3 - Insertion Sort
- 4 - Merge Sort
- 5 - Quick Sort

## How To Run
Example command from the assignment:

`py run_experiments.py -a 3 4 5 -s 100 500 3000 -e 1 -r 20`

CLI arguments:
- `-a`: exactly 3 algorithm IDs to compare (supported IDs: `3`, `4`, `5`)
- `-s`: array sizes
- `-e`: nearly-sorted experiment type (`1` = 5% noise, `2` = 20% noise)
- `-r`: repetitions per size

The script saves:
- `result1.png` - random arrays experiment
- `result2.png` - nearly sorted arrays experiment

## Result 1 - Random Arrays
![Random arrays comparison](result1.png)

Insertion Sort grows much faster than Merge Sort and Quick Sort as `n` increases, which matches expected time complexity behavior (`O(n^2)` vs `O(n log n)`).  
Merge Sort and Quick Sort remain significantly faster and scale better for larger inputs.

## Result 2 - Nearly Sorted Arrays
![Nearly sorted comparison](result2.png)

With 5% noise, Insertion Sort becomes noticeably faster than in fully random arrays because the input is close to sorted.  
Merge Sort and Quick Sort are still fast, with Quick Sort generally the fastest in this run; overall ranking is similar, but the gap to Insertion Sort is reduced compared to `result1.png`.
