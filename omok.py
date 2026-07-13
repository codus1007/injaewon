import os

SIZE = 15

# 바둑판 생성
board = [[" " for _ in range(SIZE)] for _ in range(SIZE)]


def clear():
    os.system("cls")


def print_board():
    clear()

    print("   ", end="")
    for i in range(SIZE):
        print(f"{i:2}", end=" ")
    print()

    for y in range(SIZE):
        print(f"{y:2} ", end="")

        for x in range(SIZE):
            print(f"[{board[y][x]}]", end="")

        print()

    print()


def check_win(x, y, stone):
    directions = [
        (1, 0),   # 가로
        (0, 1),   # 세로
        (1, 1),   # 대각선 \
        (1, -1)   # 대각선 /
    ]

    for dx, dy in directions:
        count = 1

        # 정방향
        nx = x + dx
        ny = y + dy

        while (
            0 <= nx < SIZE and
            0 <= ny < SIZE and
            board[ny][nx] == stone
        ):
            count += 1
            nx += dx
            ny += dy


        # 반대 방향
        nx = x - dx
        ny = y - dy

        while (
            0 <= nx < SIZE and
            0 <= ny < SIZE and
            board[ny][nx] == stone
        ):
            count += 1
            nx -= dx
            ny -= dy


        if count >= 5:
            return True

    return False



turn = "●"

while True:

    print_board()

    print(f"{turn} 차례")

    try:
        x, y = map(
            int,
            input("좌표 입력 (x y): ").split()
        )

    except:
        print("숫자 두 개를 입력하세요.")
        input("Enter...")
        continue


    if not (0 <= x < SIZE and 0 <= y < SIZE):
        print("범위를 벗어났습니다.")
        input("Enter...")
        continue


    if board[y][x] != " ":
        print("이미 돌이 있습니다.")
        input("Enter...")
        continue


    board[y][x] = turn


    # 승리 확인
    if check_win(x, y, turn):
        print_board()
        print(f"🎉 {turn} 승리!")
        break


    # 무승부 확인
    full = True

    for row in board:
        if " " in row:
            full = False
            break

    if full:
        print_board()
        print("무승부!")
        break


    # 턴 변경
    if turn == "●":
        turn = "○"
    else:
        turn = "●"