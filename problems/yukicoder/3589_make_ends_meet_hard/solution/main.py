MOD = 998244353

def modpow(a, e):
    r = 1
    while e > 0:
        if e & 1:
            r = r * a % MOD
        a = a * a % MOD
        e >>= 1
    return r

def trim(a):
    while a and a[-1] == 0:
        a.pop()

def mul_qs_minus_1(p, s, E):
    if not p:
        return []

    need = min(E + 1, len(p) + s)
    res = [0] * need

    # p(q) * q^s
    if s <= E:
        lim = min(len(p), E + 1 - s)
        for i in range(lim):
            res[i + s] = p[i]

    # - p(q)
    lim = min(len(p), need)
    for i in range(lim):
        res[i] -= p[i]
        if res[i] < 0:
            res[i] += MOD

    trim(res)
    return res

def add_shift_scaled(dst, src, shift, scale, E):
    if not src or scale == 0 or shift > E:
        return

    need = min(E + 1, shift + len(src))
    if len(dst) < need:
        dst.extend([0] * (need - len(dst)))

    length = need - shift
    for i in range(length):
        if src[i] == 0:
            continue
        dst[i + shift] = (dst[i + shift] + src[i] * scale) % MOD


N, M, K = map(int, input().split())

E = N * (N - 1) // 2
R = E - M
S = N - 2

fact = [1] * (E + 1)
ifact = [1] * (E + 1)

for i in range(1, E + 1):
    fact[i] = fact[i - 1] * i % MOD

ifact[E] = modpow(fact[E], MOD - 2)

for i in range(E, 0, -1):
    ifact[i - 1] = ifact[i] * i % MOD

def C(n, r):
    if r < 0 or r > n:
        return 0
    return fact[n] * ifact[r] % MOD * ifact[n - r] % MOD


# dp[r][s] is a polynomial in q.
# r: number of ordinary vertices not reached yet
# s: size of current BFS frontier
dp = [[[] for _ in range(S + 2)] for _ in range(S + 1)]
dp[S][1] = [1]

# Build layers 1,2,...,K-1 without reaching vertex N.
for step in range(K - 1):
    ndp = [[[] for _ in range(S + 2)] for _ in range(S + 1)]

    for r in range(S + 1):
        for s in range(S + 2):
            if not dp[r][s]:
                continue

            cur = dp[r][s][:]  # cur * (q^s - 1)^t

            for t in range(r + 1):
                shift = t * (t - 1) // 2  # free edges inside the next frontier
                ways = C(r, t)

                add_shift_scaled(ndp[r - t][t], cur, shift, ways, E)

                if t != r:
                    cur = mul_qs_minus_1(cur, s, E)

    dp = ndp


# H(q): generating polynomial for dist(1,N)=K in q=1+x.
H = [0] * (E + 1)

# N must have at least one edge to the current frontier: (q^s - 1).
# All edges among the remaining r vertices, between them and N,
# and between them and the current frontier are free.
for r in range(S + 1):
    for s in range(S + 2):
        p = dp[r][s]
        if not p:
            continue

        base = s * r + r + r * (r - 1) // 2

        for i, val in enumerate(p):
            if val == 0:
                continue

            if i + base + s <= E:
                H[i + base + s] += val
                if H[i + base + s] >= MOD:
                    H[i + base + s] -= MOD

            if i + base <= E:
                H[i + base] -= val
                if H[i + base] < 0:
                    H[i + base] += MOD


# We need [x^R] H(1+x). If H(q)=sum_c h_c q^c, then
# [x^R] H(1+x) = sum_c h_c * C(c,R).
ans = 0

for c in range(R, E + 1):
    if H[c] == 0:
        continue
    ans += H[c] * C(c, R)
    ans %= MOD

print(ans)