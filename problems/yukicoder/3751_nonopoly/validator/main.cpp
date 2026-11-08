#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <set>
#include <string>
#include <utility>

using namespace std;

namespace {

[[noreturn]] void fail(const string& message) {
    cerr << "Invalid: " << message << '\n';
    exit(1);
}

int validate(istream& input) {
    long long N, M;
    if (!(input >> N >> M)) {
        fail("failed to read N, M");
    }

    if (!(1 <= N && N <= 200000)) {
        fail("N out of range");
    }

    long long max_m = min(200000LL, N * (N - 1) / 2);
    if (!(0 <= M && M <= max_m)) {
        fail("M out of range");
    }

    set<pair<int, int>> edges;

    for (int i = 0; i < M; ++i) {
        long long u, v, w;
        if (!(input >> u >> v >> w)) {
            fail("failed to read edge " + to_string(i + 1));
        }

        if (!(1 <= u && u < v && v <= N)) {
            fail("invalid u, v at edge " + to_string(i + 1));
        }

        if (!(1 <= w && w <= 1000000000LL)) {
            fail("W out of range at edge " + to_string(i + 1));
        }

        if (!edges.emplace(static_cast<int>(u), static_cast<int>(v)).second) {
            fail("duplicate edge at edge " + to_string(i + 1));
        }
    }

    string extra;
    if (input >> extra) {
        fail("extra token after input");
    }

    cerr << "Valid\n";
    return 0;
}

} // namespace

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    return validate(cin);
}
