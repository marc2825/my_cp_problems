#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

using namespace std;

namespace {

[[noreturn]] void fail(const string& message) {
    cerr << "Validation failed: " << message << '\n';
    exit(1);
}

template <class T>
void require_range(T value, T lower, T upper, const string& name) {
    if (value < lower || value > upper) {
        fail(
            name + " = " + to_string(value) + " is outside [" +
            to_string(lower) + ", " + to_string(upper) + "]");
    }
}

int validate(istream& input) {
    constexpr int Q_MAX = 200000;
    constexpr int M_MAX = 200000;
    constexpr long long N_MAX = 1000000000LL;
    constexpr long long SUM_M_MAX = 200000LL;

    int Q;
    if (!(input >> Q)) {
        fail("Q could not be read");
    }
    require_range(Q, 1, Q_MAX, "Q");

    long long sum_m = 0;

    for (int q = 1; q <= Q; ++q) {
        long long N;
        int M;

        if (!(input >> N >> M)) {
            fail("N and M could not be read in test case " + to_string(q));
        }

        require_range(N, 1LL, N_MAX, "N in test case " + to_string(q));

        require_range(M, 1, M_MAX, "M in test case " + to_string(q));

        sum_m += M;
        if (sum_m > SUM_M_MAX) {
            fail(
                "sum of M exceeded 200000 after test case " + to_string(q) +
                ": sumM = " + to_string(sum_m));
        }

        vector<long long> S(M), G(M);

        for (int i = 0; i < M; ++i) {
            if (!(input >> S[i])) {
                fail(
                    "S_" + to_string(i + 1) +
                    " could not be read in test case " + to_string(q));
            }

            if (S[i] < 1 || S[i] > N) {
                fail(
                    "S_" + to_string(i + 1) + " = " + to_string(S[i]) +
                    " is outside [1, N] in test case " + to_string(q) +
                    ", where N = " + to_string(N));
            }
        }

        for (int i = 0; i < M; ++i) {
            if (!(input >> G[i])) {
                fail(
                    "G_" + to_string(i + 1) +
                    " could not be read in test case " + to_string(q));
            }

            if (G[i] < 1 || G[i] > N) {
                fail(
                    "G_" + to_string(i + 1) + " = " + to_string(G[i]) +
                    " is outside [1, N] in test case " + to_string(q) +
                    ", where N = " + to_string(N));
            }
        }
    }

    // 入力末尾に余計なトークンがないか確認する。
    string extra;
    if (input >> extra) {
        fail("extra token found after the last test case: \"" + extra + "\"");
    }

    cerr << "Validation succeeded\n";
    cerr << "Q = " << Q << '\n';
    cerr << "sum(M) = " << sum_m << '\n';

    return 0;
}

} // namespace

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    return validate(cin);
}
