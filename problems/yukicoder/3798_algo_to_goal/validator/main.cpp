#include <bits/stdc++.h>
using namespace std;

[[noreturn]] void fail(const string& message) {
    cerr << "Validation Error: " << message << '\n';
    exit(1);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    constexpr int MAX_Q = 100000;
    constexpr int MIN_N = 4;
    constexpr int MAX_SUM_N = 1000000;

    int Q;
    if (!(cin >> Q)) {
        fail("Failed to read Q");
    }
    if (Q < 1 || Q > MAX_Q) {
        fail("Q is out of range");
    }

    int sumN = 0;

    for (int tc = 1; tc <= Q; ++tc) {
        string S, T;
        if (!(cin >> S >> T)) {
            fail("Failed to read S or T at case " + to_string(tc));
        }

        int N = (int)S.size();

        if (N < MIN_N) {
            fail("|S| < 4 at case " + to_string(tc));
        }
        if (S.size() != T.size()) {
            fail("|S| != |T| at case " + to_string(tc));
        }

        sumN += N;
        if (sumN > MAX_SUM_N) {
            fail("Sum of |S| exceeds 1000000");
        }

        for (char c : S) {
            if (c < 'a' || c > 'z') {
                fail("Invalid character in S at case " + to_string(tc));
            }
        }
        for (char c : T) {
            if (c < 'a' || c > 'z') {
                fail("Invalid character in T at case " + to_string(tc));
            }
        }
    }

    string extra;
    if (cin >> extra) {
        fail("Extra input after the last test case");
    }

    cerr << "Validation OK\n";
    return 0;
}
