#include <cstdlib>
#include <iostream>
#include <numeric>
#include <string>
#include <utility>
#include <vector>

using namespace std;

namespace {

struct DSU {
    vector<int> p, sz;

    DSU(int n) : p(n), sz(n, 1) {
        iota(p.begin(), p.end(), 0);
    }

    int find(int x) {
        if (p[x] == x) {
            return x;
        }
        return p[x] = find(p[x]);
    }

    bool unite(int a, int b) {
        a = find(a);
        b = find(b);

        if (a == b) {
            return false;
        }

        if (sz[a] < sz[b]) {
            swap(a, b);
        }
        p[b] = a;
        sz[a] += sz[b];

        return true;
    }
};

[[noreturn]] void fail(const string& message) {
    cerr << "Validation failed: " << message << '\n';
    exit(1);
}

int validate(istream& input) {
    int N;

    if (!(input >> N)) {
        fail("N could not be read as an integer");
    }

    if (!(2 <= N && N <= 100000)) {
        fail("N is out of range");
    }

    vector<long long> A(N);

    for (int v = 0; v < N; v++) {
        if (!(input >> A[v])) {
            fail("A_" + to_string(v + 1) + " could not be read as an integer");
        }

        if (!(-1000000000LL <= A[v] && A[v] <= 1000000000LL)) {
            fail("A_" + to_string(v + 1) + " is out of range");
        }
    }

    DSU dsu(N);

    for (int i = 0; i < N - 1; i++) {
        int u, v;

        if (!(input >> u >> v)) {
            fail("edge " + to_string(i + 1) + " could not be read");
        }

        if (!(1 <= u && u <= N)) {
            fail("u_" + to_string(i + 1) + " is out of range");
        }

        if (!(1 <= v && v <= N)) {
            fail("v_" + to_string(i + 1) + " is out of range");
        }

        --u;
        --v;

        if (!dsu.unite(u, v)) {
            fail("edge " + to_string(i + 1) + " creates a cycle");
        }
    }

    int root = dsu.find(0);

    for (int v = 1; v < N; v++) {
        if (dsu.find(v) != root) {
            fail("the graph is not connected");
        }
    }

    string extra;

    if (input >> extra) {
        fail("extra token found after the expected input: " + extra);
    }

    cerr << "Validation successful\n";
    return 0;
}

} // namespace

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    return validate(cin);
}
