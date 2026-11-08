#include <cstdlib>
#include <iostream>
#include <string>

using namespace std;

namespace {

constexpr int Q_MAX = 100000;
constexpr int SUM_LENGTH_MAX = 200000;

[[noreturn]] void fail(const string& message) {
    cerr << "Validation failed: " << message << '\n';
    exit(1);
}

bool contains_good(const string& s) {
    return s.find("good") != string::npos;
}

int validate(istream& input) {
    long long Q;
    if (!(input >> Q)) {
        fail("could not read Q");
    }
    if (Q < 1 || Q > Q_MAX) {
        fail("Q out of range");
    }

    long long total = 0;
    for (long long tc = 1; tc <= Q; tc++) {
        string S, T;
        if (!(input >> S >> T)) {
            fail("not enough string tokens");
        }
        if (S.size() != T.size()) {
            fail("case " + to_string(tc) + ": |S| != |T|");
        }
        if (S.empty()) {
            fail("case " + to_string(tc) + ": empty string");
        }
        for (char c : S) {
            if (c != 'd' && c != 'o' && c != 'g') {
                fail("case " + to_string(tc) + ": invalid char in S");
            }
        }
        for (char c : T) {
            if (c != 'd' && c != 'o' && c != 'g') {
                fail("case " + to_string(tc) + ": invalid char in T");
            }
        }
        if (contains_good(S)) {
            fail("case " + to_string(tc) + ": S contains good");
        }
        if (contains_good(T)) {
            fail("case " + to_string(tc) + ": T contains good");
        }
        total += static_cast<long long>(S.size());
        if (total > SUM_LENGTH_MAX) {
            fail("sum |S_i| exceeds limit");
        }
    }

    string extra;
    if (input >> extra) {
        fail("extra token exists after the last test case");
    }
    cerr << "OK\n";
    return 0;
}

} // namespace

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    return validate(cin);
}
