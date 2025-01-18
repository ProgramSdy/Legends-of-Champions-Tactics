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

    counter_win = curses.newwin(1, 20, 10, 10)

    pad = curses.newpad(100, 100)
    stdscr.refresh()
    #'''
    for i in range(100):
        for j in range(26):
            char = chr(67 + j)
            pad.addstr(char, GREEN_AND_BLACK)

    for i in range(50):
        stdscr.clear()
        stdscr.refresh()
        #pad.refresh(0, i, 5 + i, i, 10 + i, 25 + i)
        pad.refresh(i, 0, 0, 0, 10, 25)
        time.sleep(0.2)

    # Get the size/coordinate of the screen
    #(curses.LINES -1, curses.COLS - 1)

    #pad.refresh(0, 0, 5, 5, 25, 25)
    #'''

    #stdscr.addstr(1, 1, "hello world")
    #stdscr.refresh()
    

    #stdscr.clear()

    '''
    stdscr.addstr(10, 10, "hello world", BLUE_AND_YELLOW)
    stdscr.addstr(5, 5, "Test, Test", GREEN_AND_BLACK | curses.A_BOLD)
    stdscr.addstr(5, 35, "Yes, No", MAGENTA_AND_WHITE)
    stdscr.addstr(15, 25, "tim is great!")
    

    for i in range(100):
        counter_win.clear()
        counter_win.box()
        color = BLUE_AND_YELLOW
        if i % 2 == 0:
            color = GREEN_AND_BLACK
        counter_win.addstr(f"Count: {i}", color)
        
        counter_win.refresh()
        time.sleep(0.1)
    '''

    stdscr.getch()

wrapper(main)