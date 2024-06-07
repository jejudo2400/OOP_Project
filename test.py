import pygame
import math
import sys
import random

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
yellow = (255, 255, 0)

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
        self.cooldown_timer = 0

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
        if keys[pygame.K_c] and not self.is_dashing and self.cooldown_timer == 0:
            self.is_dashing = True
            self.dash_timer = self.dash_duration
        
        self.rect.x += move_x
        self.rect.y += move_y
        
        if self.is_dashing:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.cooldown_timer = self.dash_cooldown
        
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

# 보스 총알 클래스 정의
class BossBullet:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = 100 / 60  # FPS는 게임의 프레임 수를 나타내는 변수입니다.
        self.size = 16  # 캐릭터의 절반 크기

    def update(self):
        self.x += self.speed * math.cos(self.direction)
        self.y += self.speed * math.sin(self.direction)

    def draw(self):
        pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.size)

# 공격 클래스 정의
class Attack(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill(white)
        self.rect = self.image.get_rect()
        self.rect.center = start_pos
        self.speed = 10
        angle = math.atan2(target_pos[1] - start_pos[1], target_pos[0] - start_pos[0])
        self.dx = self.speed * math.cos(angle)
        self.dy = self.speed * math.sin(angle)

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

# 보스 클래스 정의
class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill(red)
        self.rect = self.image.get_rect()
        self.rect.midtop = (screen_width // 2, 0)
        self.bullets = []
        self.current_pattern = random.choice([1, 2])
        self.pattern_timer = 0
        self.pattern_text = ""
        self.p1_cnt = 0
        self.p2_cnt = 0

    def pattern1(self, player, bullets_group):
        if self.pattern_timer == 0:
            self.pattern_text = "pattern1"
            for _ in range(10):
                direction = random.uniform(0, 2 * math.pi)
                bullet = BossBullet(self.rect.centerx, self.rect.centery, direction)
                bullets_group.append(bullet)
            # self.pattern_timer = 60  # 패턴 지속 시간 변경 제거

    def pattern2(self, player, bullets_group):
        if self.pattern_timer == 0:
            self.pattern_text = "pattern2"
            target = (player.rect.centerx, player.rect.centery)
            direction = math.atan2(target[1] - self.rect.centery, target[0] - self.rect.centerx)
            bullet = BossBullet(self.rect.centerx, self.rect.centery, direction)
            bullets_group.append(bullet)
            # self.pattern_timer = 60  # 패턴 지속 시간 변경 제거

    def update(self, player, bullets_group):
        if self.pattern_timer > 0:
            self.pattern_timer -= 1
        else:
            self.current_pattern = random.choice([1, 2])
            self.pattern_timer = 60  # 패턴 지속 시간 변경

        if self.current_pattern == 1:
            self.pattern1(player, bullets_group)
            # self.p1_cnt = 0
            
        elif self.current_pattern == 2:
            self.pattern2(player, bullets_group)
            # self.p2_cnt = 0

    def draw(self):
        screen.blit(self.image, self.rect)
        for bullet in self.bullets:
            bullet.draw()

    def draw_pattern_text(self):
        if self.pattern_text:
            text_surface = font.render(self.pattern_text, True, white)
            screen.blit(text_surface, (10, 10))

# 파티클 클래스 정의
class Particle(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((5, 5))
        self.image.fill(yellow)
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
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)
        self.all_sprites.add(self.boss)
        self.attacks = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()

    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        attack = Attack(self.player.rect.center, self.boss.rect.center)
                        self.all_sprites.add(attack)
                        self.attacks.add(attack)

            # 공격과 보스의 충돌 감지
            hits = pygame.sprite.spritecollide(self.boss, self.attacks, True)
            for hit in hits:
                for _ in range(20):  # 파티클의 수
                    particle = Particle(hit.rect.center)
                    self.all_sprites.add(particle)
                    self.particles.add(particle)

            screen.fill(black)

            # 플레이어와 공격 업데이트
            self.player.update()
            self.attacks.update()
            self.particles.update()

            # 보스 업데이트
            self.boss.update(self.player, self.boss.bullets)

            # 보스 총알 업데이트
            for bullet in self.boss.bullets:
                bullet.update()

            # 그리기
            self.boss.draw()
            self.boss.draw_pattern_text()
            self.all_sprites.draw(screen)
            
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
