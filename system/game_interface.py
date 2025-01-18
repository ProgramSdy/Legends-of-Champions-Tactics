import pygame
import sys

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class GameInterface:

    def __init__(self, width=800, height=600):
        """Initialize the game interface with a fixed window size."""
        self.width = width
        self.height = height
        self.screen = None
        self.font = None
        self.static_surface = None  # Surface for static elements
        self.dynamic_surface = None  # Surface for dynamic elements
        self.manual_target_selection = None # Manual for target selection
        self.log_rect = None #Log box
        self.game_log = [] #Game log

    def initialize_window(self):
        """Set up the Pygame window and static/dynamic surfaces."""
        pygame.init()
        print(self.width, self.height)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Legends of Champions Tactics")
        self.font = pygame.font.SysFont("Courier", 20)

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
        # Fill the static surface with black
        #self.log_surface.fill((0, 0, 0))
        gap = 10
        line_height = 25
        x, y = self.log_rect.x + gap, self.log_rect.y + 4 * gap
        y_offset = 10
        for log in self.game_log:
            log_text = self.font.render(log, True, WHITE)
            self.log_surface.blit(log_text, (x, y + y_offset))
            y_offset += line_height
        self.screen.blit(self.log_surface, (0, 0))
        pygame.display.flip()
        
    def add_log(self, entry):
        """添加新日志条目"""
        # 最大日志条数，防止文本框内容过多
        max_log_entries = 15
        self.game_log.append(entry)
        if len(self.game_log) > max_log_entries:
            self.game_log.pop(0)  # 移除最旧的日志条目

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
        self.screen.blit(self.dynamic_surface, (0, 0))  # Overlay dynamic elements
        pygame.display.flip()

    def close(self):
        """Close the Pygame window."""
        pygame.quit()
        sys.exit()
