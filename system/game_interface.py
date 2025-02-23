import pygame
import sys
import re

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class GameInterface:

    def __init__(self, width=800, height=600):
        """Initialize the game interface with a fixed window size."""
        pygame.init()
        self.width = width
        self.height = height
        self.screen = None
        self.font = pygame.font.SysFont("Consolas", 20, bold=True)  # Enable bold
        self.static_surface = None  # Surface for static elements
        self.dynamic_surface = None  # Surface for dynamic elements
        self.manual_target_selection = None # Manual for target selection
        self.log_rect = None #Log box
        self.game_log = [] #Game log

    def initialize_window(self):
        """Set up the Pygame window and static/dynamic surfaces."""
        print(self.width, self.height)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Legends of Champions Tactics")
        #self.font = pygame.font.SysFont("Courier", 20)

        # Create separate surfaces for static and dynamic elements
        self.static_surface = pygame.Surface((self.width, self.height))
        self.dynamic_surface = pygame.Surface((self.width, self.height//2), pygame.SRCALPHA)  # Allows transparency
        self.manual_target_selection = pygame.Surface((self.width, self.height//2), pygame.SRCALPHA)  # Allows transparency
        self.log_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)  # Allows transparency

        # Draw static elements once
        self.draw_static_elements()

    def draw_static_elements(self):
        """Draw static UI elements on the static surface."""
        # Fill the static surface with black
        self.static_surface.fill((0, 0, 0))

        # Dimensions
        top_height = self.height // 2
        bottom_height = self.height // 2
        section_width = self.width // 3

        # Upper left: Player Heroes
        player_rect = pygame.Rect(0, 0, section_width, top_height)
        pygame.draw.rect(self.static_surface, (255, 255, 255), player_rect, 1)  # White border
        player_text = self.font.render("Player Heroes", True, (255, 255, 255))
        self.static_surface.blit(player_text, (player_rect.x + 10, player_rect.y + 10))

        # Upper middle
        middle_rect = pygame.Rect(section_width, 0, section_width, top_height)
        pygame.draw.rect(self.static_surface, (255, 255, 255), middle_rect, 1)
        middle_text = self.font.render("Round Info", True, (255, 255, 255))
        self.static_surface.blit(middle_text, (middle_rect.x + 10, middle_rect.y + 10))

        # Upper right: Opponent Heroes
        opponent_rect = pygame.Rect(section_width * 2, 0, section_width, top_height)
        pygame.draw.rect(self.static_surface, (255, 255, 255), opponent_rect, 1)
        opponent_text = self.font.render("Opponent Heroes", True, (255, 255, 255))
        self.static_surface.blit(opponent_text, (opponent_rect.x + 10, opponent_rect.y + 10))

        # Bottom: Game Log
        self.log_rect = pygame.Rect(0, top_height, self.width, bottom_height)
        pygame.draw.rect(self.static_surface, (255, 255, 255), self.log_rect, 1)
        log_text = self.font.render("Game Log", True, (255, 255, 255))
        self.static_surface.blit(log_text, (self.log_rect.width // 2 - 50, self.log_rect.y + 10))

    def draw_game_log(self):
        """Draws game logs with automatic text wrapping, scrolling, and color recognition."""
        # Clear only the text area while keeping the border intact
        pygame.draw.rect(
            self.log_surface, 
            (0, 0, 0),  # Black background
            (self.log_rect.x + 1, self.log_rect.y + 1, self.log_rect.width - 2, self.log_rect.height - 2)
        )

        gap = 10
        line_height = 25
        log_text_x = self.log_rect.x + gap
        log_text_y = self.log_rect.y + 1 * gap  # Adjusted for spacing

        max_width = self.log_rect.width - 2 * gap  # Max width inside log box

        visible_logs = []

        # **Process the last 15 logs from game_log**
        for log_entry in self.game_log[-15:]:
            if isinstance(log_entry, list):  # Expecting a list of (text, color) pairs
                for text, color in log_entry:
                    # Text Wrapping: Break long lines into multiple lines
                    words = text.split(" ")
                    wrapped_line = ""

                    for word in words:
                        test_line = wrapped_line + " " + word if wrapped_line else word
                        if self.font.size(test_line)[0] < max_width:  
                            wrapped_line = test_line
                        else:
                            visible_logs.append((wrapped_line, color))  # Store wrapped line with color
                            wrapped_line = word  # Start a new line
                    
                    if wrapped_line:
                        visible_logs.append((wrapped_line, color))  # Add the last wrapped line

            else:
                # In case log_entry is not a list of (text, color) pairs (Fallback)
                visible_logs.append((str(log_entry), (255, 255, 255)))

        # **Limit logs to fit within the box**
        max_lines = self.log_rect.height // line_height - 1
        visible_logs = visible_logs[-max_lines:]  

        # **Render the wrapped text with color**
        y_offset = 5
        for log_text, color in visible_logs:
            log_rendered = self.font.render(log_text, True, color)
            self.log_surface.blit(log_rendered, (log_text_x, log_text_y + y_offset))
            y_offset += line_height

        # Redraw the log box border
        pygame.draw.rect(self.log_surface, (255, 255, 255), self.log_rect, 1)  

        # Update screen with new logs
        self.screen.blit(self.log_surface, (0, 0))
        pygame.display.flip()



    def add_log(self, entry):
        """Add a new log entry and process multiple color markers for display."""
        max_log_entries = 15  # Limit log size

        # Define ANSI to RGB color map
        ANSI_COLOR_MAP = {
            "\033[91m": (255, 0, 0),   # RED
            "\033[92m": (0, 255, 0),   # GREEN
            "\033[93m": (255, 255, 0), # YELLOW
            "\033[94m": (0, 112, 221),  # Brighter and more vivid terminal-style blue
            "\033[95m": (255, 0, 255), # MAGENTA
            "\033[96m": (0, 255, 255), # CYAN
            "\033[38;5;208m": (255, 165, 0), # ORANGE
            "\033[0m": (255, 255, 255), # RESET (White)
        }

        current_color = (255, 255, 255)  # Default color is white
        segments = []  # Stores (text, color) tuples

        # Use regex to match ANSI codes and text
        pattern = re.compile(r'(\033\[[0-9;]*m)|([^ \033]+)')
        matches = pattern.findall(entry)

        text_buffer = ""  # Temporary storage for text

        for match in matches:
            ansi_code, text_part = match  # Regex returns tuples (ansi_code, text)

            if ansi_code:  # If we found an ANSI code
                if text_buffer:  # Save any existing text with previous color
                    segments.append((text_buffer, current_color))
                    text_buffer = ""

                # Update current color if ANSI code exists in our map
                current_color = ANSI_COLOR_MAP.get(ansi_code, current_color)

            elif text_part:  # If we found regular text
                text_buffer += text_part + " "  # Append the word

        if text_buffer:
            segments.append((text_buffer.strip(), current_color))  # Store final text

        """
        # 🔴 **Debug Print Output**
        print("\nDEBUG: Parsed Log Segments:")
        for segment in segments:
            print(segment)  # Print each (text, color) pair
        print("\n")
        """

        # Store log entry as a list of (text, color) pairs
        self.game_log.append(segments)

        # Maintain max log limit
        if len(self.game_log) > max_log_entries:
            self.game_log.pop(0)

    def convert_ansi_to_color(self, text):
        """Extracts ANSI color codes from text and converts them to Pygame colors."""
        ANSI_COLOR_MAP = {
        "\033[38;5;208m": (255, 165, 0),  # ORANGE
        "\033[91m": (255, 0, 0),  # RED
        "\033[92m": (0, 255, 0),  # GREEN
        "\033[93m": (255, 255, 0),  # YELLOW
        "\033[94m": (0, 0, 255),  # BLUE
        "\033[95m": (255, 0, 255),  # MAGENTA
        "\033[96m": (0, 255, 255),  # CYAN
        "\033[0m": None  # RESET (Ignore)
        }

        detected_color = None
        for ansi_code, color in ANSI_COLOR_MAP.items():
            if ansi_code in text:
                detected_color = color
                text = text.replace(ansi_code, "")  # Remove ANSI code from text

        return text, detected_color


    def draw_dynamic_elements(self, game_state):
        """Draw dynamic UI elements on the dynamic surface."""
        # Clear the dynamic surface
        self.dynamic_surface.fill((0, 0, 0, 0))  # Transparent background

        # Example: Draw hero info dynamically
        top_height = self.height // 2
        section_width = self.width // 3

        # Draw player heroes
        player_rect = pygame.Rect(0, 0, section_width, top_height)
        self.draw_player_heroes(game_state.player_heroes, player_rect)

        # Draw opponent heroes
        opponent_rect = pygame.Rect(section_width * 2, 0, section_width, top_height)
        self.draw_player_heroes(game_state.opponent_heroes, opponent_rect)

        # Draw round and skill info
        self.draw_middle_section(game_state)

    def draw_player_heroes(self, heroes, rect):
        """Draw player or opponent hero info."""
        gap = 10
        line_height = 25
        x, y = rect.x + gap, rect.y + 4 * gap

        for hero in heroes:
            # Hero name and profession
            name_text = self.font.render(f"{hero.name} [{hero.faculty}]", True, (255, 255, 255))
            self.dynamic_surface.blit(name_text, (x, y))
            y += line_height

            # HP bar
            hp_percentage = hero.hp / hero.hp_max
            hp_bar_width = rect.width - 11 * gap
            hp_bar_height = 25
            hp_color = (255, 0, 0) if hp_percentage < 0.3 else (255, 255, 0) if hp_percentage < 0.7 else (0, 255, 0)

            pygame.draw.rect(self.dynamic_surface, (64, 64, 64), (x, y, hp_bar_width, hp_bar_height))  # Background
            pygame.draw.rect(self.dynamic_surface, hp_color, (x, y, hp_bar_width * hp_percentage, hp_bar_height))  # Foreground

            # HP text
            hp_text = self.font.render(f"{hero.hp}/{hero.hp_max}", True, (255, 255, 255))
            self.dynamic_surface.blit(hp_text, (x + hp_bar_width + 5, y))
            y += line_height

            # Buffs
            '''
            buffs_text = self.font.render(f"Buffs: {', '.join(hero.buffs) or 'None'}", True, (0, 255, 255))
            self.dynamic_surface.blit(buffs_text, (x, y))
            y += line_height

            # Debuffs
            debuffs_text = self.font.render(f"Debuffs: {', '.join(hero.debuffs) or 'None'}", True, (255, 0, 0))
            self.dynamic_surface.blit(debuffs_text, (x, y))
            y += line_height + gap
            '''

    def draw_middle_section(self, game_state):
        """Draw the middle section dynamically based on the game state."""
        hero = game_state.current_action_hero
        if not hero:
            return  # No action hero; skip drawing
        current_round = game_state.round_counter
        profession_icon = "⚔"  # Placeholder for profession icon
        hero_name = "Daoyu [Warrior]"  # Placeholder, dynamically update as needed
        special_events = ["Some event..."]  # Replace with game_state's special events
        skills = ["Skill 1", "Skill 2"]  # Replace with game_state's current hero skills
        selected_skill_index = 0  # Update based on player input or game logic

        # Draw round number
        round_text = self.font.render(f"Round {current_round}", True, (255, 255, 255))
        self.dynamic_surface.blit(round_text, (self.width // 2 - round_text.get_width() // 2, 10))

        # Draw profession icon and hero name
        icon_text = self.font.render(profession_icon, True, (255, 255, 255))
        self.dynamic_surface.blit(icon_text, (self.width // 2 - icon_text.get_width() // 2, 50))

        hero_name_text = self.font.render(f"Hero: {hero.name} [{hero.faculty}]", True, (255, 255, 255))
        self.dynamic_surface.blit(hero_name_text, (self.width // 2 - hero_name_text.get_width() // 2, 90))


        # Draw special events
        y_position = 140
        for event in special_events:
            event_text = self.font.render(event, True, (255, 255, 255))
            self.dynamic_surface.blit(event_text, (self.width // 2 - event_text.get_width() // 2, y_position))
            y_position += 30

    def select_target_manual_disappear(self):

        # Define the area for skill selection
        skill_selection_x = self.width // 3
        skill_selection_y = 200 
        skill_selection_width = self.width // 3
        skill_selection_height = 150

        # Preserve the dynamic surface for other elements
        dynamic_surface_snapshot = self.dynamic_surface.copy()

        # Clear only the skill selection area
        pygame.draw.rect(self.dynamic_surface, (0, 0, 0), 
                        (skill_selection_x, skill_selection_y, skill_selection_width, skill_selection_height))

        # Update only the modified portion of the screen
        #self.screen.blit(self.static_surface, (0, 0))  # Redraw static elements
        self.screen.blit(dynamic_surface_snapshot, (0, 0))  # Restore the dynamic elements
        self.screen.blit(self.dynamic_surface, (0, 0))  # Draw the updated skill selection
        pygame.display.flip()

    def select_skill(self, hero, available_skills):
        """Render skill selection in the designated area and handle input."""
        selected_index = 0

        # Define the area for skill selection
        skill_selection_x = self.width // 3
        skill_selection_y = 200 
        skill_selection_width = self.width // 3
        skill_selection_height = 150

        while True:
            # Preserve the dynamic surface for other elements
            dynamic_surface_snapshot = self.dynamic_surface.copy()

            # Clear only the skill selection area
            pygame.draw.rect(self.dynamic_surface, (0, 0, 0), 
                            (skill_selection_x, skill_selection_y, skill_selection_width, skill_selection_height))

            # Display hero name and prompt
            hero_text = self.font.render(f"{hero.name} - Select a Skill", True, (255, 255, 255))
            self.dynamic_surface.blit(hero_text, (skill_selection_x + 10, skill_selection_y + 10))

            # Display available skills
            y_position = skill_selection_y + 40
            for i, skill in enumerate(available_skills):
                color = (0, 255, 0) if i == selected_index else (255, 255, 255)
                skill_text = self.font.render(skill.name, True, color)
                self.dynamic_surface.blit(skill_text, (skill_selection_x + 10, y_position))
                y_position += 30

            # Update only the modified portion of the screen
            #self.screen.blit(self.static_surface, (0, 0))  # Redraw static elements
            self.screen.blit(dynamic_surface_snapshot, (0, 0))  # Restore the dynamic elements
            self.screen.blit(self.dynamic_surface, (0, 0))  # Draw the updated skill selection
            pygame.display.flip()

            # Handle player input
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_index = max(0, selected_index - 1)
                    elif event.key == pygame.K_DOWN:
                        selected_index = min(len(available_skills) - 1, selected_index + 1)
                    elif event.key == pygame.K_RETURN:
                        return selected_index  # Skill confirmed
                    elif event.key == pygame.K_ESCAPE:
                        return None  # Player canceled the selection

    def select_target(self, hero, available_targets, num_targets=1):
        """
        Render a target selection window and handle input.
        :param hero: Current hero taking action.
        :param available_targets: List of valid targets determined by the hero logic.
        :param num_targets: Number of targets required.
        :return: List of selected target heroes or None if canceled.
        """
        selected_targets = []
        selected_index = 0
        num_targets = min(num_targets, len(available_targets))

        while len(selected_targets) < num_targets:
            self.manual_target_selection.fill((0, 0, 0, 0))  # Clear the surface

            # Draw the selection box
            box_x, box_y = self.width // 3, 150
            box_width, box_height = self.width // 3, 300
            pygame.draw.rect(self.manual_target_selection, (50, 50, 50), (box_x, box_y, box_width, box_height))

            # Display the dynamic hint
            hint_text = f"Choose target {len(selected_targets) + 1}/{num_targets}:"
            hint_render = self.font.render(hint_text, True, (255, 255, 255))
            self.manual_target_selection.blit(hint_render, (box_x + 10, box_y + 10))

            # Display targets
            y_position = box_y + 40
            for i, target in enumerate(available_targets):
                #color = (0, 255, 0) if target.group == "opponents" else (0, 0, 255)
                text_color = (0, 255, 0) if i == selected_index else (255, 255, 255)
                target_text = self.font.render(f"{i + 1}: {target.name} (HP: {target.hp}/{target.hp_max})", True, text_color)
                self.manual_target_selection.blit(target_text, (box_x + 10, y_position))
                y_position += 30

            # "Return to Previous Menu" option
            text_color_return = (0, 255, 0) if selected_index == len(available_targets) else (255, 255, 255)
            return_text = self.font.render(f"{len(available_targets) + 1}: Return to Previous Menu", True, text_color_return)
            self.manual_target_selection.blit(return_text, (box_x + 10, y_position + 10))

            # Display updated interface
            #self.screen.blit(self.static_surface, (0, 0))  # Redraw static elements
            self.screen.blit(self.manual_target_selection, (0, 0))  # Draw the updated target selection
            pygame.display.flip()

            # Handle player input
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_index = max(0, selected_index - 1)
                    elif event.key == pygame.K_DOWN:
                        selected_index = min(len(available_targets), selected_index + 1)  # Include "Return"
                    elif event.key == pygame.K_RETURN:
                        if selected_index == len(available_targets):  # Return to previous menu
                           return ['Back to skill chosen']
                        else:
                            # Add selected target
                            selected_targets.append(available_targets[selected_index])
                            # Remove selected target from available list
                            available_targets.pop(selected_index)
                            selected_index = 0  # Reset to first option
                            self.select_target_manual_disappear()
                    elif event.key == pygame.K_ESCAPE:
                        #self.manual_target_selection.fill((0, 0, 0, 0))
                        #pygame.display.flip()
                        return ['Back to skill chosen']  # Player canceled the selection
                    

        return selected_targets
    
    def update_display(self, game_state):
        """Update the entire display."""
        self.screen.blit(self.static_surface, (0, 0))  # Draw static elements first
        self.draw_dynamic_elements(game_state)
        self.draw_game_log()  # Ensure the game log is drawn every frame
        self.screen.blit(self.dynamic_surface, (0, 0))  # Overlay dynamic elements
        pygame.display.flip()

    def close(self):
        """Close the Pygame window."""
        pygame.quit()
        sys.exit()
