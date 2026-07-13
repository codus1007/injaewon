import random
import time
import msvcrt

# 화면 크기
WIDTH = 30
HEIGHT = 15

# 뱀 초기 위치
snake = [(5, 5), (4, 5), (3, 5)]

# 방향
direction = "RIGHT"

# 먹이 생성
food = (
    random.randint(1, WIDTH - 2),
    random.randint(1, HEIGHT - 2)
)

score = 0


def move_cursor_top():
    # 화면 삭제 없이 커서만 맨 위로 이동
    print("\033[H", end="")


def draw():
    move_cursor_top()

    for y in range(HEIGHT):
        line = ""

        for x in range(WIDTH):

            # 뱀
            if (x, y) in snake:
                if (x, y) == snake[0]:
                    line += "@"
                else:
                    line += "O"

            # 먹이
            elif (x, y) == food:
                line += "*"

            # 벽
            elif x == 0 or x == WIDTH - 1 or y == 0 or y == HEIGHT - 1:
                line += "#"

            # 빈 공간
            else:
                line += " "

        print(line)


def input_key():
    global direction

    if msvcrt.kbhit():
        key = msvcrt.getch()

        # 방향키
        if key == b'\xe0':
            key = msvcrt.getch()

            if key == b'H' and direction != "DOWN":
                direction = "UP"

            elif key == b'P' and direction != "UP":
                direction = "DOWN"

            elif key == b'K' and direction != "RIGHT":
                direction = "LEFT"

            elif key == b'M' and direction != "LEFT":
                direction = "RIGHT"

        # 종료
        elif key.lower() == b'q':
            game_over()


def move():
    global food, score

    x, y = snake[0]

    if direction == "UP":
        y -= 1

    elif direction == "DOWN":
        y += 1

    elif direction == "LEFT":
        x -= 1

    elif direction == "RIGHT":
        x += 1

    new_head = (x, y)

    # 충돌 판정
    if (
        x == 0 or
        x == WIDTH - 1 or
        y == 0 or
        y == HEIGHT - 1 or
        new_head in snake
    ):
        game_over()


    snake.insert(0, new_head)


    # 먹이 먹기
    if new_head == food:
        score += 10

        while True:
            food = (
                random.randint(1, WIDTH - 2),
                random.randint(1, HEIGHT - 2)
            )

            if food not in snake:
                break

    else:
        snake.pop()


def game_over():
    print("\n\n================")
    print("   GAME OVER")
    print("================")
    print("FINAL SCORE:", score)
    exit()



# 시작 시 한번만 화면 정리
print("\033[2J", end="")

# 게임 실행
while True:
    draw()
    input_key()
    move()

    time.sleep(0.12)