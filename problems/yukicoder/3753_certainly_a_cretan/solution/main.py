from bisect import bisect_left, bisect_right
from math import ceil, sqrt

MOD = 998244353

# https://github.com/tatyam-prime/SortedSet
class SortedSet:
    BUCKET_RATIO = 16
    SPLIT_RATIO = 24

    def __init__(self, a=()):
        a = sorted(set(a))
        self.size = len(a)

        if self.size == 0:
            self.a = []
            return

        b = ceil(sqrt(self.size / self.BUCKET_RATIO))
        self.a = [
            a[self.size * i // b:self.size * (i + 1) // b]
            for i in range(b)
        ]

    def __len__(self):
        return self.size

    def __getitem__(self, i):
        if i < 0:
            for a in reversed(self.a):
                i += len(a)
                if i >= 0:
                    return a[i]
        else:
            for a in self.a:
                if i < len(a):
                    return a[i]
                i -= len(a)
        raise IndexError

    def _position(self, x):
        for bi, a in enumerate(self.a):
            if x <= a[-1]:
                return bi, a, bisect_left(a, x)
        bi = len(self.a) - 1
        a = self.a[bi]
        return bi, a, len(a)

    def add(self, x):
        if self.size == 0:
            self.a = [[x]]
            self.size = 1
            return True

        bi, a, i = self._position(x)

        if i < len(a) and a[i] == x:
            return False

        a.insert(i, x)
        self.size += 1

        if len(a) > len(self.a) * self.SPLIT_RATIO:
            mid = len(a) // 2
            self.a[bi:bi + 1] = [a[:mid], a[mid:]]

        return True

    def discard(self, x):
        if self.size == 0:
            return False

        bi, a, i = self._position(x)

        if i == len(a) or a[i] != x:
            return False

        a.pop(i)
        self.size -= 1

        if not a:
            self.a.pop(bi)

        return True

    def lt(self, x):
        for a in reversed(self.a):
            if a[0] < x:
                return a[bisect_left(a, x) - 1]
        return None

    def gt(self, x):
        for a in self.a:
            if a[-1] > x:
                return a[bisect_right(a, x)]
        return None


N, Q = map(int, input().split())
S = list(input())

fact = [1] * (N + 1)
invfact = [1] * (N + 1)

for i in range(1, N + 1):
    fact[i] = fact[i - 1] * i % MOD

invfact[N] = pow(fact[N], MOD - 2, MOD)

for i in range(N, 0, -1):
    invfact[i - 1] = invfact[i] * i % MOD


def C(n, k):
    if k < 0 or k > n:
        return 0
    return fact[n] * invfact[k] % MOD * invfact[n - k] % MOD


def cat(r):
    return fact[2 * r] * invfact[r] % MOD * invfact[r + 1] % MOD


def invcat(r):
    return invfact[2 * r] * fact[r] % MOD * fact[r + 1] % MOD


T_init = [0]
bad = 0
P = 1
last = 0

for i in range(1, N):
    if S[i - 1] == S[i]:
        continue

    if i % 2 == 1:
        bad += 1
    else:
        T_init.append(i)
        P = P * cat((i - last) // 2) % MOD
        last = i

T = SortedSet(T_init)


def insert(x):
    global P

    l = T.lt(x)
    r = T.gt(x)

    if r is not None:
        P = P * invcat((r - l) // 2) % MOD
        P = P * cat((x - l) // 2) % MOD
        P = P * cat((r - x) // 2) % MOD
    else:
        P = P * cat((x - l) // 2) % MOD

    T.add(x)


def erase(x):
    global P

    l = T.lt(x)
    r = T.gt(x)

    if r is not None:
        P = P * invcat((x - l) // 2) % MOD
        P = P * invcat((r - x) // 2) % MOD
        P = P * cat((r - l) // 2) % MOD
    else:
        P = P * invcat((x - l) // 2) % MOD

    T.discard(x)


def check_boundary(x):
    global bad

    if x <= 0 or x >= N:
        return

    diff = S[x - 1] != S[x]

    if x % 2 == 1:
        if diff:
            bad -= 1
        else:
            bad += 1
    else:
        if diff:
            erase(x)
        else:
            insert(x)


for _ in range(Q):
    t, x = map(int, input().split())

    if t == 1:
        i = x

        check_boundary(i - 1)
        check_boundary(i)

        S[i - 1] = 'N' if S[i - 1] == 'Y' else 'Y'

    else:
        K = x

        if bad > 0:
            print(0)
            continue

        B = T[-1]
        L = N - B
        q = K - B // 2

        if S[-1] == 'Y':
            if not (0 <= q <= L // 2):
                print(0)
                continue

            f = (C(L, q) - C(L, q - 1)) % MOD

        else:
            if not ((L + 1) // 2 <= q <= L):
                print(0)
                continue

            f = (C(L, q) - C(L, q + 1)) % MOD

        print(P * f % MOD)