def is_wall(X):
    rgidx = -1
    ldidx = -1

    for i in range(len(X)):
        if X[i] == "g":
            rgidx = i
        elif X[i] == "d" and ldidx == -1:
            ldidx = i

    return rgidx != -1 and ldidx != -1 and ldidx - rgidx > 3


Q = int(input())

for _ in range(Q):
    S = input()
    T = input()

    cnts = {c: S.count(c) for c in "dog"}
    cntt = {c: T.count(c) for c in "dog"}

    if cnts != cntt:
        print("No")
        continue

    print("Yes" if is_wall(S) == is_wall(T) else "No")