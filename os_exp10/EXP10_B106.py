def fcfs(req, head, end):
    order = list(req)
    total, cur = 0, head
    for r in order:
        total += abs(r - cur)
        cur = r
    return order, total


def sstf(req, head, end):
    pending = list(req)
    order = []
    total, cur = 0, head
    while pending:
        nxt = min(pending, key=lambda r: abs(r - cur))
        total += abs(nxt - cur)
        cur = nxt
        order.append(nxt)
        pending.remove(nxt)
    return order, total


def go_down(head, end):
    return head <= end - head


def scan(req, head, end):
    lo = sorted(r for r in req if r < head)
    hi = sorted(r for r in req if r >= head)
    if go_down(head, end):
        order = lo[::-1] + hi
        total = head + (hi[-1] if hi else 0)
    else:
        order = hi + lo[::-1]
        total = (end - head) + (end - lo[0] if lo else 0)
    return order, total


def cscan(req, head, end):
    lo = sorted(r for r in req if r < head)
    hi = sorted(r for r in req if r >= head)
    if go_down(head, end):
        order = lo[::-1] + hi[::-1]
        total = head + (end - hi[0] if hi else 0)
    else:
        order = hi + lo
        total = (end - head) + (lo[-1] if lo else 0)
    return order, total


def look(req, head, end):
    lo = sorted(r for r in req if r < head)
    hi = sorted(r for r in req if r >= head)
    order = lo[::-1] + hi if go_down(head, end) else hi + lo[::-1]
    total, cur = 0, head
    for r in order:
        total += abs(r - cur)
        cur = r
    return order, total


def clook(req, head, end):
    lo = sorted(r for r in req if r < head)
    hi = sorted(r for r in req if r >= head)
    if go_down(head, end):
        first, second = lo[::-1], hi[::-1]
    else:
        first, second = hi, lo
    total, cur = 0, head
    for r in first:
        total += abs(r - cur)
        cur = r
    for i, r in enumerate(second):
        if i > 0 or not first:
            total += abs(r - cur)
        cur = r
    return first + second, total


print("Name: Krishang Vikram Singh | Roll No: B106 | Batch: C1 | Class: B.Tech CE")
print("DOS & DOE: 20/10/24\n")

s = input("Enter request queue: ").split()
queue = [int(x) for x in s] if s else [95, 180, 34, 119, 11, 123, 62, 64]
head = int(input("Enter head position: ") or 50)
end = int(input("Enter last track: ") or 199)

algos = [("FCFS", fcfs), ("SSTF", sstf), ("SCAN", scan),
         ("C-SCAN", cscan), ("LOOK", look), ("C-LOOK", clook)]
results = {}

print("\nQueue:", queue, " Head:", head, " Last track:", end, "\n")
for name, fn in algos:
    order, total = fn(queue, head, end)
    results[name] = total
    print(name, "order:", head, "->", " -> ".join(map(str, order)))
    print(name, "total seek time =", total, "\n")

best = min(results, key=results.get)
print("Least head movement:", best, "=", results[best])
