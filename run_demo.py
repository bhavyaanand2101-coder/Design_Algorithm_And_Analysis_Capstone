"""
run_demo.py
Automated end-to-end Capstone verification script.
Runs:
1. Small Dataset demonstration with DP table output and route plot
2. Metropolitan City Scenario demonstration with 2-Opt and route plot
3. Benchmark suite across all phases
4. Captures complete output trace into output/execution_logs.txt
"""

import sys
import os
import subprocess


def main():
    print("🚀 Starting Automated Capstone Demonstration Suite...")
    os.makedirs("output/charts", exist_ok=True)

    log_path = "output/execution_logs.txt"
    with open(log_path, "w") as log_file:
        def run_cmd(cmd_list, label):
            header = f"\n{'='*75}\nDEMO RUN: {label}\n{'='*75}\n"
            print(header)
            log_file.write(header)
            log_file.flush()

            proc = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            for line in proc.stdout:
                sys.stdout.write(line)
                log_file.write(line)
            proc.wait()

        # 1. Run Small Dataset Demo
        run_cmd([
            ".venv/bin/python", "main.py",
            "--dataset", "data/small_dataset.json",
            "--sort", "quicksort",
            "--prefix", "small"
        ], "Phase 1-3 Demonstration on Small Fleet Dataset (N=10)")

        # 2. Run Metropolitan City Scenario Demo
        run_cmd([
            ".venv/bin/python", "main.py",
            "--dataset", "data/city_courier_scenario.json",
            "--sort", "mergesort",
            "--prefix", "city"
        ], "Phase 1-3 Demonstration on Metropolitan City Scenario (N=50)")

        # 3. Run Benchmark Suite
        run_cmd([
            ".venv/bin/python", "benchmark.py"
        ], "Phase 4 Performance Benchmarking & Scaling Suite")

    print(f"\n🎉 Demonstration run completed! Complete log saved to: {log_path}")


if __name__ == "__main__":
    main()
