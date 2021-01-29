# start:

import os, sys, pygame, threading, math, random, time, copy, json


class Board:
    def __init__(self, canvas, size=(0, 0, 30), rc=(5, 5)):
        self.canvas = canvas
        self.margin_left, self.margin_top, self.side = size
        self.size = rc
        # чей ход
        self.whose_move = 'w'
        # какой шаг сценария
        self.scenario_step = 1
        # конец ли игры?
        self.is_mat_end_game = False
        # начальная расстановка
        self.board = [['r', 'h', 'e', 'q', 'k', 'e', 'h', 'r'],
                      ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
                      ['r', 'h', 'e', 'q', 'k', 'e', 'h', 'r']]
        # начальная расстановка цветов
        self.board_colors = [['b', 'b', 'b', 'b', 'b', 'b', 'b', 'b'],
                             ['b', 'b', 'b', 'b', 'b', 'b', 'b', 'b'],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             ['w', 'w', 'w', 'w', 'w', 'w', 'w', 'w'],
                             ['w', 'w', 'w', 'w', 'w', 'w', 'w', 'w']]
        # позиции королей
        self.position_kings = {'b': [0, 4], 'w': [7, 4]}
        # инициализируем игровые фигуры (картинки)
        self.figures_links = {'pw': 'static/pawn_white.png', 'pb': 'static/pawn_black.png',
                              'rw': 'static/rook_white.png', 'rb': 'static/rook_black.png',
                              'hw': 'static/horse_white.png', 'hb': 'static/horse_black.png',
                              'ew': 'static/elephant_white.png', 'eb': 'static/elephant_black.png',
                              'qw': 'static/queen_white.png', 'qb': 'static/queen_black.png',
                              'kw': 'static/king_white.png', 'kb': 'static/king_black.png'}
        # фигуры
        self.figures = {key: pygame.transform.scale(self.load_image(link), (self.side, self.side)) for key, link in self.figures_links.items()}
        self.moves = []
        self.window_opened = False

    # поменять размер
    def set_view(self, size):
        self.margin_left, self.margin_top, self.side = size

    # получить координаты поля
    def get_cell(self, coord):
        x, y = coord
        nx = int((x - self.margin_left) / self.side); ny = int((y - self.margin_top) / self.side);
        if nx + 1 > self.size[0] or ny + 1 > self.size[1] or x < self.margin_left or y < self.margin_top:
            return None
        return (nx, ny)

    # отрисовать фигуры на доске при такой раскладке
    def draw(self):
        self.all_sprites, self.sprites_list = pygame.sprite.Group(), []
        # проходимся по клеткам таблицы
        for r in range(self.size[0]):
            for c in range(self.size[1]):
                cell_figure = self.board[r][c]; cell_color = self.board_colors[r][c];
                if cell_figure == 0:
                    continue
                # создаём спрайт определённой фигуры
                sprite = pygame.sprite.Sprite()
                sprite.image = self.figures[cell_figure + cell_color].convert_alpha()
                sprite.rect = sprite.image.get_rect()
                sprite.rect.x = self.margin_left + self.side * c
                sprite.rect.y = self.margin_top + self.side * r
                self.sprites_list.append(sprite); self.all_sprites.add(sprite);
        # отображаем
        self.all_sprites.draw(self.canvas)

    # загрузить изображение (спрайт)
    def load_image(self, name, colorkey=None):
        path = os.path.abspath(name)
        image = pygame.image.load(path)
        return image

    # заново определить позиции короля
    def define_position_kings(self):
        for r in range(self.size[0]):
            for c in range(self.size[1]):
                # получаем фигуру и цвет
                cell_figure = self.board[r][c]; cell_color = self.board_colors[r][c];
                if cell_figure == 'k':
                    self.position_kings[cell_color] = [r, c]

    # определить, есть ли шах королю при этом раскладе
    def detect_king_shah(self, color):
        for r in range(self.size[0]):
            for c in range(self.size[1]):
                # получаем фигуру и цвет
                cell_figure = self.board[r][c]; cell_color = self.board_colors[r][c];
                if cell_color != color and cell_figure != 0:
                    moves = self.define_possible_moves(c, r, shah_detect=True)
                    if self.position_kings[color][::-1] in moves:
                        return True
        return False

    # определить, есть мат при этом раскладе
    def detect_king_mat(self, color):
        shah = self.detect_king_shah(color)
        if not shah:
            return False
        for r in range(self.size[0]):
            for c in range(self.size[1]):
                # получаем фигуру и цвет
                cell_figure = self.board[r][c]; cell_color = self.board_colors[r][c];
                if cell_color == color:
                    moves = self.define_possible_moves(c, r, shah_detect=True)
                    # проходиимся по всем возможным ходам и проверяем, сохраняется ли мат
                    for c_new, r_new in moves:
                        past_figure = self.board[r_new][c_new]; past_color = self.board_colors[r_new][c_new];
                        self.board[r_new][c_new] = self.board[r][c]; self.board[r][c] = 0;
                        self.board_colors[r_new][c_new] = self.board_colors[r][c]; self.board_colors[r][c] = 0;
                        if cell_figure == 'k':
                            self.position_kings[cell_color] = [r_new, c_new]
                        # проверка шах при этой раскладке
                        shah = self.detect_king_shah(color)
                        self.board[r][c] = self.board[r_new][c_new]; self.board[r_new][c_new] = past_figure;
                        self.board_colors[r][c] = self.board_colors[r_new][c_new]; self.board_colors[r_new][c_new] = past_color;
                        if cell_figure == 'k':
                            self.position_kings[cell_color] = [r, c]
                        if not shah:
                            return False
        return True

    # определяем возможные ходы для выбранной фигуры
    def define_possible_moves(self, x, y, shah_detect=False):
        x, y = y, x
        cell_figure = self.board[x][y]; cell_color = self.board_colors[x][y];
        if self.whose_move != cell_color and not shah_detect:
            self.moves = {'iniziator': [x, y], 'moves': []}
            self.scenario_step = 1
            return []
        if cell_figure == 0 and not shah_detect:
            self.scenario_step = 1
            return []
        moves = []
        for r in range(self.size[0]):
            for c in range(self.size[1]):
                # получаем фигуру и цвет
                cell_figure_2 = self.board[r][c]; cell_color_2 = self.board_colors[r][c];
                if cell_color_2 == cell_color:
                    continue
                if cell_figure == 'p':
                    # --------- пешка
                    if cell_color == 'w' and x == 6 and 4 <= r <= 5 and c == y and cell_figure_2 == 0:
                        if r == 5:
                            moves.append([c, r])
                        elif r == 4 and self.board[5][c] == 0:
                            moves.append([c, r])
                    elif cell_color == 'b' and x == 1 and 2 <= r <= 3 and c == y and cell_figure_2 == 0:
                        if r == 2:
                            moves.append([c, r])
                        elif r == 3 and self.board[2][c] == 0:
                            moves.append([c, r])
                    else:
                        if cell_color == 'w' and x - r == 1 and c == y and cell_figure_2 == 0:
                            moves.append([c, r])
                        elif cell_color == 'w' and x - r == 1 and c - y in [-1, 1] and cell_color_2 == 'b':
                            moves.append([c, r])
                        elif cell_color == 'b' and x - r == -1 and c == y and cell_figure_2 == 0:
                            moves.append([c, r])
                        elif cell_color == 'b' and x - r == -1 and c - y in [-1, 1] and cell_color_2 == 'w':
                            moves.append([c, r])
                elif cell_figure == 'r':
                    # --------- ладья
                    if x == r or y == c:
                        t = True
                        if x == r:
                            for c1 in range(min(c, y) + 1, max(c, y)):
                                if self.board[r][c1] != 0:
                                    t = False
                                    break
                        if y == c:
                            for r1 in range(min(r, x) + 1, max(r, x)):
                                if self.board[r1][c] != 0:
                                    t = False
                                    break
                        if t:
                            moves.append([c, r])
                elif cell_figure == 'h':
                    # --------- конь
                    if [abs(x - r), abs(y - c)] in [[1, 2], [2, 1]]:
                        moves.append([c, r])
                elif cell_figure == 'e':
                    # --------- слон
                    if abs(x - r) == abs(y - c):
                        t = True
                        x, y = y, x; r, c = c, r;
                        tx = 1 if x < r else -1; ty = 1 if y < c else -1;
                        for r1 in range(x + tx, r, tx):
                            c1 = y + abs(r1 - x) * ty
                            if self.board[c1][r1] != 0:
                                t = False
                                break
                        x, y = y, x; r, c = c, r;
                        if t:
                            moves.append([c, r])
                elif cell_figure == 'q':
                    # --------- королева
                    if x == r or y == c or abs(x - r) == abs(y - c):
                        t = True
                        if x == r or y == c:
                            if x == r:
                                for c1 in range(min(c, y) + 1, max(c, y)):
                                    if self.board[r][c1] != 0:
                                        t = False
                                        break
                            if y == c:
                                for r1 in range(min(r, x) + 1, max(r, x)):
                                    if self.board[r1][c] != 0:
                                        t = False
                                        break
                        elif abs(x - r) == abs(y - c):
                            t = True
                            x, y = y, x; r, c = c, r;
                            tx = 1 if x < r else -1; ty = 1 if y < c else -1;
                            for r1 in range(x + tx, r, tx):
                                c1 = y + abs(r1 - x) * ty
                                if self.board[c1][r1] != 0:
                                    t = False
                                    break
                            x, y = y, x; r, c = c, r;
                        if t:
                             moves.append([c, r])
                elif cell_figure == 'k':
                    # --------- король
                    if abs(x - r) <= 1 and abs(y - c) <= 1:
                        moves.append([c, r])
        # сохраняем и пишем, что наступил второй шаг
        if not shah_detect:
            self.moves = {'iniziator': [x, y], 'moves': moves}
            self.scenario_step = 2
        return moves

    # нарисовать доступные ходы
    def draw_possible_moves(self, moves):
        for r, c in moves:
            # получаем фигуру и цвет
            cell_figure = self.board[c][r]; cell_color = self.board_colors[c][r];
            # решающее дерево
            if cell_figure == 0:
                color = (40, 195, 194)
            else:
                color = (255, 61, 103)
            rect = pygame.Surface((self.side, self.side), pygame.SRCALPHA)
            rect.fill((*color, 180))
            self.canvas.blit(rect, (self.margin_left + self.side * r, self.margin_top + self.side * c))

    # отобразить мат (текст)
    def display_mat(self, color):
        if color == 'w':
            text_str = 'Белым мат!'
        else:
            text_str = 'Чёрным мат!'
        font = pygame.font.Font(None, 50)
        text = font.render(text_str, True, (100, 255, 100))
        text_x = 400 - text.get_width()//2
        text_y = 400 - text.get_height()//2
        text_w = text.get_width(); text_h = text.get_height();
        pygame.draw.rect(self.canvas, (2, 51, 74), (text_x - 10, text_y - 10, text_w + 20, text_h + 20))
        self.canvas.blit(text, (text_x, text_y))

    # отрисовать кнопки на верхней панели
    def render_setting_buttons(self):
        # 1
        font = pygame.font.Font(None, 20)
        text = font.render('Начать новую партию', True, (0, 0, 0))
        text_x = 10; text_y = 10;
        text_w = text.get_width(); text_h = text.get_height();
        pygame.draw.rect(self.canvas, (189, 189, 189), (0, 0, text_w + 20, text_h + 20))
        self.canvas.blit(text, (text_x, text_y))
        margin_left = text_x - 10 + text_w + 20 + 10;
        # 2
        font = pygame.font.Font(None, 20)
        text = font.render('Сохранить', True, (0, 0, 0))
        text_x2 = 10; text_y2 = 10;
        text_w2 = text.get_width(); text_h2 = text.get_height();
        pygame.draw.rect(self.canvas, (189, 189, 189), (margin_left, 0, text_w2 + 20, text_h2 + 20))
        self.canvas.blit(text, (margin_left + text_x2, text_y2))
        margin_left2 = margin_left + text_x2 - 10 + text_w2 + 20 + 10;
        # 3
        font = pygame.font.Font(None, 20)
        text = font.render('Открыть сохранённый', True, (0, 0, 0))
        text_x3 = 10; text_y3 = 10;
        text_w3 = text.get_width(); text_h3 = text.get_height();
        pygame.draw.rect(self.canvas, (189, 189, 189), (margin_left2, 0, text_w3 + 20, text_h3 + 20))
        self.canvas.blit(text, (margin_left2 + text_x3, text_y3))
        margin_left3 = margin_left2 + text_x2 - 10 + text_w2 + 20;
        # save
        self.top_buttons = [[0, 0, text_w + 20, text_h + 20], [margin_left, 0, margin_left + text_w2 + 20, text_h2 + 20], [margin_left2, 0, margin_left2 + text_w3 + 20, text_h3 + 20]]

    # сохранить партию
    def save_partie(self, agregator):
        number = agregator['number_partie']
        agregator['saved'][number] = {'board': self.board,
                                      'board_colors': self.board_colors,
                                      'whose_move': self.whose_move,
                                      'position_kings': self.position_kings}
        agregator['number_partie'] += 1
        return agregator

    # нарисовать открывающееся окошко при клике на кнопку
    def open_window_saved(self, agregator):
        self.window_opened = True
        margin_top = self.top_buttons[2][3]
        for number in agregator['saved']:
            font = pygame.font.Font(None, 20)
            text = font.render(f'Партия {number}', True, (0, 0, 0))
            pygame.draw.rect(self.canvas, (230, 230, 230), (self.top_buttons[2][0], margin_top + self.top_buttons[2][1], self.top_buttons[2][2] - self.top_buttons[2][0], self.top_buttons[2][3] - self.top_buttons[2][1]))
            self.canvas.blit(text, (self.top_buttons[2][0] + 10, margin_top + self.top_buttons[2][1] + 10))
            margin_top += self.top_buttons[2][3]

    # начать новую партию
    def start_new_parti(self):
        self.whose_move = 'w'
        self.scenario_step = 1
        self.is_mat_end_game = False
        self.board = [['r', 'h', 'e', 'q', 'k', 'e', 'h', 'r'],
                      ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0],
                      ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
                      ['r', 'h', 'e', 'q', 'k', 'e', 'h', 'r']]
        self.board_colors = [['b', 'b', 'b', 'b', 'b', 'b', 'b', 'b'],
                             ['b', 'b', 'b', 'b', 'b', 'b', 'b', 'b'],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             ['w', 'w', 'w', 'w', 'w', 'w', 'w', 'w'],
                             ['w', 'w', 'w', 'w', 'w', 'w', 'w', 'w']]
        self.position_kings = {'b': [0, 4], 'w': [7, 4]}
        self.moves = []

    # сменить партию, на сохранённую
    def change_partie(self, number, agregator):
        i = 0
        for index in agregator['saved']:
            i += 1
            if i == int(number):
                partie = agregator['saved'][index]
                break
        # переделываем партию
        self.whose_move = partie['whose_move']
        self.scenario_step = 1
        self.is_mat_end_game = False
        self.board = partie['board']
        self.board_colors = partie['board_colors']
        self.moves = []


