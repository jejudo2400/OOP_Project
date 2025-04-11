import pygame
import math
import sys
import random
import time
from PIL import Image, ImageSequence

# 기본 설정
pygame.init()

# 모니터 해상도 기반 스크린 크기 설정
info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h

screen_resolution = (screen_width, screen_height)
screen = pygame.display.set_mode(screen_resolution, pygame.FULLSCREEN)

pygame.display.set_caption("Boss Hunter")

pygame.mixer.init()
pygame.mixer.music.load('snipersound3.mp3')

# 색상 설정
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
attack_particle_color = (255, 100, 100)
hit_particle_color = (255, 255, 0)
guard_color = (149, 242, 255, 128)
dim_guard_color = (75, 121, 128, 128)
bullet_color = (255, 20, 147)
bullet_glow_color = (0, 255, 255)  # 네온 블루 후광
awaken_bullet_glow_color = (255, 100, 100)

# 폰트 설정
font = pygame.font.Font(None, 36)


def load_gif_frames(gif_path, size):
    gif_image = Image.open(gif_path)

    frames = []
    for frame in ImageSequence.Iterator(gif_image):
        frame = frame.convert("RGBA")
        frame = frame.resize(size, Image.Resampling.LANCZOS)  # 크기 조정
        mode = frame.mode
        frame_data = frame.tobytes()
        pygame_image = pygame.image.fromstring(frame_data, size, mode)
        frames.append(pygame_image)

    frame_duration = gif_image.info[
        'duration'] if 'duration' in gif_image.info else 100

    return frames, frame_duration


def display_gif_frame(screen, frames, frame_index, position):
    """
    현재 프레임을 Pygame 스크린에 표시하는 함수.

    :param screen: Pygame 디스플레이 스크린
    :param frames: 변환된 프레임 리스트
    :param frame_index: 현재 프레임 인덱스
    :param position: GIF 이미지를 표시할 위치 (x, y)
    """
    frame = frames[frame_index]
    screen.blit(frame, position)
    return frame.get_rect(topleft=position)


