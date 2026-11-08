#include <cctype>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>

using namespace std;

namespace {

[[noreturn]] void fail(const string& message) {
    cerr << "Invalid input: " << message << '\n';
    exit(1);
}

bool parse_nonnegative_integer(const string& s, long long& x) {
    if (s.empty()) {
        return false;
    }

    // '+', '-' などの符号は禁止
    if (s[0] == '+' || s[0] == '-') {
        return false;
    }

    // 数字以外は禁止
    for (unsigned char c : s) {
        if (!isdigit(c)) {
            return false;
        }
    }

    // 先頭ゼロは禁止。ただし "0" 自体は許可
    if (static_cast<int>(s.size()) >= 2 && s[0] == '0') {
        return false;
    }

    long long val = 0;
    constexpr long long INTEGER_ABS_MAX = static_cast<long long>(4e18);

    for (char c : s) {
        int d = c - '0';
        if (val > (INTEGER_ABS_MAX - d) / 10) {
            return false;
        }
        val = val * 10 + d;
    }

    x = val;
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

int validate(istream& input) {
    string line;
    string extra;

    // 1行目: N K
    if (!getline(input, line)) {
        fail("empty input");
    }

    string n_token, k_token;
    {
        stringstream ss(line);
        if (!(ss >> n_token >> k_token) || (ss >> extra)) {
            fail("first line must contain exactly 2 integers: N K");
        }
    }

    long long N, K;
    if (!parse_nonnegative_integer(n_token, N) ||
        !parse_nonnegative_integer(k_token, K)) {
        fail(
            "N and K must be non-negative integers without sign or leading "
            "zeros");
    }

    if (!(2 <= N && N <= 200000)) {
        fail("N is out of range");
    }

    if (!(1 <= K && K <= 200000)) {
        fail("K is out of range");
    }

    // 2行目: M
    if (!getline(input, line)) {
        fail("missing second line: M");
    }

    string m_token;
    {
        stringstream ss(line);
        if (!(ss >> m_token) || (ss >> extra)) {
            fail("second line must contain exactly 1 integer: M");
        }
    }

    long long M;
    if (!parse_nonnegative_integer(m_token, M)) {
        fail("M must be a non-negative integer without sign or leading zeros");
    }

    if (!(1 <= M && M <= N)) {
        fail("M is out of range");
    }

    // 3行目: A_1 A_2 ... A_N
    if (!getline(input, line)) {
        fail("missing third line: A_1 ... A_N");
    }

    {
        stringstream ss(line);

        for (int i = 0; i < N; i++) {
            string a_token;
            if (!(ss >> a_token)) {
                fail("third line must contain exactly N integers");
            }

            long long A;
            if (!parse_nonnegative_integer(a_token, A)) {
                fail(
                    "A_i must be a non-negative integer without sign or "
                    "leading zeros");
            }

            if (!(0 <= A && A <= 200000)) {
                fail("A_i is out of range");
            }
        }

        if (ss >> extra) {
            fail("third line must contain exactly N integers");
        }
    }

    // 4行目以降は空白行のみ許可
    while (getline(input, line)) {
        if (!is_blank(line)) {
            fail("extra non-empty line after third line");
        }
    }

    return 0;
}

} // namespace

int main() {
    return validate(cin);
}
