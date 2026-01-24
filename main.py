import socket
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.clock import Clock
from plyer import accelerometer
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line
from kivy.properties import ListProperty, StringProperty

# --- CONFIG ---
Window.rotation = 0
# Deep Void Background (Dark Sci-Fi Grey)
Window.clearcolor = (0.05, 0.06, 0.08, 1)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_IP = "192.168.1.5"
SERVER_PORT = 5000

def send_msg(msg):
    try:
        sock.sendto(msg.encode('utf-8'), (SERVER_IP, int(SERVER_PORT)))
    except: pass

# --- COLOR THEMES ---
# Format: Main Body, Highlight Rim, Dark Shadow
THEMES = {
    'cyan':   ([0.0, 0.5, 0.6, 1], [0.3, 0.8, 0.9, 1], [0.0, 0.3, 0.4, 1]),
    'red':    ([0.6, 0.1, 0.1, 1], [0.9, 0.3, 0.3, 1], [0.4, 0.0, 0.0, 1]),
    'green':  ([0.1, 0.5, 0.1, 1], [0.3, 0.9, 0.3, 1], [0.0, 0.3, 0.0, 1]),
    'blue':   ([0.1, 0.2, 0.7, 1], [0.3, 0.5, 1.0, 1], [0.0, 0.1, 0.4, 1]),
    'yellow': ([0.7, 0.6, 0.0, 1], [1.0, 0.9, 0.3, 1], [0.5, 0.4, 0.0, 1]),
    'grey':   ([0.25, 0.28, 0.32, 1],[0.45, 0.48, 0.52, 1],[0.15, 0.18, 0.22, 1])
}

# --- CUSTOM COMPONENT: ANIMATED PIXEL BUTTON ---
class PixelTechButton(Button):
    theme_key = StringProperty('cyan') 
    
    def __init__(self, theme='cyan', **kwargs):
        super().__init__(**kwargs)
        self.theme_key = theme
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_down = ''
        self.color = (1, 1, 1, 1)
        self.bold = True
        self.bind(pos=self.draw_btn, size=self.draw_btn, state=self.draw_btn)

    def draw_btn(self, *args):
        self.canvas.before.clear()
        
        # 1. Retrieve Theme Colors
        base, rim, shadow = THEMES.get(self.theme_key, THEMES['cyan'])
        
        # 2. Check Input State
        is_down = self.state == 'down'
        
        # --- ANIMATION CALCULATIONS ---
        
        # A. Physical Shift (Sinks 4px when pressed)
        off_y = -4 if is_down else 0
        
        # B. Color Boost (Light up, but NOT pure white)
        if is_down:
            # We add 0.3 to the RGB channels to brighten them, capping at 1.0
            # This keeps the original hue (red stays red) but makes it glow.
            base = [min(1.0, c + 0.25) for c in base[:3]] + [1]
            rim  = [min(1.0, c + 0.30) for c in rim[:3]] + [1]
            # Shadow stays dark to maintain contrast
        
        # Geometry Setup
        x, y = self.x, self.y + off_y
        w, h = self.width, self.height
        s = 8 # The size of the "cut out" corners (Chamfer)

        with self.canvas.before:
            # LAYER 1: The Black Outline (The "Socket")
            # We draw a cross shape to create the chamfered corners
            Color(0.02, 0.02, 0.02, 1)
            Rectangle(pos=(x, y + s), size=(w, h - 2*s))       # Horizontal Bar
            Rectangle(pos=(x + s, y), size=(w - 2*s, h))       # Vertical Bar
            Rectangle(pos=(x + s, y + s), size=(w - 2*s, h - 2*s)) # Center Fill

            # LAYER 2: The Main Colored Body
            # Drawn slightly smaller to sit inside the black outline
            Color(*base)
            Rectangle(pos=(x + 4, y + s + 4), size=(w - 8, h - 2*s - 8))
            Rectangle(pos=(x + s + 4, y + 4), size=(w - 2*s - 8, h - 8))

            # LAYER 3: The Highlights (Rim)
            # Top "Bevel"
            Color(*rim)
            Rectangle(pos=(x + s + 4, y + h - s - 4), size=(w - 2*s - 8, 4))
            
            # LAYER 4: The Shadows
            # Bottom "Bevel"
            Color(*shadow)
            Rectangle(pos=(x + s + 4, y + s), size=(w - 2*s - 8, 4))

            # LAYER 5: Corner Detail Pixels (Smoothing the chamfer)
            # Small squares in the corners to join the vertical/horizontal bars
            Color(*base) 
            Rectangle(pos=(x + s, y + s), size=(4, 4))
            Rectangle(pos=(x + w - s - 4, y + s), size=(4, 4))
            Rectangle(pos=(x + s, y + h - s - 4), size=(4, 4))
            Rectangle(pos=(x + w - s - 4, y + h - s - 4), size=(4, 4))

# --- CUSTOM COMPONENT: TACTICAL TOUCHPAD ---
class TechTouchPad(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.draw_pad, size=self.draw_pad)

    def draw_pad(self, *args):
        self.canvas.before.clear()
        x, y = self.x, self.y
        w, h = self.width, self.height
        s = 10 # Larger chamfer for the pad

        with self.canvas.before:
            # 1. Background (Dark Void)
            Color(0.02, 0.02, 0.02, 1)
            Rectangle(pos=(x, y + s), size=(w, h - 2*s))
            Rectangle(pos=(x + s, y), size=(w - 2*s, h))
            
            # 2. Sunken Surface (Dark Slate)
            Color(0.12, 0.14, 0.16, 1)
            Rectangle(pos=(x + 4, y + s), size=(w - 8, h - 2*s))
            Rectangle(pos=(x + s, y + 4), size=(w - 2*s, h - 8))

            # 3. Tactical Crosshair Grid
            Color(0.2, 0.25, 0.3, 1)
            # Center Vertical Line
            Line(points=[x + w/2, y + 15, x + w/2, y + h - 15], width=1.5)
            # Center Horizontal Line
            Line(points=[x + 15, y + h/2, x + w - 15, y + h/2], width=1.5)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            send_msg(f"MOUSE_MOVE:{touch.dx},{touch.dy}")

