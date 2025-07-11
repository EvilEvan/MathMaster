import tkinter as tk
import random
import math
import time
import logging
from Explosions import ExplosionManager

class WormAnimation:
    def __init__(self, canvas, canvas_width=None, canvas_height=None, symbol_transport_callback=None, symbol_targeted_for_steal_callback=None):
        """Initialize the worm animation on the specified canvas.
        
        Args:
            canvas: The tkinter canvas where the worm will be drawn
            canvas_width: Optional initial width of the canvas
            canvas_height: Optional initial height of the canvas
            symbol_transport_callback: Callback function when a symbol is transported
                                      Should accept (line_idx, char_idx, char) parameters
            symbol_targeted_for_steal_callback: Callback when a worm targets a symbol for stealing
                                              Should accept (worm_id, symbol_data dict)
        """
        self.canvas = canvas
        self.width = canvas_width or canvas.winfo_width()
        self.height = canvas_height or canvas.winfo_height()
        self.worms = []
        self.animation_running = False
        self.animation_speed = 1.0  # Base speed multiplier
        self.after_id = None
        self.worm_segments = 8  # Number of segments in the worm
        self.worm_size = 12  # Base size of each segment
        self.blink_timer = 0  # Timer for blinking
        self.mouth_state = 0  # 0 = closed, 1 = opening, 2 = open, 3 = closing
        self.mouth_timer = 0  # Timer for mouth animation
        
        # Added for solution symbol interactions
        self.solution_symbols = []  # List to store visible solution symbol coordinates and info
        self.interaction_enabled = False  # Flag to control when interaction is enabled
        self.interaction_cooldown = {}  # Cooldown for interactions per worm
        self.symbol_shake_ids = {}  # Track active symbol shake animations
        self.interaction_particles = []  # Particle effects for interactions
        
        # Symbol transport functionality (Window B to C)
        self.symbol_transport_callback = symbol_transport_callback
        self.transport_timer = None
        self.transport_interval = 10000  # 10 seconds (reduced from 15000)
        self.transporting_symbols = {}  # Track symbols being transported
        self.symbol_targeted_for_steal_callback = symbol_targeted_for_steal_callback # New callback
        
        # Initialize Explosion Manager
        self.explosion_manager = ExplosionManager(self.canvas)
        
        # Bind to canvas resize events
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        
        # Max worms and click handling
        self.max_worms = 4
        self.canvas.tag_bind("worm_segment_clickable", "<Button-1>", self.handle_worm_click) # Bind to a new tag
        
        self.lsd_colors = [
            "#FF00FF",  # Magenta
            "#00FFFF",  # Cyan
            "#FFFF00",  # Yellow
            "#FF0000",  # Red
            "#00FF00",  # Lime Green
            "#0000FF",  # Blue
            "#FF69B4",  # Hot Pink
            "#FFA500",  # Orange
            "#ADFF2F",  # GreenYellow
            "#EE82EE"   # Violet
        ]
        self.flicker_counter = 0 # For controlling flicker speed
        self.lsd_flicker_rate = 5 # Lower is faster flicker for segment cycling

        logging.info("WormAnimation initialized")

    def on_canvas_resize(self, event=None):
        """Handle canvas resize events"""
        self.width = self.canvas.winfo_width()
        self.height = self.canvas.winfo_height()
        logging.info(f"Canvas resized to {self.width}x{self.height}")
        
    def create_worm(self, num_worms=1):
        """Create the specified number of worms on the canvas"""
        if not self.width or self.width <= 1 or not self.height or self.height <= 1:
            # Canvas not properly sized yet, try to get dimensions
            self.width = self.canvas.winfo_width()
            self.height = self.canvas.winfo_height()
            if not self.width or self.width <= 1 or not self.height or self.height <= 1:
                # Still not proper dimensions, schedule to try again shortly
                self.canvas.after(100, lambda: self.create_worm(num_worms))
                return

        # Create the specified number of worms
        for _ in range(num_worms):
            # Create a new worm with random starting position and direction
            worm = {
                'x': random.randint(50, self.width - 50),
                'y': random.randint(50, self.height - 50),
                'angle': random.uniform(0, 2 * math.pi),
                'segments': [],
                'eyes': [],
                'mouth': None,
                'blink_state': False,
                'blink_timer': random.randint(50, 200),  # Random initial blink time
                'mouth_state': 0,  # 0 = closed, 1 = open
                'mouth_timer': random.randint(20, 100),  # Random initial mouth time
                'history': [(0, 0)] * self.worm_segments,  # Position history for segments
                'segment_size': self.worm_size + random.randint(-2, 2),  # Slight size variation
                'color': f"#{random.randint(60, 120):02x}{random.randint(140, 180):02x}{random.randint(60, 100):02x}",  # Earthy colors
                'last_interaction_time': 0,  # Track when last interacted with a symbol
                'target_symbol': None,  # Target symbol when in hunting mode
                'id': random.randint(1000, 9999)  # Unique ID for this worm
            }
            
            # Draw the initial worm
            self._draw_worm(worm)
            
            # Add to the list of worms
            self.worms.append(worm)
            
        logging.info(f"Created {num_worms} worms")
        
    def add_worm(self):
        """Adds a single new worm to the animation."""
        if not self.animation_running:
            logging.warning("Attempted to add worm, but animation is not running.")
            # Optionally, start animation if no worms exist?
            # For now, just return or log.
            return

        if not self.width or self.width <= 1 or not self.height or self.height <= 1:
            self.width = self.canvas.winfo_width()
            self.height = self.canvas.winfo_height()
            if not self.width or self.width <= 1 or not self.height or self.height <= 1:
                logging.warning("Cannot add worm, canvas dimensions not ready.")
                self.canvas.after(100, self.add_worm) # Try again shortly
                return

        # Create a new worm with random starting position and direction
        new_worm = {
            'x': random.randint(50, self.width - 50),
            'y': random.randint(50, self.height - 50),
            'angle': random.uniform(0, 2 * math.pi),
            'segments': [],
            'eyes': [],
            'mouth': None,
            'blink_state': False,
            'blink_timer': random.randint(50, 200),
            'mouth_state': 0,
            'mouth_timer': random.randint(20, 100),
            'history': [(0, 0)] * self.worm_segments,
            'segment_size': self.worm_size + random.randint(-2, 2),
            'color': f"#{random.randint(60, 120):02x}{random.randint(140, 180):02x}{random.randint(60, 100):02x}",
            'last_interaction_time': 0,
            'target_symbol': None,
            'id': random.randint(10000, 19999) # Ensure unique ID range if needed
        }
        
        # Draw the initial worm
        # self._draw_worm(new_worm) # _draw_worm will be called by _update_worm via animate loop
        
        # Add to the list of worms
        self.worms.append(new_worm)
        logging.info(f"Added a new worm. Total worms: {len(self.worms)}")
        
    def _draw_worm(self, worm):
        """Draw a single worm with all its components"""
        if not self.canvas.winfo_exists():
            return
            
        # Clear previous segments
        for segment in worm['segments']:
            self.canvas.delete(segment)
        worm['segments'] = []
        
        # Clear previous eyes
        for eye in worm['eyes']:
            self.canvas.delete(eye)
        worm['eyes'] = []
        
        # Clear previous mouth
        if worm['mouth']:
            self.canvas.delete(worm['mouth'])
            worm['mouth'] = None
            
        # Determine current color for the worm
        is_transporting = bool(worm.get('transport_target'))

        # Create segments in reverse order (tail to head)
        for i in range(self.worm_segments - 1, -1, -1):
            if i >= len(worm['history']):
                continue
                
            x, y = worm['history'][i]
            if x == 0 and y == 0:  # Skip initial empty positions
                continue
                
            # Calculate segment size - gradually smaller toward the tail
            segment_size = int(worm['segment_size'] * (0.7 + 0.3 * (i / self.worm_segments)))
            
            # Create segment with enhanced visuals
            if is_transporting:
                segment_color_index = (i + int(self.flicker_counter / self.lsd_flicker_rate)) % len(self.lsd_colors)
                segment_fill_color = self.lsd_colors[segment_color_index]
                # Add glow effect for transporting worms
                glow = self.canvas.create_oval(
                    x - segment_size - 2, y - segment_size - 2,
                    x + segment_size + 2, y + segment_size + 2,
                    fill="",
                    outline=segment_fill_color,
                    width=1.5,
                    tags=("worm_glow", f"worm_{worm['id']}")
                )
                worm['segments'].append(glow)
            else:
                segment_fill_color = worm['color'] # Normal worm color
            
            # Create main segment
            segment = self.canvas.create_oval(
                x - segment_size, y - segment_size,
                x + segment_size, y + segment_size,
                fill=segment_fill_color,
                outline="",
                tags=("worm_segment", f"worm_{worm['id']}", "worm_segment_clickable")
            )
            worm['segments'].append(segment)
            
            # Add highlight to give 3D effect (only for head and middle segments)
            if i < self.worm_segments // 2:
                # Calculate lighter color for highlight
                if not is_transporting:
                    r = int(segment_fill_color[1:3], 16)
                    g = int(segment_fill_color[3:5], 16)
                    b = int(segment_fill_color[5:7], 16)
                    
                    # Brighten color for highlight
                    highlight_r = min(255, r + 50)
                    highlight_g = min(255, g + 50)
                    highlight_b = min(255, b + 50)
                    highlight_color = f"#{highlight_r:02x}{highlight_g:02x}{highlight_b:02x}"
                    
                    # Add small highlight circle in upper left of segment
                    highlight_size = segment_size * 0.4
                    highlight_x = x - segment_size * 0.3
                    highlight_y = y - segment_size * 0.3
                    
                    highlight = self.canvas.create_oval(
                        highlight_x - highlight_size, highlight_y - highlight_size,
                        highlight_x + highlight_size, highlight_y + highlight_size,
                        fill=highlight_color,
                        outline="",
                        tags=("worm_highlight", f"worm_{worm['id']}")
                    )
                    worm['segments'].append(highlight)
            
        # Add eyes only if we have segments
        if worm['segments']:
            # Head position is the first entry in the history
            head_x, head_y = worm['history'][0]
            angle = worm['angle']
            
            # Eye size
            eye_size = int(worm['segment_size'] * 0.4)
            
            # Eye positions (on either side of the head)
            eye_offset = worm['segment_size'] * 0.5
            left_eye_x = head_x + math.cos(angle + math.pi/4) * eye_offset
            left_eye_y = head_y + math.sin(angle + math.pi/4) * eye_offset
            right_eye_x = head_x + math.cos(angle - math.pi/4) * eye_offset
            right_eye_y = head_y + math.sin(angle - math.pi/4) * eye_offset
            
            # Draw eyes with enhanced details - white background with gradient
            # Draw eye whites with subtle shading
            left_eye_bg = self.canvas.create_oval(
                left_eye_x - eye_size, left_eye_y - eye_size,
                left_eye_x + eye_size, left_eye_y + eye_size,
                fill="white",
                outline="#DDDDDD",
                width=1,
                tags=("worm_eye", f"worm_{worm['id']}")
            )
            right_eye_bg = self.canvas.create_oval(
                right_eye_x - eye_size, right_eye_y - eye_size,
                right_eye_x + eye_size, right_eye_y + eye_size,
                fill="white",
                outline="#DDDDDD",
                width=1,
                tags=("worm_eye", f"worm_{worm['id']}")
            )
            worm['eyes'].extend([left_eye_bg, right_eye_bg])
            
            # Add a tiny highlight in each eye
            for eye_x, eye_y in [(left_eye_x, left_eye_y), (right_eye_x, right_eye_y)]:
                highlight = self.canvas.create_oval(
                    eye_x - eye_size*0.3, eye_y - eye_size*0.3,
                    eye_x - eye_size*0.1, eye_y - eye_size*0.1,
                    fill="white",
                    outline="",
                    tags=("worm_eye_highlight", f"worm_{worm['id']}")
                )
                worm['eyes'].append(highlight)
            
            # Pupil size
            pupil_size = int(eye_size * 0.6)
            
            # Draw pupils - if not blinking
            if not worm['blink_state']:
                left_pupil = self.canvas.create_oval(
                    left_eye_x - pupil_size, left_eye_y - pupil_size,
                    left_eye_x + pupil_size, left_eye_y + pupil_size,
                    fill="black",
                    outline="#333333",
                    width=1,
                    tags=("worm_eye", f"worm_{worm['id']}")
                )
                right_pupil = self.canvas.create_oval(
                    right_eye_x - pupil_size, right_eye_y - pupil_size,
                    right_eye_x + pupil_size, right_eye_y + pupil_size,
                    fill="black",
                    outline="#333333",
                    width=1,
                    tags=("worm_eye", f"worm_{worm['id']}")
                )
                worm['eyes'].extend([left_pupil, right_pupil])
            
            # Draw mouth with enhanced detail
            mouth_offset = worm['segment_size'] * 0.7
            mouth_x = head_x + math.cos(angle) * mouth_offset
            mouth_y = head_y + math.sin(angle) * mouth_offset
            
            mouth_width = int(worm['segment_size'] * 0.6)
            mouth_height = int(worm['segment_size'] * (0.1 if worm['mouth_state'] == 0 else 0.4))
            
            # First add mouth interior (darker red)
            if worm['mouth_state'] != 0:  # Only if mouth is open
                inner_mouth = self.canvas.create_oval(
                    mouth_x - mouth_width * 0.9, mouth_y - mouth_height * 0.9,
                    mouth_x + mouth_width * 0.9, mouth_y + mouth_height * 0.9,
                    fill="#801515",  # Darker red for inside of mouth
                    outline="",
                    tags=("worm_mouth_inner", f"worm_{worm['id']}")
                )
                worm['mouth'] = inner_mouth
            
            # Then add main mouth
            outer_mouth = self.canvas.create_oval(
                mouth_x - mouth_width, mouth_y - mouth_height,
                mouth_x + mouth_width, mouth_y + mouth_height,
                fill="#AA3333",  # Reddish mouth
                outline="#882222",  # Darker outline
                width=1,
                tags=("worm_mouth", f"worm_{worm['id']}")
            )
            if worm['mouth'] is None:
                worm['mouth'] = outer_mouth
            else:
                # Append to segments since mouth already set
                worm['segments'].append(outer_mouth)
        
    def animate(self):
        """Main animation loop for all worms"""
        if not self.animation_running:
            return
            
        # Check canvas exists before any operations
        if not self.canvas or not self.canvas.winfo_exists():
            logging.warning("Canvas destroyed during animation, stopping worm animation")
            self.animation_running = False
            return
            
        try:
            # Get current canvas dimensions (in case of resize)
            current_width = self.canvas.winfo_width()
            current_height = self.canvas.winfo_height()
            if current_width > 1 and current_height > 1:
                self.width, self.height = current_width, current_height
                
            # Increment flicker counter for LSD effect
            self.flicker_counter += 1

            # Update each worm
            for worm in self.worms:
                self._update_worm(worm)
                
            # Update any interaction particles
            self._update_particles()
                
            # Schedule next animation frame only if still running and canvas exists
            if self.animation_running and self.canvas.winfo_exists():
                self.after_id = self.canvas.after(50, self.animate)
            else:
                logging.info("Animation stopped due to canvas destruction or animation flag")
                
        except tk.TclError as e:
            logging.warning(f"TclError in worm animation (canvas likely destroyed): {e}")
            self.animation_running = False
        except Exception as e:
            logging.error(f"Error in worm animation: {e}")
            # Don't stop animation for other errors, but log them
            
    def _update_worm(self, worm):
        """Update a single worm's position and appearance"""
        if not self.canvas.winfo_exists(): return

        # Update canvas dimensions if necessary
        current_width = self.canvas.winfo_width()
        current_height = self.canvas.winfo_height()
        if current_width > 1 and current_height > 1:
            self.width, self.height = current_width, current_height
            
        # If worm is transporting a symbol, prioritize that behavior
        if worm.get('transport_target'):
            # Movement is largely handled by _begin_transport_animation during push
            # Here, we just ensure its mouth stays open and it doesn't wander off too much
            target_symbol = worm['transport_target']
            sym_pos_on_canvas = self.canvas.coords(target_symbol.get('id'))
            
            if sym_pos_on_canvas:
                sym_x, sym_y = sym_pos_on_canvas # Current position of symbol being pushed
                target_x_for_worm = sym_x
                target_y_for_worm = sym_y + worm['segment_size'] * 1.5

                dx = target_x_for_worm - worm['x']
                dy = target_y_for_worm - worm['y']
                target_angle = math.atan2(dy, dx)
                
                angle_diff = (target_angle - worm['angle'] + math.pi) % (2 * math.pi) - math.pi
                worm['angle'] += angle_diff * 0.1 # Gentle turning to stay aligned

            # Speed is controlled by 'speed_multiplier' set in _begin_transport_animation
            speed = 3 * self.animation_speed * worm.get('speed_multiplier', 1.0)
            
        else:
            # Check for interaction with solution symbols if enabled
            if self.interaction_enabled and self.animation_speed > 1.0:
                self._check_symbol_interaction(worm)
            
            # If worm has a target symbol, move toward it
            if worm.get('target_symbol') and random.random() < 0.7:  # 70% chance to follow target
                target_x, target_y = worm['target_symbol']['position']
                head_x, head_y = worm['history'][0] if worm['history'][0] != (0, 0) else (worm['x'], worm['y'])
                
                # Calculate angle to target
                dx = target_x - head_x
                dy = target_y - head_y
                target_angle = math.atan2(dy, dx)
                
                # Gradually turn toward target
                angle_diff = (target_angle - worm['angle'] + math.pi) % (2 * math.pi) - math.pi
                worm['angle'] += angle_diff * 0.2  # Smooth turning
            else:
                # Randomly change direction occasionally
                if random.random() < 0.05:
                    worm['angle'] += random.uniform(-math.pi/4, math.pi/4)
                
            # Apply speed based on animation_speed
            speed = 3 * self.animation_speed * worm.get('speed_multiplier', 1.0) # Apply multiplier here too
        
        # Calculate new position
        new_x = worm['x'] + math.cos(worm['angle']) * speed
        new_y = worm['y'] + math.sin(worm['angle']) * speed
        
        # Bounce off walls (less aggressive bouncing if transporting)
        bounced = False
        wall_margin = worm['segment_size']
        if not worm.get('transport_target'): # Normal bouncing if not transporting
            if new_x < wall_margin or new_x > self.width - wall_margin:
                worm['angle'] = math.pi - worm['angle']
                bounced = True
            if new_y < wall_margin or new_y > self.height - wall_margin:
                worm['angle'] = -worm['angle']
                bounced = True
        else: # More constrained movement if transporting to avoid erratic bounces
            if new_x < wall_margin: new_x = wall_margin; worm['angle'] += math.pi/2
            if new_x > self.width - wall_margin: new_x = self.width - wall_margin; worm['angle'] += math.pi/2
            if new_y < wall_margin: new_y = wall_margin; worm['angle'] += math.pi/2
            if new_y > self.height - wall_margin: new_y = self.height - wall_margin; worm['angle'] += math.pi/2
            
        # Add some wiggle to the movement
        if not bounced and random.random() < 0.1 and not worm.get('transport_target'):
            worm['angle'] += random.uniform(-math.pi/8, math.pi/8)
            
        # Update position
        worm['x'] = new_x # Use potentially corrected new_x, new_y
        worm['y'] = new_y
        
        # Ensure we stay within bounds (redundant if above logic is perfect, but good for safety)
        worm['x'] = max(wall_margin, min(self.width - wall_margin, worm['x']))
        worm['y'] = max(wall_margin, min(self.height - wall_margin, worm['y']))
        
        # Update position history
        worm['history'].insert(0, (worm['x'], worm['y']))
        worm['history'] = worm['history'][:self.worm_segments]
        
        # Handle blinking
        worm['blink_timer'] -= 1
        if worm['blink_timer'] <= 0:
            worm['blink_state'] = not worm['blink_state']
            # Shorter blink, longer open eyes
            worm['blink_timer'] = random.randint(5, 10) if worm['blink_state'] else random.randint(50, 200)
            
        # Handle mouth animation if not transporting
        if not worm.get('transport_target'): # Mouth is controlled by transport logic if transporting
            worm['mouth_timer'] -= 1
            if worm['mouth_timer'] <= 0:
                worm['mouth_state'] = 1 - worm['mouth_state']  # Toggle between 0 and 1
                worm['mouth_timer'] = random.randint(20, 100)
            # Reset speed multiplier if it was changed for pushing
            if 'speed_multiplier' in worm:
                 del worm['speed_multiplier'] 
            
        # Clear target if worm hasn't reached it in a while
        if worm.get('target_symbol') and random.random() < 0.01:  # Small chance to forget target
            worm['target_symbol'] = None
            
        # Redraw the worm
        self._draw_worm(worm)
        
    def _check_symbol_interaction(self, worm):
        """Check if worm head is interacting with any solution symbols"""
        # Skip if cooldown is active for this worm
        current_time = time.time()
        cooldown_time = self.interaction_cooldown.get(worm['id'], 0)
        if current_time < cooldown_time:
            return
            
        # Get head position
        head_pos = worm['history'][0] if worm['history'][0] != (0, 0) else (worm['x'], worm['y'])
        head_x, head_y = head_pos
        
        # Interaction range
        interaction_range = worm['segment_size'] * 2
        
        # Check for collision with any solution symbol
        for symbol in self.solution_symbols:
            sym_x, sym_y = symbol['position']
            # Simple distance check
            distance = math.sqrt((head_x - sym_x)**2 + (head_y - sym_y)**2)
            
            if distance < interaction_range:
                # Interaction detected!
                self._handle_symbol_interaction(worm, symbol)
                
                # Set cooldown
                self.interaction_cooldown[worm['id']] = current_time + 2.0  # 2 second cooldown
                
                # Remove this target
                if worm.get('target_symbol') == symbol:
                    worm['target_symbol'] = None
                    
                # Maybe find a new target
                if random.random() < 0.7 and self.solution_symbols:
                    potential_targets = [s for s in self.solution_symbols if s != symbol]
                    if potential_targets:
                        worm['target_symbol'] = random.choice(potential_targets)
                
                # Break after one interaction
                break
                
        # Occasionally set a random target if no collision and no current target
        if random.random() < 0.02 and not worm.get('target_symbol') and self.solution_symbols:
            worm['target_symbol'] = random.choice(self.solution_symbols)
    
    def _handle_symbol_interaction(self, worm, symbol):
        """Handle interaction between a worm and a solution symbol"""
        try:
            # Get symbol info
            symbol_id = symbol.get('id')
            symbol_char = symbol.get('char', '')
            is_placeholder = symbol.get('is_placeholder', False)

            if not symbol_id or symbol_id == -1 or is_placeholder: # Check for placeholder
                logging.info(f"Worm {worm['id']} interacted with placeholder or invalid symbol data: {symbol}")
                return
                
            # Make the symbol shake
            self._shake_symbol(symbol_id)
            
            # Create particles around the symbol
            self._create_interaction_particles(symbol['position'], worm['color'])
            
            # Make the worm open its mouth
            worm['mouth_state'] = 1
            worm['mouth_timer'] = random.randint(20, 40)
            
            # Log the interaction
            logging.info(f"Worm {worm['id']} interacted with symbol '{symbol_char}' (ID: {symbol_id})")
        except Exception as e:
            logging.error(f"Error handling symbol interaction: {e}")
    
    def _shake_symbol(self, symbol_id):
        """Make a solution symbol shake briefly"""
        if symbol_id == -1: # Explicitly check for placeholder ID
            logging.warning(f"_shake_symbol called with placeholder ID: {symbol_id}. Skipping shake.")
            return
        try:
            # Don't shake if already shaking
            if symbol_id in self.symbol_shake_ids:
                return
                
            # Original position
            original_pos = self.canvas.coords(symbol_id)
            if not original_pos or len(original_pos) < 2:
                return
                
            shake_count = 0
            max_shakes = 5
            shake_amount = 2
            
            def shake_step():
                nonlocal shake_count
                if shake_count >= max_shakes or not self.canvas.winfo_exists():
                    # Stop shaking and reset position
                    if self.canvas.winfo_exists() and symbol_id in self.symbol_shake_ids:
                        try:
                            self.canvas.coords(symbol_id, original_pos)
                            del self.symbol_shake_ids[symbol_id]
                        except tk.TclError:
                            pass
                    return
                
                # Random offset
                dx = random.uniform(-shake_amount, shake_amount)
                dy = random.uniform(-shake_amount, shake_amount)
                
                try:
                    # Move the symbol
                    self.canvas.move(symbol_id, dx, dy)
                    
                    # Schedule next shake
                    shake_count += 1
                    self.symbol_shake_ids[symbol_id] = self.canvas.after(50, shake_step)
                except tk.TclError:
                    # Symbol might have been deleted
                    if symbol_id in self.symbol_shake_ids:
                        del self.symbol_shake_ids[symbol_id]
            
            # Start shaking
            self.symbol_shake_ids[symbol_id] = self.canvas.after(0, shake_step)
            
        except Exception as e:
            logging.error(f"Error shaking symbol: {e}")
    
    def _create_interaction_particles(self, position, color, num_particles=8):
        """Create particles around interaction point"""
        x, y = position
        
        for _ in range(num_particles):
            # Create a particle with random properties
            particle = {
                'x': x,
                'y': y,
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-2, 2),
                'size': random.uniform(2, 6),
                'color': color,
                'life': random.uniform(10, 20),  # Frames
                'id': None
            }
            
            # Create the particle on canvas
            particle['id'] = self.canvas.create_oval(
                x - particle['size'], y - particle['size'],
                x + particle['size'], y + particle['size'],
                fill=particle['color'],
                outline="",
                tags="worm_particle"
            )
            
            # Add to particle list
            self.interaction_particles.append(particle)
    
    def _update_particles(self):
        """Update particle effects"""
        # Process each particle
        particles_to_remove = []
        for particle in self.interaction_particles:
            # Update position
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            # Apply gravity and friction
            particle['vy'] += 0.1
            particle['vx'] *= 0.95
            particle['vy'] *= 0.95
            
            # Decrease life
            particle['life'] -= 1
            
            # Update size based on life
            new_size = particle['size'] * (particle['life'] / 20)
            
            # Update on canvas if it still exists
            try:
                self.canvas.coords(
                    particle['id'],
                    particle['x'] - new_size, particle['y'] - new_size,
                    particle['x'] + new_size, particle['y'] + new_size
                )
                
                # Fade out
                alpha = particle['life'] / 20
                faded_color = self._adjust_color_alpha(particle['color'], alpha)
                self.canvas.itemconfig(particle['id'], fill=faded_color)
                
            except (tk.TclError, KeyError):
                # Particle's visual element might be gone
                particles_to_remove.append(particle)
                continue
                
            # Remove dead particles
            if particle['life'] <= 0:
                try:
                    self.canvas.delete(particle['id'])
                except tk.TclError:
                    pass
                particles_to_remove.append(particle)
        
        # Remove dead particles from list
        for particle in particles_to_remove:
            if particle in self.interaction_particles:
                self.interaction_particles.remove(particle)
    
    def _adjust_color_alpha(self, hex_color, alpha):
        """Adjust a hex color's opacity by blending with background"""
        # Extract RGB
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Blend with white (or whatever the canvas background is)
        bg_color = "#FFFFFF"  # Assume white background
        bg_r = int(bg_color[1:3], 16)
        bg_g = int(bg_color[3:5], 16)
        bg_b = int(bg_color[5:7], 16)
        
        r = int(r * alpha + bg_r * (1 - alpha))
        g = int(g * alpha + bg_g * (1 - alpha))
        b = int(b * alpha + bg_b * (1 - alpha))
        
        # Return new color
        return f"#{r:02x}{g:02x}{b:02x}"
        
    def start_animation(self, num_worms=1):
        """Start the worm animation with the specified number of worms"""
        if self.animation_running:
            return
            
        self.animation_running = True
        self.create_worm(num_worms)
        self.animate()
        
        # Start the symbol transport timer
        self._schedule_symbol_transport()
        
        logging.info(f"Started worm animation with {num_worms} worms")
    
    def stop_animation(self):
        """Stop the worm animation"""
        self.animation_running = False
        
        # Cancel main animation loop
        if self.after_id:
            try:
                self.canvas.after_cancel(self.after_id)
            except Exception as e:
                logging.warning(f"Error cancelling main animation after_id: {e}")
            self.after_id = None
            
        # Cancel any shake animations
        for shake_id in list(self.symbol_shake_ids.values()):
            if shake_id:
                try:
                    self.canvas.after_cancel(shake_id)
                except Exception as e:
                    logging.warning(f"Error cancelling shake animation: {e}")
        self.symbol_shake_ids.clear()
        
        # Cancel transport timer
        if self.transport_timer:
            try:
                self.canvas.after_cancel(self.transport_timer)
            except Exception as e:
                logging.warning(f"Error cancelling transport timer: {e}")
            self.transport_timer = None
            
        # Clear any pending transport operations
        self.transporting_symbols.clear()
        
        logging.info("Stopped worm animation and cleared all timers")
    
    def handle_solution_canvas_redraw(self):
        """Called when the solution canvas is redrawn, invalidating symbol IDs and positions."""
        logging.info("WormAnimation: Handling solution canvas redraw. Clearing glows and transport targets.")
        self._remove_borders_from_solution_symbols() # Clear existing glows

        for worm in self.worms:
            if worm.get('transport_target'):
                # The symbol ID and its animation path are now stale.
                # Ideally, we'd have a way to gracefully stop the self.canvas.after loop in _begin_transport_animation.
                # For now, clearing the target will prevent new actions based on it.
                # The existing animation might complete or error if symbol_id is gone from canvas.
                logging.info(f"Worm {worm['id']} transport target (ID: {worm['transport_target'].get('id', 'N/A')}) cleared due to canvas redraw.")
                worm['transport_target'] = None
                worm['mouth_state'] = 0 # Reset mouth
                # Restore original speed if it was modified for pushing
                if 'speed_multiplier' in worm and 'original_speed_before_push' in worm:
                    worm['speed_multiplier'] = worm['original_speed_before_push']
                elif 'speed_multiplier' in worm: # If original_speed_before_push was somehow not set
                    del worm['speed_multiplier']


            # Clear generic target_symbol as its position data is also stale.
            if worm.get('target_symbol'):
                logging.info(f"Worm {worm['id']} generic target symbol cleared due to canvas redraw.")
                worm['target_symbol'] = None

        # Clear any symbols currently marked as being transported internally by the worm logic
        self.transporting_symbols.clear()

        # Stop any active shake animations as their symbol IDs are now stale
        for symbol_id_key, after_id_val in list(self.symbol_shake_ids.items()): # Iterate on a copy
            if after_id_val:
                try:
                    self.canvas.after_cancel(after_id_val)
                except:
                    pass # Ignore errors if already cancelled or invalid
        self.symbol_shake_ids.clear()
        logging.info("WormAnimation: Cleared active symbol shakes.")

    def _schedule_symbol_transport(self):
        """Schedules the next attempt to transport a symbol."""
        # Clear existing timer if any
        if self.transport_timer:
            self.canvas.after_cancel(self.transport_timer)
            
        # Schedule next transport
        self.transport_timer = self.canvas.after(
            self.transport_interval, 
            self._transport_random_symbol
        )
    
    def _transport_random_symbol(self):
        """Selects a random visible symbol and a random worm to transport it."""
        if not self.solution_symbols or not self.worms or not self.interaction_enabled:
            self._schedule_symbol_transport()
            return

        # Get IDs of symbols currently being targeted for transport by any worm
        currently_targeted_for_transport_ids = set()
        for w_check in self.worms:
            tt = w_check.get('transport_target')
            if tt and tt.get('id') is not None:
                currently_targeted_for_transport_ids.add(tt.get('id'))
            # Also consider generic target_symbol if it implies a pending steal, though transport_target is more direct
            # For now, focusing on transport_target is cleaner for this specific filter.

        available_symbols_to_steal = [
            s for s in self.solution_symbols
            if s.get('id') != -1 and 
               not s.get('is_placeholder') and 
               s.get('visible_to_player') and 
               s.get('id') not in currently_targeted_for_transport_ids and
               s.get('id') not in self.transporting_symbols # Check against symbols already picked in current cycle by this function
        ]

        if not available_symbols_to_steal:
            logging.info("No available (non-placeholder, visible to player, not already targeted) solution symbols for worms to transport.")
            self._schedule_symbol_transport()
            return

        # Select a random worm that is not currently transporting or targeting
        worm = random.choice(self.worms)
        
        # Select a random symbol
        symbol = random.choice(available_symbols_to_steal)
        symbol_id = symbol.get('id')
        
        if not symbol_id:
            # Invalid symbol
            self._schedule_symbol_transport()
            return
            
        # Mark this symbol as being transported
        symbol['transported'] = True
        self.transporting_symbols[symbol_id] = symbol
        
        # --- NEW: Notify GameplayScreen that a symbol is being targeted for stealing --- 
        if self.symbol_targeted_for_steal_callback:
            # Pass worm ID and a copy of the symbol data dictionary
            # The symbol data contains original canvas ID, char, line_idx, char_idx
            self.symbol_targeted_for_steal_callback(worm['id'], dict(symbol)) 
            logging.info(f"Worm {worm['id']} targeting symbol {symbol.get('char')} (ID: {symbol_id}) for potential steal. Callback invoked.")
        # --------------------------------------------------------------------------
        
        # Target the symbol with the worm
        self._target_symbol_for_transport(worm, symbol)
        
        # Schedule the next transport
        self._schedule_symbol_transport()
    
    def _target_symbol_for_transport(self, worm, symbol):
        """Make a worm target a symbol for transport"""
        # Store the target
        worm['transport_target'] = symbol
        # Store detailed identifying information for the callback
        worm['target_line_idx'] = symbol.get('line_idx')
        worm['target_char_idx'] = symbol.get('char_idx')
        worm['target_char_original'] = symbol.get('char')

        # Make worm open its mouth
        worm['mouth_state'] = 1
        worm['mouth_timer'] = 9999  # Keep mouth open until transport complete
        
        # Log the event
        logging.info(f"Worm {worm['id']} targeting symbol {symbol.get('id')} for transport")
        
        # Check periodically if worm has reached the symbol
        self._check_worm_reached_symbol(worm)
    
    def _check_worm_reached_symbol(self, worm):
        """Check if the worm has reached its transport target symbol"""
        if not self.animation_running or not self.canvas.winfo_exists():
            return
            
        if not worm.get('transport_target'):
            return
            
        # Get head position
        head_pos = worm['history'][0] if worm['history'][0] != (0, 0) else (worm['x'], worm['y'])
        head_x, head_y = head_pos
        
        # Get symbol position
        symbol = worm['transport_target']
        sym_pos = symbol.get('position', (0, 0))
        sym_x, sym_y = sym_pos
        
        # Check distance
        distance = math.sqrt((head_x - sym_x)**2 + (head_y - sym_y)**2)
        
        if distance < worm['segment_size'] * 2:
            # Worm has reached the symbol
            self._begin_transport_animation(worm, symbol)
        else:
            # Check again in a bit
            self.canvas.after(100, lambda: self._check_worm_reached_symbol(worm))
    
    def _begin_transport_animation(self, worm, symbol):
        """Begin animating the symbol being transported to Window C"""
        # --- NEW: Check if transport was aborted (e.g., by rescue) before starting ---
        current_target_in_worm = worm.get('transport_target')
        symbol_canvas_id = symbol.get('id') # Original canvas ID of the symbol when targeting began

        if not current_target_in_worm or current_target_in_worm.get('id') != symbol_canvas_id:
            logging.info(f"Transport animation for worm {worm['id']} and original symbol canvas ID {symbol_canvas_id} aborted before start (target is None or changed). Symbol may have been rescued or worm retargeted.")
            if not current_target_in_worm: # If target was cleared entirely
                worm['mouth_state'] = 0
                worm['speed_multiplier'] = worm.get('original_speed_before_push', 1.0)
                # Clear specific target details if no longer relevant
                for key_to_clear in ['target_line_idx', 'target_char_idx', 'target_char_original']:
                    if key_to_clear in worm:
                        del worm[key_to_clear]
            return
        # --- END NEW ---
        
        # Capture original line/char indices and char for the callback
        original_line_idx_for_this_task = worm.get('target_line_idx')
        original_char_idx_for_this_task = worm.get('target_char_idx')
        original_char_for_this_task = worm.get('target_char_original')

        if original_line_idx_for_this_task is None or \
           original_char_idx_for_this_task is None or \
           original_char_for_this_task is None:
            logging.error(f"Worm {worm.get('id')}: Critical target details (line_idx, char_idx, char) missing at start of _begin_transport_animation for symbol: {symbol}")
            worm['transport_target'] = None
            worm['mouth_state'] = 0
            if 'original_speed_before_push' in worm:
                 worm['speed_multiplier'] = worm['original_speed_before_push']
            for key_to_clear in ['target_line_idx', 'target_char_idx', 'target_char_original']:
                if key_to_clear in worm:
                    del worm[key_to_clear]
            return

        try:
            sym_pos_on_canvas = self.canvas.coords(symbol_canvas_id)
            if not sym_pos_on_canvas:
                logging.warning(f"Worm {worm.get('id')}: Symbol with canvas_id {symbol_canvas_id} gone from canvas at start of transport animation.")
                worm['transport_target'] = None
                worm['mouth_state'] = 0
                if 'original_speed_before_push' in worm:
                    worm['speed_multiplier'] = worm['original_speed_before_push']
                for key_to_clear in ['target_line_idx', 'target_char_idx', 'target_char_original']:
                    if key_to_clear in worm:
                        del worm[key_to_clear]
                return

            start_x, start_y = sym_pos_on_canvas[0], sym_pos_on_canvas[1]
            end_y = -50
            total_steps = 60
            current_step = 0
            original_worm_speed = worm.get('speed_multiplier', 1.0)
            worm['speed_multiplier'] = 0.3
            worm['original_speed_before_push'] = original_worm_speed

            def animate_transport():
                nonlocal current_step
                current_worm_target = worm.get('transport_target')
                if not current_worm_target or current_worm_target.get('id') != symbol_canvas_id:
                    logging.info(f"Transport animation for original symbol canvas ID {symbol_canvas_id} aborted due to target change or clear.")
                    worm['mouth_state'] = 0
                    worm['speed_multiplier'] = worm.get('original_speed_before_push', 1.0)
                    for key_to_clear in ['target_line_idx', 'target_char_idx', 'target_char_original']:
                        if key_to_clear in worm:
                            del worm[key_to_clear]
                    return

                if current_step >= total_steps or not self.canvas.winfo_exists():
                    if self.symbol_transport_callback:
                        self.symbol_transport_callback(
                            original_line_idx_for_this_task,
                            original_char_idx_for_this_task,
                            original_char_for_this_task
                        )
                    
                    worm['transport_target'] = None
                    worm['mouth_state'] = 0
                    worm['speed_multiplier'] = worm.get('original_speed_before_push', 1.0)
                    for key_to_clear in ['target_line_idx', 'target_char_idx', 'target_char_original']:
                        if key_to_clear in worm:
                            del worm[key_to_clear]
                    
                    if symbol_canvas_id in self.transporting_symbols:
                        del self.transporting_symbols[symbol_canvas_id]
                    return
                
                progress = current_step / total_steps
                new_y = start_y + (end_y - start_y) * progress
                
                try:
                    self.canvas.coords(symbol_canvas_id, start_x, new_y)
                    worm_target_x = start_x
                    worm_target_y = new_y + worm['segment_size'] * 1.5
                    worm_dx = (worm_target_x - worm['x']) * 0.1
                    worm_dy = (worm_target_y - worm['y']) * 0.1
                    worm['x'] += worm_dx
                    worm['y'] += worm_dy
                    worm['history'].insert(0, (worm['x'], worm['y']))
                    worm['history'] = worm['history'][:self.worm_segments]
                    current_step += 1
                    self.canvas.after(75, animate_transport)
                except tk.TclError:
                    worm['transport_target'] = None
                    worm['mouth_state'] = 0
                    worm['speed_multiplier'] = worm.get('original_speed_before_push', 1.0)
                    for key_to_clear in ['target_line_idx', 'target_char_idx', 'target_char_original']:
                        if key_to_clear in worm:
                            del worm[key_to_clear]
                    return
            animate_transport()
        except Exception as e:
            logging.error(f"Error during transport animation: {e}")
            worm['transport_target'] = None
            worm['mouth_state'] = 0
            if 'original_speed_before_push' in worm:
                 worm['speed_multiplier'] = worm['original_speed_before_push']
            for key_to_clear in ['target_line_idx', 'target_char_idx', 'target_char_original']:
                if key_to_clear in worm:
                    del worm[key_to_clear]
    
    def set_symbol_transport_callback(self, callback):
        """Set callback function for when a symbol is transported to Window C.
        Callback should accept (line_idx, char_idx, char).
        """
        self.symbol_transport_callback = callback
        
    def set_symbol_targeted_for_steal_callback(self, callback):
        """Set callback for when a worm targets a symbol for stealing."""
        self.symbol_targeted_for_steal_callback = callback
        
    def clear_worms(self):
        """Clear all worms from the canvas"""
        if not self.canvas.winfo_exists():
            return
            
        # Delete all worm-related canvas items
        for worm in self.worms:
            for segment in worm['segments']:
                self.canvas.delete(segment)
            for eye in worm['eyes']:
                self.canvas.delete(eye)
            if worm['mouth']:
                self.canvas.delete(worm['mouth'])
                
        # Clear any particles
        for particle in self.interaction_particles:
            self.canvas.delete(particle.get('id'))
        self.interaction_particles = []
                
        self.worms = []
        logging.info("Cleared all worms")
        
    def increase_speed(self, percent=35):
        """Increase the animation speed by the specified percentage"""
        prev_speed = self.animation_speed
        self.animation_speed *= (1 + percent/100)
        
        # Enable interactions if speed is increased above threshold
        if prev_speed <= 1.0 and self.animation_speed > 1.0:
            self.interaction_enabled = True
            self._add_borders_to_solution_symbols()
            
        logging.info(f"Increased worm speed by {percent}%. New speed: {self.animation_speed}")
        
    def reset_speed(self):
        """Reset animation speed to the default"""
        self.animation_speed = 1.0
        self.interaction_enabled = False
        self._remove_borders_from_solution_symbols()
        logging.info("Reset worm speed to default")
        
    def celebrate(self, duration=3000):
        """Make worms celebrate by moving faster and more erratically for a duration
        
        Args:
            duration: Time in milliseconds for celebration
        """
        original_speed = self.animation_speed
        self.animation_speed = 2.0  # Double speed during celebration
        
        # Enable interactions temporarily
        prev_interaction = self.interaction_enabled
        self.interaction_enabled = True
        self._add_borders_to_solution_symbols()
        
        # Make worms more erratic during celebration
        for worm in self.worms:
            worm['angle'] += random.uniform(-math.pi/2, math.pi/2)
            
        logging.info(f"Worms celebrating for {duration}ms")
        
        # Reset after duration
        def reset_after_celebration():
            if self.canvas.winfo_exists():
                self.animation_speed = original_speed
                self.interaction_enabled = prev_interaction
                if not self.interaction_enabled:
                    self._remove_borders_from_solution_symbols()
                logging.info("Worm celebration ended")
                
        self.canvas.after(duration, reset_after_celebration)
        
    def on_step_complete(self):
        """Called when user completes a step in the solution"""
        # Increase speed by 35%
        self.increase_speed(35)
        
        # Reset speed after 10 seconds
        def reset_speed_after_delay():
            if self.canvas.winfo_exists():
                self.reset_speed()
                
        self.canvas.after(10000, reset_speed_after_delay)
        
    def update_solution_symbols(self, symbol_list):
        """Update the list of solution symbols
        
        Args:
            symbol_list: List of dictionaries with keys:
                         - id: Canvas ID of the symbol
                         - position: (x, y) tuple of coordinates
                         - char: The character this symbol represents
        """
        self.solution_symbols = symbol_list
        
        # If interaction is enabled, add borders
        if self.interaction_enabled:
            self._add_borders_to_solution_symbols()
            
        logging.info(f"Updated solution symbols: {len(symbol_list)} symbols")
        
    def _add_borders_to_solution_symbols(self):
        """Add visible borders to all solution symbols to show they're interactive"""
        if not self.canvas.winfo_exists() or not self.interaction_enabled:
            return

        # --- MODIFICATION: Prevent drawing of blue square glows --- 
        # Ensure any existing glows are cleared, log action, and skip creating new ones.
        self._remove_borders_from_solution_symbols()
        logging.info("Skipping creation of blue square glow borders as per user request.")
        return 
        # --- END MODIFICATION ---

        # The code below this point will not be reached due to the return statement above.
        # First, remove any existing glows to prevent duplicates or orphaned glows
        # self._remove_borders_from_solution_symbols() # This line is effectively covered by the call above

        # for symbol_data in self.solution_symbols: # This loop will not be reached
        #     symbol_text_id = symbol_data.get('id') # This is the ID of the TEXT item
        #     if not symbol_text_id:
        #         continue
            
        #     try:
        #         if not self.canvas.coords(symbol_text_id):
        #             logging.debug(f"Symbol text ID {symbol_text_id} seems invalid or deleted, skipping glow.")
        #             continue

        #         bbox = self.canvas.bbox(symbol_text_id)
        #         if not bbox:
        #             logging.debug(f"Cannot get bbox for symbol_text_id {symbol_text_id}, skipping glow.")
        #             continue
                    
        #         padding = 3
        #         glow_rect_id = self.canvas.create_rectangle(
        #             bbox[0] - padding, bbox[1] - padding,
        #             bbox[2] + padding, bbox[3] + padding,
        #             outline="#88CCFF", 
        #             width=2,
        #             fill="", 
        #             tags=("symbol_glow", f"glow_for_text_item_{symbol_text_id}")
        #         )
        #         self.canvas.tag_lower(glow_rect_id, symbol_text_id)
        #         symbol_data['glow_canvas_id'] = glow_rect_id 
                
        #     except tk.TclError as e:
        #         logging.warning(f"TclError adding glow for symbol ID {symbol_text_id}: {e}. Symbol might be gone.")
        #         if 'glow_canvas_id' in symbol_data: 
        #             del symbol_data['glow_canvas_id']
        #         continue
        # logging.debug(f"Finished adding/updating glow borders for {len(self.solution_symbols)} currently tracked symbols.")
                
    def _remove_borders_from_solution_symbols(self):
        """Remove borders from all solution symbols"""
        if not self.canvas.winfo_exists():
            return
            
        # Mass delete based on the general tag
        self.canvas.delete("symbol_glow")
        
        # Also ensure internal tracking of glow IDs is cleared
        for symbol_data in self.solution_symbols:
            if 'glow_canvas_id' in symbol_data:
                del symbol_data['glow_canvas_id']
        logging.debug("Removed all symbol glow borders and cleared internal glow IDs.")
                
    def _remove_specific_worm(self, worm_to_remove):
        """Removes a specific worm from the canvas and internal list.
        Also triggers an explosion if the worm is removed due to intervention.
        """
        if not self.canvas.winfo_exists():
            return

        if worm_to_remove in self.worms:
            logging.info(f"Removing worm ID: {worm_to_remove.get('id')}, current number of worms: {len(self.worms)}")
            # Clear visual components of the worm
            for segment in worm_to_remove.get('segments', []):
                self.canvas.delete(segment)
            for eye in worm_to_remove.get('eyes', []):
                self.canvas.delete(eye)
            if worm_to_remove.get('mouth'):
                self.canvas.delete(worm_to_remove.get('mouth'))
            
            # Trigger an explosion at the worm's last head position
            # The worm's head is at worm_to_remove['x'], worm_to_remove['y']
            if hasattr(self, 'explosion_manager') and self.explosion_manager:
                logging.info(f"Triggering explosion for removed worm ID {worm_to_remove.get('id')} at ({worm_to_remove.get('x')}, {worm_to_remove.get('y')})")
                self.explosion_manager.create_explosion(
                    worm_to_remove.get('x', self.width / 2), # Default to center if x not found
                    worm_to_remove.get('y', self.height / 2),# Default to center if y not found
                    base_size=self.worm_size * 3 # Explosion ~3x worm size
                )

            # Remove from list
            self.worms.remove(worm_to_remove)
            logging.info(f"Worm ID: {worm_to_remove.get('id')} removed. Worms remaining: {len(self.worms)}")
        else:
            logging.warning(f"Attempted to remove worm ID: {worm_to_remove.get('id')} but it was not in the active list.")

    def attempt_intervention_kill(self, worm_id, targeted_symbol_canvas_id):
        """Called by GameplayScreen when player attempts to intervene against a symbol theft.
        If successful (worm was targeting this symbol and hasn't fully stolen it),
        the worm is removed (dies), and the symbol it was pushing is deleted from canvas.
        """
        worm_to_check = None
        for w in self.worms:
            if w.get('id') == worm_id:
                worm_to_check = w
                break
        
        if not worm_to_check:
            logging.warning(f"Intervention attempt: Worm ID {worm_id} not found.")
            return False

        current_target_symbol_data = worm_to_check.get('transport_target')
        
        # Check if the worm is currently targeting the specified symbol for transport.
        # This means worm['transport_target'] is set and its ID matches.
        if current_target_symbol_data and current_target_symbol_data.get('id') == targeted_symbol_canvas_id:
            logging.info(f"Successful intervention! Worm ID {worm_id} was targeting symbol canvas_id {targeted_symbol_canvas_id}. Worm dies, pushed symbol deleted.")
            
            # 1. Delete the canvas item of the symbol the worm was actively pushing.
            #    The targeted_symbol_canvas_id is the ID of this item on solution_canvas.
            try:
                if self.canvas.winfo_exists() and targeted_symbol_canvas_id in self.canvas.find_all():
                    self.canvas.delete(targeted_symbol_canvas_id)
                    logging.info(f"Successfully deleted canvas item {targeted_symbol_canvas_id} (symbol pushed by worm).")
                else:
                    logging.info(f"Canvas item {targeted_symbol_canvas_id} already gone or canvas destroyed, no deletion needed.")
            except tk.TclError as e:
                logging.warning(f"TclError deleting canvas item {targeted_symbol_canvas_id} during intervention: {e}")
            except Exception as e:
                logging.error(f"Unexpected error deleting canvas item {targeted_symbol_canvas_id}: {e}")

            # 2. Clear the worm's target to prevent further transport actions for this symbol by this worm.
            worm_to_check['transport_target'] = None
            worm_to_check['mouth_state'] = 0 # Reset mouth
            worm_to_check['speed_multiplier'] = worm_to_check.get('original_speed_before_push', 1.0) # Restore speed

            # 3. Remove the worm itself.
            self._remove_specific_worm(worm_to_check)
            return True
        else:
            targeted_id_log = current_target_symbol_data.get('id') if current_target_symbol_data else "None"
            logging.info(f"Intervention attempt for worm ID {worm_id} and symbol {targeted_symbol_canvas_id} failed. Worm's current target: {targeted_id_log}.")
            return False

    def handle_worm_click(self, event):
        """Handle click events on worm segments."""
        if not self.animation_running:
            return

        clicked_items = self.canvas.find_withtag(tk.CURRENT) # Get items under cursor
        if not clicked_items:
            return

        clicked_item_id = clicked_items[0]
        tags = self.canvas.gettags(clicked_item_id)

        # Check if a clickable worm segment was actually clicked
        if "worm_segment_clickable" not in tags:
            return
            
        # Identify which worm was clicked (Optional - for now, any worm click triggers duplication if allowed)
        # worm_id_tag = next((tag for tag in tags if tag.startswith("worm_")), None)
        # if not worm_id_tag: return
        # clicked_worm_id = int(worm_id_tag.split('_')[1])

        if len(self.worms) < self.max_worms:
            logging.info(f"Worm clicked. Current worms: {len(self.worms)}. Adding a new worm (max: {self.max_worms}).")
            self.add_worm() # Reuses the existing add_worm logic
        else:
            logging.info(f"Worm clicked, but max worms ({self.max_worms}) reached. No new worm added.")

    def reset_for_new_problem(self):
        """Reset worm animation state for a new problem without destroying objects"""
        try:
            # Stop animation first
            self.animation_running = False
            
            # Clear any pending timers
            self.transport_timer_id = None
            
            # Clear all existing worms safely
            self.clear_worms()
            
            # Reset internal state
            self.update_solution_symbols([])
            self.targeted_symbol_id = None
            self.targeting_worm_id = None
            
            # Reset counters and flags
            self.worm_count = 0
            self.next_worm_id = 1
            
            logging.info("WormAnimation reset for new problem")
        except Exception as e:
            logging.error(f"Error resetting worm animation: {e}")
            
        return self  # Allow method chaining

