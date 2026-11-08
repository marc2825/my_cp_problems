NEG = -10**30


# 直線 y = ax + b の追加、最大値取得
class LiChao:
    def __init__(self, n):
        self.n = n
        self.seg = [None] * (4 * (n + 1))

    def add(self, a, b):
        k, l, r = 1, 0, self.n

        while True:
            if self.seg[k] is None:
                self.seg[k] = (a, b)
                return

            c, d = self.seg[k]
            m = (l + r) // 2

            left = a * l + b > c * l + d
            mid = a * m + b > c * m + d

            if mid:
                self.seg[k], (a, b) = (a, b), (c, d)

            if l == r:
                return

            if left != mid:
                k *= 2
                r = m
            else:
                k = k * 2 + 1
                l = m + 1

    def query(self, x):
        k, l, r = 1, 0, self.n
        res = NEG

        while True:
            if self.seg[k] is not None:
                a, b = self.seg[k]
                res = max(res, a * x + b)

            if l == r:
                return res

            m = (l + r) // 2

            if x <= m:
                k *= 2
                r = m
            else:
                k = k * 2 + 1
                l = m + 1


N = int(input())
A = list(map(int, input().split()))

G = [[] for _ in range(N)]

for _ in range(N - 1):
    u, v = map(int, input().split())
    u -= 1
    v -= 1
    G[u].append(v)
    G[v].append(u)

size = [0] * N
parent = [-1] * N
used = [False] * N

ans = A[:]
best = [NEG] * N
dp = [NEG] * N


def get_centroid(s):
    order = [s]
    parent[s] = -1

    for v in order:
        for u in G[v]:
            if used[u] or u == parent[v]:
                continue
            parent[u] = v
            order.append(u)

    for v in reversed(order):
        size[v] = 1
        for u in G[v]:
            if not used[u] and parent[u] == v:
                size[v] += size[u]

    n = len(order)

    for v in order:
        mx = n - size[v]

        for u in G[v]:
            if not used[u] and parent[u] == v:
                mx = max(mx, size[u])

        if mx * 2 <= n:
            return v


def collect(c, root):
    comp = []
    stack = [(root, c, 1, A[c] + A[root] - 1)]
    max_depth = 1

    while stack:
        v, p, d, b = stack.pop()
        comp.append((v, p, d, b))
        max_depth = max(max_depth, d)

        for u in G[v]:
            if used[u] or u == p:
                continue

            nd = d + 1
            stack.append((u, v, nd, b + A[u] - nd))

    return comp, max_depth


def solve(s):
    c = get_centroid(s)

    comps = []
    max_depth = 1

    for u in G[c]:
        if used[u]:
            continue

        comp, d = collect(c, u)
        comps.append(comp)
        max_depth = max(max_depth, d)

    if comps:
        # 左 -> 右
        cht = LiChao(max_depth)
        cht.add(0, A[c])

        for comp in comps:
            for v, p, d, b in comp:
                best[v] = cht.query(d)

            for v, p, d, b in comp:
                cht.add(-d, b)

        # 右 -> 左
        cht = LiChao(max_depth)
        cht.add(0, A[c])

        for comp in reversed(comps):
            for v, p, d, b in comp:
                best[v] = max(best[v], cht.query(d))

            for v, p, d, b in comp:
                cht.add(-d, b)

        best_c = A[c]

        for comp in comps:
            for v, p, d, b in comp:
                dp[v] = b - A[c] + best[v]
                best_c = max(best_c, dp[v])

            # 部分木最大値を子から親へ伝播
            for v, p, d, b in reversed(comp):
                ans[v] = max(ans[v], dp[v])

                if p != c:
                    dp[p] = max(dp[p], dp[v])

        ans[c] = max(ans[c], best_c)

    used[c] = True

    for u in G[c]:
        if not used[u]:
            solve(u)


solve(0)

print(min(ans))