import pygame
pygame.init()

# --- Window Setup ---
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Knightlike Prototype v2")
clock = pygame.time.Clock()

# --- Constants ---
GRAVITY = 0.6
MOVE_SPEED = 5
JUMP_FORCE = 12
DASH_FORCE = 14
DASH_COOLDOWN = 600  # ms
WALL_SLIDE_SPEED = 2.5
PLAYER_SIZE = (40, 60)
CAMERA_LAG = 0.08
CAMERA_ROTATE_STRENGTH = 4

# --- Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface(PLAYER_SIZE)
        self.image.fill((80, 80, 220))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel = pygame.Vector2(0, 0)
        self.facing = 1
        self.grounded = False
        self.can_dash = True
        self.last_dash = 0
        self.on_wall = False
        self.attacking = False
        self.attack_timer = 0

    def input(self, keys):
        self.vel.x = 0
        if keys[pygame.K_a]:
            self.vel.x = -MOVE_SPEED
            self.facing = -1
        if keys[pygame.K_d]:
            self.vel.x = MOVE_SPEED
            self.facing = 1

        # Jump
        if keys[pygame.K_SPACE]:
            if self.grounded:
                self.vel.y = -JUMP_FORCE
            elif self.on_wall:
                # Wall jump
                self.vel.y = -JUMP_FORCE
                self.vel.x = self.facing * -MOVE_SPEED * 1.2
                self.on_wall = False

        # Dash
        if keys[pygame.K_LSHIFT]:
            self.dash()

        # Attack
        if keys[pygame.K_j]:
            self.attack()

    def dash(self):
        now = pygame.time.get_ticks()
        if now - self.last_dash > DASH_COOLDOWN:
            self.vel.x = DASH_FORCE * self.facing
            self.vel.y *= 0.3  # reduce vertical speed
            self.last_dash = now

    def attack(self):
        if not self.attacking:
            self.attacking = True
            self.attack_timer = pygame.time.get_ticks()

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        self.input(keys)

        # Apply gravity
        self.vel.y += GRAVITY
        self.rect.x += self.vel.x
        self.collision(platforms, 'x')
        self.rect.y += self.vel.y
        self.collision(platforms, 'y')

        # End attack
        if self.attacking and pygame.time.get_ticks() - self.attack_timer > 300:
            self.attacking = False

    def collision(self, platforms, dir):
        self.on_wall = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if dir == 'x':
                    if self.vel.x > 0:
                        self.rect.right = p.rect.left
                        if not self.grounded and self.vel.y > 0:
                            self.wall_slide()
                    elif self.vel.x < 0:
                        self.rect.left = p.rect.right
                        if not self.grounded and self.vel.y > 0:
                            self.wall_slide()
                    self.vel.x = 0
                elif dir == 'y':
                    if self.vel.y > 0:
                        self.rect.bottom = p.rect.top
                        self.grounded = True
                    elif self.vel.y < 0:
                        self.rect.top = p.rect.bottom
                    self.vel.y = 0
                    return
        self.grounded = False

    def wall_slide(self):
        self.on_wall = True
        self.vel.y = WALL_SLIDE_SPEED

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill((220, 60, 60))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = 3

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            self.kill()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((100, 100, 100))
        self.rect = self.image.get_rect(topleft=(x, y))

# --- Setup World ---
player = Player(100, 300)
enemy = Enemy(500, 380)
platforms = pygame.sprite.Group(
    Platform(0, 500, 1000, 40),
    Platform(300, 400, 100, 20),
    Platform(700, 350, 100, 20)
)
entities = pygame.sprite.Group(player, enemy, *platforms)

camera = pygame.Vector2(0, 0)
camera_angle = 0

# --- Game Loop ---
running = True
while running:
    dt = clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    player.update(platforms)

    # Attack detection
    if player.attacking:
        attack_rect = pygame.Rect(
            player.rect.centerx + player.facing * 40,
            player.rect.centery - 20,
            40, 40
        )
        if attack_rect.colliderect(enemy.rect):
            enemy.hit()

    # Camera target position & rotation
    target_x = player.rect.centerx - WIDTH/2 + player.facing * 100
    target_y = player.rect.centery - HEIGHT/2
    camera.x += (target_x - camera.x) * CAMERA_LAG
    camera.y += (target_y - camera.y) * CAMERA_LAG
    target_angle = player.vel.x * CAMERA_ROTATE_STRENGTH * 0.02
    camera_angle += (target_angle - camera_angle) * CAMERA_LAG

    # --- Draw ---
    screen.fill((25, 25, 35))

    # Create camera surface for subtle rotation effect
    cam_surf = pygame.Surface((WIDTH, HEIGHT))
    cam_surf.fill((25, 25, 35))

    for entity in entities:
        offset_rect = entity.rect.move(-camera.x, -camera.y)
        cam_surf.blit(entity.image, offset_rect)

    if player.attacking:
        pygame.draw.rect(cam_surf, (255, 255, 0), attack_rect.move(-camera.x, -camera.y), 1)

    # Apply camera rotation
    rotated = pygame.transform.rotate(cam_surf, -camera_angle)
    r_rect = rotated.get_rect(center=(WIDTH//2, HEIGHT//2))
    screen.blit(rotated, r_rect.topleft)

    pygame.display.flip()

pygame.quit()
