INF = 10**30

# 間隔 d の状態から、片側を合計 x だけ逆向きに動かすための最小操作回数
def calc(x, d):
    total = 0
    k = 0
    while total < x:
        total = total * 2 + d
        k += 1
    return k


# 目標間隔 D、逆向きの移動距離 (A, B) について、A 側を先に完成させる最小操作回数
def solve(A, B, D):
    res = INF

    for q in range(30):
        H = (1 << q) * D
        P = (1 << q) - 1

        l = max(0, P - (B - 1) // D)
        if A > H:
            l = max(l, (A - H + D - 1) // D)

        r = min(P, (A - 1) // D)
        if l > r:
            continue

        a = l
        x = A - D * a
        y = B - D * (P - a)

        res = min(res, q + 1 + calc(y, H + x))

    return res


Q = int(input())

for _ in range(Q):
    N, M = map(int, input().split())
    S = list(map(int, input().split()))
    G = list(map(int, input().split()))

    A = sorted(zip(S, G))

    ok = True

    for i in range(1, M):
        s1, g1 = A[i - 1]
        s2, g2 = A[i]

        if g1 > g2 or (g1 == g2 and not (s1 == s2 == g1)):
            ok = False
            break

    if not ok:
        print(-1)
        continue

    # 1: R, -1: L, 0: S
    type_ = [0] * M

    for i in range(M):
        s, g = A[i]

        if s < g:
            type_[i] = 1
        if s > g:
            type_[i] = -1

    paired = [False] * M
    ans = 0

    # RL ペア
    for i in range(M - 1):
        if type_[i] == 1 and type_[i + 1] == -1:
            paired[i] = True
            paired[i + 1] = True

            s1, g1 = A[i]
            s2, g2 = A[i + 1]

            X = g1 - s1
            Y = s2 - g2
            D = g2 - g1

            ans += min(solve(X, Y, D), solve(Y, X, D))

    # RL ペアに含まれない
    for i in range(M):
        if paired[i]:
            continue

        s, g = A[i]

        if type_[i] == 1:
            if i + 1 == M:
                ans += 1
            else:
                ans += calc(g - s, A[i + 1][1] - g)

        if type_[i] == -1:
            if i == 0:
                ans += 1
            else:
                ans += calc(s - g, g - A[i - 1][1])

    print(ans)