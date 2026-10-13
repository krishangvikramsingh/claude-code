def fifo(pages, frames):
    mem, faults, steps = [], 0, []
    for p in pages:
        if p not in mem:
            faults += 1
            if len(mem) == frames:
                mem.pop(0)
            mem.append(p)
            steps.append((p, list(mem), "Fault"))
        else:
            steps.append((p, list(mem), "Hit"))
    return faults, steps


def lru(pages, frames):
    mem, faults, steps = [], 0, []
    for p in pages:
        if p in mem:
            mem.remove(p)
            mem.append(p)
            steps.append((p, list(mem), "Hit"))
        else:
            faults += 1
            if len(mem) == frames:
                mem.pop(0)
            mem.append(p)
            steps.append((p, list(mem), "Fault"))
    return faults, steps


def optimal(pages, frames):
    mem, faults, steps = [], 0, []
    for i, p in enumerate(pages):
        if p in mem:
            steps.append((p, list(mem), "Hit"))
            continue
        faults += 1
        if len(mem) < frames:
            mem.append(p)
        else:
            future = pages[i + 1:]
            victim = max(mem, key=lambda q: future.index(q) if q in future else len(future) + 1)
            mem[mem.index(victim)] = p
        steps.append((p, list(mem), "Fault"))
    return faults, steps


def show(name, pages, frames, algo):
    faults, steps = algo(pages, frames)
    print(f"\n=== {name} ({frames} frames) ===")
    print(f"{'Page':<6}{'Frames':<20}Result")
    for p, mem, res in steps:
        print(f"{p:<6}{str(mem):<20}{res}")
    print(f"Total Page Faults = {faults}")
    print(f"Page Hits         = {len(pages) - faults}")
    print(f"Fault Rate        = {faults / len(pages):.2f}")
    return faults


if __name__ == "__main__":
    print("Name: Krishang Vikram Singh | Roll No: B106 | Batch: C1 | Class: B.Tech CE | DOS & DOE: 13/10/24")
    ref = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
    n = 3
    print("Reference string:", ref)
    r = {nm: show(nm, ref, n, f) for nm, f in
         [("FIFO", fifo), ("LRU", lru), ("Optimal", optimal)]}
    print("\nSummary:", r)