# --- SCREEN 1: LOGIN ---
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # Title
        layout.add_widget(Label(text="SYSTEM LINK", font_size=40, bold=True, color=(0.3, 0.8, 0.9, 1)))
        
        # Inputs
        self.ip_input = TextInput(text="192.168.", multiline=False, font_size=30, size_hint=(1, 0.2),
                                  background_color=(0.1, 0.12, 0.15, 1), foreground_color=(0.3, 0.8, 0.9, 1), cursor_color=(1,1,1,1))
        layout.add_widget(self.ip_input)
        
        self.port_input = TextInput(text="5000", multiline=False, font_size=30, size_hint=(1, 0.2),
                                    background_color=(0.1, 0.12, 0.15, 1), foreground_color=(0.3, 0.8, 0.9, 1))
        layout.add_widget(self.port_input)
        
        # Connect Button (Big Cyan Button)
        btn = PixelTechButton(text="INITIALIZE", theme='cyan', font_size=30, size_hint=(1, 0.3))
        btn.bind(on_press=self.connect)
        layout.add_widget(btn)
        self.add_widget(layout)

    def connect(self, instance):
        global SERVER_IP, SERVER_PORT
        SERVER_IP = self.ip_input.text
        SERVER_PORT = self.port_input.text
        self.manager.current = 'game'

# --- SCREEN 2: GAMEPAD ---
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        
        # 1. GYRO TOGGLE
        self.gyro_active = True
        sw = Switch(active=True, size_hint=(None, None), size=(100, 50), pos_hint={'center_x': 0.5, 'top': 0.95})
        sw.bind(active=self.toggle_gyro)
        self.layout.add_widget(sw)

        # 2. TOUCHPAD (Center)
        tp = TechTouchPad(text="TRACK", pos_hint={'center_x': 0.5, 'center_y': 0.55}, size_hint=(0.25, 0.35))
        self.layout.add_widget(tp)

        # HELPER TO MAKE BUTTONS
        def make_btn(text, pos, size, cmd, theme='grey'):
            btn = PixelTechButton(text=text, theme=theme, pos_hint=pos, size_hint=size)
            btn.bind(on_press=lambda x: send_msg(f"{cmd}:DOWN"))
            btn.bind(on_release=lambda x: send_msg(f"{cmd}:UP"))
            self.layout.add_widget(btn)

        # 3. MOUSE CLICKS (Cyan - Matches Touchpad theme)
        make_btn("LMB", {'right': 0.49, 'top': 0.36}, (0.12, 0.12), "LMB", theme='cyan')
        make_btn("RMB", {'x': 0.51, 'top': 0.36}, (0.12, 0.12), "RMB", theme='cyan')

        # 4. PEDALS (Gas=Green, Brake=Red)
        make_btn("BRAKE", {'x': 0.02, 'top': 0.98}, (0.3, 0.25), "BTN_LB", theme='red')
        make_btn("GAS", {'right': 0.98, 'top': 0.98}, (0.3, 0.25), "BTN_RB", theme='green')

        # 5. FACE BUTTONS (Xbox/Snes Colors)
        make_btn("Y", {'right': 0.85, 'y': 0.45}, (0.08, 0.15), "BTN_Y", theme='yellow')
        make_btn("A", {'right': 0.85, 'y': 0.10}, (0.08, 0.15), "BTN_A", theme='green')
        make_btn("X", {'right': 0.94, 'y': 0.28}, (0.08, 0.15), "BTN_X", theme='blue')
        make_btn("B", {'right': 0.76, 'y': 0.28}, (0.08, 0.15), "BTN_B", theme='red')

        # 6. D-PAD (Industrial Grey)
        make_btn("U", {'x': 0.13, 'y': 0.45}, (0.08, 0.15), "BTN_UP", theme='grey')
        make_btn("D", {'x': 0.13, 'y': 0.10}, (0.08, 0.15), "BTN_DOWN", theme='grey')
        make_btn("L", {'x': 0.04, 'y': 0.28}, (0.08, 0.15), "BTN_LEFT", theme='grey')
        make_btn("R", {'x': 0.22, 'y': 0.28}, (0.08, 0.15), "BTN_RIGHT", theme='grey')
        
        # 7. MENU BUTTONS
        make_btn("SLCT", {'center_x': 0.4, 'y': 0.05}, (0.15, 0.1), "BTN_SELECT", theme='grey')
        make_btn("STRT", {'center_x': 0.6, 'y': 0.05}, (0.15, 0.1), "BTN_START", theme='grey')

        self.add_widget(self.layout)
        
        # 8. ACCELEROMETER LOGIC
        try:
            accelerometer.enable()
            Clock.schedule_interval(self.update_gyro, 1.0 / 60.0)
        except: print("No sensor")

    def toggle_gyro(self, instance, value):
        self.gyro_active = value
        if not value: send_msg("STEER:0")

    def update_gyro(self, dt):
        if not self.gyro_active: return
        try:
            val = accelerometer.acceleration
            if val[1] is None: return
            tilt = (val[1] / 9.81) * 90
            send_msg(f"STEER:{tilt:.2f}")
        except: pass

class ControllerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    ControllerApp().run()
