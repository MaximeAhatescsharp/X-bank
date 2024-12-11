import pygame
import random
import sys

# Initialize Pygame

pygame.init()
# Screen dimensions
WIDTH, HEIGHT = 1100, 700
GRID_WIDTH = 700
GRID_HEIGHT = 700
ROWS, COLS = 5, 5  # Grid dimensions
CELL_SIZE = GRID_WIDTH // COLS

# Colors
BG_COLOR = (24, 26, 27)
GRID_BORDER_COLOR = (50, 50, 50)
HIGHLIGHT_COLOR = (72, 82, 90)  # For hover effects
DIAMOND_COLOR = (0, 204, 102)   # Green diamond
MINE_COLOR = (220, 20, 60)      # Bright red for mines
HIDDEN_COLOR = (43, 47, 50)     # Hidden cell
BUTTON_COLOR = (32, 178, 70)    # Green buttons
DISABLED_BUTTON_COLOR = (64, 64, 64)
TEXT_COLOR = (255, 255, 255)

# Fonts
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 28)

# Sounds
bet_sound = pygame.mixer.Sound("audios/bet.mp3")
click_sound = pygame.mixer.Sound("audios/click.mp3")
diamond_sound = pygame.mixer.Sound("audios/diamond.mp3")
mine_sound = pygame.mixer.Sound("audios/mine.mp3")
cashout_sound = pygame.mixer.Sound("audios/cashout.mp3")
hover_sound = pygame.mixer.Sound("audios/hover.mp3")

# Set volume for sounds
bet_sound.set_volume(0.5)
click_sound.set_volume(0.5)
diamond_sound.set_volume(0.5)
mine_sound.set_volume(0.5)
cashout_sound.set_volume(0.5)
hover_sound.set_volume(0.5)

# Game settings
DEFAULT_MINE_COUNT = 6
DEFAULT_BET = 0  # Default bet amount in BTC
MAX_MINES = ROWS * COLS - 1

# Conversion rates
conversion_rates = {
    "BTC": 1,
    "ETH": 15,
    "USD": 100000,
    "EUR": 93565,
}

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stake Mines Game")

