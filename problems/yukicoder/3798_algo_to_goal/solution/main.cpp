#include <bits/stdc++.h>
using namespace std;

int main() {
    const int C = 26;

    int Q;
    cin >> Q;

    while (Q--) {
        string S, T;
        cin >> S >> T;
        int N = S.size();

        vector<vector<int>> A(2, vector<int>(C, 0));
        vector<vector<int>> B(2, vector<int>(C, 0));
        for (int i = 0; i < N; i++) {
            A[i % 2][S[i] - 'a']++;
            B[i % 2][T[i] - 'a']++;
        }

        if (A != B) {
            cout << "No\n";
            continue;
        }

        bool dup = false;
        for (int p = 0; p < 2; p++) {
            for (int c = 0; c < C; c++) {
                if (A[p][c] >= 2) dup = true;
            }
        }

        if (dup) {
            cout << "Yes\n";
            continue;
        }

        int x = 0, y = 0;
        for (int i = 0; i < N; i++) {
            for (int j = i + 1; j < N; j++) {
                if (i % 2 != j % 2) continue;
                if (S[i] > S[j]) x++;
                if (T[i] > T[j]) y++;
            }
        }

        cout << (x % 2 == y % 2 ? "Yes" : "No") << '\n';
    }

    return 0;
}