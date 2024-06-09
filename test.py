import pygame
import math
import sys
import random
import time

# 기본 설정
pygame.init()

# 화면 설정 (비율 4:3)
screen_width = 1200
screen_height = 900
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("쿼터뷰 예제")

# 색상 설정
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
attack_particle_color = (255, 100, 100)
hit_particle_color = (255, 255, 0)
bullet_glow = (255, 87, 87)
guard_color = (149, 242, 255, 128)
dim_guard_color = (75, 121, 128, 128)

# 폰트 설정
font = pygame.font.Font(None, 36)


# 플레이어 클래스 정의
class Player(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(red)
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
        
        #플레이어 공격력 설정
        self.damage = 100

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

        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= 1

        if self.guard:
            self.guard.update()


# 방어막 클래스 정의
class Guard(pygame.sprite.Sprite):

    def __init__(self, player):
        super().__init__()
        self.player = player
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(self.image, guard_color, (20, 20), 20)
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
        glow_radius = 9

        # 총알과 후광을 그릴 Surface 생성
        surface = pygame.Surface((glow_radius * 2, glow_radius * 2),
                                 pygame.SRCALPHA)
        surface = surface.convert_alpha()

        # 후광 그리기
        for alpha in range(glow_radius, 0, -1):
            pygame.draw.circle(surface,
                               (bullet_glow[0], bullet_glow[1], bullet_glow[2],
                                float(255 * (alpha / glow_radius))),
                               (glow_radius, glow_radius), alpha)

        # 총알 그리기
        pygame.draw.circle(surface, white, (glow_radius, glow_radius),
                           bullet_size // 2)

        return surface

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if not screen.get_rect().contains(self.rect):
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill((255, 0, 0))  # 빨간색
        self.rect = self.image.get_rect()
        self.rect.midtop = (screen_width // 2, 50)
        self.bullets = pygame.sprite.Group()
    
        # 패턴 관련 변수 추가
        self.current_pattern = 0
        self.pattern_timer = 0
        self.pattern_text = ""
        self.pattern1_interval = 18  # 0.3초 (18 프레임) 대기 시간
        self.pattern1_step = 0
        self.pattern1_angles = [i for i in range(0, 181, 5)]  # 0도에서 360도까지 45도씩 증가
        self.pattern1_repeat = 0

        self.pattern2_target = None
        self.pattern2_prepare_timer = 30  # 1초 준비 시간

        # 체력바 관련
        self.max_health = 100
        self.current_health = self.max_health

    def pattern1(self, bullets_group):
        if self.pattern_timer == 0:
            if self.pattern1_step == 0:
                self.pattern_text = "Pattern1_Spreadshoot"
                # 첫 번째 흩뿌리기
                for angle in self.pattern1_angles:
                    direction = math.radians(angle)
                    bullet = BossBullet(self.rect.centerx, self.rect.centery, direction)
                    bullets_group.add(bullet)
                self.pattern1_step = 1
                self.pattern_timer = self.pattern1_interval
            elif self.pattern1_step == 1:
                # 첫 번째 흩뿌린 각도의 사이로 다시 흩뿌리기
                for angle in self.pattern1_angles:
                    new_angle = angle + 22.5
                    direction = math.radians(new_angle)
                    bullet = BossBullet(self.rect.centerx, self.rect.centery, direction)
                    bullets_group.add(bullet)
                self.pattern1_step = 0
                self.pattern_timer = self.pattern1_interval
                self.pattern1_repeat += 1

            # 패턴 반복이 2번 완료되면 종료
            if self.pattern1_repeat >= 1:
                self.pattern1_repeat = 0
                self.current_pattern = 0
        else:
            self.pattern_timer -= 1

    def pattern2(self, player, bullets_group):
        if self.pattern2_prepare_timer > 0:
            # 플레이어 위치 저장
            if self.pattern2_target is None:
                self.pattern2_target = player.rect.center

            # 보스와 플레이어를 잇는 선을 화면 끝까지 연장
            start_pos = self.rect.center
            target_pos = self.pattern2_target

            direction = pygame.Vector2(target_pos[0] - start_pos[0], target_pos[1] - start_pos[1]).normalize()
            end_pos = (start_pos[0] + direction.x * screen_width, start_pos[1] + direction.y * screen_height)

            # 보스와 플레이어를 잇는 선 그리기
            pygame.draw.line(screen, (255, 0, 0), start_pos, end_pos, 2)

            # 준비 시간이 끝나면 탄환 발사
            self.pattern2_prepare_timer -= 1
            if self.pattern2_prepare_timer == 0:
                self.pattern_text = "Pattern2_Sniping"
                bullet_direction = math.atan2(target_pos[1] - self.rect.centery, target_pos[0] - self.rect.centerx)
                bullet = BossBullet(self.rect.centerx, self.rect.centery, bullet_direction)
                bullet.speed = 30  # 빠른 탄환 속도 설정
                bullets_group.add(bullet)

                # 패턴2 종료
                self.pattern2_target = None
                self.pattern2_prepare_timer = 60
                self.current_pattern = 0  # 패턴 종료
        else:
            self.pattern2_prepare_timer = 60  # 패턴 준비 시간 초기화

    def pattern3(self, player, bullets_group):
        if self.pattern_timer == 0:
            self.pattern_text = "Pattern3_HomingMissile"
            # 발사 위치를 보스의 중심으로 설정
            start_pos = self.rect.center

            for _ in range(5):  # 5개의 유도탄 생성
                missile = HomingMissile(start_pos, player)
                bullets_group.add(missile)

            self.pattern_timer = 180  # 유도탄 발사 후 3초 대기
            self.current_pattern = 0
        else:
            self.pattern_timer -= 1

    def update(self, player, bullets_group):
        if self.current_health <= 0:
            self.image.set_alpha(0)

            # 필드에 있는 총알 소멸
            bullets_group.empty()
            return
        
        if self.current_pattern != 0:
            if self.current_pattern == 1:
                self.pattern1(bullets_group)
            elif self.current_pattern == 2:
                self.pattern2(player, bullets_group)
            elif self.current_pattern == 3:
                self.pattern3(player, bullets_group)
        else:
            if len(bullets_group) == 0:
                self.current_pattern = 3  # 패턴 3으로 고정
                self.pattern_timer = 60

    def draw(self):
        health_bar_width = screen_width  # 체력 바의 최대 너비
        health_ratio = self.current_health / self.max_health
        current_health_bar_width = health_bar_width * health_ratio
        pygame.draw.rect(screen, (255, 0, 0), (0, 20, current_health_bar_width, 20))  # 빨간색 체력 바

        screen.blit(self.image, self.rect)
        self.bullets.draw(screen)

    def draw_pattern_text(self):
        if self.pattern_text:
            text_surface = font.render(self.pattern_text, True, (255, 255, 255))
            screen.blit(text_surface, (10, 10))

    def hp(self, damage):
        self.current_health -= damage

class HomingMissile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target, max_homing_distance=100, speed=7):
        super().__init__()
        outer_bullet_size = 32  # 바깥 원의 크기
        inner_bullet_size = 25  # 안쪽 원의 크기

        # 총알의 모양을 그릴 Surface 생성
        self.image = pygame.Surface((outer_bullet_size, outer_bullet_size), pygame.SRCALPHA)
        self.image = self.image.convert_alpha()

        # 바깥 원 그리기 (초록색)
        pygame.draw.circle(self.image, (0, 255, 0), (outer_bullet_size // 2, outer_bullet_size // 2), outer_bullet_size // 2)

        # 안쪽 원 그리기 (하얀색)
        pygame.draw.circle(self.image, (255, 255, 255), (outer_bullet_size // 2, outer_bullet_size // 2), inner_bullet_size // 2)
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

            if math.hypot(target_x - missile_x, target_y - missile_y) <= self.max_homing_distance:
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
        self.image = pygame.Surface((outer_bullet_size, outer_bullet_size), pygame.SRCALPHA)
        self.image = self.image.convert_alpha()

        # 바깥 원 그리기 (빨간색)
        pygame.draw.circle(self.image, red, (outer_bullet_size // 2, outer_bullet_size // 2), outer_bullet_size // 2)

        # 안쪽 원 그리기 (하얀색)
        pygame.draw.circle(self.image, white, (outer_bullet_size // 2, outer_bullet_size // 2), inner_bullet_size // 2)

        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.speed = 7 # FPS는 게임의 프레임 수를 나타내는 변수입니다.

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


# 게임 클래스 정의
class Game:

    def __init__(self):
        self.player = Player()
        self.boss = Boss()

        # 스프라이트 그룹 설정
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        self.all_sprites.add(self.boss)
        self.attacks = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.guards = pygame.sprite.Group()
    
    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
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
                    elif event.key == pygame.K_ESCAPE:
                        running = False  # ESC 키를 누르면 게임 종료

            # 플레이어 공격과 보스의 충돌 감지
            hits = pygame.sprite.spritecollide(self.boss, self.attacks, True)
            for hit in hits:
                for _ in range(20):  # 파티클의 수
                    particle = Attack_particle(hit.rect.center)
                    self.all_sprites.add(particle)
                    self.particles.add(particle)
                self.boss.hp(self.player.damage)
            # 플레이어와 보스 총알의 충돌 감지
            player_hits = pygame.sprite.spritecollide(self.player,
                                                      self.boss.bullets, True)

            for hit in player_hits:
                for _ in range(20):  # 파티클의 수
                    particle = Hit_particle(hit.rect.center)
                    self.all_sprites.add(particle)
                    self.particles.add(particle)

            if self.player.guard_cooldown_timer > 0:
                self.player.guard_cooldown_timer -= 1

            self.boss.bullets.update()
            self.player.update()
            self.attacks.update()
            self.particles.update()

            # 화면 그리기
            screen.fill(black)
            self.boss.update(self.player, self.boss.bullets)

            # 유도 미사일을 all_sprites에 추가
            for missile in self.boss.bullets:
                if isinstance(missile, HomingMissile) and missile not in self.all_sprites:
                    self.all_sprites.add(missile)

            self.boss.draw()
            self.boss.draw_pattern_text()
            self.all_sprites.draw(screen)

            # 방어막 아이콘 그리기
            self.draw_guard_icon()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

    def reset_game(self):
        self.player = Player()
        self.boss = Boss()
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
    game = Game()
    game.run()
