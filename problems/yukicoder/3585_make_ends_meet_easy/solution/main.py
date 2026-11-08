N, M, K = map(int, input().split())

T = N * (N - 1) // 2
E = T - M  # number of edges to keep

keep = [[False] * (N + 1) for _ in range(N + 1)]


def print_no():
    print("No")


def print_yes():
    print("Yes")

    for u in range(1, N + 1):
        for v in range(u + 1, N + 1):
            if not keep[u][v]:
                print(u, v)


if K == 1:
    # The distance is 1 iff the direct edge (1, N) remains.
    if E == 0:
        print_no()
        exit()

    keep[1][N] = True
    E -= 1

    for u in range(1, N + 1):
        if E <= 0:
            break
        for v in range(u + 1, N + 1):
            if E <= 0:
                break
            if u == 1 and v == N:
                continue

            keep[u][v] = True
            E -= 1

    print_yes()
    exit()


# K >= 2.
# Use the path 1 - 2 - ... - K - N as the mandatory shortest path.
U = N - K - 1  # number of vertices not on the path

min_keep = K
max_keep = K + 3 * U + U * (U - 1) // 2

if not (min_keep <= E <= max_keep):
    print_no()
    exit()

# Keep the mandatory path edges.
for i in range(1, K):
    keep[i][i + 1] = True
    E -= 1

keep[K][N] = True
E -= 1

free_edges = []

# Extra vertices are K+1, K+2, ..., N-1.
# Each of them can be connected to three consecutive path vertices.
for x in range(K + 1, N):
    free_edges.append((1, x))
    free_edges.append((2, x))

    if K == 2:
        # Path vertices are 1, 2, N.
        free_edges.append((x, N))
    else:
        # Path vertices include 1, 2, 3.
        free_edges.append((3, x))

# Extra vertices can be connected freely among themselves.
for x in range(K + 1, N):
    for y in range(x + 1, N):
        free_edges.append((x, y))

# Add arbitrary free edges until exactly E additional edges are kept.
for u, v in free_edges:
    if E == 0:
        break

    keep[u][v] = True
    E -= 1

print_yes()