#include <bits/stdc++.h>
using namespace std;

using ll = long long;
const ll INF = 1LL << 60;


// 間隔 d の状態から、片側を合計 x だけ逆向きに動かすための最小操作回数
ll calc(ll x, ll d) {
    ll sum = 0;
    int k = 0;
    while (sum < x) {
        sum = sum * 2 + d;
        k++;
    }
    return k;
}

// 目標間隔 D、逆向きの移動距離 (A, B) について、A 側を先に完成させる最小操作回数
ll solve(ll A, ll B, ll D) {
    ll res = INF;

    for (int q = 0; q < 30; ++q) {
        ll H = (1LL << q) * D;
        ll P = (1LL << q) - 1;

        ll l = max(0LL, P - (B - 1) / D);
        if (A > H) l = max(l, (A - H + D - 1) / D);

        ll r = min(P, (A - 1) / D);
        if (l > r) continue;

        ll a = l;
        ll x = A - D * a;
        ll y = B - D * (P - a);

        res = min(res, (ll)q + 1 + calc(y, H + x));
    }

    return res;
}


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

        if (!ok) {
            cout << -1 << '\n';
            continue;
        }


        // 1: R, -1: L, 0: S
        vector<int> type(M);
        for (int i = 0; i < M; ++i) {
            auto [s, g] = A[i];
            if (s < g) type[i] = 1;
            if (s > g) type[i] = -1;
        }

        vector<bool> paired(M);
        ll ans = 0;

        // RL ペア
        for (int i = 0; i + 1 < M; ++i) {
            if (type[i] == 1 && type[i + 1] == -1) {
                paired[i] = paired[i + 1] = true;

                auto [s1, g1] = A[i];
                auto [s2, g2] = A[i + 1];

                ll X = g1 - s1;
                ll Y = s2 - g2;
                ll D = g2 - g1;

                ans += min(solve(X, Y, D), solve(Y, X, D));
            }
        }

        // RL ペアに含まれない
        for (int i = 0; i < M; ++i) {
            if (paired[i]) continue;

            auto [s, g] = A[i];

            if (type[i] == 1) {
                if (i + 1 == M) ans++;
                else ans += calc(g - s, A[i + 1].second - g);
            }

            if (type[i] == -1) {
                if (i == 0) ans++;
                else ans += calc(s - g, g - A[i - 1].second);
            }
        }

        cout << ans << '\n';
    }
}