import pyxel

# Game constants
WIDTH = 128
HEIGHT = 128
TILE_SIZE = 8

# Physics constants (matched with original)
GRAVITY = 0.21
MAX_FALL_SPEED = 2
GROUND_ACCEL = 0.6
AIR_ACCEL = 0.4
DECEL = 0.15
MAX_RUN_SPEED = 2
JUMP_FORCE = -4  # Original Celeste value
COYOTE_TIME = 6  # Frames of "coyote time"
JUMP_BUFFER = 4  # Frames of input buffer for jumps

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.spd_x = 0
        self.spd_y = 0
        self.rem_x = 0  # Sub-pixel remainder for x movement
        self.rem_y = 0  # Sub-pixel remainder for y movement
        self.grace = 0  # Coyote time counter
        self.jbuffer = 0  # Jump buffer counter
        self.on_ground = False
        self.was_on_ground = False
        self.facing_right = True
        
        # Player is 8x8 pixels (single tile)
        self.width = 8
        self.height = 8
    
    def update(self):
        # Handle input
        input_x = pyxel.btn(pyxel.KEY_RIGHT) - pyxel.btn(pyxel.KEY_LEFT)
        jump = pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_C)
        jump_held = pyxel.btn(pyxel.KEY_Z) or pyxel.btn(pyxel.KEY_C)
        
        # Ground check
        self.was_on_ground = self.on_ground
        self.on_ground = self.is_solid(0, 1)
        
        # Jump buffer (input leniency)
        if jump:
            self.jbuffer = JUMP_BUFFER
        elif self.jbuffer > 0:
            self.jbuffer -= 1
            
        # Coyote time (ground leniency)
        if self.on_ground:
            self.grace = COYOTE_TIME
        elif self.grace > 0:
            self.grace -= 1
            
        # Horizontal movement
        accel = GROUND_ACCEL if self.on_ground else AIR_ACCEL
        
        if abs(self.spd_x) > MAX_RUN_SPEED:
            # Slow down if going too fast
            self.spd_x = self.approach(self.spd_x, self.sign(self.spd_x) * MAX_RUN_SPEED, DECEL)
        else:
            # Accelerate based on input
            self.spd_x = self.approach(self.spd_x, input_x * MAX_RUN_SPEED, accel)
            
        # Update facing direction
        if self.spd_x != 0:
            self.facing_right = self.spd_x > 0
            
        # Jump logic
        if self.jbuffer > 0 and self.grace > 0:
            # Execute jump
            self.jbuffer = 0
            self.grace = 0
            self.spd_y = JUMP_FORCE  # Use exact value from original
            
        # Variable jump height (like in original)
        if not jump_held and self.spd_y < 0:
            # Cut jump short if button released
            self.spd_y = self.spd_y * 0.5
            
        # Apply gravity with reduced gravity at peak of jump (like in original)
        gravity_mod = 0.5 if abs(self.spd_y) <= 0.15 else 1.0
        self.spd_y = self.approach(self.spd_y, MAX_FALL_SPEED, GRAVITY * gravity_mod)
            
        # Apply movement with collision
        self.move(self.spd_x, self.spd_y)
            
        # Death on falling off screen
        if self.y > HEIGHT:
            self.x = 32  # Respawn position
            self.y = 32
            self.spd_x = 0
            self.spd_y = 0
    
    def move(self, dx, dy):
        # Handle sub-pixel movement
        self.rem_x += dx
        move_x = int(self.rem_x + 0.5)  # Round to nearest pixel
        self.rem_x -= move_x
        self.move_x(move_x)
        
        self.rem_y += dy
        move_y = int(self.rem_y + 0.5)  # Round to nearest pixel
        self.rem_y -= move_y
        self.move_y(move_y)
    
    def move_x(self, amount):
        step = self.sign(amount)
        for _ in range(abs(amount)):
            if not self.is_solid(step, 0):
                self.x += step
            else:
                self.spd_x = 0
                self.rem_x = 0
                break
    
    def move_y(self, amount):
        step = self.sign(amount)
        for _ in range(abs(amount)):
            if not self.is_solid(0, step):
                self.y += step
            else:
                self.spd_y = 0
                self.rem_y = 0
                break
    
    def is_solid(self, offset_x, offset_y):
        # Check if position+offset collides with a solid tile
        x = self.x + offset_x
        y = self.y + offset_y
        
        # Check each corner of the player
        corners = [
            (x, y),
            (x + self.width - 1, y),
            (x, y + self.height - 1),
            (x + self.width - 1, y + self.height - 1)
        ]
        
        for cx, cy in corners:
            tile_x = cx // TILE_SIZE
            tile_y = cy // TILE_SIZE
            
            # Check if this position has a solid tile
            if 0 <= tile_x < len(App.level[0]) and 0 <= tile_y < len(App.level):
                if App.level[tile_y][tile_x] == 1:  # 1 represents a solid block
                    return True
        
        return False
    
    def draw(self):
        # Draw player as a colored rectangle
        color = 8  # Red
        if self.on_ground:
            color = 11  # Light blue
        elif self.spd_y < 0:
            color = 10  # Yellow (jumping)
        
        pyxel.rect(self.x, self.y, self.width, self.height, color)
        
        # Draw a small indicator for facing direction
        if self.facing_right:
            pyxel.rect(self.x + 6, self.y + 2, 2, 4, 7)
        else:
            pyxel.rect(self.x, self.y + 2, 2, 4, 7)
    
    @staticmethod        
    def sign(v):
        return 1 if v > 0 else (-1 if v < 0 else 0)
    
    @staticmethod
    def approach(val, target, amount):
        if val > target:
            return max(val - amount, target)
        else:
            return min(val + amount, target)


class App:
    # Simple level design using a 2D array
    # 0 = empty, 1 = solid block
    level = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Celeste Clone", fps=30)  # Original game runs at 30fps
        
        self.player = Player(32, 32)
        
        # Start the game
        pyxel.run(self.update, self.draw)
    
    def update(self):
        # Quit condition
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
            
        # Restart game
        if pyxel.btnp(pyxel.KEY_R):
            self.player = Player(32, 32)
            
        # Update player
        self.player.update()
    
    def draw(self):
        pyxel.cls(0)
        
        # Draw level blocks
        for y in range(len(self.level)):
            for x in range(len(self.level[0])):
                if self.level[y][x] == 1:
                    pyxel.rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE, 3)
        
        # Draw player
        self.player.draw()
        
        # Draw debug info
        pyxel.text(4, 4, f"POS: {self.player.x}, {self.player.y}", 7)
        pyxel.text(4, 12, f"SPD: {self.player.spd_x:.1f}, {self.player.spd_y:.1f}", 7)
        pyxel.text(4, 20, f"ON GROUND: {self.player.on_ground}", 7)
        pyxel.text(4, 28, f"GRACE: {self.player.grace}", 7)
        pyxel.text(4, 36, f"JBUFFER: {self.player.jbuffer}", 7)


# Start the application
if __name__ == "__main__":
    App()