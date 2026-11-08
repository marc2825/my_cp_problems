#include <bits/stdc++.h>
using namespace std;


int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int N;
        cin >> N;

        long long S = 0;
        bool win = false;
        for (int i = 0; i < N; ++i) {
            long long A;
            cin >> A;

            if (A == 1 && S % 2 == 0) win = true;

            S += A;
        }

        if (S % 2 == 1) win = true;

        cout << (win ? "Alice" : "Bob") << '\n';
    }

    return 0;
}