#include <bits/stdc++.h>
using namespace std;

using ll = long long;
const int MOD = 998244353;

ll modpow(ll a, ll n) {
    ll r = 1;
    while (n) {
        if (n & 1) r = r * a % MOD;
        a = a * a % MOD;
        n >>= 1;
    }
    return r;
}


int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N, Q;
    string S;
    cin >> N >> Q >> S;

    vector<ll> fact(N + 1), invfact(N + 1);
    fact[0] = 1;
    for (int i = 1; i <= N; ++i) {
        fact[i] = fact[i - 1] * i % MOD;
    }

    invfact[N] = modpow(fact[N], MOD - 2);
    for (int i = N; i >= 1; --i) {
        invfact[i - 1] = invfact[i] * i % MOD;
    }

    auto C = [&](int n, int k) -> ll {
        if (k < 0 || k > n) return 0;
        return fact[n] * invfact[k] % MOD * invfact[n - k] % MOD;
    };

    int M = N / 2;
    vector<ll> cat(M + 1), invcat(M + 1);
    for (int r = 0; r <= M; ++r) {
        cat[r] = fact[2 * r] * invfact[r] % MOD * invfact[r] % MOD;
        cat[r] = cat[r] * modpow(r + 1, MOD - 2) % MOD;

        invcat[r] = invfact[2 * r] * fact[r] % MOD * fact[r] % MOD;
        invcat[r] = invcat[r] * (r + 1) % MOD;
    }
    

    set<int> T;
    T.insert(0);
    int bad = 0;
    for (int i = 1; i < N; ++i) {
        if (S[i - 1] == S[i]) continue;

        if (i & 1) {
            bad++;
        } else {
            T.insert(i);
        }
    }

    ll P = 1;
    int last = 0;
    for (int x : T) {
        if (x == 0) continue;
        P = P * cat[(x - last) / 2] % MOD;
        last = x;
    }

    auto insert = [&](int x) {
        auto it = T.lower_bound(x);

        int r = -1;
        if (it != T.end()) r = *it;

        int l = *prev(it);

        if (r != -1) {
            P = P * invcat[(r - l) / 2] % MOD;
            P = P * cat[(x - l) / 2] % MOD;
            P = P * cat[(r - x) / 2] % MOD;
        } else {
            P = P * cat[(x - l) / 2] % MOD;
        }

        T.insert(x);
    };

    auto erase = [&](int x) {
        auto it = T.find(x);

        int l = *prev(it);

        auto jt = next(it);
        int r = -1;
        if (jt != T.end()) r = *jt;

        if (r != -1) {
            P = P * invcat[(x - l) / 2] % MOD;
            P = P * invcat[(r - x) / 2] % MOD;
            P = P * cat[(r - l) / 2] % MOD;
        } else {
            P = P * invcat[(x - l) / 2] % MOD;
        }

        T.erase(it);
    };

    auto check_boundary = [&](int x) {
        if (x <= 0 || x >= N) return;

        bool diff = (S[x - 1] != S[x]);

        if (x & 1) {
            if (diff) {
                bad--;
            } else {
                bad++;
            }
        } else {
            if (diff) {
                erase(x);
            } else {
                insert(x);
            }
        }
    };

    while (Q--) {
        int type, x;
        cin >> type >> x;

        if (type == 1) {
            int i = x;

            check_boundary(i - 1);
            check_boundary(i);

            S[i - 1] = (S[i - 1] == 'Y' ? 'N' : 'Y');
        } else {
            int K = x;

            if (bad > 0) {
                cout << 0 << '\n';
                continue;
            }

            int B = *T.rbegin();
            int L = N - B;
            int q = K - B / 2;

            ll ans = 0;
            if (S[N - 1] == 'Y') {
                if (0 <= q && q <= L / 2) {
                    ll f = (C(L, q) - C(L, q - 1) + MOD) % MOD;
                    ans = P * f % MOD;
                }
            } else {
                if ((L + 1) / 2 <= q && q <= L) {
                    ll f = (C(L, q) - C(L, q + 1) + MOD) % MOD;
                    ans = P * f % MOD;
                }
            }

            cout << ans << '\n';
        }
    }
}