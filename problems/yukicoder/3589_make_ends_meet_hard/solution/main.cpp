#include <bits/stdc++.h>
using namespace std;
using ll = long long;

static const int MOD = 998244353;

ll modpow(ll a, ll e) {
    ll r = 1;
    while (e > 0) {
        if (e & 1) r = r * a % MOD;
        a = a * a % MOD;
        e >>= 1;
    }
    return r;
}

struct Comb {
    vector<int> fact, ifact;

    void init(int n) {
        fact.assign(n + 1, 1);
        ifact.assign(n + 1, 1);
        for (int i = 1; i <= n; i++) fact[i] = (ll)fact[i - 1] * i % MOD;
        ifact[n] = (int)modpow(fact[n], MOD - 2);
        for (int i = n; i >= 1; i--) ifact[i - 1] = (ll)ifact[i] * i % MOD;
    }

    int C(int n, int r) const {
        if (r < 0 || r > n) return 0;
        return (ll)fact[n] * ifact[r] % MOD * ifact[n - r] % MOD;
    }
};

static inline void trim(vector<int> &a) {
    while (!a.empty() && a.back() == 0) a.pop_back();
}

vector<int> mul_qs_minus_1(const vector<int> &p, int s, int E) {
    if (p.empty()) return {};
    int need = min(E + 1, (int)p.size() + s);
    vector<int> res(need, 0);

    // p(q) * q^s
    if (s <= E) {
        int lim = min((int)p.size(), E + 1 - s);
        for (int i = 0; i < lim; i++) res[i + s] = p[i];
    }

    // - p(q)
    int lim = min((int)p.size(), need);
    for (int i = 0; i < lim; i++) {
        res[i] -= p[i];
        if (res[i] < 0) res[i] += MOD;
    }

    trim(res);
    return res;
}

void add_shift_scaled(vector<int> &dst, const vector<int> &src, int shift, int scale, int E) {
    if (src.empty() || scale == 0 || shift > E) return;
    int need = min(E + 1, shift + (int)src.size());
    if ((int)dst.size() < need) dst.resize(need, 0);

    int len = need - shift;
    for (int i = 0; i < len; i++) {
        if (src[i] == 0) continue;
        dst[i + shift] = (dst[i + shift] + (ll)src[i] * scale) % MOD;
    }
}


int main() {
    int N, M, K;
    cin >> N >> M >> K;

    int E = N * (N - 1) / 2;
    int R = E - M;
    int S = N - 2;

    Comb comb;
    comb.init(E);

    // dp[r][s] is a polynomial in q.
    // r: number of ordinary vertices not reached yet
    // s: size of current BFS frontier
    vector<vector<vector<int>>> dp(S + 1, vector<vector<int>>(S + 2));
    dp[S][1] = vector<int>{1};

    // Build layers 1,2,...,K-1 without reaching vertex N.
    for (int step = 0; step < K - 1; step++) {
        vector<vector<vector<int>>> ndp(S + 1, vector<vector<int>>(S + 2));

        for (int r = 0; r <= S; r++) {
            for (int s = 0; s <= S + 1; s++) {
                if (dp[r][s].empty()) continue;

                vector<int> cur = dp[r][s]; // cur * (q^s - 1)^t
                for (int t = 0; t <= r; t++) {
                    int shift = t * (t - 1) / 2; // free edges inside the next frontier
                    int ways = comb.C(r, t);
                    add_shift_scaled(ndp[r - t][t], cur, shift, ways, E);

                    if (t != r) cur = mul_qs_minus_1(cur, s, E);
                }
            }
        }
        dp.swap(ndp);
    }

    // H(q): generating polynomial for dist(1,N)=K in q=1+x.
    vector<int> H(E + 1, 0);

    // N must have at least one edge to the current frontier: (q^s - 1).
    // All edges among the remaining r vertices, between them and N, and between them and the current frontier are free.
    for (int r = 0; r <= S; r++) {
        for (int s = 0; s <= S + 1; s++) {
            const vector<int> &p = dp[r][s];
            if (p.empty()) continue;

            int base = s * r + r + r * (r - 1) / 2;

            for (int i = 0; i < (int)p.size(); i++) {
                int val = p[i];
                if (val == 0) continue;

                if (i + base + s <= E) {
                    H[i + base + s] += val;
                    if (H[i + base + s] >= MOD) H[i + base + s] -= MOD;
                }
                if (i + base <= E) {
                    H[i + base] -= val;
                    if (H[i + base] < 0) H[i + base] += MOD;
                }
            }
        }
    }

    // We need [x^R] H(1+x). If H(q)=sum_c h_c q^c, then
    // [x^R] H(1+x) = sum_c h_c * C(c,R).
    ll ans = 0;
    for (int c = R; c <= E; c++) {
        if (H[c] == 0) continue;
        ans += (ll)H[c] * comb.C(c, R) % MOD;
        ans %= MOD;
    }

    cout << ans % MOD << '\n';
    return 0;
}
