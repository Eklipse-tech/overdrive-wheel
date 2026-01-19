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

# --- CONFIGURATION ---
# 270 degrees usually fixes the "Upside Down" issue on landscape apps
Window.rotation = 270 
Window.clearcolor = (0.1, 0.1, 0.1, 1) # Dark Grey Background

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_PORT = 5000
# This is a placeholder; you will type the real IP in the app
SERVER_IP = "192.168.1.1" 

def send_msg(msg):
    try:
        sock.sendto(msg.encode('utf-8'), (SERVER_IP, int(SERVER_PORT)))
    except: pass

# --- CUSTOM TOUCHPAD (The Grey Box) ---
class TouchPad(Label):
    def on_touch_move(self, touch):
        # Only move mouse if finger is inside this widget
        if self.collide_point(*touch.pos):
            send_msg(f"MOUSE_MOVE:{touch.dx},{touch.dy}")

# --- SCREEN 1: LOGIN ---
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # Title
        layout.add_widget(Label(text="OVERDRIVE", font_size='40sp', bold=True, color=(0, 0.9, 1, 1)))
        
        # IP Input
        self.ip_input = TextInput(text="192.168.", multiline=False, font_size='30sp', size_hint=(1, 0.2),
                                  background_color=(0.2, 0.2, 0.2, 1), foreground_color=(1,1,1,1))
        layout.add_widget(self.ip_input)
        
        # Connect Button
        btn = Button(text="START ENGINE", font_size='25sp', background_color=(0, 0.8, 0, 1), size_hint=(1, 0.3))
        btn.bind(on_press=self.connect)
        layout.add_widget(btn)
        
        self.add_widget(layout)

    def connect(self, instance):
        global SERVER_IP
        SERVER_IP = self.ip_input.text
        self.manager.current = 'game'

# --- SCREEN 2: CONTROLLER ---
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        
        # Gyro Toggle Switch
        self.gyro_active = True
        sw = Switch(active=True, size_hint=(None, None), size=(100, 50), 
                    pos_hint={'center_x': 0.5, 'top': 0.95})
        sw.bind(active=self.toggle_gyro)
        self.layout.add_widget(sw)

        # Touchpad (Center Grey Box)
        tp = TouchPad(text="TOUCHPAD", color=(1,1,1,0.2), 
                      pos_hint={'center_x': 0.5, 'center_y': 0.55}, 
                      size_hint=(0.25, 0.35))
        # Draw background for Touchpad
        with tp.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.15, 0.15, 0.15, 1)
            self.tp_rect = Rectangle(pos=tp.pos, size=tp.size)
        tp.bind(pos=lambda instance, value: setattr(self.tp_rect, 'pos', instance.pos))
        tp.bind(size=lambda instance, value: setattr(self.tp_rect, 'size', instance.size))
        self.layout.add_widget(tp)

        # Helper for creating buttons
        def make_btn(text, pos, size, cmd, color=(0.3,0.3,0.3,1)):
            btn = Button(text=text, pos_hint=pos, size_hint=size, 
                         background_normal='', background_color=color, font_size='18sp', bold=True)
            btn.bind(on_press=lambda x: send_msg(f"{cmd}:DOWN"))
            btn.bind(on_release=lambda x: send_msg(f"{cmd}:UP"))
            self.layout.add_widget(btn)
            return btn

        # Mouse Buttons (Under Touchpad)
        make_btn("LMB", {'right': 0.49, 'top': 0.36}, (0.12, 0.12), "LMB")
        make_btn("RMB", {'x': 0.51, 'top': 0.36}, (0.12, 0.12), "RMB")

        # Driving Pedals (Big & Color Coded)
        make_btn("BRAKE", {'x': 0.02, 'top': 0.98}, (0.3, 0.25), "BTN_LB", color=(0.7,0,0,1))
        make_btn("GAS", {'right': 0.98, 'top': 0.98}, (0.3, 0.25), "BTN_RB", color=(0,0.7,0,1))

        # Face Buttons (ABXY)
        make_btn("Y", {'right': 0.85, 'y': 0.45}, (0.08, 0.15), "BTN_Y", color=(1,1,0,1)) # Yellow
        make_btn("A", {'right': 0.85, 'y': 0.10}, (0.08, 0.15), "BTN_A", color=(0,1,0,1)) # Green
        make_btn("X", {'right': 0.94, 'y': 0.28}, (0.08, 0.15), "BTN_X", color=(0,0,1,1)) # Blue
        make_btn("B", {'right': 0.76, 'y': 0.28}, (0.08, 0.15), "BTN_B", color=(1,0,0,1)) # Red

        # D-Pad
        make_btn("U", {'x': 0.13, 'y': 0.45}, (0.08, 0.15), "BTN_UP")
        make_btn("D", {'x': 0.13, 'y': 0.10}, (0.08, 0.15), "BTN_DOWN")
        make_btn("L", {'x': 0.04, 'y': 0.28}, (0.08, 0.15), "BTN_LEFT")
        make_btn("R", {'x': 0.22, 'y': 0.28}, (0.08, 0.15), "BTN_RIGHT")
        
        # Menu Buttons
        make_btn("SELECT", {'center_x': 0.4, 'y': 0.05}, (0.15, 0.1), "BTN_SELECT")
        make_btn("START", {'center_x': 0.6, 'y': 0.05}, (0.15, 0.1), "BTN_START")

        self.add_widget(self.layout)
        
        try:
            accelerometer.enable()
            Clock.schedule_interval(self.update_gyro, 1.0 / 60.0)
        except: pass

    def toggle_gyro(self, instance, value):
        self.gyro_active = value
        if not value: send_msg("STEER:0")

    def update_gyro(self, dt):
        if not self.gyro_active: return
        try:
            val = accelerometer.acceleration
            if val[1] is None: return
            # V1 Math: 90 degrees = Full Turn
            tilt = (val[1] / 9.81) * 90
            send_msg(f"STEER:{tilt:.2f}")
        except: pass

class OverdriveApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    OverdriveApp().run()
