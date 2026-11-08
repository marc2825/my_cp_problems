#include <bits/stdc++.h>
using namespace std;

using ll = long long;
const ll MOD = 998244353;


ll modpow(ll a, ll e) {
    ll res = 1;
    while (e > 0) {
        if (e & 1) res = res * a % MOD;
        a = a * a % MOD;
        e >>= 1;
    }
    return res;
}


int main() {
    ll N;
    cin >> N;

    // calculate C(N, 4)
    ll comb = 1;
    comb = comb * N % MOD;
    comb = comb * (N - 1) % MOD;
    comb = comb * (N - 2) % MOD;
    comb = comb * (N - 3) % MOD;
    const ll INV = modpow(1*2*3*4, MOD - 2);
    comb = comb * INV % MOD;

    ll ans = comb * modpow(26, N - 4) % MOD;
    cout << ans << '\n';

    return 0;
}