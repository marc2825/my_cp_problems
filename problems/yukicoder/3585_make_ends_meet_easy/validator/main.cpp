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
    if (!getline(input, line)) {
        fail("empty input");
    }

    string n_token, m_token, k_token, extra;
    stringstream ss(line);

    if (!(ss >> n_token >> m_token >> k_token) || (ss >> extra)) {
        fail("first line must contain exactly 3 integers: N M K");
    }

    while (getline(input, line)) {
        if (!is_blank(line)) {
            fail("extra non-empty line after first line");
        }
    }

    long long N, M, K;

    if (!parse_nonnegative_integer(n_token, N) ||
        !parse_nonnegative_integer(m_token, M) ||
        !parse_nonnegative_integer(k_token, K)) {
        fail(
            "all tokens must be non-negative integers without sign or leading "
            "zeros");
    }

    if (!(2 <= N && N <= 100)) {
        fail("N is out of range");
    }

    long long T = N * (N - 1) / 2;

    if (!(0 <= M && M <= T)) {
        fail("M is out of range");
    }

    if (!(1 <= K && K <= N - 1)) {
        fail("K is out of range");
    }

    return 0;
}

} // namespace

int main() {
    return validate(cin);
}
