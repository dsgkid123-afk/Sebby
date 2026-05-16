import pygame
import math
import random
import threading
import time

class RoboEyes:
    def __init__(self, width=800, height=400):
        self.width, self.height = width, height
        self.running = True
        
        # State variables
        self.current_mood = "default"
        self.is_nodding_yes = False
        self.is_nodding_no = False
        self.intensity = 0
        self.is_standby = False
        self.standby_intensity = 0
        self.blink_freq = 3000
        
        # Internal Positioning
        self.scale = 4
        self.ew, self.eh = 36, 26
        self.base_x = (width // self.scale - (self.ew * 2 + 10)) // 2
        self.base_y = (height // self.scale - self.eh) // 2
        self.curr_x, self.curr_y = self.base_x, self.base_y
        self.target_x, self.target_y = self.base_x, self.base_y
        
        # Start the background thread automatically
        self.thread = threading.Thread(target=self._render_loop, daemon=True)
        self.thread.start()

    def yes(self, intensity=5):
        self.is_nodding_yes, self.is_nodding_no = True, False
        self.intensity = intensity

    def no(self, intensity=8):
        self.is_nodding_no, self.is_nodding_yes = True, False
        self.intensity = intensity

    def standby(self, looking_intensity=15, blinking_avg_freq=3000):
        self.is_standby = True
        self.standby_intensity = looking_intensity
        self.blink_freq = blinking_avg_freq

    def mood(self, mood_type="default"):
        """
        Available moods: default, angry, happy, sad, suspicious, surprised, confused
        """
        self.current_mood = mood_type.lower()

    def _render_loop(self):
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        clock = pygame.time.Clock()
        
        next_move = 0
        next_blink = 0

        while self.running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    self.running = False

            # Logic: Random movement
            if self.is_standby:
                if now > next_move:
                    self.target_x = self.base_x + random.uniform(-self.standby_intensity, self.standby_intensity)
                    self.target_y = self.base_y + random.uniform(-self.standby_intensity/2, self.standby_intensity/2)
                    next_move = now + random.randint(1000, 4000)
                
                blink_h = 1.0
                if now > next_blink:
                    progress = (now - next_blink) / 200
                    if progress <= 1.0: 
                        blink_h = abs(math.cos(progress * math.pi))
                    else: 
                        next_blink = now + random.randint(int(self.blink_freq*0.5), int(self.blink_freq*1.5))
            else:
                blink_h = 1.0

            # Logic: Nodding
            off_x, off_y = 0, 0
            dt = now / 1000.0
            if self.is_nodding_yes: off_y = math.sin(dt * 12) * self.intensity
            if self.is_nodding_no: off_x = math.sin(dt * 12) * self.intensity

            # Smooth movement
            self.curr_x += (self.target_x - self.curr_x) * 0.1
            self.curr_y += (self.target_y - self.curr_y) * 0.1

            # Drawing
            bg_color = (15, 15, 15)
            screen.fill(bg_color)
            s = self.scale
            draw_y = (self.curr_y + off_y) * s + (self.eh*s - (self.eh*s * blink_h)) / 2
            
            for i in range(2):
                x = (self.curr_x + off_x + (i * (36 + 10))) * s
                rect = pygame.Rect(x, draw_y, 36*s, 36*s * blink_h)
                
                # Base eye rendering
                pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=8*s)
                
                # --- EMOTION MASKS ---
                
                if self.current_mood == "angry":
                    # Inner corners pinched down (\ /)
                    pts = [rect.topleft, rect.topright, (rect.right, rect.top + 12*s)] if i==0 else \
                          [rect.topright, rect.topleft, (rect.left, rect.top + 12*s)]
                    pygame.draw.polygon(screen, bg_color, pts)
                    
                elif self.current_mood == "sad":
                    # Outer corners drooping down (/ \)
                    pts = [rect.topleft, rect.topright, (rect.left, rect.top + 12*s)] if i==0 else \
                          [rect.topright, rect.topleft, (rect.right, rect.top + 12*s)]
                    pygame.draw.polygon(screen, bg_color, pts)
                    
                elif self.current_mood == "happy":
                    # Cheeks pushing up from the bottom
                    pygame.draw.rect(screen, bg_color, (rect.left, rect.bottom - 10*s, 36*s, 12*s), border_radius=4*s)

                elif self.current_mood == "suspicious":
                    # Squinting heavily from top and bottom
                    pygame.draw.rect(screen, bg_color, (rect.left, rect.top, 36*s, 10*s))
                    pygame.draw.rect(screen, bg_color, (rect.left, rect.bottom - 10*s, 36*s, 10*s))

                elif self.current_mood == "confused":
                    # Asymmetrical: Left eye squinted, Right eye wide/normal
                    if i == 0:
                        pygame.draw.rect(screen, bg_color, (rect.left, rect.top, 36*s, 8*s))
                        pygame.draw.rect(screen, bg_color, (rect.left, rect.bottom - 8*s, 36*s, 8*s))
                        
                elif self.current_mood == "surprised":
                    # "Pupils" shrink down to small dots
                    # Mask the whole eye, then draw a smaller inner rectangle
                    pygame.draw.rect(screen, bg_color, rect)
                    small_rect = pygame.Rect(x + 10*s, draw_y + 10*s, 16*s, 16*s * blink_h)
                    pygame.draw.rect(screen, (255, 255, 255), small_rect, border_radius=4*s)

            pygame.display.flip()
            clock.tick(60)
        pygame.quit()


# --- Test/Demo Block ---
if __name__ == "__main__":
    eyes = RoboEyes()
    eyes.standby()
    
    moods = ["default", "happy", "angry", "sad", "suspicious", "surprised", "confused"]
    
    try:
        for m in moods:
            print(f"Switching to: {m}")
            eyes.mood(m)
            time.sleep(3) # Hold each emotion for 3 seconds
    except KeyboardInterrupt:
        pass
    finally:
        eyes.running = False
        eyes.thread.join()