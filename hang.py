import random

words = [
    "python",
    "computer",
    "keyboard",
    "banana",
    "apple",
    "school",
    "game",
    "program",
    "internet",
    "window",
    "mouse",
    "monitor",
    "speaker",
    "phone",
    "camera",
    "robot",
    "machine",
    "science",
    "music",
    "movie",
    "dragon",
    "tiger",
    "lion",
    "elephant",
    "rabbit",
    "horse",
    "cat",
    "dog",
    "bird",
    "fish",
    "pizza",
    "burger",
    "coffee",
    "water",
    "cookie",
    "chocolate",
    "orange",
    "grape",
    "melon",
    "strawberry",
    "winter",
    "summer",
    "spring",
    "autumn",
    "rainbow",
    "cloud",
    "storm",
    "ocean",
    "river",
    "mountain",
    "forest",
    "flower",
    "tree",
    "star",
    "planet",
    "space",
    "rocket",
    "energy",
    "power",
    "battle",
    "warrior",
    "monster",
    "castle",
    "sword",
    "shield",
    "magic",
    "treasure",
    "adventure",
    "secret",
    "friend",
    "family",
    "dream",
    "future",
    "world",
    "travel",
    "island",
    "desert",
    "school",
    "teacher",
    "student",
    "book",
    "pencil",
    "paper",
    "chair",
    "table"
]

print("=" * 30)
print("🎯 행맨 게임")
print("=" * 30)

while True:
    answer = random.choice(words)
    hidden = ["_"] * len(answer)
    wrong = []
    life = 10

    print("\n새 게임 시작!")
    print("단어:", " ".join(hidden))
    print("남은 목숨:", life)

    while life > 0:
        print("\n틀린 글자:", wrong)
        print("현재:", " ".join(hidden))

        guess = input("글자를 입력하세요: ").lower()

        if len(guess) != 1 or not guess.isalpha():
            print("알파벳 한 글자만 입력하세요.")
            continue

        if guess in hidden or guess in wrong:
            print("이미 입력한 글자입니다.")
            continue

        if guess in answer:
            print("✅ 정답 글자입니다!")

            for i in range(len(answer)):
                if answer[i] == guess:
                    hidden[i] = guess

        else:
            print("❌ 틀렸습니다!")
            wrong.append(guess)
            life -= 1

        if "_" not in hidden:
            print("\n🎉 성공!")
            print("정답:", answer)
            break

        print("남은 목숨:", life)

    else:
        print("\n💀 게임 오버!")
        print("정답은:", answer)

    again = input("\n다시 하시겠습니까? (y/n): ").lower()

    if again != "y":
        print("게임 종료!")
        break