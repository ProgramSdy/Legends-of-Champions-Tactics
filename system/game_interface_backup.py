import pygame
import sys
from pygame import Rect

class GameInterface:
    def __init__(self, width=800, height=600):
        """Initialize the game interface with a fixed window size."""
        self.width = width
        self.height = height
        self.screen = None
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.game_state = None

    def initialize_window(self):
        """Set up the Pygame window."""
        pygame.init()
        print(self.width, self.height)
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE) # RESIZABLE/FULLSCREEN/NOFRAME
        pygame.display.set_caption("Legends of Champions Tactics")
        # Load fonts
        self.font_large = pygame.font.SysFont("Courier", 40)
        self.font_medium = pygame.font.SysFont("Courier", 30)
        self.font_small = pygame.font.SysFont("Courier", 20)
    
    def update(self, game):
        """Receive updates from the game and refresh the UI."""
        print(f"GameInterface received update: Round {game.current_round}")
        self.game_state = game  # Save the updated game state
        self.draw()

    def drawText(self, surface, text, color, rect, font, aa=False, bkg=None):
        """
        Draws text within a rectangle, wrapping lines as needed.
        """
        # Ensure rect is a pygame.Rect
        if not isinstance(rect, pygame.Rect):
            rect = pygame.Rect(rect)

        x, y = rect.topleft  # Start at the top-left corner
        lineSpacing = -2  # Adjust spacing between lines
        # Get the height of the font
        fontHeight = font.size("Tg")[1]
        while text:
            i = 1
            # Determine if the row of text will be outside our area
            if y + fontHeight > rect.bottom:
                break
            # Determine maximum width of line
            while font.size(text[:i])[0] < rect.width and i < len(text):
                i += 1
            # If we've wrapped the text, then adjust the wrap to the last word
            if i < len(text):
                i = text.rfind(" ", 0, i) + 1
            # Render the line and blit it to the surface
            if bkg:
                image = font.render(text[:i], True, color, bkg)
                image.set_colorkey(bkg)
            else:
                image = font.render(text[:i], aa, color)
            surface.blit(image, (x, y))
            y += fontHeight + lineSpacing
            # Remove the text we just blitted
            text = text[i:]

        return text


    def draw_game_screen(self):
        """Render the screen layout with three sections in the upper part and a game log at the bottom."""
        # Calculate dimensions
        top_height = self.height // (100/61)  # Upper part: 0.61 of the height
        bottom_height = self.height - top_height  # Bottom part: 0.39 of the height
        section_width = self.width // 3   # Width of each upper section

        # Fill background
        self.screen.fill((0, 0, 0))  # Black background
      
        # Draw upper left (Player Heroes)
        gap = 10
        pygame.draw.rect(self.screen, (255, 255, 255), (gap, gap, section_width - 2*gap, top_height - 2*gap), 1)  # White border
        player_text = self.font_small.render("Player Heroes", True, (255, 255, 255))
        self.screen.blit(player_text, (20, 20))

        # Draw upper right (Opponent Heroes)
        pygame.draw.rect(self.screen, (255, 255, 255), (section_width * 2 + gap, gap, section_width - 2*gap, top_height -2*gap), 1)
        opponent_text = self.font_small.render("Opponent Heroes", True, (255, 255, 255))
        self.screen.blit(opponent_text, (section_width * 2 + 20, 20))

        # Draw bottom (Game Log)
        pygame.draw.rect(self.screen, (255, 255, 255), (gap, top_height, self.width - 2*gap, bottom_height - gap), 1)
        log_text = self.font_small.render("Game Log", True, (255, 255, 255))
        self.screen.blit(log_text, (self.width // 2 - 50, top_height + 10))

        # Draw upper middle part (Interactive)
        #self.draw_middle_section()

        # Refresh screen 
        #self.update_display()

    def draw_middle_section(self, current_round, profession_icon, hero_name, special_events, skills, selected_skill_index):
        """Draw the interactive middle section."""
        # Calculate dimensions
        section_width = self.width // 3
        top_height = self.height // 2

        # Round number
        round_text = self.font_large.render(f"Round {current_round}", True, (255, 255, 255))
        self.screen.blit(round_text, (self.width // 2 - round_text.get_width() // 2, 10))

        # Profession icon
        # Mockup for the profession icon (a colored square)
        icon_rect = pygame.Rect(self.width // 2 - 50, 60, 100, 100)
        pygame.draw.rect(self.screen, (0, 128, 255), icon_rect)  # Blue placeholder
        icon_text = self.font_medium.render(profession_icon, True, (255, 255, 255))
        self.screen.blit(icon_text, (self.width // 2 - icon_text.get_width() // 2, 100))

        # Hero name
        name_text = self.font_medium.render(hero_name, True, (255, 255, 255))
        self.screen.blit(name_text, (self.width // 2 - name_text.get_width() // 2, 170))

        # Special events
        '''
        events_rect = pygame.Rect(section_width, 210, section_width, 105)
        pygame.draw.rect(self.screen, (64, 64, 64), events_rect)  # Dark gray background
        pygame.draw.rect(self.screen, (255, 255, 255), events_rect, 1)  # White border
        for i, event in enumerate(special_events):
            event_text = self.font_small.render(event, True, (255, 255, 255))
            self.screen.blit(event_text, (section_width + 10, 220 + i * 20))
        '''
        events_rect = pygame.Rect(section_width, 210, section_width, 105)
        pygame.draw.rect(self.screen, (64, 64, 64), events_rect)  # Dark gray background
        pygame.draw.rect(self.screen, (255, 255, 255), events_rect, 1)  # White border

        # Combine all special events into a single string with line breaks for clarity
        events_text = "\n".join(special_events)

        # Call drawText to render the text within the rectangle
        self.drawText(self.screen, events_text, (255, 255, 255), events_rect, self.font_small)

        # Function window (skills)
        skills_rect = pygame.Rect(section_width, 325, section_width, 152)
        pygame.draw.rect(self.screen, (64, 64, 64), skills_rect)  # Dark gray background
        pygame.draw.rect(self.screen, (255, 255, 255), skills_rect, 1)  # White border
        for i, skill in enumerate(skills):
            color = (0, 255, 0) if i == selected_skill_index else (255, 255, 255)
            skill_text = self.font_small.render(skill, True, color)
            self.screen.blit(skill_text, (section_width + 10, 335 + i * 20))
        
        # Refresh screen 
        #self.update_display()

    def update_display(self):
        """Update the display."""
        pygame.display.flip()

    def close(self):
        """Close the Pygame window."""
        pygame.quit()
        sys.exit()



    