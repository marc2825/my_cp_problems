INF = 10**9


# ==================================================
# Range-add range-min lazy segment tree
# ==================================================

class RangeAddRangeMinLazySegTree:
    def __init__(self, initial_values):
        self.n = len(initial_values)
        self.size = 1
        self.logn = 0
        while self.size < self.n:
            self.size <<= 1
            self.logn += 1

        self.min_value = [INF] * (2 * self.size)
        self.lazy_add = [0] * self.size

        for i in range(self.n):
            self.min_value[self.size + i] = initial_values[i]

        for i in range(self.size - 1, 0, -1):
            self.pull(i)

    def pull(self, node):
        self.min_value[node] = min(
            self.min_value[node * 2],
            self.min_value[node * 2 + 1]
        )

    def apply_to_node(self, node, add_value):
        self.min_value[node] += add_value
        if node < self.size:
            self.lazy_add[node] += add_value

    def push(self, node):
        if self.lazy_add[node] != 0:
            self.apply_to_node(node * 2, self.lazy_add[node])
            self.apply_to_node(node * 2 + 1, self.lazy_add[node])
            self.lazy_add[node] = 0

    def range_add(self, left, right, add_value):
        if left >= right:
            return

        left += self.size
        right += self.size

        for h in range(self.logn, 0, -1):
            if ((left >> h) << h) != left:
                self.push(left >> h)
            if ((right >> h) << h) != right:
                self.push((right - 1) >> h)

        original_left = left
        original_right = right

        while left < right:
            if left & 1:
                self.apply_to_node(left, add_value)
                left += 1
            if right & 1:
                right -= 1
                self.apply_to_node(right, add_value)
            left >>= 1
            right >>= 1

        left = original_left
        right = original_right

        for h in range(1, self.logn + 1):
            if ((left >> h) << h) != left:
                self.pull(left >> h)
            if ((right >> h) << h) != right:
                self.pull((right - 1) >> h)

    def all_min(self):
        return self.min_value[1]

    def max_right(self, left, pred):
        if left == self.n:
            return self.n

        left += self.size

        for h in range(self.logn, 0, -1):
            self.push(left >> h)

        current_min = INF

        while True:
            while left % 2 == 0:
                left >>= 1

            next_min = min(current_min, self.min_value[left])
            if not pred(next_min):
                while left < self.size:
                    self.push(left)
                    left *= 2

                    candidate_min = min(current_min, self.min_value[left])
                    if pred(candidate_min):
                        current_min = candidate_min
                        left += 1

                return left - self.size

            current_min = next_min
            left += 1

            if (left & -left) == left:
                break

        return self.n


# ==================================================
# Point-set range-min segment tree
# ==================================================

class PointSetRangeMinSegTree:
    def __init__(self, initial_values):
        self.n = len(initial_values)
        self.size = 1
        while self.size < self.n:
            self.size <<= 1

        self.min_value = [INF] * (2 * self.size)

        for i in range(self.n):
            self.min_value[self.size + i] = initial_values[i]

        for i in range(self.size - 1, 0, -1):
            self.min_value[i] = min(
                self.min_value[i * 2],
                self.min_value[i * 2 + 1]
            )

    def set_value(self, index, value):
        index += self.size
        self.min_value[index] = value

        index >>= 1
        while index:
            self.min_value[index] = min(
                self.min_value[index * 2],
                self.min_value[index * 2 + 1]
            )
            index >>= 1

    def all_min(self):
        return self.min_value[1]

    def max_right(self, left, pred):
        if left == self.n:
            return self.n

        left += self.size
        current_min = INF

        while True:
            while left % 2 == 0:
                left >>= 1

            next_min = min(current_min, self.min_value[left])
            if not pred(next_min):
                while left < self.size:
                    left *= 2

                    candidate_min = min(current_min, self.min_value[left])
                    if pred(candidate_min):
                        current_min = candidate_min
                        left += 1

                return left - self.size

            current_min = next_min
            left += 1

            if (left & -left) == left:
                break

        return self.n


# ==================================================
# Main Solution
# ==================================================

N, K = map(int, input().split())
M = int(input())
A = [0] + list(map(int, input().split()))
S = sum(A)

if S % (N + 1) != 0:
    print(-1)
    exit(0)

T = S // (N + 1)

if T < 1:
    print(-1)
    exit(0)

W = [0] * (N + 1)
for i in range(1, N + 1):
    W[i] = A[i] - T
    if W[i] < 0:
        print(-1)
        exit(0)

if W[M] < 1:
    print(-1)
    exit(0)

if A[M] - 2 < K:
    print(-1)
    exit(0)

m = T - 1

B = [0] * (N + 1)
rem = [0] * (N + 1)
deadline = [INF] * (N + 1)
deadline_count = [0] * (max(1, m) + 1)

sumB = 0

for i in range(1, N + 1):
    b = W[i] - (1 if i == M else 0)

    if b < 0:
        print(-1)
        exit(0)

    B[i] = b
    rem[i] = b
    sumB += b

    if b > 0:
        d = K + 1 - b

        if d < 1:
            print(-1)
            exit(0)

        effective_deadline = min(d, m)

        deadline[i] = effective_deadline
        deadline_count[effective_deadline] += b

assert sumB == m

if m == 0:
    print(1)
    print(M)
    exit(0)

slack_initial = [INF] * (m + 1)

pref = 0

for x in range(1, m + 1):
    pref += deadline_count[x]

    slack = x - pref

    if slack < 0:
        print(-1)
        exit(0)

    slack_initial[x] = slack

assert pref == m

slack_tree = RangeAddRangeMinLazySegTree(slack_initial)

team_initial = [INF] * (N + 1)

for i in range(1, N + 1):
    if rem[i] > 0:
        team_initial[i] = deadline[i]

team_tree = PointSetRangeMinSegTree(team_initial)

ans = []

for p in range(1, m + 1):
    if team_tree.all_min() < p:
        print(-1)
        exit(0)

    first_zero = slack_tree.max_right(p, lambda min_slack: min_slack > 0)

    if first_zero == m + 1:
        E = m + 1
    else:
        E = first_zero

    c = team_tree.max_right(1, lambda min_deadline: min_deadline > E)

    if c == N + 1:
        print(-1)
        exit(0)

    ans.append(c)

    if p < deadline[c]:
        slack_tree.range_add(p, deadline[c], -1)

    rem[c] -= 1

    if rem[c] == 0:
        team_tree.set_value(c, INF)

ans.append(M)

print(len(ans))
print(*ans)