MOD = 998244353

N = int(input())

comb = N * (N - 1) * (N - 2) * (N - 3) // (1 * 2 * 3 * 4)
ans = comb % MOD * pow(26, N - 4, MOD) % MOD
print(ans)