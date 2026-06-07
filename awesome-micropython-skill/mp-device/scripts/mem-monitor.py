#!/usr/bin/env python3
"""
mem-monitor.py — Track ESP32 memory usage over time or during a specific operation.
Usage:
  python mem-monitor.py <PORT>                     # One-shot snapshot
  python mem-monitor.py <PORT> --watch <seconds>   # Monitor every N seconds
  python mem-monitor.py <PORT> --run <script.py>   # Measure memory impact of a script
"""

import subprocess, sys, time, argparse

def mpremote(port, code, timeout=10):
    wrapped = f"try:\n"
    for line in code.strip().split("\n"):
        wrapped += f"    {line}\n"
    wrapped += "except Exception as e:\n    print('ERROR:', e)"
    try:
        r = subprocess.run(
            ["mpremote", "connect", port, "exec", wrapped],
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except Exception as e:
        return f"FAILED: {e}"

def snapshot(port):
    """Get current memory stats."""
    out = mpremote(port, "import gc; gc.collect(); print(gc.mem_free(), gc.mem_alloc())")
    try:
        free, alloc = out.split()
        return int(free), int(alloc)
    except:
        print(f"  Parse error: {out}")
        return 0, 0

def main():
    parser = argparse.ArgumentParser(description="Monitor ESP32 memory usage")
    parser.add_argument("port", help="Serial port")
    parser.add_argument("--watch", type=int, metavar="SECONDS", help="Monitor every N seconds (Ctrl+C to stop)")
    parser.add_argument("--run", metavar="SCRIPT", help="Run a script and measure its memory impact")
    args = parser.parse_args()

    if args.run:
        # Before
        free_before, alloc_before = snapshot(args.port)
        print(f"Before:  free={free_before:>8}  alloc={alloc_before:>8}")
        print(f"Running: {args.run}")
        mpremote(args.port, "", timeout=30)  # dummy, we run the script separately
        subprocess.run(["mpremote", "connect", args.port, "run", args.run],
                       capture_output=True, timeout=30)
        # After
        free_after, alloc_after = snapshot(args.port)
        delta = free_before - free_after
        print(f"After:   free={free_after:>8}  alloc={alloc_after:>8}")
        print(f"Impact:  {delta:>8} bytes {'used' if delta > 0 else 'freed'}")
        return

    if args.watch:
        interval = args.watch
        print(f"Monitoring every {interval}s. Press Ctrl+C to stop.")
        print(f"{'Time':>8}  {'Free':>10}  {'Alloc':>10}  {'Delta':>10}")
        prev_free = 0
        try:
            while True:
                free, alloc = snapshot(args.port)
                delta = free - prev_free if prev_free else 0
                ts = time.strftime("%H:%M:%S")
                print(f"{ts:>8}  {free:>10}  {alloc:>10}  {delta:>+10}")
                prev_free = free
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopped.")
        return

    # One-shot
    free, alloc = snapshot(args.port)
    total = free + alloc
    print(f"Free heap:  {free:>8} bytes ({free/1024:.1f} KB)")
    print(f"Allocated:  {alloc:>8} bytes ({alloc/1024:.1f} KB)")
    print(f"Total heap: {total:>8} bytes ({total/1024:.1f} KB)")
    print(f"Used:       {(alloc/total)*100:.1f}%")

if __name__ == "__main__":
    main()
