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
from kivy.properties import ListProperty

# --- CONFIG ---
Window.rotation = 0
# Dark, pixel-grid background color
Window.clearcolor = (0.05, 0.05, 0.07, 1)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_IP = "192.168.1.5"
SERVER_PORT = 5000

def send_msg(msg):
    try:
        sock.sendto(msg.encode('utf-8'), (SERVER_IP, int(SERVER_PORT)))
    except: pass

# --- CUSTOM UI: PIXEL STONE BUTTON WITH PRESS ANIMATION ---
class PixelStoneButton(Button):
    # Color palette based on the reference image (dark stone/metal)
    # Main body color
    bg_col = ListProperty([0.25, 0.3, 0.35, 1])
    # Very dark outline
    outline_col = ListProperty([0.1, 0.12, 0.15, 1])
    # Lighter inner border
    inner_border_col = ListProperty([0.35, 0.4, 0.45, 1])
    # Top 3D highlight
    top_highlight_col = ListProperty([0.4, 0.45, 0.5, 1])
    # Bottom 3D shadow
    bottom_shadow_col = ListProperty([0.15, 0.18, 0.2, 1])

    def __init__(self, text_col=(0.8, 0.85, 0.9, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_down = ''
        self.color = text_col
        self.bold = True
        self.bind(pos=self.draw_pixel_button, size=self.draw_pixel_button, state=self.draw_pixel_button)

    def draw_pixel_button(self, *args):
        self.canvas.before.clear()
        
        # Shift down when pressed for animation
        is_pressed = self.state == 'down'
        offset = 4 if is_pressed else 0
        
        x, y = self.x, self.y - offset
        w, h = self.width, self.height

        with self.canvas.before:
            # 1. Outer Dark Outline
            Color(*self.outline_col)
            Rectangle(pos=(x, y), size=(w, h))

            # 2. Main Body (slightly smaller)
            Color(*self.bg_col)
            Rectangle(pos=(x + 4, y + 4), size=(w - 8, h - 8))

            # 3. Inner Lighter Border (a few pixels inside)
            Color(*self.inner_border_col)
            Line(rectangle=(x + 6, y + 6, w - 12, h - 12), width=2)

            # 4. 3D Effects (Top Highlight & Bottom Shadow)
            # Top Highlight
            Color(*self.top_highlight_col)
            Rectangle(pos=(x + 4, y + h - 8), size=(w - 8, 4))
            # Bottom Shadow
            Color(*self.bottom_shadow_col)
            Rectangle(pos=(x + 4, y + 4), size=(w - 8, 4))

# --- CUSTOM UI: SUNKEN PIXEL TRACKPAD ---
class TouchPad(Label):
    # Palette for sunken pad (reversed highlights/shadows)
    bg_col = ListProperty([0.15, 0.18, 0.2, 1])
    outline_col = ListProperty([0.1, 0.12, 0.15, 1])
    inner_shadow_col = ListProperty([0.1, 0.12, 0.15, 1])
    bottom_highlight_col = ListProperty([0.25, 0.3, 0.35, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.draw_pad, size=self.draw_pad)

    def draw_pad(self, *args):
        self.canvas.before.clear()
        x, y = self.x, self.y
        w, h = self.width, self.height
        
        with self.canvas.before:
            # 1. Outer Outline
            Color(*self.outline_col)
            Rectangle(pos=(x, y), size=(w, h))
            
            # 2. Main Sunken Body
            Color(*self.bg_col)
            Rectangle(pos=(x + 4, y + 4), size=(w - 8, h - 8))

            # 3. Inner Shadow (Top/Left)
            Color(*self.inner_shadow_col)
            Rectangle(pos=(x + 4, y + h - 8), size=(w - 8, 4))
            Rectangle(pos=(x + 4, y + 4), size=(4, h - 8))

            # 4. Bottom/Right Highlight
            Color(*self.bottom_highlight_col)
            Rectangle(pos=(x + 4, y + 4), size=(w - 8, 4))
            Rectangle(pos=(x + w - 8, y + 4), size=(4, h - 8))

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            send_msg(f"MOUSE_MOVE:{touch.dx},{touch.dy}")

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # Pixel-style title
        layout.add_widget(Label(text="CONNECT TO PC", font_size=40, bold=True, color=(0.8, 0.85, 0.9, 1)))
        
        # Pixel-style inputs
        self.ip_input = TextInput(text="192.168.", multiline=False, font_size=30, size_hint=(1, 0.2),
                                  background_color=(0.15, 0.18, 0.2, 1), foreground_color=(0.8, 0.85, 0.9, 1), cursor_color=(0.8, 0.85, 0.9, 1))
        layout.add_widget(self.ip_input)
        
        self.port_input = TextInput(text="5000", multiline=False, font_size=30, size_hint=(1, 0.2),
                                    background_color=(0.15, 0.18, 0.2, 1), foreground_color=(0.8, 0.85, 0.9, 1), cursor_color=(0.8, 0.85, 0.9, 1))
        layout.add_widget(self.port_input)
        
        # Pixel Stone Start Button
        btn = PixelStoneButton(text="START ENGINE", font_size=30, size_hint=(1, 0.3))
        # Override color for the start button
        btn.bg_col = [0.2, 0.4, 0.6, 1]
        btn.inner_border_col = [0.3, 0.5, 0.7, 1]
        btn.top_highlight_col = [0.4, 0.6, 0.8, 1]
        btn.bind(on_press=self.connect)
        layout.add_widget(btn)
        self.add_widget(layout)

    def connect(self, instance):
        global SERVER_IP, SERVER_PORT
        SERVER_IP = self.ip_input.text
        SERVER_PORT = self.port_input.text
        self.manager.current = 'game'

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        
        # GYRO
        self.gyro_active = True
        sw = Switch(active=True, size_hint=(None, None), size=(100, 50), pos_hint={'center_x': 0.5, 'top': 0.95})
        sw.bind(active=self.toggle_gyro)
        self.layout.add_widget(sw)

        # TOUCHPAD (Sunken Pixel Style)
        tp = TouchPad(text="TOUCHPAD", color=(0.5, 0.55, 0.6, 1), 
                      pos_hint={'center_x': 0.5, 'center_y': 0.55}, 
                      size_hint=(0.25, 0.35))
        self.layout.add_widget(tp)

        # MOUSE BUTTONS
        def make_btn(text, pos, size, cmd, bg_override=None):
            btn = PixelStoneButton(text=text, pos_hint=pos, size_hint=size)
            if bg_override:
                btn.bg_col = bg_override[0]
                btn.inner_border_col = bg_override[1]
                btn.top_highlight_col = bg_override[2]

            btn.bind(on_press=lambda x: send_msg(f"{cmd}:DOWN"))
            btn.bind(on_release=lambda x: send_msg(f"{cmd}:UP"))
            self.layout.add_widget(btn)

        make_btn("LMB", {'right': 0.49, 'top': 0.36}, (0.12, 0.12), "LMB")
        make_btn("RMB", {'x': 0.51, 'top': 0.36}, (0.12, 0.12), "RMB")

        # CONTROLS
        # Red Brake Pedal
        brake_cols = ([0.5, 0.2, 0.2, 1], [0.6, 0.3, 0.3, 1], [0.7, 0.4, 0.4, 1])
        make_btn("BRAKE", {'x': 0.02, 'top': 0.98}, (0.3, 0.25), "BTN_LB", bg_override=brake_cols)
        
        # Green Gas Pedal
        gas_cols = ([0.2, 0.5, 0.2, 1], [0.3, 0.6, 0.3, 1], [0.4, 0.7, 0.4, 1])
        make_btn("GAS", {'right': 0.98, 'top': 0.98}, (0.3, 0.25), "BTN_RB", bg_override=gas_cols)

        # Pixel ABXY
        make_btn("Y", {'right': 0.85, 'y': 0.45}, (0.08, 0.15), "BTN_Y")
        make_btn("A", {'right': 0.85, 'y': 0.10}, (0.08, 0.15), "BTN_A")
        make_btn("X", {'right': 0.94, 'y': 0.28}, (0.08, 0.15), "BTN_X")
        make_btn("B", {'right': 0.76, 'y': 0.28}, (0.08, 0.15), "BTN_B")

        # Pixel DPAD
        make_btn("U", {'x': 0.13, 'y': 0.45}, (0.08, 0.15), "BTN_UP")
        make_btn("D", {'x': 0.13, 'y': 0.10}, (0.08, 0.15), "BTN_DOWN")
        make_btn("L", {'x': 0.04, 'y': 0.28}, (0.08, 0.15), "BTN_LEFT")
        make_btn("R", {'x': 0.22, 'y': 0.28}, (0.08, 0.15), "BTN_RIGHT")
        
        # Pixel Start/Select
        make_btn("SLCT", {'center_x': 0.4, 'y': 0.05}, (0.15, 0.1), "BTN_SELECT")
        make_btn("STRT", {'center_x': 0.6, 'y': 0.05}, (0.15, 0.1), "BTN_START")

        self.add_widget(self.layout)
        
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
