import sys
import os
import argparse
from core.csv_utils import read_csv_schedule

def compare_csv(file1_path: str, file2_path: str, summary_only: bool = False):
    """
    Compares two CSV schedule files and prints differences in metadata, weekly assignments, and statistics.
    """
    if not os.path.exists(file1_path):
        print(f"Error: File 1 not found: {file1_path}")
        sys.exit(1)
    if not os.path.exists(file2_path):
        print(f"Error: File 2 not found: {file2_path}")
        sys.exit(1)

    sched1, meta1, map1, fest1, _ = read_csv_schedule(file1_path)
    sched2, meta2, map2, fest2, _ = read_csv_schedule(file2_path)

    merged_map = {**map1, **map2}
    def get_fname(fid):
        return merged_map.get(fid, f"F{fid}")

    print("=" * 80)
    print(f" CSV Schedule Comparison")
    print(f" File 1: {file1_path}")
    print(f" File 2: {file2_path}")
    print("=" * 80)

    # 1. Metadata comparison
    all_meta_keys = sorted(set(meta1.keys()).union(set(meta2.keys())))
    print("\n--- Metadata Comparison ---")
    if all_meta_keys:
        for k in all_meta_keys:
            v1 = meta1.get(k, "N/A")
            v2 = meta2.get(k, "N/A")
            match_str = "MATCH" if v1 == v2 else "DIFF"
            print(f"  {k:<18}: File1 = {v1:<15} | File2 = {v2:<15} [{match_str}]")
    else:
        print("  No # Metadata: headers found.")

    # 2. Weekly Assignment Diffs
    all_weeks = sorted(set(sched1.keys()).union(set(sched2.keys())))
    matching_weeks = []
    differing_weeks = []

    for w in all_weeks:
        p1 = sched1.get(w, set())
        p2 = sched2.get(w, set())
        if p1 == p2:
            matching_weeks.append(w)
        else:
            differing_weeks.append((w, p1, p2))

    print(f"\n--- Weekly Assignments ({len(matching_weeks)} matching weeks, {len(differing_weeks)} differing weeks) ---")
    if not summary_only and differing_weeks:
        print(f"  {'Week':<8} | {'File 1 Pharmacies':<30} | {'File 2 Pharmacies':<30}")
        print("  " + "-" * 72)
        for w, p1, p2 in differing_weeks:
            p1_str = ", ".join(get_fname(f) for f in sorted(p1)) if p1 else "None"
            p2_str = ", ".join(get_fname(f) for f in sorted(p2)) if p2 else "None"
            print(f"  Wk {w:<5} | {p1_str:<30} | {p2_str:<30}")
    elif summary_only and differing_weeks:
        print(f"  {len(differing_weeks)} weeks differ in assignments.")
    else:
        print("  [MATCH] All weekly assignments are IDENTICAL between File 1 and File 2!")

    # 3. Pharmacy Workload Comparison
    print("\n--- Pharmacy Shift Statistics Comparison ---")
    print(f"  {'Farmacia':<18} | {'File 1 Shifts':<15} | {'File 2 Shifts':<15} | {'Delta':<10}")
    print("  " + "-" * 65)
    for fid in range(1, 11):
        c1 = sum(fid in p for p in sched1.values())
        c2 = sum(fid in p for p in sched2.values())
        delta = c2 - c1
        delta_str = f"{delta:+d}" if delta != 0 else "0"
        fname = get_fname(fid)
        print(f"  {fname:<18} | {c1:<15} | {c2:<15} | {delta_str:<10}")

    print("=" * 80 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="Comparator script to compare two generated CSV schedule files."
    )
    parser.add_argument('file1', help="Path to first CSV schedule file.")
    parser.add_argument('file2', help="Path to second CSV schedule file.")
    parser.add_argument('--summary-only', action='store_true', help="Only show summary counts instead of detailed weekly diffs.")

    args = parser.parse_args()
    compare_csv(args.file1, args.file2, summary_only=args.summary_only)

if __name__ == '__main__':
    main()
