#include <cctype>
#include <charconv>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

using namespace std;

namespace {

constexpr long long Q_MIN = 1;
constexpr long long Q_MAX = 200000;
constexpr long long N_MIN = 1;
constexpr long long N_MAX = 1000000000LL;
constexpr long long M_MIN = 1;
constexpr long long M_MAX = 200000;
constexpr long long SUM_M_MAX = 200000;

[[noreturn]] void fail(long long line_number, const string& message) {
    cerr << "Validation failed";
    if (line_number >= 1) {
        cerr << " at line " << line_number;
    }
    cerr << ": " << message << '\n';
    exit(1);
}

bool is_space(unsigned char c) {
    return std::isspace(c) != 0;
}

vector<string_view> split_whitespace(const string& line) {
    vector<string_view> tokens;

    size_t i = 0;
    while (i < line.size()) {
        while (i < line.size() &&
               is_space(static_cast<unsigned char>(line[i]))) {
            ++i;
        }
        if (i == line.size()) {
            break;
        }

        const size_t begin = i;
        while (i < line.size() &&
               !is_space(static_cast<unsigned char>(line[i]))) {
            ++i;
        }
        tokens.emplace_back(line.data() + begin, i - begin);
    }

    return tokens;
}

long long parse_integer(
    string_view token,
    long long line_number,
    const string& name) {
    if (token.empty()) {
        fail(line_number, name + " is empty");
    }

    long long value = 0;
    const char* begin = token.data();
    const char* end = token.data() + token.size();

    const auto [ptr, ec] = from_chars(begin, end, value);

    if (ec == errc::invalid_argument || ptr != end) {
        fail(
            line_number,
            name + " is not a valid decimal integer: \"" + string(token) +
                "\"");
    }
    if (ec == errc::result_out_of_range) {
        fail(
            line_number,
            name + " is outside the range of 64-bit signed integers");
    }

    return value;
}

string read_required_line(
    istream& input,
    long long& line_number,
    const string& description) {
    string line;
    if (!getline(input, line)) {
        fail(
            line_number + 1,
            "unexpected end of file while reading " + description);
    }

    ++line_number;

    // CRLF の '\r' は getline で残る場合があるため除去する。
    if (!line.empty() && line.back() == '\r') {
        line.pop_back();
    }

    return line;
}

void require_token_count(
    const vector<string_view>& tokens,
    size_t expected,
    long long line_number,
    const string& description) {
    if (tokens.size() != expected) {
        ostringstream oss;
        oss << description << " must contain exactly " << expected
            << " integer(s), but contains " << tokens.size();
        fail(line_number, oss.str());
    }
}

void require_range(
    long long value,
    long long lower,
    long long upper,
    long long line_number,
    const string& name) {
    if (value < lower || value > upper) {
        ostringstream oss;
        oss << name << " must satisfy " << lower << " <= " << name
            << " <= " << upper << ", but is " << value;
        fail(line_number, oss.str());
    }
}

int validate(istream& input) {
    long long line_number = 0;

    // 1 行目: Q
    const string q_line = read_required_line(input, line_number, "Q");
    const auto q_tokens = split_whitespace(q_line);
    require_token_count(q_tokens, 1, line_number, "the Q line");

    const long long Q = parse_integer(q_tokens[0], line_number, "Q");
    require_range(Q, Q_MIN, Q_MAX, line_number, "Q");

    long long sum_m = 0;

    for (long long q = 1; q <= Q; ++q) {
        // 各ケース1行目: N M
        const string nm_line = read_required_line(
            input,
            line_number,
            "N and M of test case " + to_string(q));
        const auto nm_tokens = split_whitespace(nm_line);
        require_token_count(
            nm_tokens,
            2,
            line_number,
            "the N M line of test case " + to_string(q));

        const long long N = parse_integer(
            nm_tokens[0],
            line_number,
            "N of test case " + to_string(q));
        const long long M = parse_integer(
            nm_tokens[1],
            line_number,
            "M of test case " + to_string(q));

        require_range(
            N,
            N_MIN,
            N_MAX,
            line_number,
            "N of test case " + to_string(q));
        require_range(
            M,
            M_MIN,
            M_MAX,
            line_number,
            "M of test case " + to_string(q));

        sum_m += M;
        if (sum_m > SUM_M_MAX) {
            ostringstream oss;
            oss << "the sum of M over test cases must be at most " << SUM_M_MAX
                << ", but it has already reached " << sum_m
                << " after test case " << q;
            fail(line_number, oss.str());
        }

        // 各ケース2行目: S_1 ... S_M
        const string s_line = read_required_line(
            input,
            line_number,
            "S of test case " + to_string(q));
        const auto s_tokens = split_whitespace(s_line);
        require_token_count(
            s_tokens,
            static_cast<size_t>(M),
            line_number,
            "the S line of test case " + to_string(q));

        for (long long i = 0; i < M; ++i) {
            const string name =
                "S_" + to_string(i + 1) + " of test case " + to_string(q);
            const long long value = parse_integer(
                s_tokens[static_cast<size_t>(i)],
                line_number,
                name);
            require_range(value, 1, N, line_number, name);
        }

        // 各ケース3行目: G_1 ... G_M
        const string g_line = read_required_line(
            input,
            line_number,
            "G of test case " + to_string(q));
        const auto g_tokens = split_whitespace(g_line);
        require_token_count(
            g_tokens,
            static_cast<size_t>(M),
            line_number,
            "the G line of test case " + to_string(q));

        for (long long i = 0; i < M; ++i) {
            const string name =
                "G_" + to_string(i + 1) + " of test case " + to_string(q);
            const long long value = parse_integer(
                g_tokens[static_cast<size_t>(i)],
                line_number,
                name);
            require_range(value, 1, N, line_number, name);
        }
    }

    // Q ケースを読み終えた後に余分な行がないことを確認する。
    string extra_line;
    if (getline(input, extra_line)) {
        ++line_number;
        fail(line_number, "extra line found after all Q test cases");
    }

    cout << "OK\n";
    cout << "Q = " << Q << '\n';
    cout << "sum(M) = " << sum_m << '\n';

    return 0;
}

} // namespace

int main(int argc, char* argv[]) {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    if (argc > 2) {
        cerr << "Usage: " << argv[0] << " [input_file]\n";
        return 2;
    }

    if (argc == 2) {
        ifstream file(argv[1]);
        if (!file) {
            cerr << "Failed to open input file: " << argv[1] << '\n';
            return 2;
        }
        return validate(file);
    } else {
        return validate(cin);
    }

    return 0;
}
