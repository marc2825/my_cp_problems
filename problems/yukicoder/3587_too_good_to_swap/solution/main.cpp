#include <bits/stdc++.h>
using namespace std;


int main() {
    int Q;
    cin >> Q;

    while(Q--) {
        string S, T;
        cin >> S >> T;
        int N = S.size();

        map<char, int> cnts, cntt;

        for(int i = 0; i < N; i++) {
            cnts[S[i]]++;
            cntt[T[i]]++;
        }

        if(cnts != cntt) {
            cout << "No\n";
            continue;
        }

        auto isWall = [&](const string& X) {
            int rgidx = -1;
            int ldidx = -1;

            for(int i = 0; i < N; i++) {
                if(X[i] == 'g') {
                    rgidx = i;
                }
                else if(X[i] == 'd' && ldidx == -1) {
                    ldidx = i;
                }
            }

            return rgidx != -1
                && ldidx != -1
                && ldidx - rgidx > 3;
        };

        cout << (isWall(S) == isWall(T) ? "Yes" : "No") << '\n';
    }

    return 0;
}