# For testing the animation standalone
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Worm Animation Test with Symbol Transport")
    root.geometry("600x400")
    
    canvas = tk.Canvas(root, bg="white")
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # Test callback for symbol transport
    def on_symbol_transported(line_idx, char_idx, char):
        print(f"Symbol '{char}' (line: {line_idx}, char: {char_idx}) transported to Window C!")
        
        # Recreate the symbol at the bottom of the screen (simulating reapplication)
        new_x = random.randint(100, 500)
        new_y = random.randint(300, 350)
        
        new_symbol_id = canvas.create_text(
            new_x, new_y, text=char, font=("Arial", 24, "bold"),
            fill="black", tags="test_symbol"
        )
        
        # Add to symbols list
        new_symbol = {
            'id': new_symbol_id,
            'position': (new_x, new_y),
            'char': char,
            'visible': True
        }
        
        worm_animation.solution_symbols.append(new_symbol)
        
        print(f"Symbol reapplied at ({new_x}, {new_y}) with new ID: {new_symbol_id}")
    
    worm_animation = WormAnimation(canvas, 600, 400, on_symbol_transported)
    
    # Create some test symbols
    def create_test_symbols():
        symbols = []
        for i in range(5):
            x = random.randint(100, 500)
            y = random.randint(100, 300)
            char = random.choice("0123456789+-=xX")
            
            # Create text on canvas
            symbol_id = canvas.create_text(
                x, y, text=char, font=("Arial", 24, "bold"),
                fill="black", tags="test_symbol"
            )
            
            # Add to symbols list
            symbols.append({
                'id': symbol_id,
                'position': (x, y),
                'char': char,
                'visible': True
            })
            
        # Update worm animation with symbols
        worm_animation.update_solution_symbols(symbols)
    
    def start_animation():
        worm_animation.start_animation(2)  # Start with 2 worms
        
    def stop_animation():
        worm_animation.stop_animation()
        
    def clear_worms():
        worm_animation.clear_worms()
        
    def increase_speed():
        worm_animation.increase_speed(35)
        
    def reset_speed():
        worm_animation.reset_speed()
        
    def celebrate():
        worm_animation.celebrate()
        
    def add_test_symbols():
        create_test_symbols()
        
    def force_transport():
        worm_animation._transport_random_symbol()
        
    # Add control buttons
    control_frame = tk.Frame(root)
    control_frame.pack(fill=tk.X)
    
    tk.Button(control_frame, text="Start", command=start_animation).pack(side=tk.LEFT, padx=5, pady=5)
    tk.Button(control_frame, text="Stop", command=stop_animation).pack(side=tk.LEFT, padx=5, pady=5)
    tk.Button(control_frame, text="Clear", command=clear_worms).pack(side=tk.LEFT, padx=5, pady=5)
    tk.Button(control_frame, text="Speed Up", command=increase_speed).pack(side=tk.LEFT, padx=5, pady=5)
    tk.Button(control_frame, text="Reset Speed", command=reset_speed).pack(side=tk.LEFT, padx=5, pady=5)
    tk.Button(control_frame, text="Celebrate", command=celebrate).pack(side=tk.LEFT, padx=5, pady=5)
    tk.Button(control_frame, text="Add Symbols", command=add_test_symbols).pack(side=tk.LEFT, padx=5, pady=5)
    tk.Button(control_frame, text="Transport Symbol", command=force_transport).pack(side=tk.LEFT, padx=5, pady=5)
    
    root.mainloop() 