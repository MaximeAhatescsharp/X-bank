import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1100, 700
LINE_WIDTH = 600
LINE_HEIGHT = 20
LINE_Y = HEIGHT // 2
CURSOR_WIDTH = 10

# Padding and dimensions
DASHBOARD_WIDTH = 300
DASHBOARD_PADDING = 20
LINE_PADDING = 40  # Space between line and dashboard

# Colors
BG_COLOR = (24, 26, 27)
LINE_COLOR = (43, 47, 50)
GREEN_COLOR = (0, 204, 102)
RED_COLOR = (220, 20, 60)
CURSOR_COLOR = (128, 128, 128)
TEXT_COLOR = (255, 255, 255)
HIDDEN_COLOR = (24, 24, 24)

# Fonts
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 28)

# Sounds
slide_sound = pygame.mixer.Sound("audios/slide.mp3")
arrow_sound = pygame.mixer.Sound("audios/arrow.mp3")
win_sound = pygame.mixer.Sound("audios/win.mp3")
lose_sound = pygame.mixer.Sound("audios/lose.mp3")
bet_sound = pygame.mixer.Sound("audios/bet.mp3")

# Set volume for sounds
slide_sound.set_volume(0.5)
arrow_sound.set_volume(0.5)
win_sound.set_volume(0.5)
lose_sound.set_volume(0.5)

# Conversion rates
conversion_rates = {
    "BTC": 1,
    "ETH": 15,
    "USD": 100000,
    "EUR": 93565,
}

class Button:
    def __init__(self, x, y, width, height, text, action=None, enabled=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.enabled = enabled
        self.hovered = False

    def draw(self, screen):
        color = CURSOR_COLOR if self.hovered else GREEN_COLOR if self.enabled else RED_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        text_surface = small_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)

    def handle_click(self, pos):
        if self.enabled and self.is_hovered(pos) and self.action:
            self.action()

