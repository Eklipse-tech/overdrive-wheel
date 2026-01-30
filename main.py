import socket
import math
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line
from kivy.properties import StringProperty, OptionProperty
from kivy.clock import Clock

# --- CONFIG ---
Window.rotation = 0
Window.clearcolor = (0.05, 0.06, 0.08, 1) # Sci-Fi Dark

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_IP = "192.168.1.5"
SERVER_PORT = 5000

def send_msg(msg):
    try:
        sock.sendto(msg.encode('utf-8'), (SERVER_IP, int(SERVER_PORT)))
    except: pass

# --- THEMES ---
THEMES = {
    'cyan':   ([0.0, 0.6, 0.7, 1], [0.4, 0.9, 1.0, 1], [0.0, 0.3, 0.4, 1]),
    'red':    ([0.7, 0.1, 0.1, 1], [1.0, 0.4, 0.4, 1], [0.4, 0.0, 0.0, 1]),
    'green':  ([0.1, 0.6, 0.1, 1], [0.4, 1.0, 0.4, 1], [0.0, 0.3, 0.0, 1]),
    'blue':   ([0.1, 0.3, 0.8, 1], [0.4, 0.6, 1.0, 1], [0.0, 0.1, 0.4, 1]),
    'yellow': ([0.8, 0.7, 0.0, 1], [1.0, 0.9, 0.3, 1], [0.5, 0.4, 0.0, 1]),
    'grey':   ([0.25, 0.28, 0.32, 1],[0.45, 0.48, 0.52, 1],[0.15, 0.18, 0.22, 1]),
    'dark':   ([0.1, 0.1, 0.12, 1], [0.2, 0.2, 0.25, 1], [0.05, 0.05, 0.08, 1])
}

# --- HELPER: DRAW CHAMFERED RECT ---
def draw_chamfer_rect(canvas, x, y, w, h, s, base, rim, shadow):
    with canvas:
        Color(0.02, 0.02, 0.02, 1) # Outline
        Rectangle(pos=(x, y+s), size=(w, h-2*s))
        Rectangle(pos=(x+s, y), size=(w-2*s, h))
        Rectangle(pos=(x+s, y+s), size=(w-2*s, h-2*s))
        
        Color(*base) # Body
        Rectangle(pos=(x+4, y+s+4), size=(w-8, h-2*s-8))
        Rectangle(pos=(x+s+4, y+4), size=(w-2*s-8, h-8))
        
        Color(*rim) # Highlight
        Rectangle(pos=(x+s+4, y+h-s-4), size=(w-2*s-8, 4))
        
        Color(*shadow) # Shadow
        Rectangle(pos=(x+s+4, y+s), size=(w-2*s-8, 4))
        
        Color(*base) # Corners
        Rectangle(pos=(x+s, y+s), size=(4, 4))
        Rectangle(pos=(x+w-s-4, y+s), size=(4, 4))
        Rectangle(pos=(x+s, y+h-s-4), size=(4, 4))
        Rectangle(pos=(x+w-s-4, y+h-s-4), size=(4, 4))

# --- WIDGET 1: PIXEL TECH BUTTON ---
class PixelTechButton(Button):
    theme_key = StringProperty('grey') 
    def __init__(self, theme='grey', **kwargs):
        super().__init__(**kwargs)
        self.theme_key = theme
        self.background_color = (0,0,0,0)
        self.background_normal = ''
        self.bind(pos=self.draw_btn, size=self.draw_btn, state=self.draw_btn)

    def draw_btn(self, *args):
        self.canvas.before.clear()
        base, rim, shadow = THEMES.get(self.theme_key, THEMES['grey'])
        is_down = self.state == 'down'
        off_y = -4 if is_down else 0
        
        if is_down:
            base = [min(1.0, c + 0.2) for c in base]
            rim  = [min(1.0, c + 0.2) for c in rim]

        draw_chamfer_rect(self.canvas.before, self.x, self.y + off_y, self.width, self.height, 8, base, rim, shadow)

