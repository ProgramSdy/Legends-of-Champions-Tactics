import pygame
import sys

# This is for test only

class BlitTest:

    def __init__(self, width=400, height=400):
        """Initialize the testing window."""
        pygame.init()
        pygame.font.init()
        self.width = width
        self.height = height
        self.screen = None
        self.font = pygame.font.SysFont("Courier", 10)

    def run(self):
        """Main loop to run the blit test."""
        #font = pygame.font.SysFont(None, 15)
        log = 'Hello World!'
        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)

        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Blit Test")
        
        # Draw a red rectangle then wait 3 seconds then change block pos to x :-567 y:124 
        red_surface = pygame.Surface((100, 100))
        red_surface.fill((255, 0, 0))  # Red color
        #self.screen.blit(red_surface, (50, 50))  # Position at (50, 50)

        # Draw text on red surface
        text_surface = self.font.render(log, True, BLACK)
        red_surface.blit(text_surface, (10, 10))

        # Update the screen with the new red_surface that contains the text
        self.screen.blit(red_surface, (50, 50))  # Position at (50, 50) again

        # Draw a blue rectangle on top
        blue_surface = pygame.Surface((100, 100), pygame.SRCALPHA)
        blue_surface.fill((0, 0, 255, 128))  # Blue with 50% transparency
        self.screen.blit(blue_surface, (275, 75))  # Position at (75, 75), overlaps red

        #self.screen.fill((0, 0, 0))  # Black background

        
        # Update display
        pygame.display.flip()

        # Event loop to keep the window open
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    test = BlitTest()
    test.run()
