import pygame
import math
import sys

# 기본 설정
pygame.init()

# 화면 설정 (비율 4:3)
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("탄막 게임")

# 색상 설정
black = (0, 0, 0)
red = (255, 0, 0)
white = (255, 255, 255)

# 보스 클래스 정의
class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill(red)
        self.rect = self.image.get_rect()
        self.rect.midtop = (screen_width // 2, 50)
        self.bullets = pygame.sprite.Group()
        self.shoot_interval = 30  # 탄을 발사하는 간격 (프레임 수)
        self.shoot_timer = 0

    def update(self):
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot()
            self.shoot_timer = self.shoot_interval

    def shoot(self):
        for angle in range(0, 181, 10):
            direction = math.radians(angle)
            bullet = Bullet(self.rect.centerx, self.rect.centery, direction)
            self.bullets.add(bullet)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        self.bullets.draw(screen)

# 탄환 클래스 정의
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(white)
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.speed = 5

    def update(self):
        self.rect.x += self.speed * math.cos(self.direction)
        self.rect.y += self.speed * math.sin(self.direction)
        if not screen.get_rect().contains(self.rect):
            self.kill()

# 게임 클래스 정의
class Game:
    def __init__(self):
        self.boss = Boss()
        self.all_sprites = pygame.sprite.Group(self.boss)

    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.all_sprites.update()
            self.boss.bullets.update()

            screen.fill(black)
            self.all_sprites.draw(screen)
            self.boss.draw(screen)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
