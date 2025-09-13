import pyxel
import random

class LunarLander:
    # Sprite patterns
    LANDER_SPRITES = [
        0b01110000,  # Ship body
        0b11111000,
        0b11111000,
        0b01010000,
        0b11011000
    ]
    
    THRUST_SPRITES = [
        0b01010000,  # Thrust flame
        0b00100000,
        0b00100000
    ]
    
    EXPLOSION_SPRITES = [
        [0b00000, 0b00100, 0b01010, 0b00100, 0b00000],  # Frame 1
        [0b00000, 0b01010, 0b00100, 0b01010, 0b00000],  # Frame 2
        [0b00000, 0b01010, 0b10001, 0b01010, 0b00000],  # Frame 3
        [0b01010, 0b10001, 0b00000, 0b10001, 0b01010],  # Frame 4
        [0b10101, 0b00000, 0b10001, 0b00000, 0b10101]   # Frame 5
    ]
    
    # Game constants
    SCREEN_WIDTH = 128
    SCREEN_HEIGHT = 64
    FUEL_GAUGE_X = 120
    INITIAL_FUEL = 64
    LANDING_SPEED_MAX = 24    # Maximum vertical speed for safe landing
    LANDING_HORZ_MAX = 16     # Maximum horizontal speed for safe landing
    BASE_LANDING_SCORE = 25   # Points awarded for landing
    FUEL_SCORE_MULTIPLIER = 2 # Additional points per fuel unit
    
    def __init__(self):
        # Initialize Pyxel
        pyxel.init(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, title="Lunar Lander")
        
        # Set up sounds
        self._setup_sounds()
        
        # Generate color palette
        self.colors = self._generate_random_palette()
        
        # Initialize game state
        self.level = 0
        self.score = 0
        self.game_over = False
        
        # Start first level
        self._start_new_level()
        
        # Run the game
        pyxel.run(self.update, self.draw)

    def _setup_sounds(self):
        """Configure game sound effects"""
        pyxel.sounds[0].set("c3", "s", "7", "f", 5)   # Thrust sound
        pyxel.sounds[1].set("e2", "n", "5", "f", 20)  # Explosion sound

    def _generate_random_palette(self):
        """Create a random color palette for the game"""
        return {
            'background': 1,
            'terrain': random.randint(6, 7),
            'platform': random.randint(10, 11),
            'lander': random.randint(14, 15),
            'flame': random.randint(8, 9),
            'explosion': random.randint(12, 13),
            'gauge_frame': random.randint(4, 5),
            'gauge_fill': random.randint(2, 3)
        }

    def _start_new_level(self):
        """Initialize a new game level"""
        # Increment level counter
        self.level += 1
        
        # Set lander starting position and velocity
        self.lander_x = random.randint(32, 96)
        self.lander_y = 0
        self.velocity_x = random.randint(-15, 15)
        self.velocity_y = 8
        
        # Physics properties
        self.thrust = 0x80  # Internal physics calculation value
        self.tilt = 0x80    # Internal physics calculation value
        
        # Fuel management
        self.fuel = self.INITIAL_FUEL
        self.fuel_consumption = 0
        
        # Visual states
        self.thrust_visible = False
        self.landed = False
        self.explosion_frame = -1
        
        # Gravity timer (controls fall speed)
        self.gravity_timer = 10
        
        # Generate terrain and landing pad
        self._generate_terrain()
        self._place_landing_pad()

    def _generate_terrain(self):
        """Create a random terrain profile"""
        # Start with a random base elevation
        base_elevation = random.randint(20, 40)
        self.terrain_elevations = [base_elevation] * 15
        
        # Create some terrain variation
        for segment in range(3):
            height_change = random.randint(-8, 8)
            for point in range(5):
                index = segment * 5 + point
                if index < 15:  # Stay within array bounds
                    # Update elevation, keeping within reasonable limits
                    current = self.terrain_elevations[index]
                    new_elevation = current + height_change
                    self.terrain_elevations[index] = max(10, min(50, new_elevation))
                    # Use the last elevation as the starting point for the next segment
                    base_elevation = self.terrain_elevations[index]

    def _place_landing_pad(self):
        """Place the landing platform at the lowest point of terrain"""
        # Find the lowest points in the terrain
        lowest_elevation = min(self.terrain_elevations)
        possible_positions = [i for i, e in enumerate(self.terrain_elevations) 
                             if e == lowest_elevation]
        
        # Choose a random position from the lowest points
        pad_position = random.choice(possible_positions)
        self.platform_x = pad_position * 8  # Convert to pixel coordinates

    def update(self):
        """Main game update loop"""
        if self.game_over:
            self._handle_game_over_state()
            return

        self._handle_player_input()
        self._update_physics()
        self._check_landing_collision()

    def _handle_game_over_state(self):
        """Process game over animations and input"""
        if self.explosion_frame < 4:
            # Advance explosion animation
            self.explosion_frame += 1
        elif pyxel.btnp(pyxel.KEY_Q):
            # Quit on Q press when game is over
            pyxel.quit()

    def _handle_player_input(self):
        """Process player controls for thrust and direction"""
        if self.fuel <= 0:
            return  # No control without fuel
            
        # Main engine thrust (up key)
        if pyxel.btn(pyxel.KEY_UP):
            self.velocity_y -= 2
            self.fuel_consumption -= 0xC0  # High fuel use for main engine
            self.thrust_visible = True
            pyxel.play(0, 0)  # Play thrust sound
            
        # Left thruster
        if pyxel.btn(pyxel.KEY_LEFT):
            if self.velocity_x > -60:  # Limit maximum leftward velocity
                self.velocity_x -= 2
            self.fuel_consumption -= 0x60
            
        # Right thruster
        if pyxel.btn(pyxel.KEY_RIGHT):
            if self.velocity_x < 60:  # Limit maximum rightward velocity
                self.velocity_x += 2
            self.fuel_consumption -= 0x60
            
        # Process fuel consumption
        if self.fuel_consumption < 0:
            self.fuel -= 1
            self.fuel_consumption = 0
            if self.fuel < 0:
                self.fuel = 0

    def _update_physics(self):
        """Update lander physics including gravity and movement"""
        # Apply gravity
        self.gravity_timer -= 1
        if self.gravity_timer <= 0:
            self.velocity_y += 1
            self.gravity_timer = 10
            self.thrust_visible = False

        # Internal physics values for smooth movement
        self.thrust += self.velocity_y
        self.tilt += self.velocity_x

        # Vertical movement based on thrust
        if self.thrust >= 0xC0:
            self.lander_y += 1
            self.thrust = 0x80
        elif self.thrust <= 0x40:
            self.lander_y -= 1
            self.thrust = 0x80

        # Horizontal movement based on tilt
        if self.tilt <= 0x40:
            self.lander_x -= 1
            self.tilt = 0x80
        elif self.tilt >= 0xC0:
            self.lander_x += 1
            self.tilt = 0x80

        # Keep lander within screen bounds
        self.lander_x = max(0, min(self.SCREEN_WIDTH - 1, self.lander_x))

    def _check_landing_collision(self):
        """Check for collision with terrain and handle landing or crash"""
        # Get terrain height at current position
        terrain_segment = self.lander_x // 8
        if terrain_segment >= len(self.terrain_elevations):
            return  # Safety check for out of bounds
            
        ground_height = self.terrain_elevations[terrain_segment]
        ground_y = self.SCREEN_HEIGHT - ground_height
        
        # Check if lander has reached the ground level
        if self.lander_y + 5 >= ground_y:
            # Position lander at ground level
            self.lander_y = ground_y - 5
            
            # Check for successful landing
            if (self.platform_x <= self.lander_x <= self.platform_x + 8 and 
                self.velocity_y < self.LANDING_SPEED_MAX and 
                abs(self.velocity_x) < self.LANDING_HORZ_MAX):
                # Successful landing
                self._handle_successful_landing()
            else:
                # Crash landing
                self._handle_crash()

    def _handle_successful_landing(self):
        """Process a successful landing"""
        # Award points for landing plus bonus for remaining fuel
        self.score += self.BASE_LANDING_SCORE + (self.fuel * self.FUEL_SCORE_MULTIPLIER)
        self.landed = True
        # Start next level
        self._start_new_level()

    def _handle_crash(self):
        """Process a crash landing"""
        self.game_over = True
        self.explosion_frame = 0
        pyxel.play(1, 1)  # Play explosion sound

    def draw(self):
        """Main rendering function"""
        # Clear screen with background color
        pyxel.cls(self.colors['background'])

        # Draw game elements
        self._draw_terrain()
        self._draw_landing_pad()
        self._draw_lander()
        self._draw_explosion()
        self._draw_fuel_gauge()
        self._draw_hud()

    def _draw_terrain(self):
        """Draw the terrain grid pattern"""
        for i, elevation in enumerate(self.terrain_elevations):
            # Ensure even elevation for grid pattern
            if elevation % 2 == 1:
                elevation -= 1
                
            # Draw grid pattern for terrain
            for y in range(self.SCREEN_HEIGHT - elevation, self.SCREEN_HEIGHT, 2):
                for x in range(i * 8, i * 8 + 8, 2):
                    pyxel.pset(x, y, self.colors['terrain'])

    def _draw_landing_pad(self):
        """Draw the landing platform"""
        segment = self.platform_x // 8
        if segment < len(self.terrain_elevations):
            height = self.terrain_elevations[segment]
            pyxel.rect(
                self.platform_x, 
                self.SCREEN_HEIGHT - height, 
                8, 1, 
                self.colors['platform']
            )

    def _draw_lander(self):
        """Draw the lunar lander sprite"""
        # Only draw lander if not in explosion animation
        if not self.game_over or self.explosion_frame == -1:
            # Draw ship body
            for y, row in enumerate(self.LANDER_SPRITES):
                for x in range(8):
                    if row & (1 << (7 - x)):
                        pyxel.pset(
                            self.lander_x + x, 
                            self.lander_y + y, 
                            self.colors['lander']
                        )
            
            # Draw thrust flame when active
            if self.thrust_visible and self.fuel > 0:
                for y, row in enumerate(self.THRUST_SPRITES):
                    for x in range(8):
                        if row & (1 << (7 - x)):
                            pyxel.pset(
                                self.lander_x + x, 
                                self.lander_y + 5 + y, 
                                self.colors['flame']
                            )

    def _draw_explosion(self):
        """Draw explosion animation if crashed"""
        if self.explosion_frame >= 0:
            current_frame = self.EXPLOSION_SPRITES[self.explosion_frame]
            for y, row in enumerate(current_frame):
                for x in range(5):
                    if row & (1 << (4 - x)):
                        pyxel.pset(
                            self.lander_x + x + 1, 
                            self.lander_y + y, 
                            self.colors['explosion']
                        )

    def _draw_fuel_gauge(self):
        """Draw the fuel gauge on the right side of the screen"""
        # Draw gauge frame
        pyxel.rect(
            self.FUEL_GAUGE_X, 0, 
            8, self.SCREEN_HEIGHT, 
            self.colors['gauge_frame']
        )
        
        # Draw fuel level bar
        pyxel.rect(
            self.FUEL_GAUGE_X + 1, 
            self.SCREEN_HEIGHT - self.fuel, 
            6, self.fuel, 
            self.colors['gauge_fill']
        )
        
        # Draw "FUEL" text vertically
        self._draw_vertical_text(
            self.FUEL_GAUGE_X + 2, 2, 
            "FUEL", 
            self.colors['lander']
        )

    def _draw_hud(self):
        """Draw the heads-up display with score and level"""
        # Show level and score
        pyxel.text(2, 2, f"LEVEL {self.level}", self.colors['lander'])
        pyxel.text(2, 10, f"SCORE {self.score}", self.colors['lander'])

        # Show game over message when applicable
        if self.game_over and self.explosion_frame >= 4:
            pyxel.text(40, 25, "GAME OVER", self.colors['platform'])

    def _draw_vertical_text(self, x, y, text, color):
        """Draw text vertically, one character per line"""
        for i, char in enumerate(text.upper()):
            pyxel.text(x, y + i * 6, char, color)


LunarLander()