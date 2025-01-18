import curses
from curses import wrapper
import time

def main(stdscr):
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_YELLOW)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
    BLUE_AND_YELLOW = curses.color_pair(1)
    GREEN_AND_BLACK = curses.color_pair(2)
    MAGENTA_AND_WHITE = curses.color_pair(3)
    

    #stdscr.clear()

    stdscr.addstr(10, 10, "hello world", BLUE_AND_YELLOW)
    stdscr.addstr(5, 5, "Test, Test", GREEN_AND_BLACK | curses.A_BOLD)
    stdscr.addstr(5, 35, "Yes, No", MAGENTA_AND_WHITE)
    stdscr.addstr(15, 25, "tim is great!")

    for i in range(100):
        stdscr.clear()
        color = BLUE_AND_YELLOW
        if i % 2 == 0:
            color = GREEN_AND_BLACK
        stdscr.addstr(f"Count: {i}", color)
        stdscr.refresh()
        time.sleep(0.1)
    stdscr.getch()

wrapper(main)