class Dropdown:
    def __init__(self, x, y, width, height, options, selected_index=0, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = selected_index
        self.expanded = False
        self.action = action

    def draw(self, screen):
        pygame.draw.rect(screen, GREEN_COLOR, self.rect, border_radius=8)
        selected_option = self.options[self.selected_index]
        text_surface = small_font.render(selected_option, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

        if self.expanded:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                pygame.draw.rect(screen, GREEN_COLOR, option_rect, border_radius=8)
                option_text = small_font.render(option, True, TEXT_COLOR)
                option_text_rect = option_text.get_rect(center=option_rect.center)
                screen.blit(option_text, option_text_rect)

    def handle_click(self, pos):
        if self.expanded:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                if option_rect.collidepoint(pos):
                    self.selected_index = i
                    self.expanded = False
                    if self.action:
                        self.action(self.options[self.selected_index])
                    return
        if self.rect.collidepoint(pos):
            self.expanded = not self.expanded

class StakeDiceGame:
    def __init__(self, balance):
        self.balance = balance
        self.bet_amount = 0.00001
        self.reward = 0
        self.cursor_pos = LINE_PADDING + LINE_WIDTH // 2  # Center the cursor on the line
        self.currency = "EUR"
        self.holding_cursor = False

        # UI Elements
        button_width, button_height = 150, 40
        button_x = WIDTH - DASHBOARD_WIDTH + DASHBOARD_PADDING
        self.dropdown = Dropdown(940, DASHBOARD_PADDING, button_width, button_height, ["BTC", "ETH", "USD", "EUR"], action=self.change_currency)
        self.buttons = {
            "bet": Button(button_x, DASHBOARD_PADDING + 80, button_width, button_height, "Bet", self.bet),
            "increase_bet": Button(button_x, DASHBOARD_PADDING + 140, button_width, button_height, "+ Bet", lambda: self.change_bet(0.0001)),
            "decrease_bet": Button(button_x, DASHBOARD_PADDING + 200, button_width, button_height, "- Bet", lambda: self.change_bet(-0.0001)),
        }

    def draw_line(self, screen):
        """Draw the main horizontal line with red and green sides."""
        line_start_x = LINE_PADDING
        line_end_x = line_start_x + LINE_WIDTH

        mid_x = self.cursor_pos  # Midpoint divides red and green sections
        pygame.draw.line(screen, RED_COLOR, (line_start_x, LINE_Y), (mid_x, LINE_Y), LINE_HEIGHT)
        pygame.draw.line(screen, GREEN_COLOR, (mid_x, LINE_Y), (line_end_x, LINE_Y), LINE_HEIGHT)

    def draw_cursor(self, screen):
        """Draw the cursor on the line."""
        cursor_rect = pygame.Rect(self.cursor_pos - CURSOR_WIDTH // 2, LINE_Y - LINE_HEIGHT // 2 - 20, CURSOR_WIDTH, LINE_HEIGHT + 40)
        pygame.draw.rect(screen, CURSOR_COLOR, cursor_rect, border_radius=8)
        percentage = (self.cursor_pos - LINE_PADDING) / LINE_WIDTH * 100
        text_surface = font.render(f"{percentage:.1f}%", True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(self.cursor_pos, LINE_Y - 40))
        screen.blit(text_surface, text_rect)

    def calculate_reward(self, chance):
        """Calculate the reward based on the chance."""
        # Slightly less than bet amount at 50%
        if chance == 50:
            return self.bet_amount * 0.9
        if chance != 0:
            return (self.bet_amount / (chance / 105)) / 2
        else:
            return 0

    def bet(self):
        """Handle the betting logic."""
        if self.bet_amount > self.balance:
            print("Cannot bet more than your current balance!")
            return

        arrow_pos = random.randint(LINE_PADDING, LINE_PADDING + LINE_WIDTH)
        arrow_sound.play()

        pygame.draw.line(screen, CURSOR_COLOR, (arrow_pos, LINE_Y - LINE_HEIGHT // 2 - 20), (arrow_pos, LINE_Y + LINE_HEIGHT // 2 + 20), 5)
        pygame.display.flip()
        pygame.time.wait(1000)

        chance = ((LINE_PADDING + LINE_WIDTH) - self.cursor_pos) / LINE_WIDTH * 100
        potential_reward = self.calculate_reward(chance)

        if arrow_pos > self.cursor_pos:
            win_sound.play()
            self.reward = potential_reward
            self.balance += self.reward
            print(f"Win! Reward: {self.reward:.2f} {self.currency}")
        else:
            lose_sound.play()
            self.balance -= self.bet_amount
            print("Lose!")

        self.reward = 0

    def change_bet(self, amount):
        """Increase or decrease the bet amount."""
        new_bet = max(0.001, self.bet_amount + amount)
        if new_bet > self.balance:
            print("Cannot bet more than your current balance!")
        else:
            self.bet_amount = new_bet

    def change_currency(self, currency):
        self.currency = currency

    def convert_currency(self, amount):
        return amount * conversion_rates[self.currency]

    def draw(self, screen):
        screen.fill(BG_COLOR)
        self.draw_line(screen)
        self.draw_cursor(screen)
        self.draw_interface(screen)

    def draw_interface(self, screen):
        pygame.draw.rect(screen, HIDDEN_COLOR, (WIDTH - DASHBOARD_WIDTH, 0, DASHBOARD_WIDTH, HEIGHT))  # Adjusted dashboard size

        balance_text = f"Balance: {self.convert_currency(self.balance):.2f} {self.currency}"
        bet_text = f"Bet Amount: {self.convert_currency(self.bet_amount):.2f} {self.currency}"
        chance = ((LINE_PADDING + LINE_WIDTH) - self.cursor_pos) / LINE_WIDTH * 100
        potential_reward = self.calculate_reward(chance)
        chance_text = f"Chance (Green): {chance:.1f}%"
        potential_reward_text = f"Recompense: {self.convert_currency(potential_reward):.2f} {self.currency}"

        y_offset = DASHBOARD_PADDING + 300
        spacing = 50
        for idx, text in enumerate([balance_text, bet_text, chance_text, potential_reward_text]):
            text_surface = font.render(text, True, TEXT_COLOR)
            screen.blit(text_surface, (WIDTH - DASHBOARD_WIDTH + DASHBOARD_PADDING, y_offset + idx * spacing))

        self.dropdown.draw(screen)
        for button in self.buttons.values():
            button.draw(screen)

    def run(self):
        """Main game loop."""
        global screen
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Stake Dice Game")
        clock = pygame.time.Clock()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if LINE_PADDING <= pos[0] <= LINE_PADDING + LINE_WIDTH and LINE_Y - LINE_HEIGHT // 2 <= pos[1] <= LINE_Y + LINE_HEIGHT // 2:
                        self.holding_cursor = True
                        bet_sound.play()
                    else:
                        for button in self.buttons.values():
                            button.handle_click(pos)
                        self.dropdown.handle_click(pos)
                if event.type == pygame.MOUSEBUTTONUP:
                    self.holding_cursor = False

            if self.holding_cursor:
                pos = pygame.mouse.get_pos()
                self.cursor_pos = max(LINE_PADDING, min(pos[0], LINE_PADDING + LINE_WIDTH))

            for button in self.buttons.values():
                button.hovered = button.is_hovered(pygame.mouse.get_pos())

            self.draw(screen)
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()


def run_dice(balance):
    return StakeDiceGame(balance)

