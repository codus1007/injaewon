# -*- coding: utf-8 -*-
"""
PowerShell / cmd 콘솔에서 실행하는 테트리스 (jstris 스타일 키 배치)
실행법: python tetris.py

조작법:
  ← / →     : 좌우 이동 (누르고 있으면 계속 이동)
  ↓         : 소프트 드롭 (누르고 있으면 빠르게 계속 낙하)
  Space     : 하드 드롭(즉시 떨어뜨리기)
  ↑ / X     : 시계 방향 회전 (CW)
  Z         : 반시계 방향 회전 (CCW)
  A         : 180도 회전
  C         : 홀드(보관)
  R         : 다시 시작
  P         : 일시정지
  Q         : 게임 종료
"""

import sys
import os
import re
import time
import random

try:
    import msvcrt
except ImportError:
    print("이 게임은 Windows(PowerShell / cmd)에서만 동작합니다.")
    sys.exit(1)

import ctypes

# ---------------------------------------------------------
# Windows 콘솔에서 ANSI 색상 코드를 사용할 수 있도록 활성화
# ---------------------------------------------------------
def enable_ansi():
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        kernel32.SetConsoleMode(handle, 7)
    except Exception:
        pass


# 실제 키보드의 물리적 눌림 상태를 직접 확인 (이벤트 타이밍 추측 대신 사용)
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28

def is_key_down(vk_code):
    try:
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)
    except Exception:
        return False


# ---------------------------------------------------------
# 게임 상수
# ---------------------------------------------------------
WIDTH = 10
HEIGHT = 20

RESET = '\x1b[0m'
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def visible_len(s):
    return len(_ANSI_RE.sub('', s))


def pad_visible(s, width):
    gap = width - visible_len(s)
    return s + (' ' * gap if gap > 0 else '')


COLORS = {
    'I': '\x1b[96m',
    'O': '\x1b[93m',
    'T': '\x1b[95m',
    'S': '\x1b[92m',
    'Z': '\x1b[91m',
    'J': '\x1b[94m',
    'L': '\x1b[33m',
}

