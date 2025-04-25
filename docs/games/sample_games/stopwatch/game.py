import pyxel
import math
import time

# global variables
ANIMATION_SPEED = 5 # change every 5 frames
count = 0 # counts the frames

class StopwatchApp:
    def __init__(self):
        pyxel.init(160, 160, title="Pyxel Stopwatch")
        pyxel.load('game.pyxres')
        
        self.center_x = 80
        self.center_y = 80
        self.radius = 60

        self.running = False
        self.start_time = 0
        self.elapsed = 0

        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_S):
            if not self.running:
                self.running = True
                self.start_time = time.time() - self.elapsed

        if pyxel.btnp(pyxel.KEY_P):
            if self.running:
                self.running = False
                self.elapsed = time.time() - self.start_time

        if pyxel.btnp(pyxel.KEY_R):
            self.running = False
            self.elapsed = 0
            self.start_time = 0

        if self.running:
            self.elapsed = time.time() - self.start_time

    def draw(self):
        global count, ANIMATION_SPEED
        pyxel.cls(0)

        # Draw dial
        pyxel.circb(self.center_x, self.center_y, self.radius, 7)
        
        # draw animated runner
        if self.running:
            if count < ANIMATION_SPEED:
                count += 1
                pyxel.blt(72,100, 0, 0,0, 16,16, colkey=0)
            elif count < 2*ANIMATION_SPEED:
                count += 1
                pyxel.blt(72,100, 0, 32,0, 16,16, colkey=0)
            else:
                count = 0
        else:
            count=0
            pyxel.blt(72,100, 0, 16,0, 16,16, colkey=0)
            
        # Calculate second hand angle
        seconds = self.elapsed % 60
        angle = -math.pi / 2 + (2 * math.pi * seconds / 60)

        # End point of the second hand
        hand_length = self.radius - 10
        end_x = int(self.center_x + math.cos(angle) * hand_length)
        end_y = int(self.center_y + math.sin(angle) * hand_length)

        # Draw second hand
        pyxel.line(self.center_x, self.center_y, end_x, end_y, 8)

        # Show time in text
        pyxel.text(50, 10, f"Time: {int(self.elapsed):02d}s", 6)
        pyxel.text(10, 145, "S: Start | P: Pause | R: Reset", 5)

if __name__ == "__main__":
    StopwatchApp()
