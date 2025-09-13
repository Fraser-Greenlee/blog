import pyxel
import numpy as np
import random

# Game constants
WIDTH = 160
HEIGHT = 180  # Increased depth for larger underground area
DISPLAY_WIDTH = 15  # Zoomed display is 15x15 pixels
DISPLAY_HEIGHT = 15
INVENTORY_HEIGHT = 3  # Height of the inventory bar
TOTAL_DISPLAY_HEIGHT = DISPLAY_HEIGHT + INVENTORY_HEIGHT
BLOCK_SIZE = 1  # Each block is 1 pixel

# Block types
AIR = 0
BEDROCK = 0  # Black
STONE = 13  # Gray
DIRT = 4  # Brown
GRASS = 11  # Light green
WATER = 12  # Blue
SAND = 10  # Light yellow
COAL_ORE = 1  # Dark blue (representing coal in stone)
IRON_ORE = 7  # Light gray
GOLD_ORE = 9  # Orange
DIAMOND_ORE = 3  # Teal

# Block keys (for selecting blocks)
BLOCK_KEYS = {
    pyxel.KEY_1: DIRT,
    pyxel.KEY_2: GRASS,
    pyxel.KEY_3: STONE,
    pyxel.KEY_4: SAND,
    pyxel.KEY_5: WATER,
    pyxel.KEY_6: COAL_ORE,
    pyxel.KEY_7: IRON_ORE,
    pyxel.KEY_8: GOLD_ORE,
    pyxel.KEY_9: DIAMOND_ORE
}

# Mining times (frames) for each block type
MINING_TIMES = {
    STONE: 15,
    DIRT: 10,
    GRASS: 5,
    SAND: 5,
    WATER: 5,
    COAL_ORE: 15,
    IRON_ORE: 15,
    GOLD_ORE: 30,
    DIAMOND_ORE: 60,
    BEDROCK: 999999  # Effectively unmineable
}

# Player constants
PLAYER_COLOR = 8  # Pink (color 8)
PLAYER_HEIGHT = 2  # Player is 2 pixels tall
PLAYER_SPEED = 1
GRAVITY = 0.3
JUMP_FORCE = 1
WATER_SLOWDOWN = 0.5
MINING_RANGE = 5  # How far the player can mine from their position
PLACING_RANGE = 5  # How far the player can place blocks

# Initialize blocks array
blocks = np.zeros((WIDTH, HEIGHT), dtype=np.uint8)
terrain_height = []  # Store the terrain height for collision detection

# Block being mined data
mining_block = {
    "active": False,
    "x": 0,
    "y": 0,
    "type": 0,
    "progress": 0,
    "total_time": 0,
    "flash_state": False,
    "last_mined_x": -1,  # Track last mined block to prevent repeatedly mining same block
    "last_mined_y": -1
}

def generate_terrain():
    """Generate the terrain with improved features like caves and a proper surface layer"""
    global terrain_height
    # Set the base of the world to bedrock
    blocks[:, HEIGHT-1] = BEDROCK
    
    # Create a surface padding area at the top
    surface_padding = 40  # Extra padding at the top of the world for sky
    
    # Generate base terrain height using simplified noise
    terrain_height = []
    base_height = surface_padding + (HEIGHT - surface_padding) * 0.4  # Position terrain below the padding
    
    # Generate a simple terrain height map
    prev_height = int(base_height)
    for x in range(WIDTH):
        # Small random change from previous height
        change = random.randint(-1, 1)
        new_height = prev_height + change
        
        # Ensure height stays within reasonable bounds
        new_height = max(surface_padding, min(HEIGHT - 15, new_height))
        terrain_height.append(new_height)
        prev_height = new_height
    
    # Fill the terrain based on the height map
    for x in range(WIDTH):
        height = terrain_height[x]
        
        # Create a 5-pixel deep surface layer
        surface_depth = 5
        
        # Fill below the surface with dirt and stone
        stone_start = height + surface_depth  # 5 blocks of dirt beneath the surface
        
        # Dirt layer (including the surface blocks)
        for y in range(height, min(stone_start, HEIGHT - 1)):
            blocks[x, y] = DIRT
            
        # Stone layer with occasional ores (no gold - only in caves)
        for y in range(stone_start, HEIGHT - 1):
            blocks[x, y] = STONE
            
            # Add ores with decreasing probability based on depth and value
            ore_chance = random.random()
            depth_factor = (y - stone_start) / (HEIGHT - stone_start - 1)
            
            if ore_chance < 0.01 + depth_factor * 0.05:  # Coal (common)
                blocks[x, y] = COAL_ORE
            elif ore_chance < 0.015 + depth_factor * 0.03:  # Iron (less common)
                blocks[x, y] = IRON_ORE
            elif ore_chance < 0.018 + depth_factor * 0.01 and y > HEIGHT * 0.8:  # Diamond (very rare, deep only)
                blocks[x, y] = DIAMOND_ORE
            # No gold generation here - gold will only be in caves
    
    # Add caves - ensure they start below terrain surface
    generate_caves(surface_padding)
    
    # Add surface features (grass and trees)
    generate_surface_features()

