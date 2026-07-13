import random
import time

symbols = ["🍒", "🍋", "🍊", "🍬", "🍎"]

coin = 100

print("=" * 30)
print("🎰 슬롯머신 게임")
print("=" * 30)
print("시작 코인:", coin)

while True:
    print("\n현재 코인:", coin)

    if coin <= 0:
        print("💸 코인이 모두 떨어졌습니다!")
        break

    play = input("슬롯을 돌리시겠습니까? (y/n): ").lower()

    if play == "n":
        print("게임 종료!")
        print("남은 코인:", coin)
        break

    if play != "y":
        print("y 또는 n을 입력하세요.")
        continue

    # 베팅
    bet = int(input("베팅할 코인: "))

    if bet > coin:
        print("코인이 부족합니다.")
        continue

    if bet <= 0:
        print("올바른 금액을 입력하세요.")
        continue

    coin -= bet

    print("\n🎰 돌리는 중...")
    time.sleep(1)

    result = [
        random.choice(symbols),
        random.choice(symbols),
        random.choice(symbols)
    ]

    print(" | ".join(result))

    # 결과 판정
    if result[0] == result[1] == result[2]:
        if result[0] == "7️⃣":
            reward = bet * 10
            print("🔥 JACKPOT!!!")
        else:
            reward = bet * 5
            print("🎉 대박!")
        
        coin += reward
        print(f"+{reward} 코인 획득!")

    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        reward = bet * 2
        coin += reward
        print("👍 2개 일치!")
        print(f"+{reward} 코인 획득!")

    else:
        print("😢 꽝!")

    print("-" * 30)