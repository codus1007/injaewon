import random

while True:
    # 새 게임 시작 화면
    print("\n" + "=" * 30)
    print("⚾ 숫자 야구 게임 ⚾")
    print("1~9의 서로 다른 숫자 3개를 맞혀보세요!")
    print("예: 123")
    print("종료하려면 q 입력")
    print("=" * 30)

    # 컴퓨터 숫자 생성
    numbers = random.sample(range(1, 10), 3)
    count = 0

    while True:
        user = input("\n숫자 입력: ")

        if user.lower() == "q":
            print("게임을 종료합니다.")
            exit()

        if len(user) != 3 or not user.isdigit():
            print("3자리 숫자를 입력하세요.")
            continue

        guess = [int(i) for i in user]

        if len(set(guess)) != 3:
            print("중복되지 않는 숫자를 입력하세요.")
            continue

        count += 1

        strike = 0
        ball = 0

        for i in range(3):
            if guess[i] == numbers[i]:
                strike += 1
            elif guess[i] in numbers:
                ball += 1

        if strike == 3:
            print(f"\n🎉 정답입니다! ({''.join(map(str, numbers))})")
            print(f"{count}번 만에 맞혔습니다!")
            break

        elif strike == 0 and ball == 0:
            print("OUT!")

        else:
            print(f"{strike} Strike {ball} Ball")

    # 다시 시작 여부
    again = input("\n새 게임 시작할까요? (y/n): ").lower()

    if again != "y":
        print("게임을 종료합니다.")
        break