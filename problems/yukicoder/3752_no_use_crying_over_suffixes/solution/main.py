T = int(input())

for _ in range(T):
    N = int(input())
    A = list(map(int, input().split()))

    S = 0
    win = False
    
    for a in A:
        if a == 1 and S % 2 == 0:
            win = True
        S += a

    if S % 2 == 1:
        win = True

    print("Alice" if win else "Bob")