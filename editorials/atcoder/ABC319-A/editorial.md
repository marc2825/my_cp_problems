この問題で与えられているデータのフォーマットは各行全て<br>
　　**『（ハンドルネーム）（空白1つ）（4桁の数字）』**<br>
であるため、ハンドルネームから右に2~5文字進んだ位置に対応する文字列が求めるレートとなります。<br>

よって、開始位置を1文字ずつ前から愚直に探索して、ハンドルネームと一致するタイミングを見つければ、埋め込んだデータの整形などをせずとも問題に答えることが出来ます。<br>

C++による解答例：
```C++
#include <bits/stdc++.h>
using namespace std;

int main() {
    string T = R"(tourist 3858
ksun48 3679
Benq 3658
Um_nik 3648
apiad 3638
Stonefeang 3630
ecnerwala 3613
mnbvmar 3555
newbiedmy 3516
semiexp 3481)";

    string S; cin >> S;
    for(int i=0; i<T.size(); i++) {
        if(T.substr(i, S.size()) == S) {
            cout << T.substr(i + S.size() + 1, 4) << endl;
            return 0;
        }
    }

}
```

<br>
（ここで、複数行からなる文字列を一つの文字列とみなすために、C++の「生文字列リテラル」と呼ばれる言語仕様を用いております。<br>　参考 : https://cpprefjp.github.io/lang/cpp11/raw_string_literals.html ）<br>