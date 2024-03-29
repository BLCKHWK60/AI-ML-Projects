import math
from time import process_time
from random import uniform, randint, choice

import pygame


def init():
    pygame.init()
    pygame.font.init()


class MarsLander:
    def __init__(self, fps=20, width=1200, height=750):
        self.screen = pygame.display.set_mode((width, height))
        self.process_time = pygame.time.Clock()
        self.FPS = fps
        self.regular_font = pygame.font.SysFont('Comic Sans MS', 15)
        self.alert_font = pygame.font.SysFont('Comic Sans MS', 18)
        self.large_font = pygame.font.SysFont('Comic Sans MS', 50)

        self.score = 0
        self.lives = 3

        self.obstacles = pygame.sprite.Group()
        self.meteors = pygame.sprite.Group()
        self.landing_pads = pygame.sprite.Group()
        self.background = Sprite('mars_background_instr.png', 0, 0)

        self.lander = Lander(width)
        self.height = height

        # Create sprites for landing pads and add them to the pads group
        # TODO have coordinates dependent on actual width and height
        Sprite('pad.png', 732, randint(858, 1042)).add(self.landing_pads)
        Sprite('pad_tall.png', 620, randint(458, 700)).add(self.landing_pads)
        Sprite('pad.png', 650, randint(0, 300)).add(self.landing_pads)

        self.reset_obstacles()
        self.create_new_storm()
        self.create_new_alert()

    @property
    def game_over(self):
        return self.lives < 1

    def reset_obstacles(self):
        """Create obstacles at a fixed location and add the to the obstacles group"""
        # TODO have coordinates dependent on actual width and height

        self.obstacles.empty()
        Sprite('pipe_ramp_NE.png', 540, 90).add(self.obstacles)
        Sprite('building_dome.png', 575, 420).add(self.obstacles)
        Sprite('satellite_SW.png', 435, 1150).add(self.obstacles)
        Sprite('rocks_ore_SW.png', 620, 1080).add(self.obstacles)
        Sprite('building_station_SW.png', 640, 850).add(self.obstacles)

    def create_new_storm(self, number_of_images=4):
        """Create meteors and add the to the meteors group"""
        # TODO have coordinates dependent on actual width and height

        now = int(process_time())
        self.random_storm = randint(now + 3, now + 12)

        self.meteors.empty()
        for i in range(randint(1, 10)):
            image_name = 'spaceMeteors_{}.png'.format(randint(1, number_of_images))
            Meteor(image_name, -2 * i * self.FPS, randint(300, 900)).add(self.meteors)

    def create_new_alert(self):
        self.random_alert = randint(int(process_time() + 5), int(process_time() + 15))
        self.alert_key = choice((pygame.K_SPACE, pygame.K_LEFT, pygame.K_RIGHT))

    def draw_text(self, message, position, color=(255, 0, 0)):
        text = self.regular_font.render(message, False, color)
        self.screen.blit(text, position)

    def run(self):
        meteor_storm = False  # Set to True whenever a storm should occur

        while not self.game_over:
            self.process_time.tick(self.FPS)

            # If the user clicks the 'X' button on the window it quits the program
            if any(event.type == pygame.QUIT for event in pygame.event.get()):
                return

            self.screen.fill([255, 255, 255])  # Fill the empty spaces with white color
            self.screen.blit(self.background.image, self.background.rect)  # Place the background image
            self.landing_pads.draw(self.screen)
            self.obstacles.draw(self.screen)

            # Check for collisions with obstacles and remove hit ones
            obstacles_hit = pygame.sprite.spritecollide(self.lander, self.obstacles, True)
            self.lander.damage += 10 * len(obstacles_hit)

            pressed_key = pygame.key.get_pressed()  # Take pressed key value

            if not meteor_storm and process_time() > self.random_storm:
                # As soon as the clock passes the random storm time it causes meteor rain
                meteor_storm = True

            if meteor_storm:
                self.meteors.update()
                self.meteors.draw(self.screen)

                # Check for collisions with meteors and remove hit ones
                meteors_hit = pygame.sprite.spritecollide(self.lander, self.meteors, True)
                self.lander.damage += 25 * len(meteors_hit)

            if pressed_key[pygame.K_ESCAPE]:  # Stop game if the 'Esc' button is pressed
                return

            if self.random_alert < process_time() < self.random_alert + 2:
                alert_msg = self.large_font.render('*ALERT*', False, (0, 0, 255))
                self.screen.blit(alert_msg, (190, 80))
                thrust = self.lander.handle_inputs(pressed_key, self.alert_key)
            else:
                thrust = self.lander.handle_inputs(pressed_key)
            if thrust:
                self.screen.blit(thrust.rot_image, thrust.rect)
            self.screen.blit(self.lander.rot_image, self.lander.rect)

            self.draw_text('{:1.0f} s'.format(process_time()), (72, 10))
            self.draw_text('{:.1f} m/s'.format(self.lander.veloc_y), (280, 56))
            self.draw_text('{:.1f} m/s'.format(self.lander.veloc_x), (280, 33))
            self.draw_text('{:d} kg'.format(self.lander.fuel), (72, 33))
            self.draw_text('{:.0f} m'.format(self.lander.altitude), (280, 10))
            self.draw_text('{} %'.format(self.lander.damage), (95, 56))
            self.draw_text('{:.0f} pts'.format(self.score), (77, 82))

            self.lander.free_fall()
            pygame.display.update()

            landing_pad_reached = pygame.sprite.spritecollideany(self.lander, self.landing_pads)
            if landing_pad_reached or self.lander.rect.bottom > self.height:
                self.create_new_alert()
                self.create_new_storm()
                self.reset_obstacles()
                meteor_storm = False
                if landing_pad_reached and self.lander.has_landing_position():
                    self.score += 50
                else:
                    self.lives -= 1
                    should_exit = self.show_crash()
                    if should_exit:
                        return
                self.lander.reset_stats()

    def show_crash(self):
        """Display crash message in the middle of the screen and wait for a key press"""
        crash_msg = self.large_font.render('You Have Crashed!', False, (255, 0, 0))
        self.screen.blit(crash_msg, (420, 300))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Quit the game if the 'X' button is clicked
                    return True
                if event.type == pygame.KEYDOWN:
                    # Wait for a key to be pressed and if so resumes the game
                    return False

            pygame.display.update()
            self.process_time.tick(self.FPS)


