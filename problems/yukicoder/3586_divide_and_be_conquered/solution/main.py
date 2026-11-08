def value(x):
    if x == 3:
        return 2
    r = x % 5
    if r == 2 or r == 3:
        return 1
    return 0


T = int(input())

for _ in range(T):
    N = int(input())
    A = list(map(int, input().split()))

    xr = 0
    for x in A:
        xr ^= value(x)

    print("First" if xr else "Second")