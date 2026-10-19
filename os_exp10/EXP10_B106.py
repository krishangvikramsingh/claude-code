"""
Experiment No. 10 : Disk Scheduling Algorithms
Subject : Operating Systems  (NMIMS Mumbai - MPSTME)
Name    : Krishang Vikram Singh
Roll No : B106
Batch   : C1
Class   : B.Tech CE
DOS & DOE : 20/10/24

Implements FCFS, SSTF, SCAN, C-SCAN, LOOK and C-LOOK.
Head moves toward the nearest end first (as in the manual's example).
The return jump in C-SCAN / C-LOOK is NOT counted as head movement.
"""


def fcfs(req, head, disk_end):
    order, cur, total = [], head, 0
    for r in req:
        total += abs(r - cur)
        cur = r
        order.append(r)
    return order, total


def sstf(req, head, disk_end):
    pending, order, cur, total = list(req), [], head, 0
    while pending:
        nxt = min(pending, key=lambda r: abs(r - cur))
        total += abs(nxt - cur)
        cur = nxt
        order.append(nxt)
        pending.remove(nxt)
    return order, total


def _direction(req, head, disk_end):
    # go toward nearest end first: down if closer to 0, else up
    return "down" if head <= disk_end - head else "up"


def scan(req, head, disk_end):
    lo = sorted(r for r in req if r < head)
    hi = sorted(r for r in req if r >= head)
    if _direction(req, head, disk_end) == "down":
        order = lo[::-1] + hi
        total = head + (hi[-1] if hi else 0)          # head->0, then 0->highest
    else:
        order = hi + lo[::-1]
        total = (disk_end - head) + (disk_end - (lo[0] if lo else disk_end))
    return order, total


def cscan(req, head, disk_end):
    lo = sorted(r for r in req if r < head)
    hi = sorted(r for r in req if r >= head)
    if _direction(req, head, disk_end) == "down":
        order = lo[::-1] + hi[::-1]
        total = head + (disk_end - (hi[0] if hi else disk_end))   # ->0, jump, ->down to lowest upper req
    else:
        order = hi + lo
        total = (disk_end - head) + (lo[-1] if lo else 0)          # ->end, jump, 0->highest lower req
    return order, total


def look(req, head, disk_end):
    lo = sorted(r for r in req if r < head)
    hi = sorted(r for r in req if r >= head)
    if _direction(req, head, disk_end) == "down":
        order = lo[::-1] + hi
    else:
        order = hi + lo[::-1]
    total, cur = 0, head
    for r in order:
        total += abs(r - cur)
        cur = r
    return order, total


def clook(req, head, disk_end):
    lo = sorted(r for r in req if r < head)
    hi = sorted(r for r in req if r >= head)
    if _direction(req, head, disk_end) == "down":
        order = lo[::-1] + hi[::-1]
    else:
        order = hi + lo
    total, cur = 0, head
    for i, r in enumerate(order):
        # skip the return jump (between the two sweeps)
        jump = (i == len(lo) and lo and hi) if _direction(req, head, disk_end) == "down" \
            else (i == len(hi) and hi and lo)
        if not jump:
            total += abs(r - cur)
        cur = r
    return order, total


if __name__ == "__main__":
    print("Name: Krishang Vikram Singh | Roll No: B106 | Batch: C1 | Class: B.Tech CE")
    print("DOS & DOE: 20/10/24\n")

    # Manual's example is the default; press Enter to accept it
    s = input("Enter request queue (space separated) [95 180 34 119 11 123 62 64]: ").strip()
    queue = list(map(int, s.split())) if s else [95, 180, 34, 119, 11, 123, 62, 64]
    h = input("Enter initial head position [50]: ").strip()
    head = int(h) if h else 50
    e = input("Enter last (tail) track [199]: ").strip()
    end = int(e) if e else 199

    algos = [("FCFS", fcfs), ("SSTF", sstf), ("SCAN", scan),
             ("C-SCAN", cscan), ("LOOK", look), ("C-LOOK", clook)]
    results = {}
    print(f"\nQueue: {queue}   Head: {head}   Tail track: {end}\n")
    for name, fn in algos:
        order, total = fn(queue, head, end)
        results[name] = total
        print(f"{name:7s} order: {head} -> " + " -> ".join(map(str, order)))
        print(f"{'':7s} total head movement (seek time) = {total} tracks\n")

    best = min(results, key=results.get)
    print("Summary:", results)
    print(f"Best (least head movement): {best} = {results[best]} tracks")
