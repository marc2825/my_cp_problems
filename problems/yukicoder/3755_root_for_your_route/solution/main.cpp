#include <bits/stdc++.h>
using namespace std;

using ll = long long;

/// https://github.com/marc2825/cp_library/blob/main/data_structure/ConvexHullTrick.hpp
// max query 用 Dynamic CHT Library
struct Line {
    mutable ll k, m, p;

    bool operator<(const Line& o) const {
        return k < o.k;
    }

    bool operator<(ll x) const {
        return p < x;
    }
};

struct CHT : multiset<Line, less<>> {
    static const ll INF = LLONG_MAX;

    ll div(ll a, ll b) {
        return a / b - ((a ^ b) < 0 && a % b);
    }

    bool isect(iterator x, iterator y) {
        if (y == end()) {
            x->p = INF;
            return false;
        }

        if (x->k == y->k) {
            x->p = (x->m > y->m ? INF : -INF);
        } else {
            x->p = div(y->m - x->m, x->k - y->k);
        }

        return x->p >= y->p;
    }

    void add(ll k, ll m) {
        auto z = insert({k, m, 0});
        auto y = z++;
        auto x = y;

        while (isect(y, z)) {
            z = erase(z);
        }

        if (x != begin() && isect(--x, y)) {
            isect(x, y = erase(y));
        }

        while ((y = x) != begin() && (--x)->p >= y->p) {
            isect(x, erase(y));
        }
    }

    ll query(ll x) {
        auto l = *lower_bound(x);
        return l.k * x + l.m;
    }
};

struct Node {
    int v, p, d;
    ll b;
};


int N;
vector<ll> A, ans, best, sub;
vector<vector<int>> G;
vector<int> sz, par;
vector<bool> used;


// 現在の連結成分の重心を求める
int get_centroid(int s) {
    vector<int> vs, st = {s};
    par[s] = -1;

    while (!st.empty()) {
        int v = st.back();
        st.pop_back();

        vs.push_back(v);

        for (int u : G[v]) {
            if (used[u] || u == par[v]) continue;
            par[u] = v;
            st.push_back(u);
        }
    }

    for (int i = (int)vs.size() - 1; i >= 0; --i) {
        int v = vs[i];
        sz[v] = 1;

        for (int u : G[v]) {
            if (!used[u] && par[u] == v) {
                sz[v] += sz[u];
            }
        }
    }

    int n = vs.size();

    for (int v : vs) {
        int mx = n - sz[v];

        for (int u : G[v]) {
            if (!used[u] && par[u] == v) {
                mx = max(mx, sz[u]);
            }
        }

        if (mx * 2 <= n) return v;
    }

    return -1;
}


void solve(int s) {
    int c = get_centroid(s);

    // c を除いてできる各連結成分
    vector<vector<Node>> comps;

    for (int root : G[c]) {
        if (used[root]) continue;

        struct State {
            int v, p, d;
            ll sum;
        };

        vector<Node> cur;
        vector<State> st = {
            {root, c, 1, A[c] + A[root]}
        };

        while (!st.empty()) {
            auto [v, p, d, sum] = st.back();
            st.pop_back();

            ll b = sum - 1LL * d * (d + 1) / 2;
            cur.push_back({v, p, d, b});

            for (int u : G[v]) {
                if (used[u] || u == p) continue;
                st.push_back({u, v, d + 1, sum + A[u]});
            }
        }

        comps.push_back(move(cur));
    }

    // 左側の成分から相方を選ぶ
    {
        CHT cht;
        cht.add(0, A[c]);

        for (auto& cur : comps) {
            for (auto& [v, p, d, b] : cur) {
                best[v] = cht.query(d);
            }

            for (auto& [v, p, d, b] : cur) {
                cht.add(-d, b);
            }
        }
    }

    // 右側の成分から相方を選ぶ
    {
        CHT cht;
        cht.add(0, A[c]);

        for (int i = (int)comps.size() - 1; i >= 0; --i) {
            for (auto& [v, p, d, b] : comps[i]) {
                best[v] = max(best[v], cht.query(d));
            }

            for (auto& [v, p, d, b] : comps[i]) {
                cht.add(-d, b);
            }
        }
    }

    ll best_c = A[c];

    for (auto& cur : comps) {
        // Q_v を計算
        for (auto& [v, p, d, b] : cur) {
            sub[v] = b - A[c] + best[v];
            best_c = max(best_c, sub[v]);
        }

        // 部分木最大値を子から親へ伝播
        for (int i = (int)cur.size() - 1; i >= 0; --i) {
            auto [v, p, d, b] = cur[i];

            ans[v] = max(ans[v], sub[v]);

            if (p != c) {
                sub[p] = max(sub[p], sub[v]);
            }
        }
    }

    ans[c] = max(ans[c], best_c);

    // 重心を削除して各成分へ再帰
    used[c] = true;

    for (int u : G[c]) {
        if (!used[u]) {
            solve(u);
        }
    }
}


int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    cin >> N;
    A.resize(N);
    for (ll& x : A) cin >> x;

    G.resize(N);
    for (int i = 0; i < N - 1; ++i) {
        int u, v;
        cin >> u >> v;
        u--;
        v--;

        G[u].push_back(v);
        G[v].push_back(u);
    }

    sz.resize(N);
    par.resize(N);
    used.assign(N, false);

    // s = t = r の場合
    ans = A;

    best.resize(N);
    sub.resize(N);

    solve(0);

    cout << *min_element(ans.begin(), ans.end()) << '\n';
}