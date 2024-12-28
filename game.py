import os
import pygame
import sys
import math
import time

# 初始化颜色常量
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRID_COLOR = (230, 230, 230)


class SoundManager:
    def __init__(self):
        # 初始化混音器，设置合适的参数支持ogg格式
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()

        # 设置音量
        self.sfx_volume = 0.5  # 音效音量
        self.bgm_volume = 1  # 背景音乐音量

        # 加载音效
        self.sounds = {
            'shoot': pygame.mixer.Sound('sounds/player/shoot.wav'),
            'explode': pygame.mixer.Sound('sounds/player/explode.wav')
        }

        # 设置音效音量
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)

        # 背景音乐路径 (.ogg格式)
        self.bgm = {
            'background': 'sounds/bgm/bg.ogg',
            'victory': 'sounds/bgm/victory.ogg',
            'lose': 'sounds/bgm/lose.ogg'
        }

        # 当前播放的背景音乐
        self.current_bgm = None

    def play_sound(self, sound_name):
        """播放音效"""
        if sound_name in self.sounds:
            channel = self.sounds[sound_name].play()
            if channel:  # 如果成功获取到播放通道
                channel.set_volume(self.sfx_volume)

    def play_bgm(self, bgm_name, loop=-1):
        """播放背景音乐"""
        try:
            if bgm_name in self.bgm:
                # 如果当前正在播放的是同一个音乐，则不重新加载
                if self.current_bgm != bgm_name:
                    # 先停止当前播放的音乐
                    pygame.mixer.music.stop()
                    # 加载并播放新的音乐
                    pygame.mixer.music.load(self.bgm[bgm_name])
                    pygame.mixer.music.set_volume(self.bgm_volume)
                    pygame.mixer.music.play(loop)
                    self.current_bgm = bgm_name
        except pygame.error as e:
            print(f"无法播放背景音乐 {bgm_name}: {e}")

    def stop_bgm(self):
        """停止背景音乐"""
        pygame.mixer.music.stop()
        self.current_bgm = None

    def fade_out_bgm(self, time_ms=500):
        """淡出背景音乐"""
        pygame.mixer.music.fadeout(time_ms)
        self.current_bgm = None

    def set_bgm_volume(self, volume):
        """设置背景音乐音量"""
        self.bgm_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.bgm_volume)

    def set_sfx_volume(self, volume):
        """设置音效音量"""
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)
class Game: #基础类
    def __init__(self):
        pygame.init()
        # 设置更大的游戏窗口
        self.WIDTH = 1200
        self.HEIGHT = 800
        self.GRID_SIZE = 40  # 网格大小
        # self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("X的逆袭")
        self.clock = pygame.time.Clock()
        self.enemy = None
        self.level_complete = False
        # self.player.health = 100
        self.score = 0
        self.collision_particles = []
        # 字体
        self.font_path_CH = os.path.join("fonts", "FZLTHJW.TTF")  # 使用os.path.join确保跨平台兼容
        self.font_path_EN = os.path.join("fonts", "HuaweiSans-Regular.ttf")
        self.player = Player(self.WIDTH // 2, self.HEIGHT - 100, self)
        # 初始化移动偏移量
        self.offset_x = 0
        self.offset_y = 0
        # 倒计时
        self.transition_timer = None
        self.transition_start_time = None
        self.transition_duration = 5  # 5秒倒计时

        # 移动速度 (像素/秒)
        self.MOVE_SPEED = 15  # 较小的值使移动更缓慢

        # 颜色定义
        self.BLACK = (0, 0, 0)
        self.GRID_COLOR = (200, 200, 200)  # 浅灰色网格
        # 游戏状态
        self.running = True
        self.current_level = 1
        
        # 缩放和网格设置
        self.GRID_SIZE = 25  # 每个网格的大小（像素）
        self.AXIS_UNIT = 50  # 每个单位长度（像素）
        # 道具功能
        self.power_up = None
        self.power_up_timer = 0
        self.spiral_mode_timer = 0
        self.spiral_mode = False

        # 菜单
        self.game_state = "START"  # 可能的状态: "START", "PLAYING", "END"
        # 加载必要的图片
        self.title_image = pygame.image.load("images/x的逆袭.png").convert_alpha()
        self.start_no = pygame.image.load("images/start_no.png").convert_alpha()
        self.start_yes = pygame.image.load("images/start_yes.png").convert_alpha()
        self.exit_no = pygame.image.load("images/exit_no.png").convert_alpha()
        self.exit_yes = pygame.image.load("images/exit_yes.png").convert_alpha()
        self.restart_no = pygame.image.load("images/restart_no.png").convert_alpha()
        self.restart_yes = pygame.image.load("images/restart_yes.png").convert_alpha()

        # 设置按钮位置
        self.title_rect = self.title_image.get_rect(center=(self.WIDTH // 2, 150))
        self.start_rect = self.start_no.get_rect(center=(self.WIDTH // 2, 400))
        self.exit_rect = self.exit_no.get_rect(center=(self.WIDTH // 2, 500))
        self.restart_rect = self.restart_no.get_rect(center=(self.WIDTH // 2, 450))
        # 添加音效管理器
        self.sound_manager = SoundManager()
        # 开始播放背景音乐
        self.sound_manager.play_bgm('background', -1)  # -1表示循环播放

        # 初始化游戏对象
        self.init_game()

    def reset_game(self):
        """重置游戏状态"""
        self.current_level = 1
        self.score = 0
        self.player.health = 100
        self.enemy = None
        self.level_complete = False
        self.transition_timer = None
        self.game_state = "PLAYING"
        # 重新播放背景音乐
        self.sound_manager.fade_out_bgm(500)
        pygame.time.wait(500)  # 等待淡出完成
        self.sound_manager.play_bgm('background', -1)

    def start_level_transition(self):

        """开始关卡转换"""
        self.transition_timer = self.transition_duration
        self.transition_start_time = time.time()
        self.level_complete = True
        self.current_level += 1  # 在这里增加关卡数

    def start_level(self):

        """开始新关卡"""
        self.enemy = Enemy(self, self.current_level)
        self.level_complete = False

    def game_win(self):
        """游戏胜利处理"""
        self.game_state = "END"
        # 不要立即退出游戏
        # self.running = False
        self.sound_manager.fade_out_bgm(500)
        pygame.time.wait(500)  # 等待淡出完成
        self.sound_manager.play_bgm('victory', 0)  # 播放一次 # 播放一次
        print("Congratulations! You've completed all levels!")
    def init_game(self):
        # 计算坐标系原点（屏幕中心）
        self.origin_x = self.WIDTH // 2
        self.origin_y = self.HEIGHT // 2


    def check_collisions(self):
        if not self.enemy:
            return

        # 1. 检测玩家子弹与敌机的碰撞
        for bullet in self.player.bullets[:]:
            if self.check_bullet_enemy_collision(bullet, self.enemy):
                self.enemy.health -= 1
                self.player.bullets.remove(bullet)
                self.score += 100
                self.create_collision_effect(bullet.x, bullet.y)

        # 2. 检测敌机子弹与玩家的碰撞
        for bullet in self.enemy.bullets[:]:
            if self.check_bullet_player_collision(bullet):
                self.player.health -= 10
                self.enemy.bullets.remove(bullet)
                self.create_collision_effect(bullet.x, bullet.y)

        # 3. 检测玩家子弹与敌机子弹的碰撞
        for p_bullet in self.player.bullets[:]:
            for e_bullet in self.enemy.bullets[:]:
                if self.check_bullets_collision(p_bullet, e_bullet):
                    if p_bullet in self.player.bullets:
                        self.player.bullets.remove(p_bullet)
                    if e_bullet in self.enemy.bullets:
                        self.enemy.bullets.remove(e_bullet)
                    self.score += 10  # 奖励积分
                    self.create_collision_effect(p_bullet.x, p_bullet.y)
                    break

    def check_bullet_enemy_collision(self, bullet, enemy):
        # 简单的矩形碰撞检测
        bullet_rect = pygame.Rect(bullet.x - bullet.radius,
                                  bullet.y - bullet.radius,
                                  bullet.radius * 2,
                                  bullet.radius * 2)
        enemy_rect = pygame.Rect(enemy.x - enemy.width // 2,
                                 enemy.y - enemy.height // 2,
                                 enemy.width,
                                 enemy.height)
        return bullet_rect.colliderect(enemy_rect)

    def check_bullet_player_collision(self, bullet):
        bullet_rect = pygame.Rect(bullet.x - bullet.radius,
                                  bullet.y - bullet.radius,
                                  bullet.radius * 2,
                                  bullet.radius * 2)
        player_rect = pygame.Rect(self.player.x - self.player.width // 2,
                                  self.player.y - self.player.height // 2,
                                  self.player.width,
                                  self.player.height)
        return bullet_rect.colliderect(player_rect)

    def check_bullets_collision(self, bullet1, bullet2):
        # 使用圆形碰撞检测，更适合子弹
        distance = math.sqrt((bullet1.x - bullet2.x) ** 2 +
                             (bullet1.y - bullet2.y) ** 2)
        return distance < (bullet1.radius + bullet2.radius)

    def create_collision_effect(self, x, y):
        # 创建简单的碰撞粒子效果
        for _ in range(5):
            speed = random.uniform(2, 5)
            angle = random.uniform(0, math.pi * 2)
            self.collision_particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': 20  # 粒子持续帧数
            })

    def update_collision_effects(self):
        # 更新碰撞粒子效果
        for particle in self.collision_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['lifetime'] -= 1
            if particle['lifetime'] <= 0:
                self.collision_particles.remove(particle)


    def draw_collision_effects(self):
        # 绘制碰撞粒子效果
        for particle in self.collision_particles:
            alpha = int(255 * (particle['lifetime'] / 20))
            color = (0, 0, 0, alpha)  # 修改为黑色粒子
            pygame.draw.circle(self.screen, color,
                               (int(particle['x']), int(particle['y'])), 2)

    def draw_game_status(self):
        # 绘制游戏状态（生命值和分数）
        font = pygame.font.Font(self.font_path_EN, 36)
        # 生命值
        health_text = f"Health: {self.player.health}"
        health_surface = font.render(health_text, True, BLACK)
        self.screen.blit(health_surface, (10, 70))
        # 分数
        score_text = f"Score: {self.score}"
        score_surface = font.render(score_text, True, BLACK)
        self.screen.blit(score_surface, (10, 100))

    def screen_to_game_coords(self, screen_x, screen_y):
        """将屏幕坐标转换为游戏坐标"""
        game_x = (screen_x - self.origin_x) / self.AXIS_UNIT
        game_y = -(screen_y - self.origin_y) / self.AXIS_UNIT
        return game_x, game_y
    
    def game_to_screen_coords(self, game_x, game_y):
        """将游戏坐标转换为屏幕坐标"""
        screen_x = self.origin_x + game_x * self.AXIS_UNIT
        screen_y = self.origin_y - game_y * self.AXIS_UNIT
        return screen_x, screen_y
    
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif self.game_state == "START":
                # 开始界面的事件处理
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.start_rect.collidepoint(mouse_pos):
                        self.game_state = "PLAYING"
                    elif self.exit_rect.collidepoint(mouse_pos):
                        self.running = False

            elif self.game_state == "PLAYING":
                # 游戏进行中的事件处理
                if event.type == pygame.MOUSEMOTION:
                    self.player.x = max(50, min(mouse_pos[0], self.WIDTH - 50))
                    self.player.y = max(50, min(mouse_pos[1], self.HEIGHT - 50))
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.player.shoot()

            elif self.game_state == "END":
                # 结束界面的事件处理
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.restart_rect.collidepoint(mouse_pos):
                        self.reset_game()




    def draw_start_screen(self):
        """绘制开始界面"""
        self.screen.fill(WHITE)
        # 绘制静态网格
        for x in range(0, self.WIDTH + self.GRID_SIZE, self.GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, self.HEIGHT))
        for y in range(0, self.HEIGHT + self.GRID_SIZE, self.GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (self.WIDTH, y))

        # 绘制标题和按钮
        self.screen.blit(self.title_image, self.title_rect)

        # 检查鼠标悬停状态
        mouse_pos = pygame.mouse.get_pos()
        if self.start_rect.collidepoint(mouse_pos):
            self.screen.blit(self.start_yes, self.start_rect)
        else:
            self.screen.blit(self.start_no, self.start_rect)

        if self.exit_rect.collidepoint(mouse_pos):
            self.screen.blit(self.exit_yes, self.exit_rect)
        else:
            self.screen.blit(self.exit_no, self.exit_rect)


    def draw_end_screen(self):
        """绘制结束界面"""
        # 保持背景和网格
        self.screen.fill(WHITE)
        # 绘制静态网格
        for x in range(0, self.WIDTH + self.GRID_SIZE, self.GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, self.HEIGHT))
        for y in range(0, self.HEIGHT + self.GRID_SIZE, self.GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (self.WIDTH, y))

        # 根据游戏结果显示不同的标题和描述
        title_font = pygame.font.Font(self.font_path_CH, 74)
        desc_font = pygame.font.Font(self.font_path_CH, 36)

        if self.player.health <= 0:
            # 失败情况
            title_text = "游戏结束"
            title_color = (255, 0, 0)  # 红色
            desc_text = "很遗憾，你的飞船被击毁了"
        else:
            # 胜利情况
            title_text = "胜利！"
            title_color = (0, 128, 0)  # 绿色
            desc_text = "恭喜你成功通过了所有关卡！"

        # 绘制标题
        title_surface = title_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(self.WIDTH // 2, 200))

        # 绘制描述
        desc_surface = desc_font.render(desc_text, True, BLACK)
        desc_rect = desc_surface.get_rect(center=(self.WIDTH // 2, 300))

        # 显示最终分数
        score_font = pygame.font.Font(self.font_path_CH, 48)
        score_text = f"最终得分: {self.score}"
        score_surface = score_font.render(score_text, True, BLACK)
        score_rect = score_surface.get_rect(center=(self.WIDTH // 2, 400))

        # 添加游戏统计信息
        stats_font = pygame.font.Font(self.font_path_CH, 28)
        stats_texts = [
            f"已通过关卡数: {self.current_level}",
            f"剩余生命值: {max(0, self.player.health)}%"
        ]

        # 绘制所有元素
        self.screen.blit(title_surface, title_rect)
        self.screen.blit(desc_surface, desc_rect)
        self.screen.blit(score_surface, score_rect)

        # 绘制统计信息
        for i, text in enumerate(stats_texts):
            stats_surface = stats_font.render(text, True, BLACK)
            stats_rect = stats_surface.get_rect(
                center=(self.WIDTH // 2, 500 + i * 40)
            )
            self.screen.blit(stats_surface, stats_rect)

        # 绘制重新开始按钮
        mouse_pos = pygame.mouse.get_pos()
        if self.restart_rect.collidepoint(mouse_pos):
            self.screen.blit(self.restart_yes, self.restart_rect)
        else:
            self.screen.blit(self.restart_no, self.restart_rect)


    def update(self):
        if self.game_state == "PLAYING":
            self.player.update()
            self.check_collisions()
            self.update_collision_effects()

            self.spawn_power_up()
            self.check_power_up_collision()

            # 更新涡旋模式状态
            if self.spiral_mode and time.time() - self.spiral_mode_timer > 10:
                self.spiral_mode = False

            if self.power_up:
                self.power_up.update()

            # 检查游戏结束条件
            if self.player.health <= 0:
                self.game_over()

            # 处理关卡转换
            if self.transition_timer is not None:
                current_time = time.time()
                elapsed_time = current_time - self.transition_start_time
                self.transition_timer = self.transition_duration - int(elapsed_time)

                # 当倒计时结束
                if self.transition_timer <= 0:
                    self.transition_timer = None
                    self.level_complete = False  # 重置关卡完成状态
                    self.start_level()
            # 正常游戏更新
            elif self.enemy:
                self.enemy.update()
                # 检查关卡完成
                if self.enemy.health <= 0:
                    self.sound_manager.play_sound('explode')
                    self.enemy = None
                    if self.current_level < 5:  # 如果还没到最后一关
                        self.level_complete = True  # 设置关卡完成状态
                        self.start_level_transition()  # 开始关卡转换
                    else:
                        self.game_win()  # 游戏胜利
            elif not self.level_complete:  # 如果不在关卡完成状态，才开始新关卡
                self.start_level()

    def draw_grid(self, dt):
        # 更新偏移量
        self.offset_x = (self.offset_x + self.MOVE_SPEED * dt) % self.GRID_SIZE
        self.offset_y = (self.offset_y + self.MOVE_SPEED * dt) % self.GRID_SIZE

        # 绘制垂直线
        # 多绘制一条线确保移动时边缘平滑
        for x in range(-self.GRID_SIZE + int(self.offset_x), self.WIDTH + self.GRID_SIZE, self.GRID_SIZE):
            # color = self.BLACK if abs(x - self.origin_x) < 2 else self.GRID_COLOR
            # width = 2 if abs(x - self.origin_x) < 2 else 1
            # pygame.draw.line(self.screen, color, (x, 0), (x, self.HEIGHT), width)
            pygame.draw.line(self.screen, self.GRID_COLOR, (x, 0), (x, self.HEIGHT), 1)

        # 绘制水平线
        # 多绘制一条线确保移动时边缘平滑
        for y in range(-self.GRID_SIZE + int(self.offset_y), self.HEIGHT + self.GRID_SIZE, self.GRID_SIZE):
            # color = self.BLACK if abs(y - self.origin_y) < 2 else self.GRID_COLOR
            # width = 2 if abs(y - self.origin_y) < 2 else 1
            pygame.draw.line(self.screen, self.GRID_COLOR, (0, y), (self.WIDTH, y), 1)

    def draw(self):
        # 清空屏幕
        if self.game_state == "START":
            self.draw_start_screen()
        elif self.game_state == "PLAYING":
            self.screen.fill(WHITE)
        # 绘制网格
        # self.draw_grid()
        #dt = pygame.time.Clock().tick(144) / 1000.0
            dt = pygame.time.Clock().tick(60) / 1000.0

        # 清空屏幕
            self.screen.fill((255, 255, 255))  # 白色背景

        # 绘制移动的网格
            self.draw_grid(dt)

            if self.power_up:
                self.power_up.draw(self.screen)

            # 显示涡旋模式剩余时间
            if self.spiral_mode:

                time_left = int(10 - (time.time() - self.spiral_mode_timer))
                font = pygame.font.Font(self.font_path_EN, 36)
                text = font.render(f"Spiral Mode: {time_left}s", True, (0, 0, 255))
                self.screen.blit(text, (10, 130))
        
        # 绘制玩家
            self.player.draw(self.screen)
            font = pygame.font.Font(self.font_path_CH, 36)

        # 显示玩家坐标
            game_x, game_y = self.screen_to_game_coords(self.player.x, self.player.y)
            coords_text = f"坐标: ({game_x:.1f}, {game_y:.1f})"
            text_surface = font.render(coords_text, True, BLACK)
            self.screen.blit(text_surface, (10, 10))

            if self.enemy:
                self.enemy.draw(self.screen)

            # 显示关卡信息
            font = pygame.font.Font(self.font_path_EN, 36)
            level_text = f"Level {self.current_level}"
            text_surface = font.render(level_text, True, BLACK)
            self.screen.blit(text_surface, (10, 40))
            self.draw_collision_effects()
            self.draw_game_status()

        # 如果在关卡转换中，绘制倒计时
            if self.transition_timer is not None:
                font = pygame.font.Font(self.font_path_CH, 74)  # 使用更大的字体
                text = f"还有{self.transition_timer}秒进入第{self.current_level}关"
                text_surface = font.render(text, True, (0, 0, 0))

                # 计算文本位置（屏幕上方居中）
                text_rect = text_surface.get_rect(center=(self.WIDTH // 2, 100))

                # 添加文本背景
                padding = 20
                background_rect = text_rect.inflate(padding * 2, padding * 2)
                pygame.draw.rect(self.screen, (255, 255, 255), background_rect)
                pygame.draw.rect(self.screen, (0, 0, 0), background_rect, 2)

                # 绘制文本
                self.screen.blit(text_surface, text_rect)
            # 刷新屏幕
            # pygame.display.flip()

        elif self.game_state == "END":
            self.draw_end_screen()


        pygame.display.flip()

    def game_over(self):
        """游戏结束处理"""
        self.game_state = "END"
    # 不要立即退出游戏
    # self.running = False
        self.sound_manager.fade_out_bgm(500)
        pygame.time.wait(500)  # 等待淡出完成
        self.sound_manager.play_bgm('lose', 0)  # 播放一次)  # 播放一次
        print(f"Game Over! Final Score: {self.score}")
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            # self.clock.tick(144)
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

    def spawn_power_up(self):
        if self.power_up is None and time.time() - self.power_up_timer > 20:
            # 随机选择道具类型和位置
            power_up_type = random.choice(['health', 'spiral'])
            x = random.randint(100, self.WIDTH - 100)
            y = random.randint(100, self.HEIGHT - 100)
            self.power_up = PowerUp(x, y, power_up_type)

    def check_power_up_collision(self):
        if self.power_up is None:
            return

        # 检查玩家是否接触到道具
        player_rect = pygame.Rect(self.player.x - self.player.width // 2,
                                  self.player.y - self.player.height // 2,
                                  self.player.width,
                                  self.player.height)
        power_up_rect = pygame.Rect(self.power_up.x - self.power_up.width // 2,
                                    self.power_up.y - self.power_up.height // 2,
                                    self.power_up.width,
                                    self.power_up.height)

        if player_rect.colliderect(power_up_rect):
            if self.power_up.type == 'health':
                self.player.health = min(100, self.player.health + 30)  # 恢复30点生命值
                self.create_heal_effect()
            else:  # spiral
                self.spiral_mode = True
                self.spiral_mode_timer = time.time()

            self.power_up = None
            self.power_up_timer = time.time()

    def create_heal_effect(self):
        # 创建治疗特效
        for _ in range(10):
            speed = random.uniform(2, 5)
            angle = random.uniform(0, math.pi * 2)
            self.collision_particles.append({
                'x': self.player.x,
                'y': self.player.y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'lifetime': 20,
                'color': (0, 255, 0)  # 绿色粒子表示治疗
            })
class Player:
    def __init__(self, x, y, game):  # 添加game参数
        self.x = x
        self.y = y
        # self.width = 20
        # self.height = 20
        self.bullets = []
        self.speed = 5
        self.game = game  # 保存game实例的引用
        self.health = 100
        # 加载玩家贴图
        self.image = pygame.image.load('images/x.png').convert_alpha()
        self.width = 40
        self.height = 40
        self.image = pygame.transform.scale(self.image, (self.width, self.height))
        # 获取贴图矩形
        self.rect = self.image.get_rect()

    def shoot(self):
        if self.game.spiral_mode:
            # 减少同时发射的涡旋数量，但增加发射频率
            bullet = SpiralBullet(self.x, self.y)
            self.bullets.append(bullet)
        else:
            # 原有的直线子弹
            bullet = Bullet(self.x, self.y)
            self.bullets.append(bullet)
        # 播放射击音效
        self.game.sound_manager.play_sound('shoot')
    
    def update(self):
        # 更新所有子弹
        for bullet in self.bullets:
            bullet.update()

    def draw(self, screen):
        # 更新贴图位置
        self.rect.center = (self.x, self.y)
        # 绘制玩家贴图
        screen.blit(self.image, self.rect)

        # 绘制子弹
        for bullet in self.bullets:
            bullet.draw(screen)

class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True
        self.radius = 3  # 保留用于碰撞检测
        self.image = pygame.image.load("images/bullet0.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (20, 20))
        self.speed = 6

    
    def update(self):
        # 直线运动 (y = x)
        self.y -= self.speed
        self.x += self.speed / 2
    
    def draw(self, screen):

        # 使用图片中心点对齐子弹位置
        image_rect = self.image.get_rect()
        image_rect.center = (int(self.x), int(self.y))
        screen.blit(self.image, image_rect)


# 添加到现有代码中的新类和修改

import random
import numpy as np

class Enemy:
    def __init__(self, game, level):
        self.image = None
        if level == 1:
            self.image = pygame.image.load("images/x^2.png").convert_alpha()
        if level == 2:
            self.image = pygame.image.load("images/sinx.png").convert_alpha()
        if level == 3:
            self.image = pygame.image.load("images/absx.png").convert_alpha()
        if level == 4:
            self.image = pygame.image.load("images/logx.png").convert_alpha()
        if level == 5:
            self.image = pygame.image.load("images/e^x.png").convert_alpha()

        self.game = game
        self.level = level
        self.width = 30
        self.height = 30
        # self.health = 3
        # 基于关卡的血量计算
        self.max_health = 3 * (2 ** (level - 1))  # 3, 6, 12, 24, 48
        self.health = self.max_health

        self.bullets = []
        self.time = 0  # 用于控制移动轨迹

        # 基于关卡的射击冷却时间调整
        self.shoot_delay = max(60 - (level * 8), 20)  # 60, 52, 44, 36, 28
        self.shoot_cooldown = 0  # 射击冷却时间
        self.shoot_delay = 60  # 射击间隔（帧数）

        # 初始位置（从顶部中央出现）
        # self.x = game.WIDTH // 2
        # self.y = 50
        self.x = game.WIDTH // 2
        self.y = game.HEIGHT // 4

        # self.base_speed = 0.02 * (1 + (level - 1) * 0.2)  # 增加20%的基础速度
        # 运动相关的初始化参数
        self.base_speed = 0.02 * (1 + (level - 1) * 0.2)
        self.movement_phase = 0  # 用于复杂移动模式
        # self.target_x = self.x  # 用于第四关的目标位置
        # self.target_y = self.y
        # 为第四关添加特殊的初始化参数
        self.target_x = game.WIDTH // 2
        self.target_y = game.HEIGHT // 4
        self.move_timer = 0
        self.target_change_delay = 60  # 每60帧更新一次目标
        self.min_move_distance = 50  # 最小移动距离
        self.movement_speed = 4  # 基础移动速度

        # 定义活动范围（从顶部到中间偏下的区域）
        self.move_bounds = {
            'x_min': 100,
            'x_max': game.WIDTH - 100,
            'y_min': 100,
            'y_max': game.HEIGHT * 0.6  # 限制在画布60%的高度内
        }
        # 射击相关参数
        self.shoot_delay = max(30 - (level * 4), 10)  # 提高射击频率
        self.shoot_cooldown = 0
        self.bullet_patterns = {
            1: self.shoot_quadratic,  # y = x²
            2: self.shoot_sine,  # y = sin(x)
            3: self.shoot_absolute,  # y = |x|
            4: self.shoot_logarithmic,  # y = log(x)
            5: self.shoot_exponential  # y = eˣ
        }

        # 子弹图案参数
        self.pattern_width = 400  # 函数图像的宽度范围
        self.pattern_points = 20  # 每次发射的点数

    def move(self):
        # self.time += 0.02
        self.time += self.base_speed
        if self.level == 4:
            self.move_timer += 1
            # 定期更新目标位置
            if self.move_timer >= self.target_change_delay:
                self.move_timer = 0
                # 获取当前位置到新目标的最小距离
                while True:
                    new_target_x = random.randint(
                        int(self.move_bounds['x_min']),
                        int(self.move_bounds['x_max'])
                    )
                    new_target_y = random.randint(
                        int(self.move_bounds['y_min']),
                        int(self.move_bounds['y_max'])
                    )

                    # 计算到新目标的距离
                    distance_to_new = math.sqrt(
                        (new_target_x - self.x) ** 2 +
                        (new_target_y - self.y) ** 2
                    )

                    # 确保新目标至少在最小移动距离之外
                    if distance_to_new >= self.min_move_distance:
                        self.target_x = new_target_x
                        self.target_y = new_target_y
                        break
            # 计算到目标的方向向量
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.sqrt(dx * dx + dy * dy)

            # 平滑移动
            if distance > 0:
                # 使用easing function使移动更自然
                move_factor = min(1, self.movement_speed / distance)

                self.x += dx * move_factor
                self.y += dy * move_factor

                # 添加轻微的正弦波动，使移动更自然
                self.x += math.sin(self.time * 2) * 0.5
                self.y += math.cos(self.time * 2) * 0.5

        elif self.level == 1:
            # 第一关：简单的左右移动，但幅度更大
            self.x = self.game.WIDTH // 2 + math.sin(self.time) * (self.game.WIDTH // 3)
            self.y = self.game.HEIGHT // 4 + math.sin(self.time * 2) * 50  # 添加轻微的上下移动

        elif self.level == 2:
            # 第二关：以画布中心为圆心的大圆形轨迹，添加螺旋变化
            center_x = self.game.WIDTH // 2
            center_y = self.game.HEIGHT // 2
            radius = 300 + math.sin(self.time * 0.5) * 50  # 半径在300-350之间变化
            self.x = center_x + math.cos(self.time) * radius
            self.y = center_y + math.sin(self.time) * radius * 0.6  # 椭圆轨迹，考虑屏幕比例

        elif self.level == 3:
            # 第三关：复杂的8字形 + 波浪组合轨迹
            base_x = self.game.WIDTH // 2
            base_y = self.game.HEIGHT // 3

            # 大范围的8字形
            figure8_x = math.sin(2 * self.time) * (self.game.WIDTH // 2.5)
            figure8_y = math.sin(self.time) * (self.game.HEIGHT // 3)

            # 添加波浪调制
            wave_x = math.sin(self.time * 3) * 50
            wave_y = math.cos(self.time * 2) * 30

            self.x = base_x + figure8_x + wave_x
            self.y = base_y + figure8_y + wave_y



        elif self.level == 5:
            # 第五关：复杂的多重螺旋 + 跳跃移动
            # 基础螺旋
            spiral_radius = 300 * (1 - 0.5 * math.exp(-0.1 * self.time))
            spiral_x = math.cos(self.time * 2) * spiral_radius
            spiral_y = math.sin(self.time * 2) * spiral_radius * 0.7

            # 螺旋中心点的移动
            center_x = self.game.WIDTH // 2 + math.sin(self.time * 0.5) * (self.game.WIDTH // 4)
            center_y = self.game.HEIGHT // 3 + math.cos(self.time * 0.3) * (self.game.HEIGHT // 4)

            # 最终位置
            self.x = center_x + spiral_x
            self.y = center_y + spiral_y

            # 随机跳跃
            if random.random() < 0.01:  # 1%的概率发生跳跃
                jump_distance = 100 + random.random() * 100
                jump_angle = random.random() * 2 * math.pi
                self.x += math.cos(jump_angle) * jump_distance
                self.y += math.sin(jump_angle) * jump_distance

            # 确保边界检查
        self.x = max(self.move_bounds['x_min'],
                     min(self.x, self.move_bounds['x_max']))
        self.y = max(self.move_bounds['y_min'],
                     min(self.y, self.move_bounds['y_max']))


        # 确保敌机不会移出屏幕
        self.x = max(50, min(self.x, self.game.WIDTH - 50))
        self.y = max(50, min(self.y, self.game.HEIGHT // 2))


    def shoot(self):
        if self.shoot_cooldown <= 0:
            # 调用对应关卡的射击模式
            shoot_function = self.bullet_patterns.get(self.level)
            if shoot_function:
                shoot_function()
            self.shoot_cooldown = self.shoot_delay
        else:
            self.shoot_cooldown -= 1

    def shoot_quadratic(self):
        """第一关：抛物线 y = ax² """
        a = 0.01  # 抛物线弧度系数
        x_range = np.linspace(-self.pattern_width / 2, self.pattern_width / 2, self.pattern_points)

        for x in x_range:
            # 计算相对于敌机位置的坐标
            y = a * (x ** 2)

            # 创建子弹并设置初始位置和速度
            bullet = QuadraticBullet(
                self.x + x / 10,  # 缩放x以适应屏幕
                self.y + y / 10,  # 缩放y以适应屏幕
                self.game.player.x,
                self.game.player.y,
                1,
                self.level
            )
            self.bullets.append(bullet)

    def shoot_sine(self):
        """第二关：正弦函数 y = sin(x) """
        x_range = np.linspace(-2 * np.pi, 2 * np.pi, self.pattern_points)
        amplitude = 100  # 正弦波振幅

        for x in x_range:
            y = amplitude * np.sin(x)

            bullet = SineBullet(
                self.x + x * 20,
                self.y + y,
                self.game.player.x,
                self.game.player.y,
                self.level
            )
            self.bullets.append(bullet)

    def shoot_absolute(self):
        """第三关：绝对值函数 y = |x| """
        x_range = np.linspace(-self.pattern_width / 2, self.pattern_width / 2, self.pattern_points)

        for x in x_range:
            y = abs(x)

            bullet = AbsoluteBullet(
                self.x + x / 5,
                self.y + y / 5,
                self.game.player.x,
                self.game.player.y,
                self.level
            )
            self.bullets.append(bullet)

    def shoot_logarithmic(self):
        """第四关：对数函数 y = ln(x) """
        x_range = np.linspace(1, self.pattern_width / 2, self.pattern_points)

        for x in x_range:
            y = 50 * np.log(x)

            # 创建对称的两侧
            for sign in [-1, 1]:
                bullet = LogarithmicBullet(
                    self.x + sign * x / 3,
                    self.y + y / 3,
                    self.game.player.x,
                    self.game.player.y,
                    self.level
                )
                self.bullets.append(bullet)

    def shoot_exponential(self):
        """第五关：指数函数 y = eˣ """
        x_range = np.linspace(-5, 2, self.pattern_points)

        for x in x_range:
            y = 30 * np.exp(x)

            bullet = ExponentialBullet(
                self.x + x * 30,
                self.y + y,
                self.game.player.x,
                self.game.player.y,
                self.level
            )
            self.bullets.append(bullet)
    def create_bullet(self):
            # 根据关卡返回不同类型的子弹
        bullet_types = {
            1: QuadraticBullet,
            2: SineBullet,
            3: AbsoluteBullet,
            4: LogarithmicBullet,
            5: ExponentialBullet
        }
        bullet_class = bullet_types.get(self.level, QuadraticBullet)
            # 对于 QuadraticBullet，需要传递 direction 参数
        if self.level == 1:
            return QuadraticBullet(self.x, self.y, self.game.player.x, self.game.player.y, 1, self.level)
        else:
            return bullet_class(self.x, self.y, self.game.player.x, self.game.player.y, self.level)


    def update(self):
        self.move()
        self.shoot()

        # 更新子弹
        for bullet in self.bullets[:]:
            bullet.update()
            # 移除超出屏幕的子弹
            if (bullet.y < 0 or bullet.y > self.game.HEIGHT or
                    bullet.x < 0 or bullet.x > self.game.WIDTH):
                self.bullets.remove(bullet)


    def draw(self, screen):
        # 绘制敌机（六边形）
        if self.image:
            # 计算图片绘制位置（使图片中心与敌机坐标对齐）
            image_rect = self.image.get_rect()
            image_rect.center = (self.x, self.y)
            screen.blit(self.image, image_rect)
        else:
            # 保留原来的几何图形绘制作为其他关卡的后备
            points = [
                (self.x, self.y - self.height // 2),
                (self.x + self.width // 2, self.y - self.height // 4),
                (self.x + self.width // 2, self.y + self.height // 4),
                (self.x, self.y + self.height // 2),
                (self.x - self.width // 2, self.y + self.height // 4),
                (self.x - self.width // 2, self.y - self.height // 4)
            ]
            pygame.draw.polygon(screen, RED, points)

        # 继续绘制生命值条
        health_width = 30
        health_height = 4
        health_x = self.x - health_width // 2
        health_y = self.y - self.height // 2 - 10
        # 背景条
        pygame.draw.rect(screen, (200, 200, 200),
                         (health_x, health_y, health_width, health_height))

        # 当前生命值条
        health_percentage = self.health / self.max_health
        pygame.draw.rect(screen, (255, 0, 0),
                         (health_x, health_y, health_width * health_percentage, health_height))

        # 绘制子弹
        for bullet in self.bullets:
            bullet.draw(screen)


class EnemyBullet:
    def __init__(self, x, y, target_x, target_y, direction, level):  # 添加direction参数
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.target_x = target_x
        self.target_y = target_y
        self.direction = direction  # 新增方向属性
        self.radius = 4  # 保留用于碰撞检测
        self.time = 0
        self.level = level
        self.active = True
        self.speed = 3
        # 根据关卡加载对应子弹图片
        self.image = pygame.image.load(f"images/bullet{level}.png").convert_alpha()
        # 如果需要调整子弹大小，取消下面的注释并修改尺寸
        self.image = pygame.transform.scale(self.image, (20, 20))

    def update(self):
        self.time += self.speed / 50
        self.calculate_position()
    def update_common(self):
        """通用的更新逻辑"""
        # 检查子弹是否超出屏幕边界
        if (self.x < 0 or self.x > 1200 or
            self.y < 0 or self.y > 800):
            self.active = False
    def calculate_position(self):
        pass  # 在子类中实现具体的轨迹计算

    def draw(self, screen):
        # pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
        image_rect = self.image.get_rect()
        image_rect.center = (int(self.x), int(self.y))
        screen.blit(self.image, image_rect)




class QuadraticBullet(EnemyBullet):
    def __init__(self, x, y, target_x, target_y, direction,level):
        super().__init__(x, y, target_x, target_y,direction,level)
        self.direction = 1  # 1 表示向右的抛物线，-1 表示向左的抛物线
        self.a = 0.01  # 抛物线的开口大小
        self.max_x_distance = 400  # 子弹最大水平移动距离
    def update(self):
        self.time += self.speed / 50
        # 保持抛物线轨迹
        dx = (self.x - self.start_x)
        self.x += self.speed
        self.y = self.start_y + 0.01 * dx * dx
        self.update_common()


    def calculate_position(self):
        # y = ax² + bx + c
        dx = self.target_x - self.start_x
        self.x = self.start_x + self.time * dx
        # 使用二次函数计算y坐标
        a = 0.01  # 抛物线的开口大小
        dy = a * (self.x - self.start_x) ** 2
        self.y = self.start_y + dy


class SineBullet(EnemyBullet):
    def __init__(self, x, y, target_x, target_y, level=1):
        super().__init__(x, y, target_x, target_y, direction=1,level=level)
        self.time = 0
    def update(self):
        self.time += self.speed / 50
        # 保持正弦波轨迹
        self.x += self.speed
        self.y = self.start_y + 100 * math.sin((self.x - self.start_x) / 100)
        self.update_common()
    def calculate_position(self):
        # y = A * sin(Bx) + Cx
        amplitude = 50
        frequency = 0.1
        self.x = self.start_x + self.time * 100
        self.y = self.start_y + amplitude * math.sin(frequency * self.time) + self.time * 50


class AbsoluteBullet(EnemyBullet):
    def __init__(self, x, y, target_x, target_y, level=1):
        super().__init__(x, y, target_x, target_y,direction=1, level=level)
    def update(self):
        self.time += self.speed / 50
        # 保持绝对值函数轨迹
        dx = (self.x - self.start_x)
        self.x += self.speed
        self.y = self.start_y + abs(dx) * 0.5
        self.update_common()
    def calculate_position(self):
        # y = |x - x₀| + y₀
        dx = self.target_x - self.start_x
        self.x = self.start_x + self.time * 100
        self.y = self.start_y + abs(self.x - self.start_x) * 0.2


class LogarithmicBullet(EnemyBullet):
    def __init__(self, x, y, target_x, target_y, level=1):
        super().__init__(x, y, target_x, target_y, direction=1,level=level)
    def update(self):
        self.time += self.speed / 50
        # 保持对数函数轨迹
        dx = max(1, abs(self.x - self.start_x))
        self.x += self.speed
        self.y = self.start_y + 30 * math.log(dx)
        self.update_common()
    def calculate_position(self):
        # y = a * ln(x - x₀) + y₀
        self.x = self.start_x + self.time * 100
        if self.x - self.start_x > 0:
            self.y = self.start_y + 30 * math.log(self.x - self.start_x + 1)


class ExponentialBullet(EnemyBullet):
    def __init__(self, x, y, target_x, target_y, level=1):
        super().__init__(x, y, target_x, target_y,direction=1, level=level)
    def update(self):
        self.time += self.speed / 50
        # 保持指数函数轨迹
        dx = (self.x - self.start_x) / 100
        self.x += self.speed
        self.y = self.start_y + 20 * (math.exp(dx) - 1)
        self.update_common()
    def calculate_position(self):
        # y = a * e^(bx) + y₀
        dx = self.target_x - self.start_x
        self.x = self.start_x + self.time * 100
        self.y = self.start_y + 20 * math.exp(0.01 * (self.x - self.start_x))


class PowerUp:
    def __init__(self, x, y, type_):
        self.x = x
        self.y = y
        self.type = type_  # 'health' 或 'spiral'
        self.width = 30
        self.height = 30
        self.float_offset = 0  # 用于悬浮效果
        self.float_speed = 0.1

    def update(self):
        # 添加悬浮效果
        self.float_offset = math.sin(time.time() * 2) * 5
        
    def draw(self, screen):
        y_pos = self.y + self.float_offset
        if self.type == 'health':
            # 绘制心形道具
            points = [
                (self.x, y_pos - 10),  # 顶部中心
                (self.x + 10, y_pos - 15),  # 右上
                (self.x + 15, y_pos - 5),  # 右边
                (self.x, y_pos + 10),  # 底部
                (self.x - 15, y_pos - 5),  # 左边
                (self.x - 10, y_pos - 15),  # 左上
            ]
            pygame.draw.polygon(screen, (255, 0, 0), points)
        else:  # spiral
            # 绘制涡旋标志
            pygame.draw.circle(screen, (0, 0, 255), (int(self.x), int(y_pos)), 15)
            # 绘制螺旋线条
            for i in range(0, 360, 30):
                angle = math.radians(i)
                end_x = self.x + math.cos(angle) * 10
                end_y = y_pos + math.sin(angle) * 10
                pygame.draw.line(screen, WHITE, (self.x, y_pos), (end_x, end_y), 2)

class SpiralBullet(Bullet):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.initial_x = x
        self.initial_y = y
        self.angle = 0
        self.radius = 3  # 增大子弹半径，使其更容易看见
        self.expand_speed = 0.3  # 降低扩展速度
        self.rotation_speed = 0.1  # 降低旋转速度
        self.max_radius = 300  # 限制最大半径
        self.time = 0

    def update(self):
        # 更平滑的涡旋轨迹
        self.time += self.rotation_speed
        # 使用参数方程表示阿基米德螺旋线
        r = self.time * self.expand_speed * 20  # 减小系数使螺旋更紧密

        # 限制最大半径
        if r > self.max_radius:
            self.active = False  # 超出最大半径后消失
            return

        # 计算新位置
        self.x = self.initial_x + r * math.cos(self.time * 5)  # 降低角速度
        self.y = self.initial_y + r * math.sin(self.time * 5)

    def draw(self, screen):
        # 为螺旋弹道的每个点都绘制子弹图片
        for i in range(3):
            trail_time = self.time - i * 0.1
            if trail_time > 0:
                r = trail_time * self.expand_speed * 20
                trail_x = self.initial_x + r * math.cos(trail_time * 5)
                trail_y = self.initial_y + r * math.sin(trail_time * 5)

                # 设置拖尾的透明度
                alpha = 255 - i * 70
                # 创建一个临时surface来处理透明度
                temp_surface = self.image.copy()
                temp_surface.set_alpha(alpha)

                # 绘制带透明度的子弹
                image_rect = temp_surface.get_rect()
                image_rect.center = (int(trail_x), int(trail_y))
                screen.blit(temp_surface, image_rect)


# 运行游戏
if __name__ == "__main__":
    game = Game()
    game.run()