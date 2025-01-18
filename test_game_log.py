import pygame
import sys


def main():
    
    # 初始化 Pygame
    pygame.init()

    # 设置屏幕尺寸
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Game Log Example")

    # 设置字体
    font = pygame.font.SysFont("monospace", 15)

    # 定义文本框的位置和大小
    log_box_rect = pygame.Rect(10, 10, 300, 200)

    # 游戏日志内容
    game_log = []

    # 最大日志条数，防止文本框内容过多
    max_log_entries = 15

    # 颜色定义
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    def add_log(entry):
        """添加新日志条目"""
        game_log.append(entry)
        if len(game_log) > max_log_entries:
            game_log.pop(0)  # 移除最旧的日志条目

    def draw_log_box():
        """绘制日志文本框和文本"""
        # 填充文本框背景
        pygame.draw.rect(screen, WHITE, log_box_rect)
        
        # 渲染并绘制日志文本
        y_offset = 10
        for log in game_log:
            text_surface = font.render(log, True, BLACK)
            screen.blit(text_surface, (log_box_rect.x + 10, log_box_rect.y + y_offset))
            y_offset += 20

    # 主游戏循环
    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # 按下空格键时添加新日志
                    add_log(f"Log entry {len(game_log) + 1}")

        # 填充屏幕背景
        screen.fill((50, 50, 50))
        
        # 绘制日志文本框
        draw_log_box()
        
        # 更新屏幕
        pygame.display.flip()
        
        # 控制帧率
        clock.tick(30)

    # 退出 Pygame
    pygame.quit()
    sys.exit()




if __name__ == "__main__":
    main()