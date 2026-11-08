#include <bits/stdc++.h>
using namespace std;


int value(long long x) {
    if (x == 3) return 2;
    long long r = x % 5;
    if (r == 2 || r == 3) return 1;
    return 0;
}

int main() {
    int T;
    cin >> T;
    while (T--) {
        int N;
        cin >> N;
        int xr = 0;
        for (int i = 0; i < N; ++i) {
            long long A;
            cin >> A;
            xr ^= value(A);
        }
        cout << (xr ? "First" : "Second") << '\n';
    }
    return 0;
}