class Button:
    def __init__(self, x, y, width, height, text, action=None, enabled=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.enabled = enabled
        self.hovered = False

    def draw(self, screen):
        color = HIGHLIGHT_COLOR if self.hovered else BUTTON_COLOR if self.enabled else DISABLED_BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        text_surface = small_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hovered(self, pos):
        return self.rect.collidepoint(pos)

    def handle_click(self, pos):
        if self.enabled and self.is_hovered(pos) and self.action:
            self.action()

class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.is_mine = False
        self.is_revealed = False
        self.rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)

    def draw(self, screen):
        pygame.draw.rect(screen, GRID_BORDER_COLOR, self.rect, 1)
        if self.is_revealed:
            color = MINE_COLOR if self.is_mine else DIAMOND_COLOR
            shape = 'circle' if self.is_mine else 'polygon'
            if shape == 'circle':
                pygame.draw.circle(screen, color, self.rect.center, CELL_SIZE // 4)
            else:
                pygame.draw.polygon(screen, color, self._diamond_points())
        else:
            pygame.draw.rect(screen, HIDDEN_COLOR, self.rect)

    def _diamond_points(self):
        cx, cy = self.rect.center
        size = CELL_SIZE // 4
        return [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]

class Dropdown:
    def __init__(self, x, y, width, height, options, selected_index=0, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = selected_index
        self.expanded = False
        self.action = action

    def draw(self, screen):
        pygame.draw.rect(screen, BUTTON_COLOR, self.rect, border_radius=8)
        selected_option = self.options[self.selected_index]
        text_surface = small_font.render(selected_option, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

        if self.expanded:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                pygame.draw.rect(screen, BUTTON_COLOR, option_rect, border_radius=8)
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

class MinesGame:
    def __init__(self, balance):
        self.grid = [[Cell(row, col) for col in range(COLS)] for row in range(ROWS)]
        self.mine_count = DEFAULT_MINE_COUNT
        self.place_mines()
        self.running = True
        self.revealed_cells = 0
        self.bet_amount = DEFAULT_BET
        self.current_reward = 0
        self.balance = balance
        self.currency = "EUR"  # Default currency
        # Centered dropdown menu and smaller buttons
        button_width, button_height = 150, 40
        dropdown_x = (WIDTH - GRID_WIDTH) // 2 - button_width // 2
        button_x = GRID_WIDTH + 20
        self.dropdown = Dropdown(900, 300, button_width, button_height, ["BTC", "ETH", "USD", "EUR"], action=self.change_currency)
        self.buttons = {
            "cashout": Button(button_x, 300, button_width, button_height, "Cashout", self.cashout, enabled=False),
            "replay": Button(button_x, 360, button_width, button_height, "Replay", self.reset),
            "increase_mines": Button(button_x, 420, button_width, button_height, "+ Mines", lambda: self.change_mines(1)),
            "decrease_mines": Button(button_x, 480, button_width, button_height, "- Mines", lambda: self.change_mines(-1)),
            "increase_bet": Button(button_x, 540, button_width, button_height, "+ Bet", lambda: self.change_bet(0.0001)),
            "decrease_bet": Button(button_x, 600, button_width, button_height, "- Bet", lambda: self.change_bet(-0.0001)),
        }

    def place_mines(self):
        mine_positions = random.sample(range(ROWS * COLS), self.mine_count)
        for pos in mine_positions:
            row, col = divmod(pos, COLS)
            self.grid[row][col].is_mine = True

    def reset(self):
        self.grid = [[Cell(row, col) for col in range(COLS)] for row in range(ROWS)]
        self.place_mines()
        self.revealed_cells = 0
        self.running = True
        self.current_reward = 0

    def reveal_cell(self, row, col):
        if not self.running:
            return

        cell = self.grid[row][col]
        if cell.is_revealed:
            return

        click_sound.play()
        cell.is_revealed = True
        if cell.is_mine:
            mine_sound.play()
            self.balance -= self.bet_amount
            self.running = False
        else:
            diamond_sound.play()
            self.revealed_cells += 1
            # Apply conservative multiplier
            mine_multiplier = 1 + (self.mine_count / (MAX_MINES))
            self.current_reward = round(self.bet_amount * (1.01 + (mine_multiplier))  ** (self.revealed_cells / 5), 8)

        if self.balance <= 0:
            print("Balance is zero. Game over!")
            pygame.quit()


    def draw(self, screen):
        screen.fill(BG_COLOR)
        for row in self.grid:
            for cell in row:
                cell.draw(screen)
        self.draw_interface(screen)

    def draw_interface(self, screen):
        panel_x = GRID_WIDTH + 20
        panel_width = WIDTH - GRID_WIDTH - 40

        pygame.draw.rect(screen, HIDDEN_COLOR, (panel_x, 0, panel_width, HEIGHT))

        # Define consistent padding and spacing
        padding = 20
        line_height = 40  # Height between lines of text
        button_spacing = 10  # Space between buttons

        # Draw text elements
        balance_text = f"Balance: {self.convert_currency(self.balance):.2f} {self.currency}"
        bet_text = f"Bet Amount: {self.convert_currency(self.bet_amount):.2f} {self.currency}"
        reward_text = f"Reward: {self.convert_currency(self.current_reward):.2f} {self.currency}"
        status_text = f"Revealed: {self.revealed_cells} | Mines: {self.mine_count}"
        multiplier_text = f"Current Multiplier: {1.01 + (self.mine_count / (2 * MAX_MINES)):.3f}"

        y_offset = padding
        for text in [balance_text, bet_text, reward_text, status_text, multiplier_text]:
            text_surface = font.render(text, True, TEXT_COLOR)
            screen.blit(text_surface, (panel_x + padding, y_offset))
            y_offset += line_height

        # Draw dropdown
        self.dropdown.rect.y = y_offset + padding  # Position dropdown below text
        self.dropdown.draw(screen)
        y_offset += self.dropdown.rect.height + padding

        # Draw buttons with even spacing
        for button in self.buttons.values():
            button.rect.y = y_offset
            button.rect.x = panel_x + padding
            button.draw(screen)
            y_offset += button.rect.height + button_spacing

    def cashout(self):
        self.balance += self.current_reward
        cashout_sound.play()
        print(f"Cashed out: {self.current_reward:.8f} {self.currency}")
        self.reset()

    def change_mines(self, delta):
        new_mine_count = max(1, min(MAX_MINES, self.mine_count + delta))
        self.mine_count = new_mine_count
        self.reset()

    def change_bet(self, amount):
        new_bet = max(0.001, self.bet_amount + amount)
        if new_bet > self.balance:
            print("Cannot bet more than your current balance!")
        else:
            self.bet_amount = new_bet


    def change_currency(self, currency):
        self.currency = currency

    def convert_currency(self, amount):
        return amount * conversion_rates[self.currency]

    def run(self):

        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Stake Mines Game")
        clock = pygame.time.Clock()
        holding = False

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if pos[0] < GRID_WIDTH:  # Click inside grid
                        col, row = pos[0] // CELL_SIZE, pos[1] // CELL_SIZE
                        holding = True
                        if row < ROWS and col < COLS:
                            self.reveal_cell(row, col)
                    else:  # Click on buttons or dropdown menu
                        for button in self.buttons.values():
                            button.handle_click(pos)
                        self.dropdown.handle_click(pos)

                if event.type == pygame.MOUSEBUTTONUP:
                    holding = False

            if holding:
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[0] < GRID_WIDTH:
                    col, row = mouse_pos[0] // CELL_SIZE, mouse_pos[1] // CELL_SIZE
                    if row < ROWS and col < COLS:
                        self.reveal_cell(row, col)

            # Update button hover state
            for button in self.buttons.values():
                if button.is_hovered(pygame.mouse.get_pos()) and not button.hovered:
                    hover_sound.play()
                button.hovered = button.is_hovered(pygame.mouse.get_pos())

            # Update cashout button state
            self.buttons["cashout"].enabled = self.current_reward > 0 and self.running

            # Draw everything
            self.draw(screen)

            pygame.display.flip()
            clock.tick(30)

        pygame.quit()

def run_mines(balance):
    """Create and return a MinesGame instance."""
    return MinesGame(balance)
