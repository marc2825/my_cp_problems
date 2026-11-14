Q = int(input())
C = 26

for _ in range(Q):
    S = input()
    T = input()
    N = len(S)

    A = [[0] * C for _ in range(2)]
    B = [[0] * C for _ in range(2)]

    for i in range(N):
        A[i % 2][ord(S[i]) - ord('a')] += 1
        B[i % 2][ord(T[i]) - ord('a')] += 1

    if A != B:
        print("No")
        continue

    dup = False
    for p in range(2):
        for c in range(C):
            if A[p][c] >= 2:
                dup = True

    if dup:
        print("Yes")
        continue

    x, y = 0, 0
    for i in range(N):
        for j in range(i + 1, N):
            if i % 2 != j % 2:
                continue
            if S[i] > S[j]:
                x += 1
            if T[i] > T[j]:
                y += 1

    print("Yes" if x % 2 == y % 2 else "No")