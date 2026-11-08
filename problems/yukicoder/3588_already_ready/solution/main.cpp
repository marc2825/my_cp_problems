#include <bits/stdc++.h>
#include <atcoder/all>
using namespace std;

// ACL: https://github.com/atcoder/ac-library

const int INF = 1000000000;

int op(int a, int b) { return min(a, b); }
int e() { return INF; }
int mapping(int f, int x) { return f + x; }
int composition(int f, int g) { return f + g; }
int id() { return 0; }


int main() {
    int N, K, M;
    cin >> N >> K >> M;

    vector<int> A(N + 1);
    long long S = 0;

    for (int i = 1; i <= N; i++) {
        cin >> A[i];
        S += A[i];
    }

    if (S % (N + 1) != 0) {
        cout << -1 << '\n';
        return 0;
    }

    long long T = S / (N + 1);

    if (T < 1) {
        cout << -1 << '\n';
        return 0;
    }

    vector<int> W(N + 1);

    for (int i = 1; i <= N; i++) {
        W[i] = A[i] - T;

        if (W[i] < 0) {
            cout << -1 << '\n';
            return 0;
        }
    }

    if (W[M] < 1) {
        cout << -1 << '\n';
        return 0;
    }

    if (A[M] - 2 < K) {
        cout << -1 << '\n';
        return 0;
    }

    int m = (int)(T - 1);

    vector<int> B(N + 1, 0);
    vector<int> rem(N + 1, 0);
    vector<int> dline(N + 1, INF);
    vector<int> dline_cnt(max(1, m) + 1, 0);

    int sumB = 0;

    for (int i = 1; i <= N; i++) {
        int b = W[i] - (i == M ? 1 : 0);

        if (b < 0) {
            cout << -1 << '\n';
            return 0;
        }

        B[i] = b;
        rem[i] = b;
        sumB += b;

        if (b > 0) {
            int d = K + 1 - b;

            if (d < 1) {
                cout << -1 << '\n';
                return 0;
            }

            d = min(d, m);
            dline[i] = d;
            dline_cnt[d] += b;
        }
    }

    assert(sumB == m);

    if (m == 0) {
        cout << 1 << '\n';
        cout << M << '\n';
        return 0;
    }

    vector<int> slack_init(m + 1, INF);
    int pref = 0;

    for (int x = 1; x <= m; x++) {
        pref += dline_cnt[x];

        int slack = x - pref;

        if (slack < 0) {
            cout << -1 << '\n';
            return 0;
        }

        slack_init[x] = slack;
    }

    assert(pref == m);

    atcoder::lazy_segtree<int, op, e, int, mapping, composition, id> slack_tree(slack_init);

    vector<int> team_init(N + 1, INF);

    for (int i = 1; i <= N; i++) {
        if (rem[i] > 0) {
            team_init[i] = dline[i];
        }
    }

    atcoder::segtree<int, op, e> team_tree(team_init);

    vector<int> ans;
    ans.reserve((size_t)T);

    for (int p = 1; p <= m; p++) {
        if (team_tree.all_prod() < p) {
            cout << -1 << '\n';
            return 0;
        }

        int E = slack_tree.max_right(p, [](int min_slack) {
            return min_slack > 0;
        });

        int c = team_tree.max_right(1, [&](int min_dline) {
            return min_dline > E;
        });

        if (c == N + 1) {
            cout << -1 << '\n';
            return 0;
        }

        ans.push_back(c);

        if (p < dline[c]) {
            slack_tree.apply(p, dline[c], -1);
        }

        rem[c]--;

        if (rem[c] == 0) {
            team_tree.set(c, INF);
        }
    }

    ans.push_back(M);

    cout << ans.size() << '\n';

    for (int i = 0; i < (int)ans.size(); i++) {
        if (i) cout << ' ';
        cout << ans[i];
    }

    cout << '\n';

    return 0;
}