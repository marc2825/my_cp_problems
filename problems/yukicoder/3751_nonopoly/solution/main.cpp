#include <bits/stdc++.h>
using namespace std;


int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N, M;
    cin >> N >> M;

    vector<long long> D(N);
    for (int i = 0; i < M; ++i) {
        int u, v;
        long long w;
        cin >> u >> v >> w;
        u--, v--;
        D[u] += w;
        D[v] += w;
    }

    sort(D.begin(), D.end(), greater<>());

    long long ans = 0;
    for (int i = 0; i < N; ++i) {
        if (i % 2 == 0) ans += D[i];
        else ans -= D[i];
    }

    cout << ans / 2 << '\n';
}