#include <iostream>
#include <string>

using namespace std;

namespace {

int validate(istream& input) {
    long long N, Q;
    if (!(input >> N >> Q)) {
        cerr << "Failed to read N, Q\n";
        return 1;
    }

    if (!(1 <= N && N <= 1000000)) {
        cerr << "N out of range: " << N << '\n';
        return 1;
    }

    if (!(1 <= Q && Q <= 100000)) {
        cerr << "Q out of range: " << Q << '\n';
        return 1;
    }

    string S;
    if (!(input >> S)) {
        cerr << "Failed to read S\n";
        return 1;
    }

    if (static_cast<long long>(S.size()) != N) {
        cerr << "Invalid length of S: " << S.size() << '\n';
        return 1;
    }

    for (char c : S) {
        if (c != 'Y' && c != 'N') {
            cerr << "Invalid character in S: " << c << '\n';
            return 1;
        }
    }

    bool has_type2 = false;

    for (int q = 0; q < Q; ++q) {
        int type;
        long long x;

        if (!(input >> type >> x)) {
            cerr << "Failed to read query " << q + 1 << '\n';
            return 1;
        }

        if (type == 1) {
            if (!(1 <= x && x <= N)) {
                cerr << "i out of range in query " << q + 1 << ": " << x
                     << '\n';
                return 1;
            }
        } else if (type == 2) {
            if (!(0 <= x && x <= N)) {
                cerr << "K out of range in query " << q + 1 << ": " << x
                     << '\n';
                return 1;
            }
            has_type2 = true;
        } else {
            cerr << "Invalid query type in query " << q + 1 << ": " << type
                 << '\n';
            return 1;
        }
    }

    if (!has_type2) {
        cerr << "No type-2 query exists\n";
        return 1;
    }

    string extra;
    if (input >> extra) {
        cerr << "Extra token after all queries: " << extra << '\n';
        return 1;
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