def generate_caves(surface_padding):
    """Generate cave systems underground"""
    # Make sure caves start below the terrain surface
    min_cave_y = surface_padding + 20  # Ensure caves start well below the surface
    
    # First, generate smaller caves in the upper underground (but below surface)
    generate_cave_layer(min_cave_y, HEIGHT * 0.6, 25, 10, 30, 0.5, False)
    
    # Generate medium caves in the middle underground
    generate_cave_layer(HEIGHT * 0.6, HEIGHT * 0.8, 20, 20, 50, 0.6, True)
    
    # Then, generate very large caves deeper underground
    generate_cave_layer(HEIGHT * 0.8, HEIGHT - 10, 10, 40, 100, 0.8, True)
    
    # Finally, generate a few massive caverns
    generate_large_caverns()
    
def generate_large_caverns():
    """Generate a few massive caverns (up to 10 pixels high) in the deep underground"""
    # Create 2-3 massive caverns
    num_caverns = random.randint(2, 3)
    
    for _ in range(num_caverns):
        # Place seed in deep area
        seed_x = random.randint(20, WIDTH - 20)
        seed_y = random.randint(int(HEIGHT * 0.85), HEIGHT - 15)
        
        # Define cavern size (horizontal and vertical)
        width = random.randint(20, 35)
        height = random.randint(6, 10)  # Caves up to 10 blocks high
        
        # Create the main cavern chamber
        for x in range(seed_x - width // 2, seed_x + width // 2):
            if x < 0 or x >= WIDTH:
                continue
                
            for y in range(seed_y - height // 2, seed_y + height // 2):
                if y < 0 or y >= HEIGHT - 1:  # Avoid bedrock
                    continue
                    
                # Distance from center (normalized to 0-1)
                dx = abs(x - seed_x) / (width / 2)
                dy = abs(y - seed_y) / (height / 2)
                
                # Use elliptical equation to create natural cavern shape
                # Add randomness to make edges less perfect
                if dx*dx + dy*dy + random.uniform(-0.1, 0.2) <= 1.0:
                    blocks[x, y] = AIR
                    
                    # Add gold in the walls of the cavern (only on stone blocks)
                    if random.random() < 0.04:  # 4% chance for gold in large caverns
                        # Check adjacent blocks for potential gold placement
                        for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
                            if (0 <= nx < WIDTH and 0 <= ny < HEIGHT - 1 and 
                                blocks[nx, ny] == STONE):
                                blocks[nx, ny] = GOLD_ORE
                                break
    
def generate_cave_layer(min_y, max_y, num_seeds, min_size, max_size, width_chance, add_gold):
    """Generate cave systems in a specific layer of the underground"""
    # Randomly place cave seeds
    cave_seeds = []
    for _ in range(num_seeds):  # Number of cave seeds
        x = random.randint(5, WIDTH - 5)
        # Caves start in the specified section of the underground
        y = random.randint(int(min_y), int(max_y))
        cave_seeds.append((x, y))
    
    # For each seed, grow a cave in random directions
    all_cave_blocks = []  # Keep track of cave blocks for gold deposit placement
    
    for seed_x, seed_y in cave_seeds:
        # Skip if seed is not in stone
        if blocks[seed_x, seed_y] != STONE and blocks[seed_x, seed_y] != DIRT:
            continue
            
        # Start with the seed
        cave_points = [(seed_x, seed_y)]
        blocks[seed_x, seed_y] = AIR
        all_cave_blocks.append((seed_x, seed_y))
        
        # Grow the cave
        cave_size = random.randint(int(min_size), int(max_size))  # Size of this cave system
        for _ in range(cave_size):
            if not cave_points:  # If we've hit a dead end
                break
                
            # Pick a random existing cave point to grow from
            point_idx = random.randint(0, len(cave_points) - 1)
            x, y = cave_points[point_idx]
            
            # Try to grow in a random direction
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                
                # Check bounds
                if 0 <= new_x < WIDTH and terrain_height[new_x] < new_y < HEIGHT - 1:
                    # Only carve through stone or dirt, not surface or bedrock
                    if blocks[new_x, new_y] in [STONE, DIRT, COAL_ORE, IRON_ORE, GOLD_ORE, DIAMOND_ORE]:
                        blocks[new_x, new_y] = AIR
                        cave_points.append((new_x, new_y))
                        all_cave_blocks.append((new_x, new_y))
                        
                        # Add width to the cave - make adjacent blocks air too
                        # For deeper caves, add more width
                        width_blocks = [(new_x+1, new_y), (new_x-1, new_y), (new_x, new_y+1), (new_x, new_y-1)]
                        # Add diagonal blocks for larger caves
                        if y > max_y * 0.7:  # For deeper caves, add even more width with diagonals
                            width_blocks.extend([(new_x+1, new_y+1), (new_x-1, new_y-1), 
                                               (new_x+1, new_y-1), (new_x-1, new_y+1)])
                        
                        # For the deepest caves, occasionally create vertical expansions up to 3-4 blocks high
                        if y > HEIGHT * 0.85 and random.random() < 0.15:
                            # Create vertical shaft
                            vert_height = random.randint(2, 4)
                            for vy in range(1, vert_height + 1):
                                if 0 <= new_y - vy < HEIGHT - 1:
                                    blocks[new_x, new_y - vy] = AIR
                                    all_cave_blocks.append((new_x, new_y - vy))
                        
                        for nx, ny in width_blocks:
                            if (0 <= nx < WIDTH and terrain_height[nx] < ny < HEIGHT - 1 and 
                                blocks[nx, ny] in [STONE, DIRT, COAL_ORE, IRON_ORE, GOLD_ORE, DIAMOND_ORE]):
                                # Chance to expand width (higher for deeper caves)
                                if random.random() < width_chance:
                                    blocks[nx, ny] = AIR
                                    all_cave_blocks.append((nx, ny))
                        break
    
    # Add gold deposits inside caves for the deeper layer
    if add_gold:
        # Find blocks adjacent to the cave air pockets to place gold
        cave_walls = []
        for cave_x, cave_y in all_cave_blocks:
            # Check adjacent blocks to find cave walls
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                wall_x, wall_y = cave_x + dx, cave_y + dy
                if (0 <= wall_x < WIDTH and terrain_height[wall_x] < wall_y < HEIGHT - 1 and 
                    blocks[wall_x, wall_y] == STONE):  # Only replace stone with gold
                    cave_walls.append((wall_x, wall_y))
        
        # Place gold in some of the cave walls (more densely in deeper caves)
        num_gold_deposits = len(cave_walls) // 20  # About 5% of cave walls will have gold
        if cave_walls and num_gold_deposits > 0:
            gold_positions = random.sample(cave_walls, min(num_gold_deposits, len(cave_walls)))
            for gold_x, gold_y in gold_positions:
                blocks[gold_x, gold_y] = GOLD_ORE
                
                # Create small gold veins for some deposits (1-3 connected blocks)
                if random.random() < 0.3:  # 30% chance for a vein
                    vein_size = random.randint(1, 3)
                    for _ in range(vein_size):
                        # Find adjacent stone blocks
                        adjacent_blocks = []
                        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                            adj_x, adj_y = gold_x + dx, gold_y + dy
                            if (0 <= adj_x < WIDTH and terrain_height[adj_x] < adj_y < HEIGHT - 1 and 
                                blocks[adj_x, adj_y] == STONE):
                                adjacent_blocks.append((adj_x, adj_y))
                        
                        # Add gold to a random adjacent block if possible
                        if adjacent_blocks:
                            next_x, next_y = random.choice(adjacent_blocks)
                            blocks[next_x, next_y] = GOLD_ORE
                            gold_x, gold_y = next_x, next_y  # Continue vein from this new point

def generate_surface_features():
    """Generate surface features - add grass on top and trees"""
    # Add grass to the top layer of dirt
    for x in range(WIDTH):
        # Find the top dirt block
        for y in range(HEIGHT):
            if blocks[x, y] == DIRT:
                # Make the top dirt block grass
                blocks[x, y] = GRASS
                break
    
    # Add trees on the grass
    generate_trees()

def generate_trees():
    """Generate trees on the grass surface"""
    # Find suitable spots for trees (grass blocks with space above)
    potential_tree_spots = []
    
    for x in range(5, WIDTH - 5):  # Stay away from edges
        # Check if this is a suitable spot for a tree
        for y in range(HEIGHT):
            if blocks[x, y] == GRASS and all(blocks[x, y-i] == AIR for i in range(1, 8)):
                # We found a grass block with 7 air blocks above it
                # Check if there's enough flat area for a tree (at least 3 blocks wide)
                is_flat = True
                for i in range(-1, 2):
                    if x + i < 0 or x + i >= WIDTH:
                        is_flat = False
                        break
                    # Find the top block for this column
                    for cy in range(HEIGHT):
                        if blocks[x + i, cy] != AIR:
                            # Check if it's close to our current height
                            if abs(cy - y) > 1:
                                is_flat = False
                            break
                
                if is_flat:
                    potential_tree_spots.append((x, y))
                break  # Only check the topmost grass block
    
    # Place trees at some of the potential spots
    num_trees = min(len(potential_tree_spots) // 2, 15)  # Place more trees
    
    # Randomly select spots for trees
    if potential_tree_spots:
        tree_spots = random.sample(potential_tree_spots, min(num_trees, len(potential_tree_spots)))
        
        for x, surface_y in tree_spots:
            # Tree height (2-5 blocks)
            tree_height = random.randint(3, 5)
            
            # Create trunk (dirt blocks)
            for y in range(1, tree_height):
                tree_y = surface_y - y
                if 0 <= tree_y < HEIGHT:
                    blocks[x, tree_y] = DIRT
            
            # Create leaves (grass blocks in a triangle shape)
            leaf_width = min(3, tree_height - 1)
            for y in range(leaf_width + 1):
                leaf_y = surface_y - tree_height - y
                if leaf_y < 0:  # Don't go off the top of the world
                    continue
                    
                # Width of leaves at this level (wider at the bottom, narrower at top)
                width = 2 * (leaf_width - y) + 1
                width = max(1, min(width, 5))  # Ensure width is between 1-5
                half_width = width // 2
                
                # Place leaves
                for i in range(-half_width, half_width + 1):
                    leaf_x = x + i
                    if 0 <= leaf_x < WIDTH and 0 <= leaf_y < HEIGHT:
                        # Only replace air or overwrite other leaves
                        if blocks[leaf_x, leaf_y] == AIR or blocks[leaf_x, leaf_y] == GRASS:
                            blocks[leaf_x, leaf_y] = GRASS

class Camera:
    def __init__(self, target=None):
        self.target = target
        self.x = 0
        self.y = 0
        self.width = DISPLAY_WIDTH
        self.height = DISPLAY_HEIGHT
    
    def update(self):
        if self.target:
            # Center camera on target
            self.x = int(self.target.x - self.width // 2)
            self.y = int(self.target.y - self.height // 2)
            
            # Keep camera within world bounds
            self.x = max(0, min(WIDTH - self.width, self.x))
            self.y = max(0, min(HEIGHT - self.height, self.y))
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        world_x = screen_x + self.x
        world_y = screen_y + self.y
        return world_x, world_y

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_y = 0
        self.on_ground = False
        self.in_water = False
    
    def update(self):
        # Handle left/right movement
        if pyxel.btn(pyxel.KEY_LEFT):
            self.move(-PLAYER_SPEED)
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.move(PLAYER_SPEED)
        
        # Handle jumping
        if pyxel.btnp(pyxel.KEY_SPACE) and self.on_ground:
            self.vel_y = -JUMP_FORCE
            self.on_ground = False
        
        # Apply gravity
        speed_modifier = WATER_SLOWDOWN if self.in_water else 1.0
        self.vel_y += GRAVITY * speed_modifier
        
        # Limit falling speed
        max_fall_speed = 3 if not self.in_water else 1.5
        self.vel_y = min(self.vel_y, max_fall_speed)
        
        # Apply vertical velocity
        self.y += self.vel_y
        
        # Check collision with terrain
        self.check_collision()
        
        # Check if in water
        feet_y = int(self.y + PLAYER_HEIGHT - 1)
        head_y = int(self.y)
        self.in_water = (0 <= int(self.x) < WIDTH and 
                         ((0 <= feet_y < HEIGHT and blocks[int(self.x), feet_y] == WATER) or
                          (0 <= head_y < HEIGHT and blocks[int(self.x), head_y] == WATER)))
    
    def move(self, dx):
        # Apply water slowdown if applicable
        if self.in_water:
            dx *= WATER_SLOWDOWN
        
        # Apply movement
        new_x = self.x + dx
        
        # Check horizontal collision
        feet_y = int(self.y + PLAYER_HEIGHT - 1)
        body_y = int(self.y + PLAYER_HEIGHT // 2)
        
        # Ensure we don't go off the screen edges
        if new_x < 0:
            new_x = 0
        elif new_x >= WIDTH:
            new_x = WIDTH - 1
        
        # Check collision with terrain horizontally
        if (0 <= feet_y < HEIGHT and 
            blocks[int(new_x), feet_y] not in [AIR, WATER]):
            # There's a block at foot level, check if we can step up
            if (feet_y - 1 >= 0 and 
                blocks[int(new_x), feet_y - 1] in [AIR, WATER]):
                # We can step up one block
                self.y -= 1
                self.x = new_x
            # Otherwise, we can't move
        elif (0 <= body_y < HEIGHT and 
              blocks[int(new_x), body_y] not in [AIR, WATER]):
            # There's a block at body level, we can't move
            pass
        else:
            # No collision, proceed with movement
            self.x = new_x
    
    def check_collision(self):
        # Check collision below (feet)
        feet_y = int(self.y + PLAYER_HEIGHT)
        
        # First, check if we're still within the world bounds
        if feet_y >= HEIGHT:
            self.y = HEIGHT - PLAYER_HEIGHT
            self.vel_y = 0
            self.on_ground = True
            return
        
        # Check if standing on a solid block
        if 0 <= int(self.x) < WIDTH and feet_y < HEIGHT:
            block_below = blocks[int(self.x), feet_y]
            
            if block_below not in [AIR, WATER]:
                # Collision with terrain
                self.y = feet_y - PLAYER_HEIGHT  # Position precisely on top of the block
                self.vel_y = 0
                self.on_ground = True
            else:
                self.on_ground = False
        
        # Check collision above (head)
        head_y = int(self.y - 1)
        if head_y >= 0 and head_y < HEIGHT and int(self.x) < WIDTH:
            block_above = blocks[int(self.x), head_y]
            
            if block_above not in [AIR, WATER]:
                # Hit head on a block
                self.y = head_y + 1
                self.vel_y = 0
    
    def draw(self, camera):
        # Only draw if player is in camera view
        screen_x = int(self.x) - camera.x
        screen_y = int(self.y) - camera.y
        
        if (0 <= screen_x < DISPLAY_WIDTH and 
            0 <= screen_y < DISPLAY_HEIGHT):
            pyxel.pset(screen_x, screen_y, PLAYER_COLOR)  # Head
        
        if (0 <= screen_x < DISPLAY_WIDTH and 
            0 <= screen_y + 1 < DISPLAY_HEIGHT):
            pyxel.pset(screen_x, screen_y + 1, PLAYER_COLOR)  # Body
    
    def can_reach_block(self, block_x, block_y):
        """Check if the player can reach a block for mining/placing"""
        dx = abs(block_x - self.x)
        dy = abs(block_y - self.y)
        distance = max(dx, dy)  # Use maximum distance (Chebyshev distance)
        return distance <= MINING_RANGE

class Game:
    def __init__(self):
        # Initialize Pyxel with the zoomed display size plus inventory bar
        pyxel.init(DISPLAY_WIDTH, TOTAL_DISPLAY_HEIGHT, title="2D Minecraft Demake", fps=30, display_scale=8)
        
        generate_terrain()
        
        # Create player at a good starting position
        spawn_x = WIDTH // 2
        spawn_y = 0
        # Find suitable y position just above the terrain
        for y in range(HEIGHT):
            if y + PLAYER_HEIGHT < HEIGHT and blocks[spawn_x, y + PLAYER_HEIGHT] != AIR:
                spawn_y = y - 2  # Position player slightly above the ground
                break
        # Ensure player is not spawning too deep
        if spawn_y > HEIGHT // 2:
            spawn_y = HEIGHT // 4
        
        self.player = Player(spawn_x, spawn_y)
        self.camera = Camera(self.player)
        
        # Initialize inventory
        # Dictionary of block types the player has with counts
        self.inventory = {
            DIRT: 5,     # Start with 5 dirt blocks
            GRASS: 3,    # Start with 3 grass blocks
            STONE: 0,
            SAND: 0,
            WATER: 0,
            COAL_ORE: 0,
            IRON_ORE: 0,
            GOLD_ORE: 0,
            DIAMOND_ORE: 0
        }
        
        # Selected block for placement
        self.selected_block = DIRT  # Start with dirt selected
        
        # Mining settings
        self.flash_counter = 0
        self.flash_rate = 3  # Frames per flash
        
        pyxel.run(self.update, self.draw)
    
    def update(self):
        # Check for quit
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        # Update player
        self.player.update()
        
        # Update camera to follow player
        self.camera.update()
        
        # Handle block selection
        self.handle_block_selection()
        
        # Handle mining
        self.handle_mining()
        
        # Handle block placing
        self.handle_placing()
        
        # Update mining progress
        self.update_mining_progress()
    
    def handle_block_selection(self):
        # Check number keys for block selection
        for key, block_type in BLOCK_KEYS.items():
            if pyxel.btnp(key):
                # Only select if player has this block
                if self.inventory.get(block_type, 0) > 0:
                    self.selected_block = block_type
    
    def find_next_available_block(self):
        """Find the next available block in inventory after current selection is depleted"""
        # Get all block types in order of their keys
        block_types = [block_type for _, block_type in sorted(BLOCK_KEYS.items())]
        
        # Find current block index
        try:
            current_index = block_types.index(self.selected_block)
        except ValueError:
            current_index = -1
        
        # Search for next available block, starting after current
        for i in range(1, len(block_types) + 1):
            next_index = (current_index + i) % len(block_types)
            block_type = block_types[next_index]
            if self.inventory.get(block_type, 0) > 0:
                self.selected_block = block_type
                return
        
        # If no blocks available, default to first type (even with 0 count)
        self.selected_block = block_types[0]
    
    def handle_mining(self):
        # Start mining a block on mouse click or continue mining if mouse is held down
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            # If we're not currently mining a block, or if we've finished mining a block,
            # try to start mining a new block
            if not mining_block["active"]:
                # Convert screen coordinates to world coordinates
                world_x, world_y = self.camera.screen_to_world(pyxel.mouse_x, pyxel.mouse_y)
                
                # Skip if this is the block we just mined to prevent immediately re-mining it
                if (world_x == mining_block["last_mined_x"] and 
                    world_y == mining_block["last_mined_y"]):
                    return
                
                # Check if clicked position is within world bounds
                if (0 <= world_x < WIDTH and 0 <= world_y < HEIGHT):
                    # Check if there's a block to mine
                    block_type = blocks[world_x, world_y]
                    
                    # Don't mine AIR
                    if block_type != AIR:
                                        # Check if player can reach this block
                        if self.player.can_reach_block(world_x, world_y):
                            # Start mining this block
                            mining_block["active"] = True
                            mining_block["x"] = world_x
                            mining_block["y"] = world_y
                            mining_block["type"] = block_type
                            mining_block["progress"] = 0
                            mining_block["total_time"] = MINING_TIMES.get(block_type, 30)
                            mining_block["flash_state"] = False
    
    def handle_placing(self):
        # Place a block with right mouse button
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            # Convert screen coordinates to world coordinates
            world_x, world_y = self.camera.screen_to_world(pyxel.mouse_x, pyxel.mouse_y)
            
            # Check if clicked position is within world bounds
            if (0 <= world_x < WIDTH and 0 <= world_y < HEIGHT):
                # Check if there's no block at this position (can only place on AIR)
                if blocks[world_x, world_y] == AIR:
                    # Check if player can reach this position
                    if self.player.can_reach_block(world_x, world_y):
                        # Check if placing block here would trap the player
                        player_x, player_y = int(self.player.x), int(self.player.y)
                        player_body_y = int(self.player.y + 1)
                        
                        # Don't place block on player
                        if not (world_x == player_x and (world_y == player_y or world_y == player_body_y)):
                            # Check if player has this block in inventory
                            if self.inventory.get(self.selected_block, 0) > 0:
                                # Place the selected block
                                blocks[world_x, world_y] = self.selected_block
                                
                                # Decrease block count in inventory
                                self.inventory[self.selected_block] -= 1
                                
                                # If we're out of this block type, select a different block if available
                                if self.inventory[self.selected_block] <= 0:
                                    self.find_next_available_block()
    
    def update_mining_progress(self):
        # Update mining progress if we're mining a block
        if mining_block["active"]:
            # Increment progress
            mining_block["progress"] += 1
            
            # Update flash state
            self.flash_counter += 1
            if self.flash_counter >= self.flash_rate:
                self.flash_counter = 0
                mining_block["flash_state"] = not mining_block["flash_state"]
            
            # Check if mining is complete
            if mining_block["progress"] >= mining_block["total_time"]:
                # Mining complete, add to inventory
                block_type = mining_block["type"]
                self.inventory[block_type] = self.inventory.get(block_type, 0) + 1
                
                # Remove block from world
                blocks[mining_block["x"], mining_block["y"]] = AIR
                
                # Store the position of the last mined block
                mining_block["last_mined_x"] = mining_block["x"]
                mining_block["last_mined_y"] = mining_block["y"]
                
                # Reset mining state
                mining_block["active"] = False
            
            # Check if player is still in range
            elif not self.player.can_reach_block(mining_block["x"], mining_block["y"]):
                # Player moved out of range, cancel mining
                mining_block["active"] = False
            
            # Check if user is still holding mouse button
            elif not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
                # Player released mouse button, cancel mining
                mining_block["active"] = False
    
    def draw(self):
        pyxel.cls(0)
        
        # Only draw blocks that are within the camera view
        for x in range(self.camera.width):
            for y in range(self.camera.height):
                # Convert screen coordinates to world coordinates
                world_x = x + self.camera.x
                world_y = y + self.camera.y
                
                # Make sure we're within the world bounds
                if 0 <= world_x < WIDTH and 0 <= world_y < HEIGHT:
                    block_type = blocks[world_x, world_y]
                    
                    # Check if this is the block being mined
                    is_mining_block = (mining_block["active"] and 
                                      world_x == mining_block["x"] and 
                                      world_y == mining_block["y"])
                    
                    # Draw the block
                    if block_type != AIR:  # Don't draw air blocks
                        # If it's the block being mined and in a flash state, draw as black
                        if is_mining_block and mining_block["flash_state"]:
                            pyxel.pset(x, y, BEDROCK)  # Flash to black
                        else:
                            pyxel.pset(x, y, block_type)
        
        # Draw player relative to camera
        self.player.draw(self.camera)
        
        # Draw inventory bar
        self.draw_inventory()
        
        # Draw mining progress bar if mining
        if mining_block["active"]:
            self.draw_mining_progress()
        
        # Draw mining/placing indicator on mouse hover
        self.draw_interaction_indicator()
    
    def draw_inventory(self):
        # Draw background for inventory bar
        for y in range(DISPLAY_HEIGHT, TOTAL_DISPLAY_HEIGHT):
            for x in range(DISPLAY_WIDTH):
                pyxel.pset(x, y, 0)  # Black background
        
        # Define inventory slots - each material gets a 1-pixel space
        inventory_items = [
            (DIRT, 1),
            (GRASS, 2),
            (STONE, 3),
            (SAND, 4),
            (WATER, 5),
            (COAL_ORE, 6),
            (IRON_ORE, 7),
            (GOLD_ORE, 8),
            (DIAMOND_ORE, 9),
        ]
        
        # Draw inventory items
        for block_type, x_pos in inventory_items:
            block_count = self.inventory.get(block_type, 0)
            if block_count > 0:
                # Draw filled slot if player has this material
                pyxel.pset(x_pos, DISPLAY_HEIGHT + 1, block_type)
                
                # Draw white pixel under selected block
                if block_type == self.selected_block:
                    pyxel.pset(x_pos, DISPLAY_HEIGHT + 2, 7)  # White (color 7)
    
    def draw_mining_progress(self):
        # The flashing effect on the block itself is sufficient visual feedback
        pass
    
    def draw_interaction_indicator(self):
        # Get world coordinates of mouse position
        mouse_world_x, mouse_world_y = self.camera.screen_to_world(pyxel.mouse_x, pyxel.mouse_y)
        
        # Check if mouse is within display bounds
        if 0 <= pyxel.mouse_x < DISPLAY_WIDTH and 0 <= pyxel.mouse_y < DISPLAY_HEIGHT:
            # Check if position is valid and within world bounds
            if 0 <= mouse_world_x < WIDTH and 0 <= mouse_world_y < HEIGHT:
                block_type = blocks[mouse_world_x, mouse_world_y]
                can_reach = self.player.can_reach_block(mouse_world_x, mouse_world_y)
                
                if block_type != AIR:
                    # Show mining indicator (green for in range, pink for out of range)
                    if can_reach:
                        pyxel.pset(pyxel.mouse_x, pyxel.mouse_y, 11)  # Green for mining
                    else:
                        pyxel.pset(pyxel.mouse_x, pyxel.mouse_y, 8)   # Pink for out of range
                else:
                    # Show placing indicator (white for in range, pink for out of range)
                    if can_reach:
                        # Check if placing would trap player
                        player_x, player_y = int(self.player.x), int(self.player.y)
                        player_body_y = int(self.player.y + 1)
                        
                        # Check if player has selected block in inventory
                        has_block = self.inventory.get(self.selected_block, 0) > 0
                        
                        if (mouse_world_x == player_x and 
                            (mouse_world_y == player_y or mouse_world_y == player_body_y)):
                            # Can't place here (would trap player)
                            pyxel.pset(pyxel.mouse_x, pyxel.mouse_y, 8)  # Pink 
                        elif not has_block:
                            # Don't have this block in inventory
                            pyxel.pset(pyxel.mouse_x, pyxel.mouse_y, 8)  # Pink
                        else:
                            # Can place block here
                            pyxel.pset(pyxel.mouse_x, pyxel.mouse_y, 7)  # White for placing
                    else:
                        pyxel.pset(pyxel.mouse_x, pyxel.mouse_y, 8)   # Pink for out of range

if __name__ == "__main__":
    Game()