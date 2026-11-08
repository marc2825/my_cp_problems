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

    print("Yes" if ok else "No")