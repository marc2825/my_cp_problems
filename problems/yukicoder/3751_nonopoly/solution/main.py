N, M = map(int, input().split())

D = [0] * N
for _ in range(M):
    u, v, w = map(int, input().split())
    u -= 1
    v -= 1
    D[u] += w
    D[v] += w

D.sort(reverse=True)

ans = 0
for i in range(N):
    if i % 2 == 0:
        ans += D[i]
    else:
        ans -= D[i]

print(ans // 2)