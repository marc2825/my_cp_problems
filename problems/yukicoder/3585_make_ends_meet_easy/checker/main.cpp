#include <bits/stdc++.h>
using namespace std;

[[noreturn]] void wa(const string& msg) {
    cerr << "Wrong Answer: " << msg << '\n';
    exit(1);
}

bool parse_ll(const string& s, long long& x) {
    if (s.empty()) return false;
    int i = 0;
    int sign = 1;
    if (s[0] == '+' || s[0] == '-') {
        sign = (s[0] == '-') ? -1 : 1;
        i = 1;
    }
    if (i == (int)s.size()) return false;
    long long val = 0;
    const long long LIM = (long long)4e18;
    for (; i < (int)s.size(); ++i) {
        if (!isdigit((unsigned char)s[i])) return false;
        int d = s[i] - '0';
        if (val > (LIM - d) / 10) return false;
        val = val * 10 + d;
    }
    x = sign * val;
    return true;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Judge Error: input file path is not given\n";
        return 1;
    }

    ifstream input_ifs(argv[1]);
    if (!input_ifs) {
        cerr << "Judge Error: cannot open input file\n";
        return 1;
    }

    long long N, M, K;
    input_ifs >> N >> M >> K;
    if (!input_ifs) {
        cerr << "Judge Error: cannot read input\n";
        return 1;
    }

    long long T = N * (N - 1) / 2;
    bool feasible;
    if (K == 1) {
        feasible = (0 <= M && M <= T - 1);
    } else {
        long long min_removed = K * (K - 1) / 2 + (N - K - 1) * (K - 2);
        long long max_removed = T - K;
        feasible = (min_removed <= M && M <= max_removed);
    }

    string first;
    if (!(cin >> first)) wa("empty output");

    auto ensure_no_extra = [&]() {
        string extra;
        if (cin >> extra) wa("extra output token: " + extra);
    };

    if (first == "No") {
        if (feasible) wa("contestant printed No, but a construction exists");
        ensure_no_extra();
        return 0;
    }

    if (first != "Yes") {
        wa("first token must be Yes or No");
    }

    if (!feasible) {
        wa("contestant printed Yes, but no construction exists");
    }

    vector<vector<int>> removed((int)N + 1, vector<int>((int)N + 1, 0));

    for (long long i = 0; i < M; ++i) {
        string su, sv;
        if (!(cin >> su >> sv)) wa("not enough edge pairs");

        long long u_ll, v_ll;
        if (!parse_ll(su, u_ll) || !parse_ll(sv, v_ll)) {
            wa("edge endpoint is not an integer");
        }
        if (u_ll < 1 || u_ll > N || v_ll < 1 || v_ll > N) {
            wa("edge endpoint is out of range");
        }
        if (u_ll == v_ll) {
            wa("self-loop is not an edge of the complete graph");
        }

        int u = (int)u_ll;
        int v = (int)v_ll;
        if (u > v) swap(u, v);
        if (removed[u][v]) {
            wa("duplicate edge");
        }
        removed[u][v] = 1;
    }

    ensure_no_extra();

    vector<vector<int>> g((int)N + 1);
    for (int u = 1; u <= (int)N; ++u) {
        for (int v = u + 1; v <= (int)N; ++v) {
            if (!removed[u][v]) {
                g[u].push_back(v);
                g[v].push_back(u);
            }
        }
    }

    vector<int> dist((int)N + 1, -1);
    queue<int> q;
    dist[1] = 0;
    q.push(1);
    while (!q.empty()) {
        int v = q.front();
        q.pop();
        for (int to : g[v]) {
            if (dist[to] == -1) {
                dist[to] = dist[v] + 1;
                q.push(to);
            }
        }
    }

    if (dist[(int)N] != K) {
        wa("shortest distance from 1 to N is " + to_string(dist[(int)N]) + ", not " + to_string(K));
    }

    return 0;
}