class Sprite(pygame.sprite.Sprite):
    def __init__(self, image_file, top, left):
        super().__init__()
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect()
        self.rect.top = top
        self.rect.left = left


class EngineThrust(Sprite):  # class for the thrust image
    def __init__(self, lander_rect, lander_angle):
        super().__init__('thrust.png', lander_rect.bottom - 10, lander_rect.left + 31)
        self.rot_image = pygame.transform.rotate(self.image, lander_angle)


class Meteor(Sprite):
    def __init__(self, image_file, top, left):
        super().__init__(image_file, top, left)
        self.speed_y = uniform(5, 10)
        self.speed_x = uniform(-2, 2)

    def update(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y


class Lander(Sprite):
    def __init__(self, width):
        super().__init__('lander.png', 0, 0)
        self.width = width
        self.reset_stats()

    def reset_stats(self):
        self.rect.top = 0
        self.rect.left = randint(0, self.width - self.rect.width)
        self.veloc_y = uniform(0.0, 1.0)
        self.veloc_x = uniform(-1.0, 1.0)
        self.fuel = 500
        self.angle = 0
        self.damage = 0
        self.rot_image = self.image

    def free_fall(self):
        self.rect.y += self.veloc_y
        self.rect.x += self.veloc_x
        self.veloc_y += 0.1

        if self.rect.top < 0:
            self.rect.top = 0
            self.veloc_y = uniform(0.0, 1.0)

        if self.rect.right < 0:
            self.rect.left = self.width

        if self.rect.left > self.width:
            self.rect.right = 0

    def start_engine(self):
        self.fuel -= 5
        self.veloc_x = self.veloc_x + 0.33 * math.sin(math.radians(-self.angle))
        self.veloc_y = self.veloc_y - 0.33 * math.cos(math.radians(self.angle))

    @property
    def altitude(self):
        return 1000 - self.rect.top * 1.436

    @property
    def can_land(self):
        return self.fuel > 0 and self.damage < 100

    def has_landing_position(self):
        return self.can_land and (self.veloc_y < 5) and (-5 < self.veloc_x < 5) and (-7 <= self.angle <= 7)

    def handle_inputs(self, pressed_key, alert_key=None):
        if not self.can_land:
            return

        thrust = None
        rotated = False
        if alert_key != pygame.K_SPACE and pressed_key[pygame.K_SPACE]:
            # Show thrust image when 'space' is pressed
            thrust = EngineThrust(self.rect, self.angle)
            self.start_engine()

        if alert_key != pygame.K_LEFT and pressed_key[pygame.K_LEFT]:
            # Rotate lander anticlockwise when 'left' is pressed
            self.angle += 1
            rotated = True

        if alert_key != pygame.K_RIGHT and pressed_key[pygame.K_RIGHT]:
            # Rotate lander clockwise when 'left' is pressed
            self.angle -= 1
            rotated = True

        if rotated:
            self.angle %= 360
            self.rot_image = pygame.transform.rotate(self.image, self.angle)

        return thrust


if __name__ == '__main__':
    init()
    game = MarsLander()
    game.run()
    pygame.quit()