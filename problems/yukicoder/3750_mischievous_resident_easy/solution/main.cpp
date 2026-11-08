#include <bits/stdc++.h>
using namespace std;


int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int Q;
    cin >> Q;
    while (Q--) {
        int N, M;
        cin >> N >> M;

        vector<pair<int, int>> A(M);
        for (auto& [s, g] : A) cin >> s;
        for (auto& [s, g] : A) cin >> g;

        sort(A.begin(), A.end());

        bool ok = true;
        for (int i = 1; i < M; ++i) {
            auto [s1, g1] = A[i - 1];
            auto [s2, g2] = A[i];

            if (g1 > g2 ||
                (g1 == g2 && !(s1 == s2 && s1 == g1))) {
                ok = false;
                break;
            }
        }

        cout << (ok ? "Yes\n" : "No\n");
    }
}