# 플레이어 클래스 정의
class Player(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.image = pygame.image.load(
            'ingame_player.png').convert_alpha()  # 이미지 로드 및 알파 채널 포함
        self.image = pygame.transform.scale(self.image, (50, 50))  # 이미지 크기 조정
        self.rect = self.image.get_rect()
        self.rect.center = (screen_width // 2, screen_height // 2)
        self.speed = 5
        self.dash_speed = 20
        self.is_dashing = False
        self.dash_duration = 10  # 프레임 수
        self.dash_cooldown = 30  # 프레임 수
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.guard = None
        self.guard_cooldown_timer = 0
        self.is_invincible = False  # 무적 상태 초기화

        # 플레이어 공격력 설정
        self.base_damage = 2
        self.damage = self.base_damage

        # 플레이어 체력 설정
        self.player_max_health = 100
        self.player_current_health = self.player_max_health

        # 각성 모드 관련 변수
        self.is_awakened = False
        self.awaken_duration = 600  # 10초 (60 FPS 기준)
        self.awaken_timer = 0

        # 각성 모드용 GIF 관련 변수
        self.awaken_gif_frames, self.awaken_gif_duration = load_gif_frames(
            'awake.gif', (130, 130))
        self.awaken_gif_frame_index = 0
        self.awaken_gif_last_update = pygame.time.get_ticks()

    def update(self):
        keys = pygame.key.get_pressed()
        move_x, move_y = 0, 0
        current_speed = self.dash_speed if self.is_dashing else self.speed

        if keys[pygame.K_LEFT]:
            move_x = -current_speed
        if keys[pygame.K_RIGHT]:
            move_x = current_speed
        if keys[pygame.K_UP]:
            move_y = -current_speed
        if keys[pygame.K_DOWN]:
            move_y = current_speed
        if keys[pygame.
                K_c] and not self.is_dashing and self.dash_cooldown_timer == 0:
            self.is_dashing = True
            self.dash_timer = self.dash_duration
            self.is_invincible = True  # 대쉬 시작 시 무적 상태로 설정

        self.rect.x += move_x
        self.rect.y += move_y

        # 화면 경계를 벗어나지 않도록 설정
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > screen_height:
            self.rect.bottom = screen_height

        if self.is_dashing:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.dash_cooldown_timer = self.dash_cooldown
                self.is_invincible = False  # 대쉬 종료 시 무적 상태 해제

        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= 1

        if self.guard:
            self.guard.update()

        # 각성 모드 타이머 업데이트
        if self.is_awakened:
            self.awaken_timer -= 1
            if self.awaken_timer <= 0:
                self.is_awakened = False
                self.damage = self.base_damage  # 공격력 원래대로
            else:
                # 각성 모드일 때 GIF 프레임 업데이트
                current_time = pygame.time.get_ticks()
                if current_time - self.awaken_gif_last_update >= self.awaken_gif_duration:
                    self.awaken_gif_frame_index = (
                        self.awaken_gif_frame_index + 1) % len(
                            self.awaken_gif_frames)
                    self.awaken_gif_last_update = current_time

    def awaken(self):
        self.is_awakened = True
        self.awaken_timer = self.awaken_duration
        self.damage = self.base_damage * 1.5  # 공격력 50% 증가

    def draw(self, screen):
        # 각성 상태라면 GIF 이펙트 그리기
        if self.is_awakened:
            frame = self.awaken_gif_frames[self.awaken_gif_frame_index]
            frame_rect = frame.get_rect(
                center=(self.rect.centerx,
                        self.rect.centery - 25))  # gif 위치 조정 부분
            screen.blit(frame, frame_rect)

        # 플레이어 이미지를 그리기
        screen.blit(self.image, self.rect)

    def player_hp(self, damage):
        self.player_current_health -= damage
        if self.player_current_health < 0:
            self.player_current_health = 0


# 플레이어 UI 클래스 정의
class PlayerUI(pygame.sprite.Sprite):

    def __init__(self, player):
        super().__init__()
        self.player = player  # Player 객체 참조
        self.player_max_energy = 100  # 최대 에너지 설정
        self.player_current_energy = 0  # 현재 에너지 초기화

        # 플레이어 초상화 이미지 로드
        self.portrait = pygame.image.load('player.png')
        self.portrait = pygame.transform.scale(self.portrait,
                                               (110, 110))  # 원하는 크기로 조정

        # 현재 모니터 해상도 정보를 가져옴
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h

        # UI 위치를 화면 좌측 하단의 90% 위치에 설정
        ui_x = screen_width * 0.13
        ui_y = screen_height * 0.98
        self.image = self.player_ui()
        self.rect = self.image.get_rect()
        self.rect.midbottom = (ui_x, ui_y)

    def update(self):
        if self.player.player_current_health <= 0:
            return
        self.image = self.player_ui()  # UI 업데이트

    def player_ui(self):
        ui_screen = pygame.Surface((450, 200))  # UI 화면 생성
        ui_screen.fill((255, 255, 255))  # 색 채우기

        # 플레이어 초상화 그리기
        ui_screen.blit(self.portrait, (5, 5))

        # 플레이어 에너지바 그리기
        pygame.draw.rect(ui_screen, (255, 255, 255), (150, 70, 275, 30))

        player_bar_width = 275
        player_hp_ratio = self.player.player_current_health / self.player.player_max_health
        player_current_health = player_bar_width * player_hp_ratio
        # 플레이어 HP바 그리기
        pygame.draw.rect(ui_screen, (255, 0, 0),
                         (150, 20, player_current_health, 30))

        # 플레이어 에너지바 그리기
        player_energy_ratio = self.player_current_energy / self.player_max_energy
        player_current_energy = player_bar_width * player_energy_ratio
        pygame.draw.rect(ui_screen, (181, 230, 29),
                         (150, 70, player_current_energy, 30))

        # 각성 지속시간 타이머 그리기
        if self.player.is_awakened:
            remaining_time = self.player.awaken_timer // 60  # 남은 시간을 초 단위로 표시
            font = pygame.font.Font(None, 36)
            timer_text = font.render(f'Awaken Time: {remaining_time}s', True,
                                     (255, 80, 80))
            ui_screen.blit(timer_text, (150, 110))

        # 방어막 아이콘 그리기
        if self.player.guard_cooldown_timer == 0:
            icon_color = guard_color
        else:
            icon_color = dim_guard_color

        icon_radius = 20
        icon_surface = pygame.Surface((icon_radius * 2, icon_radius * 2),
                                      pygame.SRCALPHA)
        pygame.draw.circle(icon_surface, icon_color,
                           (icon_radius, icon_radius), icon_radius)
        icon_x = 240  # X 위치 조정
        icon_y = 140  # Y 위치 조정
        font = pygame.font.Font(None, 36)
        guard_text = font.render(f'Gaurd:', True, (0, 0, 0))
        ui_screen.blit(guard_text, (150, 145))
        ui_screen.blit(icon_surface, (icon_x, icon_y))

        return ui_screen

    def increase_energy(self, amount):
        self.player_current_energy += amount
        if self.player_current_energy > self.player_max_energy:
            self.player_current_energy = self.player_max_energy

    def reset_energy(self):
        self.player_current_energy = 0


# 각성 클래스 정의
class Awaken(pygame.sprite.Sprite):

    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.image = self.create_large_bullet()
        self.rect = self.image.get_rect()
        self.rect.center = start_pos
        self.speed = 15  # 느린 속도
        angle = math.atan2(target_pos[1] - start_pos[1],
                           target_pos[0] - start_pos[0])
        self.dx = self.speed * math.cos(angle)
        self.dy = self.speed * math.sin(angle)
        self.damage = 20  # 큰 피해량

    def create_large_bullet(self):
        bullet_size = 16
        glow_radius = 24

        surface = pygame.Surface((glow_radius * 2, glow_radius * 2),
                                 pygame.SRCALPHA)
        surface = surface.convert_alpha()

        for alpha in range(glow_radius, 0, -1):
            pygame.draw.circle(
                surface,
                (awaken_bullet_glow_color[0], awaken_bullet_glow_color[1],
                 awaken_bullet_glow_color[2], int(255 *
                                                  (alpha / glow_radius))),
                (glow_radius, glow_radius), alpha)

        # 총알 그리기
        pygame.draw.circle(surface, bullet_color, (glow_radius, glow_radius),
                           bullet_size // 2)

        return surface

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if not screen.get_rect().contains(self.rect):
            self.kill()


# 방어막 클래스 정의
class Guard(pygame.sprite.Sprite):

    def __init__(self, player):
        super().__init__()
        self.player = player
        self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(self.image, guard_color, (30, 30),
                           30)  # 중앙 좌표와 반지름 맞추기
        self.rect = self.image.get_rect(center=self.player.rect.center)
        self.duration = 60  # 방어막 지속 시간 (1초)
        self.is_guard = False

    def update(self):
        self.rect.center = self.player.rect.center
        if self.is_guard:
            self.duration -= 1
            if self.duration <= 0:
                self.is_guard = False
                self.player.guard = None
                self.kill()


# 공격 클래스 정의
class Attack(pygame.sprite.Sprite):

    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.image = self.create_bullet_with_glow()
        self.rect = self.image.get_rect()
        self.rect.center = start_pos
        self.speed = 35
        angle = math.atan2(target_pos[1] - start_pos[1],
                           target_pos[0] - start_pos[0])
        self.dx = self.speed * math.cos(angle)
        self.dy = self.speed * math.sin(angle)

    def create_bullet_with_glow(self):
        # 총알의 크기와 후광의 반지름 설정
        bullet_size = 8
        glow_radius = 20

        # 총알과 후광을 그릴 Surface 생성
        surface = pygame.Surface((glow_radius * 2, glow_radius * 2),
                                 pygame.SRCALPHA)
        surface = surface.convert_alpha()

        # 후광 그리기
        for alpha in range(glow_radius, 0, -1):
            pygame.draw.circle(
                surface,
                (bullet_glow_color[0], bullet_glow_color[1],
                 bullet_glow_color[2], int(255 * (alpha / glow_radius))),
                (glow_radius, glow_radius), alpha)

        # 총알 그리기
        pygame.draw.circle(surface, bullet_color, (glow_radius, glow_radius),
                           bullet_size // 2)

        return surface

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if not screen.get_rect().contains(self.rect):
            self.kill()


def draw_crosshair(surface, center, color=(255, 0, 0), radius=50):
    pygame.draw.circle(surface, color, center, radius, 3)
    pygame.draw.line(surface, color, (center[0] - radius, center[1]),
                     (center[0] + radius, center[1]), 3)
    pygame.draw.line(surface, color, (center[0], center[1] - radius),
                     (center[0], center[1] + radius), 3)
    inner_radius = radius // 4
    pygame.draw.circle(surface, color, center, inner_radius, 3)\


class Boss(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()

        # boss.gif 프레임 로드
        self.boss_gif_path = 'boss.gif'
        self.boss_size = (300, 300)  # 보스의 크기
        self.boss_frames, self.boss_frame_duration = load_gif_frames(
            self.boss_gif_path, self.boss_size)
        self.boss_frame_index = 0
        self.boss_last_frame_update = pygame.time.get_ticks()

        # self.image를 첫 번째 프레임으로 설정
        self.image = self.boss_frames[0]
        self.rect = self.image.get_rect()
        self.rect.midtop = (screen_width // 2, 50)  # 초기 위치 설정
        self.bullets = pygame.sprite.Group()

        # 패턴 관련 변수 추가
        self.current_pattern = 0
        self.pattern_timer = 0
        self.pattern_text = ""
        self.pattern1_interval = 18  # 0.3초 (18 프레임) 대기 시간
        self.pattern1_step = 0
        self.pattern1_angles1 = [i for i in range(0, 181, 10)]
        self.pattern1_angles2 = [i for i in range(0, 181, 15)]
        self.pattern1_repeat = 0
        self.angle = 0

        self.pattern2_target = None
        self.pattern2_prepare_timer = 60  # 1초 준비 시간
        self.crosshair_offset = [0, 0]
        self.recoil_timer = 0
        self.snipershoot = True

        self.pattern3_cnt = 0
        self.pattern3_interval = 80  # 1초 대기 시간

        self.move = True

        # pattern4 관련 변수 초기화
        self.pattern4_gif_path = 'laser.gif'
        self.pattern4_size = (400, 1200)  # 원하는 크기
        self.pattern4_position = [150, 150]  # 원하는 위치
        self.pattern4_frames, self.pattern4_frame_duration = load_gif_frames(
            self.pattern4_gif_path, self.pattern4_size)
        self.pattern4_frame_index = 0
        self.pattern4_last_frame_update = pygame.time.get_ticks()

        # pattern5 관련 변수 초기화
        self.pattern5_gif_path1 = 'RangeAttack1.gif'
        self.pattern5_size1 = (300, 900)  # 원하는 크기
        self.pattern5_position1 = [150, 300]  # 원하는 위치
        self.pattern5_frames1, self.pattern5_frame_duration1 = load_gif_frames(
            self.pattern5_gif_path1, self.pattern5_size1)
        self.pattern5_frame_index1 = 0
        self.pattern5_last_frame_update1 = pygame.time.get_ticks()

        self.pattern5_gif_path2 = 'RangeAttack2.gif'
        self.pattern5_size2 = (300, 900)  # 원하는 크기
        self.pattern5_position2 = [450, 300]  # 원하는 위치
        self.pattern5_frames2, self.pattern5_frame_duration2 = load_gif_frames(
            self.pattern5_gif_path2, self.pattern5_size2)
        self.pattern5_frame_index2 = 0
        self.pattern5_last_frame_update2 = pygame.time.get_ticks()

        self.pattern5_position3 = [750, 300]
        self.pattern5_position4 = [1050, 300]
        self.pattern5_position5 = [1650, 300]
        self.cnt = 0
        self.hit = True

        # 체력바 관련
        self.max_health = 100
        self.current_health = self.max_health

        self.boss_damage = 2

    def pattern1(self, bullets_group):
        if self.pattern_timer == 0:
            if self.pattern1_step == 0:
                self.pattern_text = "Pattern1_Spreadshoot"
                # 첫 번째 흩뿌리기
                for self.angle in self.pattern1_angles1:
                    direction = math.radians(self.angle)
                    bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                        direction)
                    bullets_group.add(bullet)
                self.pattern1_step = 1
                self.pattern_timer = self.pattern1_interval

            elif self.pattern1_step == 1:
                # 첫 번째 흩뿌린 각도의 사이로 다시 흩뿌리기
                for self.angle in self.pattern1_angles2:
                    new_angle = self.angle
                    direction = math.radians(new_angle)
                    bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                        direction)
                    bullets_group.add(bullet)
                self.pattern1_step = 0
                self.pattern_timer = self.pattern1_interval
                self.pattern1_repeat += 1

            # 패턴 반복이 2번 완료되면 종료
            if self.pattern1_repeat >= 5:
                self.pattern1_repeat = 0
                self.current_pattern = 0
        else:
            self.pattern_timer -= 1

    def pattern2(self, player, bullets_group):
        if self.pattern2_prepare_timer > 0:
            # 플레이어 위치 저장
            if self.snipershoot == True:
                self.pattern2_target = player.rect.center

            # 조준경을 플레이어 위치로 이동
            crosshair_pos = (self.pattern2_target[0] +
                             self.crosshair_offset[0],
                             self.pattern2_target[1] +
                             self.crosshair_offset[1])

            # 조준경 그리기
            draw_crosshair(screen, crosshair_pos)

            # 준비 시간이 끝나면 탄환 발사
            self.pattern2_prepare_timer -= 1

            if self.pattern2_prepare_timer <= 30:
                pygame.mixer.music.play()

            # 조준선 반동 효과 적용
            if self.pattern2_prepare_timer <= 10:
                # 중앙에 glass.png 이미지 그리기
                glass_image = pygame.image.load("glass.png")
                glass_rect = glass_image.get_rect(center=crosshair_pos)
                screen.blit(glass_image, glass_rect)
                self.apply_recoil()

        elif self.pattern2_prepare_timer == 0:
            self.pattern_text = "Pattern2_Sniping"
            bullet_direction = math.atan2(
                self.pattern2_target[1] - self.rect.centery,
                self.pattern2_target[0] - self.rect.centerx)

            # 탄환 발사
            bullet = BossBullet(self.rect.centerx, self.rect.centery,
                                bullet_direction)
            bullet.speed = 60  # 빠른 탄환 속도 설정
            bullets_group.add(bullet)

            # 패턴2 종료 및 초기화
            self.pattern2_target = None
            self.pattern2_prepare_timer = 60
            self.current_pattern = 0  # 패턴 종료
            self.snipershoot = True

        else:
            self.pattern2_prepare_timer = 60  # 패턴 준비 시간 초기화

    def apply_recoil(self):
        # 반동 효과 적용: 좌우로 흔들리며 위로 올라감
        self.crosshair_offset[0] = random.randint(-10, 10)
        self.crosshair_offset[1] = random.randint(-10, 10)

    def pattern3(self, player, bullets_group):
        if self.pattern_timer == 0:
            self.pattern_text = "Pattern3_HomingMissile"
            if self.pattern3_cnt == 0:
                start_pos = [(100, 100), (screen_width - 100, 100),
                             (100, screen_height - 100),
                             (screen_width - 100, screen_height - 100)]

                for i in range(4):
                    missile = HomingMissile(start_pos[i], player)
                    bullets_group.add(missile)

                self.pattern_timer = self.pattern3_interval
                self.pattern3_cnt = 1

            elif self.pattern3_cnt == 1:
                start_pos = [(self.rect.centerx, 100),
                             (100, screen_height // 2),
                             (self.rect.centerx, screen_height - 100),
                             (screen_width - 100, screen_height // 2)]

                for i in range(4):
                    missile = HomingMissile(start_pos[i], player)
                    bullets_group.add(missile)

                self.pattern3_cnt = 0
                self.current_pattern = 0
        else:
            self.pattern_timer -= 1

    def pattern4(self, player, event=None):
        if self.pattern_timer == 0:
            self.pattern_text = "Pattern4_Laser"

            # 보스가 왼쪽으로 부드럽게 이동
            if self.rect.x > 80 and self.move:
                self.rect.x -= 10
                if self.rect.x <= 80:
                    self.move = False

            elif self.rect.x <= screen_width * 0.8 and not self.move:
                # 레이저 이미지의 위치 설정 (보스의 하단 중앙 기준)
                self.position = [
                    self.rect.centerx - self.pattern4_size[0] // 2 + 35,
                    self.rect.bottom - 130
                ]

                # GIF 프레임 업데이트 타이밍
                current_time = pygame.time.get_ticks()
                if current_time - self.pattern4_last_frame_update >= self.pattern4_frame_duration:
                    self.pattern4_frame_index = (self.pattern4_frame_index +
                                                 1) % len(self.pattern4_frames)
                    self.pattern4_last_frame_update = current_time

                pattern4_gif = display_gif_frame(screen, self.pattern4_frames,
                                                 self.pattern4_frame_index,
                                                 self.position)

                self.rect.x += 15

                # 플레이어와 각 GIF 프레임의 충돌 감지
                if (player.rect.colliderect(pattern4_gif)
                        and not player.is_invincible and
                    (player.guard is None or not player.guard.is_guard)):
                    player.player_hp(1)  # 플레이어 체력 감소

                if self.rect.x >= screen_width * 0.8:
                    self.rect.x = screen_width // 2
                    self.move = True
                    self.current_pattern = 0
                    self.rect.midtop = (screen_width // 2, 50)  # 보스 위치 초기화
        else:
            self.pattern_timer -= 1

    def pattern5(self, player, event=None):
        if self.pattern_timer == 0:
            self.pattern_text = "Pattern5_RangeAttack"

            # GIF 프레임 업데이트 타이밍
            current_time = pygame.time.get_ticks()
            # 첫 번째 GIF 프레임 업데이트
            if current_time - self.pattern5_last_frame_update1 >= self.pattern5_frame_duration1:
                self.pattern5_frame_index1 = (self.pattern5_frame_index1 +
                                              1) % len(self.pattern5_frames1)
                self.pattern5_last_frame_update1 = current_time

            # 두 번째 GIF 프레임 업데이트
            if current_time - self.pattern5_last_frame_update2 >= self.pattern5_frame_duration2:
                self.pattern5_frame_index2 = (self.pattern5_frame_index2 +
                                              1) % len(self.pattern5_frames2)
                self.pattern5_last_frame_update2 = current_time

            # 첫 번째 GIF 표시
            gif_rect1 = display_gif_frame(screen, self.pattern5_frames1,
                                          self.pattern5_frame_index1,
                                          self.pattern5_position1)
            gif_rect3 = display_gif_frame(screen, self.pattern5_frames1,
                                          self.pattern5_frame_index1,
                                          self.pattern5_position3)

            # 두 번째 GIF 표시
            gif_rect2 = display_gif_frame(screen, self.pattern5_frames2,
                                          self.pattern5_frame_index2,
                                          self.pattern5_position2)
            gif_rect4 = display_gif_frame(screen, self.pattern5_frames2,
                                          self.pattern5_frame_index2,
                                          self.pattern5_position4)
            gif_rect5 = display_gif_frame(screen, self.pattern5_frames2,
                                          self.pattern5_frame_index2,
                                          self.pattern5_position5)

            # 플레이어와 각 GIF 프레임의 충돌 감지
            if (player.rect.colliderect(gif_rect1)
                    or player.rect.colliderect(gif_rect2)
                    or player.rect.colliderect(gif_rect3)
                    or player.rect.colliderect(gif_rect4) or
                    player.rect.colliderect(gif_rect5)) and self.hit == True:
                if not player.is_invincible and (player.guard is None
                                                 or not player.guard.is_guard):
                    player.player_hp(20)  # 플레이어 체력 감소
                    self.hit = False

            if self.pattern5_frame_index1 == 0 and self.pattern5_frame_index2 == 0:
                self.current_pattern = 0  # 패턴 종료
                self.pattern_timer = 60  # 다음 패턴 준비를 위해 타이머 초기화
                self.hit = True

                # 보스 위치를 중앙 상단으로 재설정
                self.rect.midtop = (screen_width // 2, 50)
        else:
            # 'SAFE' 직사각형 그리기
            if 0 < self.pattern_timer <= 120:
                safe_rect = pygame.Rect(1350, 300, 300, 600)
                pygame.draw.rect(screen, (0, 255, 0), safe_rect)
                font = pygame.font.Font(None, 74)
                text = font.render("SAFE", True, (255, 255, 255))
                text_rect = text.get_rect(center=safe_rect.center)
                screen.blit(text, text_rect)

            self.pattern_timer -= 1

    def update(self, player, bullets_group):
        if self.current_health <= 0:
            self.image.set_alpha(0)
            bullets_group.empty()
            return

        # GIF 프레임 업데이트
        current_time = pygame.time.get_ticks()
        if current_time - self.boss_last_frame_update >= self.boss_frame_duration:
            self.boss_frame_index = (self.boss_frame_index + 1) % len(
                self.boss_frames)
            self.boss_last_frame_update = current_time

            # self.image를 현재 프레임으로 업데이트
            self.image = self.boss_frames[self.boss_frame_index]

        if self.current_pattern != 0:
            if self.current_pattern == 1:
                self.pattern1(bullets_group)
            elif self.current_pattern == 2:
                self.pattern2(player, bullets_group)
            elif self.current_pattern == 3:
                self.pattern3(player, bullets_group)
            elif self.current_pattern == 4:
                self.pattern4(player)
            elif self.current_pattern == 5:
                self.pattern5(player)
        else:
            if len(bullets_group) == 0:
                self.current_pattern = random.choice([1, 2, 3, 4, 5])
                # self.current_pattern = 4
                if self.current_pattern == 1:
                    self.pattern_timer = self.pattern1_interval
                elif self.current_pattern == 2:
                    self.pattern_timer = 60
                elif self.current_pattern == 3:
                    self.pattern_timer = self.pattern3_interval
                elif self.current_pattern == 4:
                    self.pattern_timer = 60
                elif self.current_pattern == 5:
                    self.pattern_timer = 120

    def draw(self):
        health_bar_width = screen_width  # 체력 바의 최대 너비
        health_ratio = self.current_health / self.max_health
        current_health_bar_width = health_bar_width * health_ratio
        pygame.draw.rect(screen, (255, 0, 0),
                         (0, 20, current_health_bar_width, 20))  # 빨간색 체력 바

        # 현재 프레임을 화면에 그리기
        screen.blit(self.image, self.rect)
        self.bullets.draw(screen)

    def draw_pattern_text(self):
        if self.pattern_text:
            text_surface = font.render(self.pattern_text, True, (0, 0, 0))
            screen.blit(text_surface, (10, 10))

    def hp(self, damage):
        self.current_health -= damage


class HomingMissile(pygame.sprite.Sprite):

    def __init__(self, start_pos, target, max_homing_distance=100, speed=7):
        super().__init__()
        outer_bullet_size = 32  # 바깥 원의 크기
        inner_bullet_size = 25  # 안쪽 원의 크기

        # 총알의 모양을 그릴 Surface 생성
        self.image = pygame.Surface((outer_bullet_size, outer_bullet_size),
                                    pygame.SRCALPHA)
        self.image = self.image.convert_alpha()

        # 바깥 원 그리기 (초록색)
        pygame.draw.circle(self.image, (0, 255, 0),
                           (outer_bullet_size // 2, outer_bullet_size // 2),
                           outer_bullet_size // 2)

        # 안쪽 원 그리기 (하얀색)
        pygame.draw.circle(self.image, (255, 255, 255),
                           (outer_bullet_size // 2, outer_bullet_size // 2),
                           inner_bullet_size // 2)
        self.rect = self.image.get_rect(center=start_pos)
        self.target = target
        self.max_homing_distance = max_homing_distance
        self.speed = speed
        self.homing = True

    def update(self):
        if self.homing:
            target_x, target_y = self.target.rect.center
            missile_x, missile_y = self.rect.center

            angle = math.atan2(target_y - missile_y, target_x - missile_x)
            self.move_x = self.speed * math.cos(angle)
            self.move_y = self.speed * math.sin(angle)

            if math.hypot(target_x - missile_x,
                          target_y - missile_y) <= self.max_homing_distance:
                self.homing = False

        self.rect.x += self.move_x
        self.rect.y += self.move_y

        if not screen.get_rect().contains(self.rect):
            self.kill()


# 보스 총알 클래스 정의
class BossBullet(pygame.sprite.Sprite):

    def __init__(self, x, y, direction):
        super().__init__()
        outer_bullet_size = 32  # 바깥 원의 크기
        inner_bullet_size = 25  # 안쪽 원의 크기

        # 총알의 모양을 그릴 Surface 생성
        self.image = pygame.Surface((outer_bullet_size, outer_bullet_size),
                                    pygame.SRCALPHA)
        self.image = self.image.convert_alpha()

        # 바깥 원 그리기 (빨간색)
        pygame.draw.circle(self.image, red,
                           (outer_bullet_size // 2, outer_bullet_size // 2),
                           outer_bullet_size // 2)

        # 안쪽 원 그리기 (하얀색)
        pygame.draw.circle(self.image, white,
                           (outer_bullet_size // 2, outer_bullet_size // 2),
                           inner_bullet_size // 2)

        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.speed = 7

    def update(self):
        self.rect.x += self.speed * math.cos(self.direction)
        self.rect.y += self.speed * math.sin(self.direction)

        if not screen.get_rect().contains(self.rect):
            self.kill()


# 공격 파티클 클래스 정의
class Attack_particle(pygame.sprite.Sprite):

    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((5, 5))
        self.image.fill(attack_particle_color)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.lifetime = random.randint(20, 40)
        self.speed = random.uniform(1, 4)
        self.angle = random.uniform(0, 2 * math.pi)
        self.dx = self.speed * math.cos(self.angle)
        self.dy = self.speed * math.sin(self.angle)

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


# 히트 파티클 클래스 정의
class Hit_particle(pygame.sprite.Sprite):

    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((5, 5))
        self.image.fill(hit_particle_color)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.lifetime = random.randint(20, 40)
        self.speed = random.uniform(1, 4)
        self.angle = random.uniform(0, 2 * math.pi)
        self.dx = self.speed * math.cos(self.angle)
        self.dy = self.speed * math.sin(self.angle)

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


# 게임 시작 클래스 정의
class GameStart:

    def __init__(self, screen):
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.font = pygame.font.Font(None, 74)
        self.button_font = pygame.font.Font(None, 50)
        self.start_button_rect = pygame.Rect(self.screen_width // 2 - 100,
                                             self.screen_height // 2 - 50, 200,
                                             100)

    def draw(self):
        self.screen.fill((0, 0, 0))
        title_text = self.font.render('Boss Hunter', True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.screen_width // 2,
                                                 self.screen_height // 3))
        self.screen.blit(title_text, title_rect)

        pygame.draw.rect(self.screen, (0, 255, 0), self.start_button_rect)
        start_text = self.button_font.render('Start', True, (0, 0, 0))
        start_rect = start_text.get_rect(center=self.start_button_rect.center)
        self.screen.blit(start_text, start_rect)

        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button_rect.collidepoint(event.pos):
                return True
        return False


# 게임 매니저 클래스 정의
class GameManager:

    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 74)
        self.game_over = False
        self.game_clear = False

    def show_game_over(self):
        self.screen.fill((0, 0, 0))
        game_over_text = self.font.render('Game Over', True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(screen_width // 2,
                                                         screen_height // 2))
        self.screen.blit(game_over_text, game_over_rect)
        pygame.display.flip()

    def show_game_clear(self):
        self.screen.fill((0, 0, 0))
        game_clear_text = self.font.render('Game Clear', True, (0, 255, 0))
        game_clear_rect = game_clear_text.get_rect(center=(screen_width // 2,
                                                           screen_height // 2))
        self.screen.blit(game_clear_text, game_clear_rect)
        pygame.display.flip()

    def check_game_state(self, player, boss):
        if player.player_current_health <= 0:
            self.game_over = True
        elif boss.current_health <= 0:
            self.game_clear = True

    def handle_event(self, event, game):
        if self.game_over or self.game_clear:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game.reset_game()
                self.game_over = False
                self.game_clear = False


# 게임 클래스 정의
class Game:

    def __init__(self):
        self.player = Player()
        self.playerui = PlayerUI(self.player)  # Player 객체 전달
        self.boss = Boss()
        self.manager = GameManager(screen)  # GameManager 객체 생성

        # 배경 이미지 로드
        self.background = pygame.image.load('map2.png')
        self.background = pygame.transform.scale(self.background,
                                                 (screen_width, screen_height))

        # 스프라이트 그룹 설정
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        self.all_sprites.add(self.boss)
        self.attacks = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.guards = pygame.sprite.Group()

    def run(self):
        global screen
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        if self.player.is_awakened and random.random(
                        ) < 0.15:  # 15% 확률로 큰 총알 발사
                            awaken_bullet = Awaken(self.player.rect.center,
                                                   self.boss.rect.center)
                            self.all_sprites.add(awaken_bullet)
                            self.attacks.add(awaken_bullet)
                        else:
                            attack = Attack(self.player.rect.center,
                                            self.boss.rect.center)
                            self.all_sprites.add(attack)
                            self.attacks.add(attack)
                    elif event.key == pygame.K_x and self.player.guard_cooldown_timer == 0:
                        guard = Guard(self.player)
                        self.all_sprites.add(guard)
                        self.guards.add(guard)
                        self.player.guard = guard
                        guard.is_guard = True
                        self.player.guard_cooldown_timer = 300  # 5초 쿨타임
                    elif event.key == pygame.K_r:
                        self.reset_game()  # 게임 리셋 함수 호출
                    elif event.key == pygame.K_q and self.playerui.player_current_energy == self.playerui.player_max_energy:
                        self.player.awaken()  # 각성 모드 활성화
                        self.playerui.reset_energy()  # 에너지 초기화
                    elif event.key == pygame.K_ESCAPE:
                        running = False  # ESC 키로 종료
                        pygame.display.init()
                        screen = pygame.display.set_mode(
                            (screen_width, screen_height),
                            pygame.FULLSCREEN)  # ESC 키를 누르면 게임 종료

                self.manager.handle_event(
                    event, self)  # GameManager의 handle_event 메서드 호출 추가

            # 게임 상태 확인
            self.manager.check_game_state(self.player, self.boss)
            if self.manager.game_over:
                self.manager.show_game_over()
                pygame.time.wait(3000)  # 3초 대기 후 종료
                continue
            elif self.manager.game_clear:
                self.manager.show_game_clear()
                pygame.time.wait(3000)  # 3초 대기 후 종료
                continue

            # 플레이어 공격과 보스의 충돌 감지
            hits = pygame.sprite.spritecollide(self.boss, self.attacks, True)
            for hit in hits:
                for _ in range(20):  # 파티클의 수
                    particle = Attack_particle(hit.rect.center)
                    self.all_sprites.add(particle)
                    self.particles.add(particle)
                self.boss.hp(self.player.damage)
                self.playerui.increase_energy(10)  # 에너지 증가
                if isinstance(hit, Awaken):
                    self.boss.hp(hit.damage)  # Awaken 총알의 피해 적용
                else:
                    self.boss.hp(self.player.damage)

            # 플레이어와 보스 총알의 충돌 감지
            player_hits = pygame.sprite.spritecollide(self.player,
                                                      self.boss.bullets, True)
            for hit in player_hits:
                for _ in range(20):  # 파티클의 수
                    particle = Hit_particle(hit.rect.center)
                    self.all_sprites.add(particle)
                    self.particles.add(particle)
                if not self.player.is_invincible:  # 플레이어가 무적 상태가 아닐 때만 피해를 받음
                    if self.player.guard is None or not self.player.guard.is_guard:
                        self.player.player_hp(self.boss.boss_damage)
                    else:
                        hit.kill()  # 총알을 제거

            if self.player.guard_cooldown_timer > 0:
                self.player.guard_cooldown_timer -= 1

            self.boss.bullets.update()
            self.player.update()
            self.attacks.update()
            self.particles.update()
            self.playerui.update()

            # 화면을 흰색으로 채우는 대신 배경 이미지 그리기
            screen.blit(self.background, (0, 0))

            self.boss.update(self.player, self.boss.bullets)  # 보스 업데이트
            self.boss.draw()  # 보스 그리기
            self.boss.draw_pattern_text()  # 보스 패턴 텍스트 그리기

            self.all_sprites.draw(screen)

            self.playerui.image = self.playerui.player_ui()
            screen.blit(self.playerui.image, self.playerui.rect)

            self.player.draw(screen)  # 각성 오오라 그리기

            pygame.display.flip()
            clock.tick(60)

        pygame.display.quit()
        pygame.display.init()
        screen = pygame.display.set_mode((screen_width, screen_height),
                                         pygame.FULLSCREEN)

        pygame.quit()
        sys.exit()

    def reset_game(self):
        self.player = Player()
        self.boss = Boss()
        self.playerui = PlayerUI(self.player)  # Player 객체 전달
        self.all_sprites.empty()
        self.attacks.empty()
        self.particles.empty()
        self.guards.empty()
        self.all_sprites.add(self.player)
        self.all_sprites.add(self.boss)

    def draw_guard_icon(self):
        # 방어막 쿨타임이 0일 때 아이콘을 밝게 표시
        if self.player.guard_cooldown_timer == 0:
            icon_color = guard_color
        else:
            return  # 쿨타임 중에는 아이콘을 표시하지 않음

        icon_radius = 20
        icon_surface = pygame.Surface((icon_radius * 2, icon_radius * 2),
                                      pygame.SRCALPHA)
        pygame.draw.circle(icon_surface, icon_color,
                           (icon_radius, icon_radius), icon_radius)
        icon_position = (screen_width - icon_radius * 2 - 10,
                         screen_height - icon_radius * 2 - 10)  # 오른쪽 하단 위치
        screen.blit(icon_surface, icon_position)


if __name__ == "__main__":
    # 파이게임 초기화
    pygame.init()

    # 원하는 스크린 크기 설정
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h
    screen_resolution = (screen_width, screen_height)

    # 스크린 초기화 (풀스크린)
    screen = pygame.display.set_mode(screen_resolution, pygame.FULLSCREEN)

    # 스타트 화면 생성
    game_start = GameStart(screen)
    game_started = False

    # 스타트 화면 루프
    while not game_started:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if game_start.handle_event(event):
                game_started = True

        game_start.draw()

    # 게임 실행
    game = Game()
    game.run()