class Game:
    # функция инициализации
    def __init__(self):
        # основные настройки размера
        size = (800, 800)
        self.w, self.h = size
        self.center = (self.w // 2, self.h // 2)
        # начинаем инициализацию
        pygame.init()
        pygame.display.set_caption('Chess game')
        self.canvas = pygame.display.set_mode(size)
        # background
        self.background = pygame.image.load("static/board.png")
        self.background = pygame.transform.scale(self.background, (800, 800))
        self.clear()
        # внутреигровые часы
        self.clock = pygame.time.Clock()
        self.rendering = True
        # открываем базу
        self.agregator = json.loads(open('db/agregator.json', 'r').read())
        # render
        threading.Thread(target = self.render(), args = ()).start()

    # функция начальной отрисовки
    def render(self):
        # initial rendering
        self.play_game = False
        self.fps = 60
        # создаём класс поля
        self.board = Board(self.canvas, size = (37, 41, 91), rc = (8, 8))
        self.board.draw()
        self.board.render_setting_buttons()
        pygame.display.flip()
        # start track events
        self.events()
        # quit game
        pygame.quit()

    # функция событий
    def events(self):
        while self.rendering:
            re_draw = False
            # цикл из событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.rendering = False
                # если произошёл клик
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.play_game:
                    X, Y = event.pos
                    gloar = False
                    # первая кнопка
                    if self.board.top_buttons[0][0] <= X <= self.board.top_buttons[0][2] and self.board.top_buttons[0][1] <= Y <= self.board.top_buttons[0][3]:
                        # начинаем новую партию
                        self.clear()
                        self.board.start_new_parti()
                        self.board.draw()
                        re_draw = True
                        continue
                    elif self.board.top_buttons[1][0] <= X <= self.board.top_buttons[1][2] and self.board.top_buttons[1][1] <= Y <= self.board.top_buttons[1][3]:
                        # сохраняем партию в базу
                        if self.board.is_mat_end_game:
                            # ничего не сохраняем, так как партия уже кончилась
                            pass
                        else:
                            self.agregator = self.board.save_partie(self.agregator)
                            self.save_agregator()
                            continue
                    # если нажали на вторую кнопку
                    elif self.board.top_buttons[2][0] <= X <= self.board.top_buttons[2][2] and self.board.top_buttons[2][1] <= Y <= self.board.top_buttons[2][3]:
                        self.board.draw()
                        self.board.open_window_saved(self.agregator)
                        re_draw = True
                        gloar = True
                    # если нажали на третью кнопку
                    elif self.board.window_opened and self.board.top_buttons[2][0] <= X <= self.board.top_buttons[2][2]:
                        number = int(Y / self.board.top_buttons[2][3])
                        # ищем номер нажатой кнопки
                        if len(self.agregator['saved']) >= number and number != 0:
                            self.board.change_partie(number, self.agregator)
                            self.board.window_opened = False
                        else:
                            self.board.window_opened = False
                    if not gloar:
                        self.board.window_opened = False
                    if self.board.is_mat_end_game:
                        continue
                    coord = self.board.get_cell(event.pos)
                    if coord is None:
                        continue
                    X, Y = coord
                    if self.board.scenario_step == 2:
                        # либо ходим, либо обратно меняем шаг на первый
                        if [X, Y] in self.board.moves['moves']:
                            Y, X = X, Y
                            # ищем фигуру инициатор
                            iniziator = self.board.moves['iniziator']
                            cell_figure = self.board.board[iniziator[0]][iniziator[1]]
                            self.board.board[X][Y] = self.board.board[iniziator[0]][iniziator[1]]
                            self.board.board[iniziator[0]][iniziator[1]] = 0
                            self.board.board_colors[X][Y] = self.board.board_colors[iniziator[0]][iniziator[1]]
                            self.board.board_colors[iniziator[0]][iniziator[1]] = 0
                            self.board.scenario_step = 1
                            if self.board.whose_move == 'w':
                                self.board.whose_move = 'b'
                            else:
                                self.board.whose_move = 'w'
                            if cell_figure == 'k':
                                self.board.define_position_kings()
                            self.clear()
                            self.board.draw()
                            mat = self.board.detect_king_mat(self.board.whose_move)
                            # прекращаем игру если наступил мат
                            if mat:
                                self.board.is_mat_end_game = True
                                self.board.display_mat(self.board.whose_move)
                            # и обновляем
                            re_draw = True
                            continue
                    moves = self.board.define_possible_moves(X, Y)
                    # очищаем и дорисовываем
                    self.clear()
                    self.board.draw_possible_moves(moves)
                    self.board.draw()
                    re_draw = True
            if re_draw:
                # если заново отрисовать
                self.board.render_setting_buttons()
                pygame.display.flip()

    def clear(self):
        # очистить экран, для новой отрисовки
        self.canvas.blit(self.background, (0, 0))

    def save_agregator(self):
        # сохранить базу данных (переделанную)
        str_agregator = json.dumps(self.agregator)
        open('db/agregator.json', 'w').write(str_agregator)


game = Game()

# end.
