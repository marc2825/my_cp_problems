#include <iostream>
#include <string>

using namespace std;

namespace {

int validate(istream& input) {
    constexpr long long T_MAX = 100000;
    constexpr long long SUM_N_MAX = 200000;
    constexpr long long A_MAX = 1000000000LL;

    long long T;

    if (!(input >> T)) {
        cerr << "ERROR: T が読み込めません\n";
        return 1;
    }

    if (T < 1 || T > T_MAX) {
        cerr << "ERROR: T が制約違反です: T = " << T << '\n';
        return 1;
    }

    long long sum_n = 0;

    for (long long tc = 1; tc <= T; ++tc) {
        long long N;

        if (!(input >> N)) {
            cerr << "ERROR: test case " << tc << " の N が読み込めません\n";
            return 1;
        }

        if (N < 1) {
            cerr << "ERROR: test case " << tc << " で N < 1 です: N = " << N
                 << '\n';
            return 1;
        }

        sum_n += N;

        if (sum_n > SUM_N_MAX) {
            cerr << "ERROR: sum N が制約違反です\n";
            cerr << "  test case = " << tc << '\n';
            cerr << "  sum N = " << sum_n << '\n';
            return 1;
        }

        for (long long i = 1; i <= N; ++i) {
            long long A;

            if (!(input >> A)) {
                cerr << "ERROR: test case " << tc << ", A_" << i
                     << " が読み込めません\n";
                return 1;
            }

            if (A < 1 || A > A_MAX) {
                cerr << "ERROR: test case " << tc << ", A_" << i
                     << " が制約違反です: " << A << '\n';
                return 1;
            }
        }
    }

    // 規定の入力を読み終えた後に余計なトークンがないか確認
    string extra;
    if (input >> extra) {
        cerr << "ERROR: 入力末尾に余計なトークンがあります: " << extra << '\n';
        return 1;
    }

    cerr << "OK\n";
    cerr << "T = " << T << '\n';
    cerr << "sum N = " << sum_n << '\n';

    return 0;
}

} // namespace

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    return validate(cin);
}
