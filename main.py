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
from kivy.properties import NumericProperty

# --- CONFIG ---
Window.rotation = 0
# Changed background to a slightly darker, retro grid-like color
Window.clearcolor = (0.05, 0.05, 0.07, 1) 

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_IP = "192.168.1.5"
SERVER_PORT = 5000

def send_msg(msg):
    try:
        sock.sendto(msg.encode('utf-8'), (SERVER_IP, int(SERVER_PORT)))
    except: pass

# --- CUSTOM UI: PIXEL 3D BUTTON WITH PRESS ANIMATION ---
class Pixel3DButton(Button):
    offset = NumericProperty(6) # The "3D" depth of the button

    def __init__(self, bg_col=(0.3, 0.3, 0.3, 1), text_col=(1,1,1,1), **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_down = ''
        self.color = text_col
        self.bold = True # Bold text fits the pixel aesthetic better
        
        # Colors: Main, Highlight (top/left), Shadow (bottom/right), and Deep Shadow (underneath)
        self.bg_col = bg_col
        self.highlight_col = [min(1, c * 1.5) for c in bg_col[:3]] + [1]
        self.shadow_col = [max(0, c * 0.6) for c in bg_col[:3]] + [1]
        self.deep_shadow_col = (0.02, 0.02, 0.02, 1)

        self.bind(pos=self.draw_3d, size=self.draw_3d, state=self.draw_3d)

    def draw_3d(self, *args):
        self.canvas.before.clear()
        
        # Determine if pressed to animate the "push down" effect
        is_pressed = self.state == 'down'
        shift_x = self.offset if is_pressed else 0
        shift_y = -self.offset if is_pressed else 0

        with self.canvas.before:
            # 1. DEEP SHADOW (Static, doesn't move)
            Color(*self.deep_shadow_col)
            Rectangle(pos=(self.x + self.offset, self.y - self.offset), size=self.size)

            # 2. MAIN BUTTON FACE (Shifts when pressed)
            curr_pos = (self.x + shift_x, self.y + shift_y)
            Color(*self.bg_col)
            Rectangle(pos=curr_pos, size=self.size)

            # 3. 3D BEVELS (Highlights and Shadows)
            # Top Highlight
            Color(*self.highlight_col)
            Rectangle(pos=(curr_pos[0], curr_pos[1] + self.height - 4), size=(self.width, 4))
            # Left Highlight
            Rectangle(pos=(curr_pos[0], curr_pos[1]), size=(4, self.height))

            # Bottom Shadow
            Color(*self.shadow_col)
            Rectangle(pos=(curr_pos[0], curr_pos[1]), size=(self.width, 4))
            # Right Shadow
            Rectangle(pos=(curr_pos[0] + self.width - 4, curr_pos[1]), size=(4, self.height))

# --- CUSTOM UI: SUNKEN TRACKPAD ---
class TouchPad(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.draw_pad, size=self.draw_pad)

    def draw_pad(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Dark base (sunken effect)
            Color(0.1, 0.1, 0.12, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Inner Shadow (top and left) to make it look indented
            Color(0.02, 0.02, 0.02, 1)
            Rectangle(pos=(self.x, self.top - 4), size=(self.width, 4))
            Rectangle(pos=(self.x, self.y), size=(4, self.height))
            
            # Outer Highlight (bottom and right)
            Color(0.2, 0.2, 0.25, 1)
            Rectangle(pos=(self.x, self.y), size=(self.width, 4))
            Rectangle(pos=(self.right - 4, self.y), size=(4, self.height))

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            send_msg(f"MOUSE_MOVE:{touch.dx},{touch.dy}")

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        layout.add_widget(Label(text="CONNECT TO PC", font_size=40, bold=True, color=(0.2, 1, 0.2, 1)))
        
        # Matrix-green style inputs
        self.ip_input = TextInput(text="192.168.", multiline=False, font_size=30, size_hint=(1, 0.2),
                                  background_color=(0.1, 0.1, 0.1, 1), foreground_color=(0.2, 1, 0.2, 1))
        layout.add_widget(self.ip_input)
        
        self.port_input = TextInput(text="5000", multiline=False, font_size=30, size_hint=(1, 0.2),
                                    background_color=(0.1, 0.1, 0.1, 1), foreground_color=(0.2, 1, 0.2, 1))
        layout.add_widget(self.port_input)
        
        # 3D Pixel Start Button
        btn = Pixel3DButton(text="START ENGINE", font_size=30, bg_col=(0, 0.5, 0.8, 1), size_hint=(1, 0.3))
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

        # TOUCHPAD (Now Sunken 3D)
        tp = TouchPad(text="TOUCHPAD", color=(0.4, 0.4, 0.4, 1), 
                      pos_hint={'center_x': 0.5, 'center_y': 0.55}, 
                      size_hint=(0.25, 0.35))
        self.layout.add_widget(tp)

        # MOUSE BUTTONS
        def make_btn(text, pos, size, cmd, bg_col=(0.25, 0.25, 0.28, 1), txt_col=(1,1,1,1)):
            btn = Pixel3DButton(text=text, pos_hint=pos, size_hint=size, bg_col=bg_col, text_col=txt_col)
            btn.bind(on_press=lambda x: send_msg(f"{cmd}:DOWN"))
            btn.bind(on_release=lambda x: send_msg(f"{cmd}:UP"))
            self.layout.add_widget(btn)

        make_btn("LMB", {'right': 0.49, 'top': 0.36}, (0.12, 0.12), "LMB")
        make_btn("RMB", {'x': 0.51, 'top': 0.36}, (0.12, 0.12), "RMB")

        # CONTROLS
        # 3D Pixel Pedals
        make_btn("BRAKE", {'x': 0.02, 'top': 0.98}, (0.3, 0.25), "BTN_LB", bg_col=(0.6, 0.1, 0.1, 1))
        make_btn("GAS", {'right': 0.98, 'top': 0.98}, (0.3, 0.25), "BTN_RB", bg_col=(0.1, 0.6, 0.1, 1))

        # 3D Pixel ABXY
        make_btn("Y", {'right': 0.85, 'y': 0.45}, (0.08, 0.15), "BTN_Y", txt_col=(1, 1, 0.4, 1))
        make_btn("A", {'right': 0.85, 'y': 0.10}, (0.08, 0.15), "BTN_A", txt_col=(0.4, 1, 0.4, 1))
        make_btn("X", {'right': 0.94, 'y': 0.28}, (0.08, 0.15), "BTN_X", txt_col=(0.4, 0.6, 1, 1))
        make_btn("B", {'right': 0.76, 'y': 0.28}, (0.08, 0.15), "BTN_B", txt_col=(1, 0.4, 0.4, 1))

        # 3D Pixel DPAD
        make_btn("U", {'x': 0.13, 'y': 0.45}, (0.08, 0.15), "BTN_UP")
        make_btn("D", {'x': 0.13, 'y': 0.10}, (0.08, 0.15), "BTN_DOWN")
        make_btn("L", {'x': 0.04, 'y': 0.28}, (0.08, 0.15), "BTN_LEFT")
        make_btn("R", {'x': 0.22, 'y': 0.28}, (0.08, 0.15), "BTN_RIGHT")
        
        # 3D Pixel Start/Select
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