SHAPES = {
    'I': [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    'O': [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    'T': [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    'S': [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    'Z': [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    'J': [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    'L': [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}

# 좌우 자동 반복(DAS) 타이밍
DAS_DELAY = 0.15          # 처음 누른 뒤 자동 반복이 시작되기까지의 지연
ARR = 0.03                # 자동 반복 간격
SOFT_DROP_INTERVAL = 0.018 # 소프트 드롭 중 낙하 간격

# 락 딜레이: 바닥에 닿은 뒤 실제로 고정되기까지 주어지는 유예 시간
LOCK_DELAY = 0.5
MAX_LOCK_RESETS = 15      # 무한정 유예되는 것을 막기 위한 최대 리셋 횟수


# ---------------------------------------------------------
# 게임 로직
# ---------------------------------------------------------
def new_board():
    return [[None] * WIDTH for _ in range(HEIGHT)]


def collision(board, ptype, rot, x, y):
    for (ox, oy) in SHAPES[ptype][rot]:
        bx, by = x + ox, y + oy
        if bx < 0 or bx >= WIDTH or by >= HEIGHT:
            return True
        if by >= 0 and board[by][bx] is not None:
            return True
    return False


def lock_piece(board, piece):
    for (ox, oy) in SHAPES[piece['type']][piece['rot']]:
        bx, by = piece['x'] + ox, piece['y'] + oy
        if 0 <= by < HEIGHT and 0 <= bx < WIDTH:
            board[by][bx] = piece['type']


def clear_lines(board):
    new_b = [row for row in board if any(c is None for c in row)]
    cleared = HEIGHT - len(new_b)
    for _ in range(cleared):
        new_b.insert(0, [None] * WIDTH)
    return new_b, cleared


class PieceQueue:
    """7-bag 방식이며, 다음에 나올 조각을 preview 개수만큼 미리 볼 수 있다."""
    def __init__(self, preview=5):
        self.preview = preview
        self.bag = []
        self.queue = []
        self._fill()

    def _refill_bag(self):
        types = list(SHAPES.keys())
        random.shuffle(types)
        self.bag.extend(types)

    def _fill(self):
        while len(self.queue) < self.preview + 1:
            if not self.bag:
                self._refill_bag()
            self.queue.append(self.bag.pop(0))

    def next(self):
        self._fill()
        val = self.queue.pop(0)
        self._fill()
        return val

    def peek(self, n):
        self._fill()
        return list(self.queue[:n])


HS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tetris_highscore.txt')


def load_high_score():
    try:
        with open(HS_FILE, 'r') as f:
            return int(f.read().strip())
    except Exception:
        return 0


def save_high_score(value):
    try:
        with open(HS_FILE, 'w') as f:
            f.write(str(value))
    except Exception:
        pass


def count_filled_corners(board, px, py):
    """T-스핀 판정을 위한 3-코너 규칙: 중심 셀 대각선 4칸 중 몇 칸이 막혀있는지 센다."""
    filled = 0
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        cx, cy = px + dx, py + dy
        if cy < 0:
            continue  # 보드 위쪽은 열려있는 것으로 취급
        if cx < 0 or cx >= WIDTH or cy >= HEIGHT:
            filled += 1
        elif board[cy][cx] is not None:
            filled += 1
    return filled


def check_spin(board, piece, last_action_rotate):
    """마지막으로 성공한 동작이 '회전'이었을 때 스핀 여부를 판정한다.
    - T 피스: 공식 가이드라인의 3-코너 규칙 (중심 대각선 4칸 중 3칸 이상 막힘)
    - J/L/S/Z 피스: 회전 후 좌/우/아래 어느 방향으로도 전혀 움직일 수 없으면
      (완전히 틈에 끼워진 상태) 스핀으로 인정한다. (jstris 등에서 말하는
      S-스핀/Z-스핀/J-스핀/L-스핀에 해당)
    - I, O 피스는 스핀 판정 대상에서 제외한다."""
    if not last_action_rotate:
        return False
    ptype = piece['type']
    if ptype == 'T':
        px, py = piece['x'] + 1, piece['y'] + 1  # T 피스의 회전축(피벗) 셀
        return count_filled_corners(board, px, py) >= 3
    if ptype in ('J', 'L', 'S', 'Z'):
        rot = piece['rot']
        blocked_left = collision(board, ptype, rot, piece['x'] - 1, piece['y'])
        blocked_right = collision(board, ptype, rot, piece['x'] + 1, piece['y'])
        blocked_down = collision(board, ptype, rot, piece['x'], piece['y'] + 1)
        return blocked_left and blocked_right and blocked_down
    return False


def spawn_piece(ptype):
    return {'type': ptype, 'rot': 0, 'x': 3, 'y': 0}


def try_move(board, piece, dx, dy):
    nx, ny = piece['x'] + dx, piece['y'] + dy
    if not collision(board, piece['type'], piece['rot'], nx, ny):
        piece['x'], piece['y'] = nx, ny
        return True
    return False


# ---------------------------------------------------------
# SRS(Super Rotation System) 킥 테이블
# (dx, dy) - dy는 이 코드의 좌표계 기준(양수 = 아래쪽)으로 이미 변환되어 있음.
# 이 상하 킥이 있어야 2칸 깊이 홈에 T를 밀어넣는 T-스핀 트리플이나
# S/Z 피스를 좁은 틈에 끼워 넣는 스핀이 가능해진다.
# ---------------------------------------------------------
JLSTZ_KICKS = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
}

I_KICKS = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
}

# 180도 회전에 대한 공식 표준은 없으므로, 실전에서 흔히 쓰이는 소규모 오프셋을 사용한다.
KICKS_180 = [(0, 0), (0, -1), (-1, 0), (1, 0), (0, 1), (-1, -1), (1, -1)]


def get_kicks(ptype, from_rot, to_rot):
    if ptype == 'O':
        return [(0, 0)]
    if ptype == 'I':
        return I_KICKS.get((from_rot, to_rot), [(0, 0)])
    return JLSTZ_KICKS.get((from_rot, to_rot), [(0, 0)])


def try_rotate(board, piece, steps):
    """steps: +1 = CW, -1 = CCW, 2 = 180
    SRS 킥 테이블 순서대로 오프셋을 시도하며, 상하(dy) 이동도 포함되어 있어
    T-스핀 트리플처럼 2칸 깊이 홈에 끼워 넣는 회전도 가능하다."""
    from_rot = piece['rot']
    new_rot = (from_rot + steps) % 4
    if steps == 2:
        kicks = KICKS_180
    else:
        kicks = get_kicks(piece['type'], from_rot, new_rot)
    for dx, dy in kicks:
        nx, ny = piece['x'] + dx, piece['y'] + dy
        if not collision(board, piece['type'], new_rot, nx, ny):
            piece['x'], piece['y'] = nx, ny
            piece['rot'] = new_rot
            return True
    return False


def is_grounded(board, piece):
    return collision(board, piece['type'], piece['rot'], piece['x'], piece['y'] + 1)


def hard_drop(board, piece):
    while try_move(board, piece, 0, 1):
        pass


# ---------------------------------------------------------
# 렌더링
# ---------------------------------------------------------
def render(board, piece, next_list, hold_type, score, level, total_lines, paused, game_over,
           high_score=0, combo=0, b2b=False, message='', message_active=False,
           pieces_placed=0, elapsed=0.0):
    active_cells = {}
    ghost_cells = {}
    if piece and not game_over:
        for (ox, oy) in SHAPES[piece['type']][piece['rot']]:
            bx, by = piece['x'] + ox, piece['y'] + oy
            active_cells[(bx, by)] = piece['type']

        # 착지 예상 위치(고스트 피스) 계산
        gy = piece['y']
        while not collision(board, piece['type'], piece['rot'], piece['x'], gy + 1):
            gy += 1
        for (ox, oy) in SHAPES[piece['type']][piece['rot']]:
            bx, by = piece['x'] + ox, gy + oy
            if (bx, by) not in active_cells:
                ghost_cells[(bx, by)] = piece['type']

    board_lines = ['+' + '--' * WIDTH + '+']
    for r in range(HEIGHT):
        line = '|'
        for c in range(WIDTH):
            if (c, r) in active_cells:
                line += COLORS[active_cells[(c, r)]] + '[]' + RESET
            elif (c, r) in ghost_cells:
                # 'dim'(\x1b[2m) 효과는 구형 cmd.exe/PowerShell 콘솔에서 무시되는 경우가 많아
                # 조각 색과 상관없이 밝은 흰색 윤곽으로 표시해 확실히 구분되게 한다.
                line += '\x1b[1;97m' + '::' + RESET
            elif board[r][c]:
                line += COLORS[board[r][c]] + '[]' + RESET
            else:
                line += '  '
        line += '|'
        board_lines.append(line)
    board_lines.append('+' + '--' * WIDTH + '+')

    if game_over:
        overlay = ['', 'GAME OVER', '', f'SCORE {score}', '', 'Press R']
        start = 1 + max(0, (HEIGHT - len(overlay)) // 2)
        for i, text in enumerate(overlay):
            row = start + i
            if 1 <= row <= HEIGHT:
                centered = text.center(WIDTH * 2)
                board_lines[row] = '|' + '\x1b[1;91m' + centered + RESET + '|'

    def mini_grid(ptype):
        rows = []
        if ptype is None:
            for _ in range(4):
                rows.append('        ')
            return rows
        grid = [[False] * 4 for _ in range(4)]
        for (ox, oy) in SHAPES[ptype][0]:
            grid[oy][ox] = True
        for r in range(4):
            s = ''
            for c in range(4):
                s += (COLORS[ptype] + '[]' + RESET) if grid[r][c] else '  '
            rows.append(s)
        return rows

    mins, secs = divmod(int(elapsed), 60)
    pps = (pieces_placed / elapsed) if elapsed > 0 else 0.0

    # ---- 왼쪽 컬럼: 홀드 + 점수 + 단축키 ----
    left = ['Hold:']
    left.append('')
    left.extend(mini_grid(hold_type))
    left.append(f'Score : {score}')
    left.append(f'Best  : {high_score}')
    left.append(f'Level : {level}')
    left.append(f'Lines : {total_lines}')
    left.append(f'Time  : {mins:02d}:{secs:02d}')
    left.append(f'Pieces: {pieces_placed} ({pps:.2f} pps)')

    if combo > 0:
        left.append(f'Combo x{combo}')
    if b2b:
        left.append('B2B!')
    if message_active and message:
        left.append('')
        left.append(f'>> {message} <<')
    if paused:
        left.append('')
        left.append('*** PAUSED ***')
    if game_over:
        left.append('')
        left.append('*** GAME OVER ***')
        left.append(f'Final Score: {score}')
        left.append('Press R to restart, Q to exit')

    left.append('')
    left.append('Controls:')
    left.append('<-/-> : Move (hold)')
    left.append('Down  : Soft Drop (hold)')
    left.append('Space : Hard Drop')
    left.append('Up/X  : Rotate CW')
    left.append('Z     : Rotate CCW')
    left.append('A     : Rotate 180')
    left.append('C     : Hold')
    left.append('R     : Restart')
    left.append('P     : Pause')
    left.append('Q     : Quit')

    # ---- 오른쪽 컬럼: 다음 5개 조각을 실제 모양으로 ----
    right = ['Next:', '']
    for t in next_list:
        right.extend(mini_grid(t))

    LEFT_WIDTH = 36
    left_blank = ' ' * LEFT_WIDTH
    board_blank = ' ' * (WIDTH * 2 + 2)

    out = ['\x1b[H']
    max_len = max(len(left), len(board_lines), len(right))
    for i in range(max_len):
        l = left[i] if i < len(left) else left_blank
        m = board_lines[i] if i < len(board_lines) else board_blank
        r = right[i] if i < len(right) else ''
        out.append(pad_visible(l, LEFT_WIDTH) + ' ' + m + '   ' + r + '\x1b[K')
    out.append('\x1b[J')
    sys.stdout.write('\n'.join(out))
    sys.stdout.flush()


# ---------------------------------------------------------
# 메인 루프
# ---------------------------------------------------------
def main():
    enable_ansi()
    os.system('cls')
    sys.stdout.write('\x1b[?25l')  # 커서 숨기기

    def new_game():
        state = {}
        state['board'] = new_board()
        state['queue'] = PieceQueue(preview=5)
        state['current_type'] = state['queue'].next()
        state['piece'] = spawn_piece(state['current_type'])
        state['hold_type'] = None
        state['can_hold'] = True
        state['score'] = 0
        state['total_lines'] = 0
        state['level'] = 1
        state['paused'] = False
        state['game_over'] = False
        state['fall_interval'] = 0.5
        state['last_fall'] = time.time()
        # 좌우 DAS 상태
        state['das_dir'] = 0
        state['das_next_move'] = 0.0
        state['soft_active'] = False
        # 락 딜레이 상태
        state['lock_timer'] = None
        state['lock_resets'] = 0
        # T-스핀 판정용: 마지막 성공 동작이 회전이었는지
        state['last_action_rotate'] = False
        # 콤보 / 백투백
        state['combo'] = -1
        state['b2b'] = False
        # 화면 메시지
        state['message'] = ''
        state['message_until'] = 0.0
        # 통계
        state['pieces_placed'] = 0
        state['start_time'] = time.time()
        state['paused_duration'] = 0.0
        state['pause_started_at'] = None
        state['end_time'] = None
        state['high_score'] = load_high_score()
        return state

    s = new_game()

    def reset_lock_state():
        s['lock_timer'] = None
        s['lock_resets'] = 0

    def maybe_reset_lock():
        """플레이어가 성공적으로 움직이거나 회전했을 때, 바닥에 닿아있다면
        락 딜레이 타이머를 다시 시작해 조작할 시간을 더 준다."""
        if is_grounded(s['board'], s['piece']) and s['lock_resets'] < MAX_LOCK_RESETS:
            s['lock_timer'] = time.time()
            s['lock_resets'] += 1

    def spawn_next():
        s['current_type'] = s['queue'].next()
        s['piece'] = spawn_piece(s['current_type'])
        s['can_hold'] = True
        s['last_action_rotate'] = False
        reset_lock_state()
        if collision(s['board'], s['piece']['type'], s['piece']['rot'], s['piece']['x'], s['piece']['y']):
            s['game_over'] = True
            s['end_time'] = time.time()
            if s['score'] > s['high_score']:
                s['high_score'] = s['score']
                save_high_score(s['score'])

    def flash_message(text):
        s['message'] = text
        s['message_until'] = time.time() + 1.5

    def lock_and_advance():
        spin = check_spin(s['board'], s['piece'], s['last_action_rotate'])
        spin_type = s['piece']['type']
        lock_piece(s['board'], s['piece'])
        s['board'], cleared = clear_lines(s['board'])
        s['pieces_placed'] += 1

        gained = 0
        label = ''
        difficult = False

        if spin:
            spin_scores = {0: 400, 1: 800, 2: 1200, 3: 1600}
            gained = spin_scores.get(cleared, 1600) * s['level']
            suffix_map = {0: '', 1: ' SINGLE', 2: ' DOUBLE', 3: ' TRIPLE'}
            label = f"{spin_type}-SPIN{suffix_map.get(cleared, ' TRIPLE')}"
            difficult = cleared > 0
        elif cleared > 0:
            gained = LINE_SCORES[cleared] * s['level']
            label_map = {1: 'SINGLE', 2: 'DOUBLE', 3: 'TRIPLE', 4: 'TETRIS'}
            label = label_map[cleared]
            difficult = (cleared == 4)

        if cleared > 0:
            s['combo'] = 0 if s['combo'] < 0 else s['combo'] + 1
            if s['combo'] > 0:
                gained += 50 * s['combo'] * s['level']
            if difficult:
                if s['b2b']:
                    gained = int(gained * 1.5)
                    label += ' B2B'
                s['b2b'] = True
            else:
                s['b2b'] = False
        else:
            s['combo'] = -1

        s['score'] += gained

        if cleared > 0 and all(all(c is None for c in row) for row in s['board']):
            s['score'] += 2000 * s['level']
            label = (label + ' + ALL CLEAR') if label else 'ALL CLEAR'

        if label:
            flash_message(label)

        if cleared:
            s['total_lines'] += cleared
            s['level'] = s['total_lines'] // 10 + 1
            s['fall_interval'] = max(0.08, 0.5 - (s['level'] - 1) * 0.03)

        if s['score'] > s['high_score']:
            s['high_score'] = s['score']

        spawn_next()
        s['last_fall'] = time.time()

    def do_hold():
        if not s['can_hold'] or s['game_over']:
            return
        if s['hold_type'] is None:
            s['hold_type'] = s['current_type']
            s['current_type'] = s['queue'].next()
        else:
            s['current_type'], s['hold_type'] = s['hold_type'], s['current_type']
        s['piece'] = spawn_piece(s['current_type'])
        s['can_hold'] = False
        s['last_action_rotate'] = False
        reset_lock_state()
        if collision(s['board'], s['piece']['type'], s['piece']['rot'], s['piece']['x'], s['piece']['y']):
            s['game_over'] = True
            s['end_time'] = time.time()

    def redraw():
        now = time.time()
        message_active = now < s['message_until']
        ref_time = s['end_time'] if (s['game_over'] and s['end_time'] is not None) else now
        elapsed = ref_time - s['start_time'] - s['paused_duration']
        if s['pause_started_at'] is not None:
            elapsed -= (ref_time - s['pause_started_at'])
        elapsed = max(0.0, elapsed)
        render(s['board'], s['piece'], s['queue'].peek(5), s['hold_type'],
               s['score'], s['level'], s['total_lines'], s['paused'], s['game_over'],
               high_score=s['high_score'], combo=s['combo'], b2b=s['b2b'],
               message=s['message'], message_active=message_active,
               pieces_placed=s['pieces_placed'], elapsed=elapsed)

    redraw()

    try:
        while True:
            now = time.time()

            # ---- 이산적인 키 입력 처리 (회전/홀드/드롭/일시정지 등) ----
            while msvcrt.kbhit():
                key = msvcrt.getch()
                if key in (b'\x00', b'\xe0'):
                    key2 = msvcrt.getch()
                    if not s['game_over'] and not s['paused']:
                        if key2 == b'H':      # up arrow -> CW
                            if try_rotate(s['board'], s['piece'], 1):
                                maybe_reset_lock()
                                s['last_action_rotate'] = True
                    # K(왼쪽)/M(오른쪽)/P(아래쪽) 화살표는 아래 폴링 방식으로 처리하므로
                    # 여기서는 큐만 비워준다.
                else:
                    try:
                        k = key.decode('utf-8', errors='ignore').lower()
                    except Exception:
                        k = ''
                    if k == 'q':
                        raise KeyboardInterrupt
                    elif k == 'r':
                        s = new_game()
                        while msvcrt.kbhit():   # 재시작 이전에 남아있던 키 입력은 버린다
                            msvcrt.getch()
                        redraw()
                        break
                    elif k == 'p' and not s['game_over']:
                        s['paused'] = not s['paused']
                        if s['paused']:
                            s['pause_started_at'] = time.time()
                        elif s['pause_started_at'] is not None:
                            s['paused_duration'] += time.time() - s['pause_started_at']
                            s['pause_started_at'] = None
                    elif not s['game_over'] and not s['paused']:
                        if k == 'z':          # CCW
                            if try_rotate(s['board'], s['piece'], -1):
                                maybe_reset_lock()
                                s['last_action_rotate'] = True
                        elif k == 'x':        # CW
                            if try_rotate(s['board'], s['piece'], 1):
                                maybe_reset_lock()
                                s['last_action_rotate'] = True
                        elif k == 'a':        # 180
                            if try_rotate(s['board'], s['piece'], 2):
                                maybe_reset_lock()
                                s['last_action_rotate'] = True
                        elif k == 'c':        # hold
                            do_hold()
                        elif k == ' ':        # hard drop
                            hard_drop(s['board'], s['piece'])
                            lock_and_advance()

            # ---- 실제 키보드 상태를 직접 폴링 (좌우/아래 홀드 이동) ----
            if not s['paused'] and not s['game_over']:
                left_down = is_key_down(VK_LEFT)
                right_down = is_key_down(VK_RIGHT)
                down_down = is_key_down(VK_DOWN)

                if left_down and not right_down:
                    if s['das_dir'] != -1:
                        if try_move(s['board'], s['piece'], -1, 0):
                            maybe_reset_lock()
                            s['last_action_rotate'] = False
                        s['das_dir'] = -1
                        s['das_next_move'] = now + DAS_DELAY
                    elif now >= s['das_next_move']:
                        if try_move(s['board'], s['piece'], -1, 0):
                            maybe_reset_lock()
                            s['last_action_rotate'] = False
                        s['das_next_move'] = now + ARR
                elif right_down and not left_down:
                    if s['das_dir'] != 1:
                        if try_move(s['board'], s['piece'], 1, 0):
                            maybe_reset_lock()
                            s['last_action_rotate'] = False
                        s['das_dir'] = 1
                        s['das_next_move'] = now + DAS_DELAY
                    elif now >= s['das_next_move']:
                        if try_move(s['board'], s['piece'], 1, 0):
                            maybe_reset_lock()
                            s['last_action_rotate'] = False
                        s['das_next_move'] = now + ARR
                else:
                    s['das_dir'] = 0

                s['soft_active'] = down_down

                # ---- 중력 / 소프트 드롭 ----
                effective_interval = SOFT_DROP_INTERVAL if s['soft_active'] else s['fall_interval']
                if now - s['last_fall'] >= effective_interval:
                    try_move(s['board'], s['piece'], 0, 1)
                    s['last_fall'] = now

                # ---- 락 딜레이: 바닥에 닿아도 바로 고정하지 않고 유예 시간을 준다 ----
                if is_grounded(s['board'], s['piece']):
                    if s['lock_timer'] is None:
                        s['lock_timer'] = now
                    elif now - s['lock_timer'] >= LOCK_DELAY:
                        lock_and_advance()
                else:
                    s['lock_timer'] = None

            redraw()
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        if s['score'] > s['high_score']:
            s['high_score'] = s['score']
        save_high_score(s['high_score'])
        sys.stdout.write('\x1b[?25h')  # 커서 다시 표시
        sys.stdout.write(RESET)
        sys.stdout.flush()
        print(f"\n\n게임을 종료합니다. 최종 점수: {s['score']}  (최고 점수: {s['high_score']})")


if __name__ == '__main__':
    main()
