#include <cctype>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace std;

namespace {

[[noreturn]] void fail(const string& message) {
    cerr << "Invalid input: " << message << '\n';
    exit(1);
}

bool parse_integer(const string& s, long long& x) {
    if (s.empty()) {
        return false;
    }

    int i = 0;
    int sign = 1;
    if (s[0] == '+' || s[0] == '-') {
        sign = (s[0] == '-') ? -1 : 1;
        i = 1;
    }
    if (i == static_cast<int>(s.size())) {
        return false;
    }

    long long val = 0;
    constexpr long long INTEGER_ABS_MAX = static_cast<long long>(4e18);

    for (; i < static_cast<int>(s.size()); ++i) {
        if (!isdigit(static_cast<unsigned char>(s[i]))) {
            return false;
        }
        int d = s[i] - '0';
        if (val > (INTEGER_ABS_MAX - d) / 10) {
            return false;
        }
        val = val * 10 + d;
    }

    x = sign * val;
    return true;
}

bool is_blank(const string& s) {
    for (unsigned char c : s) {
        if (!isspace(c)) {
            return false;
        }
    }
    return true;
}

vector<string> split_whitespace(const string& line) {
    stringstream ss(line);
    vector<string> tokens;
    string t;
    while (ss >> t) {
        tokens.push_back(t);
    }
    return tokens;
}

int validate(istream& input) {
    string line;

    if (!getline(input, line)) {
        fail("empty input");
    }

    {
        vector<string> tokens = split_whitespace(line);
        if (tokens.size() != 1) {
            fail("first line must contain exactly 1 integer: T");
        }

        long long T;
        if (!parse_integer(tokens[0], T)) {
            fail("T must be an integer");
        }
        if (!(1 <= T && T <= 100000)) {
            fail("T is out of range");
        }

        long long sum_n = 0;

        for (long long tc = 1; tc <= T; ++tc) {
            if (!getline(input, line)) {
                fail("missing N line");
            }

            vector<string> n_tokens = split_whitespace(line);
            if (n_tokens.size() != 1) {
                fail("N line must contain exactly 1 integer");
            }

            long long N;
            if (!parse_integer(n_tokens[0], N)) {
                fail("N must be an integer");
            }
            if (!(1 <= N)) {
                fail("N is out of range");
            }

            sum_n += N;
            if (sum_n > 200000) {
                fail("sum of N is too large");
            }

            if (!getline(input, line)) {
                fail("missing A line");
            }

            vector<string> a_tokens = split_whitespace(line);
            if (static_cast<long long>(a_tokens.size()) != N) {
                fail("A line must contain exactly N integers");
            }

            for (int i = 0; i < N; ++i) {
                long long A;
                if (!parse_integer(a_tokens[i], A)) {
                    fail("A_i must be an integer");
                }
                if (!(1 <= A &&
                      A <= static_cast<long long>(1000000000000000000LL))) {
                    fail("A_i is out of range");
                }
            }
        }
    }

    while (getline(input, line)) {
        if (!is_blank(line)) {
            fail("extra non-empty line after all test cases");
        }
    }

    return 0;
}

} // namespace

int main() {
    return validate(cin);
}
