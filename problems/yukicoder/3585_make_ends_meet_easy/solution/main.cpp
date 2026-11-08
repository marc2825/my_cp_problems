#include <bits/stdc++.h>
using namespace std;

int N, M, K;
vector<vector<bool>> keep;

void print_no() {
    cout << "No\n";
}

void print_yes() {
    cout << "Yes\n";

    for (int u = 1; u <= N; ++u) {
        for (int v = u + 1; v <= N; ++v) {
            if (!keep[u][v]) {
                cout << u << ' ' << v << '\n';
            }
        }
    }
}


int main() {
    cin >> N >> M >> K;

    int T = N * (N - 1) / 2;
    int E = T - M; // number of edges to keep

    keep.assign(N + 1, vector<bool>(N + 1, false));

    if (K == 1) {
        // The distance is 1 iff the direct edge (1, N) remains.
        if (E == 0) {
            print_no();
            return 0;
        }

        keep[1][N] = true;
        E--;

        for (int u = 1; u <= N && E > 0; ++u) {
            for (int v = u + 1; v <= N && E > 0; ++v) {
                if (u == 1 && v == N) continue;

                keep[u][v] = true;
                E--;
            }
        }

        print_yes();
        return 0;
    }

    // K >= 2.
    // Use the path 1 - 2 - ... - K - N as the mandatory shortest path.
    int U = N - K - 1; // number of vertices not on the path

    int min_keep = K;
    int max_keep = K + 3 * U + U * (U - 1) / 2;

    if (!(min_keep <= E && E <= max_keep)) {
        print_no();
        return 0;
    }

    // Keep the mandatory path edges.
    for (int i = 1; i < K; ++i) {
        keep[i][i + 1] = true;
        E--;
    }
    keep[K][N] = true;
    E--;

    vector<pair<int, int>> free_edges;

    // Extra vertices are K+1, K+2, ..., N-1.
    // Each of them can be connected to three consecutive path vertices.
    for (int x = K + 1; x <= N - 1; ++x) {
        free_edges.push_back({1, x});
        free_edges.push_back({2, x});

        if (K == 2) {
            // Path vertices are 1, 2, N.
            free_edges.push_back({x, N});
        } else {
            // Path vertices include 1, 2, 3.
            free_edges.push_back({3, x});
        }
    }

    // Extra vertices can be connected freely among themselves.
    for (int x = K + 1; x <= N - 1; ++x) {
        for (int y = x + 1; y <= N - 1; ++y) {
            free_edges.push_back({x, y});
        }
    }

    // Add arbitrary free edges until exactly E additional edges are kept.
    for (auto [u, v] : free_edges) {
        if (E == 0) break;

        keep[u][v] = true;
        E--;
    }

    print_yes();
    return 0;
}