# --- WIDGET 2: DUAL-MODE JOYSTICK ---
class TechJoystick(Widget):
    # Mode: 'keys' (WASD/Arrows) OR 'mouse' (Camera Look)
    mode = OptionProperty('keys', options=['keys', 'mouse'])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.outer_size = 300
        self.stick_size = 120
        self.size = (self.outer_size, self.outer_size)
        
        self.active_keys = {'UP': False, 'DOWN': False, 'LEFT': False, 'RIGHT': False}
        self.stick_pos = None
        self.is_touched = False
        
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        Clock.schedule_interval(self.network_loop, 1.0 / 60.0)

    def network_loop(self, dt):
        if not self.is_touched or self.stick_pos is None: return

        # Calculate normalized X/Y (-1.0 to 1.0)
        bx, by = self.pos
        sx, sy = self.stick_pos
        
        # Center of base
        cx = bx + (self.outer_size / 2)
        cy = by + (self.outer_size / 2)
        
        # Center of stick
        scx = sx + (self.stick_size / 2)
        scy = sy + (self.stick_size / 2)
        
        dx = scx - cx
        dy = scy - cy
        
        max_dist = (self.outer_size / 2) - (self.stick_size / 2)
        norm_x = dx / max_dist
        norm_y = dy / max_dist

        if self.mode == 'mouse':
            # MOUSE MODE: Send relative movement scaling
            speed = 25.0 # Sensitivity
            mx = int(norm_x * speed)
            my = int(norm_y * speed)
            if abs(mx) > 0 or abs(my) > 0:
                send_msg(f"MOUSE_MOVE:{mx},{my}")
        
        else:
            # KEY MODE: Send UP/DOWN/LEFT/RIGHT signals
            threshold = 0.3
            new_keys = {
                'UP': norm_y > threshold,
                'DOWN': norm_y < -threshold,
                'RIGHT': norm_x > threshold,
                'LEFT': norm_x < -threshold
            }
            # Only send changes to avoid spamming network too hard
            for k, v in new_keys.items():
                if v and not self.active_keys[k]:
                    send_msg(f"{k}:DOWN")
                elif not v and self.active_keys[k]:
                    send_msg(f"{k}:UP")
                self.active_keys[k] = v

    def update_canvas(self, *args):
        self.canvas.clear()
        bx, by = self.pos
        draw_chamfer_rect(self.canvas, bx, by, self.outer_size, self.outer_size, 15, *THEMES['dark'])
        
        if self.stick_pos is None:
            sx = bx + (self.outer_size - self.stick_size)/2
            sy = by + (self.outer_size - self.stick_size)/2
        else:
            sx, sy = self.stick_pos
            
        theme = THEMES['cyan'] if self.mode == 'mouse' else THEMES['grey']
        draw_chamfer_rect(self.canvas, sx, sy, self.stick_size, self.stick_size, 10, *theme)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.is_touched = True
            self.update_stick(touch)
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.update_stick(touch)
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.is_touched = False
            self.reset_stick()
            if self.mode == 'keys':
                for k in self.active_keys:
                    if self.active_keys[k]:
                        send_msg(f"{k}:UP")
                        self.active_keys[k] = False
            return True

    def reset_stick(self):
        self.stick_pos = None
        self.update_canvas()

    def update_stick(self, touch):
        cx = self.x + (self.width / 2)
        cy = self.y + (self.height / 2)
        dx = touch.x - cx
        dy = touch.y - cy
        dist = math.sqrt(dx**2 + dy**2)
        max_dist = (self.width / 2) - (self.stick_size / 2)
        
        if dist > max_dist:
            scale = max_dist / dist
            dx *= scale
            dy *= scale
            
        self.stick_pos = (cx + dx - self.stick_size/2, cy + dy - self.stick_size/2)
        self.update_canvas()


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=80, spacing=30)
        layout.add_widget(Label(text="CONTROLLER LINK", font_size='40sp', bold=True, color=THEMES['cyan'][1]))
        
        self.ip_input = TextInput(text="192.168.", multiline=False, font_size='30sp', size_hint=(1, 0.25),
                                  background_color=(0.1, 0.12, 0.15, 1), foreground_color=THEMES['cyan'][1])
        layout.add_widget(self.ip_input)
        
        btn = PixelTechButton(text="CONNECT", theme='cyan', font_size='30sp', size_hint=(1, 0.3))
        btn.bind(on_press=self.connect)
        layout.add_widget(btn)
        self.add_widget(layout)

    def connect(self, instance):
        global SERVER_IP
        SERVER_IP = self.ip_input.text
        self.manager.current = 'game'

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        
        # --- TOP ROW (TRIGGERS & BUMPERS) ---
        # L2 (Trigger)
        self.make_btn("LT", {'x': 0.02, 'top': 0.98}, (0.2, 0.15), "BTN_LB", 'red')
        # L1 (Bumper)
        self.make_btn("LB", {'x': 0.02, 'top': 0.82}, (0.2, 0.12), "BTN_L1", 'red')
        
        # R2 (Trigger)
        self.make_btn("RT", {'right': 0.98, 'top': 0.98}, (0.2, 0.15), "BTN_RB", 'green')
        # R1 (Bumper)
        self.make_btn("RB", {'right': 0.98, 'top': 0.82}, (0.2, 0.12), "BTN_R1", 'green')

        # --- LEFT SIDE (MOVEMENT) ---
        # Left Stick (WASD)
        self.l_stick = TechJoystick(mode='keys', pos_hint={'x': 0.08, 'center_y': 0.4})
        self.layout.add_widget(self.l_stick)
        
        # D-Pad (Small, tucked between Stick and Center)
        dp_size = (0.07, 0.12)
        self.make_btn("U", {'x': 0.38, 'y': 0.30}, dp_size, "BTN_UP", 'grey')
        self.make_btn("D", {'x': 0.38, 'y': 0.04}, dp_size, "BTN_DOWN", 'grey')
        self.make_btn("L", {'x': 0.32, 'y': 0.17}, dp_size, "BTN_LEFT", 'grey')
        self.make_btn("R", {'x': 0.44, 'y': 0.17}, dp_size, "BTN_RIGHT", 'grey')

        # --- RIGHT SIDE (ACTION) ---
        # Right Stick (Mouse/Camera)
        self.r_stick = TechJoystick(mode='mouse', pos_hint={'right': 0.92, 'center_y': 0.35})
        # Note: We need to override size for the right stick to make it slightly smaller if desired, 
        # but standard size is fine. 
        self.layout.add_widget(self.r_stick)

        # Face Buttons (ABXY) - Positioned above Right Stick
        fb_size = (0.09, 0.14)
        self.make_btn("Y", {'right': 0.75, 'top': 0.85}, fb_size, "BTN_Y", 'yellow')
        self.make_btn("B", {'right': 0.65, 'top': 0.70}, fb_size, "BTN_B", 'red')
        self.make_btn("X", {'right': 0.85, 'top': 0.70}, fb_size, "BTN_X", 'blue')
        self.make_btn("A", {'right': 0.75, 'top': 0.55}, fb_size, "BTN_A", 'green')

        # --- CENTER (MENU) ---
        self.make_btn("SELECT", {'center_x': 0.42, 'top': 0.95}, (0.15, 0.1), "BTN_SELECT", 'grey')
        self.make_btn("START",  {'center_x': 0.58, 'top': 0.95}, (0.15, 0.1), "BTN_START", 'grey')

        self.add_widget(self.layout)

    def make_btn(self, text, pos, size, cmd, theme='grey'):
        btn = PixelTechButton(text=text, theme=theme, pos_hint=pos, size_hint=size, font_size='18sp')
        btn.bind(on_press=lambda x: send_msg(f"{cmd}:DOWN"))
        btn.bind(on_release=lambda x: send_msg(f"{cmd}:UP"))
        self.layout.add_widget(btn)

class ControllerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    ControllerApp().run()
