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
from kivy.graphics import Color, RoundedRectangle

# --- CONFIG ---
Window.rotation = 0
Window.clearcolor = (0.08, 0.08, 0.1, 1) # Deep Dark Grey

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_IP = "192.168.1.5"
SERVER_PORT = 5000

def send_msg(msg):
    try:
        sock.sendto(msg.encode('utf-8'), (SERVER_IP, int(SERVER_PORT)))
    except: pass

# --- CUSTOM UI: ROUNDED BUTTON ---
# This replaces the standard square button with a custom drawn rounded one
class RoundedButton(Button):
    def __init__(self, bg_col=(0.3, 0.3, 0.3, 1), text_col=(1,1,1,1), **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0) # Hide default square background
        self.background_normal = '' 
        self.color = text_col
        self.bg_col = bg_col
        
        with self.canvas.before:
            Color(*self.bg_col)
            # radius=[15] gives the curve. Increase for rounder buttons.
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
            
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

# --- CUSTOM UI: ROUNDED TOUCHPAD ---
class TouchPad(Label):
    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            send_msg(f"MOUSE_MOVE:{touch.dx},{touch.dy}")

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        layout.add_widget(Label(text="CONNECT TO PC", font_size=40, bold=True, color=(0, 0.8, 0.8, 1)))
        
        self.ip_input = TextInput(text="192.168.", multiline=False, font_size=30, size_hint=(1, 0.2),
                                  background_color=(0.2, 0.2, 0.2, 1), foreground_color=(1,1,1,1))
        layout.add_widget(self.ip_input)
        
        self.port_input = TextInput(text="5000", multiline=False, font_size=30, size_hint=(1, 0.2),
                                    background_color=(0.2, 0.2, 0.2, 1), foreground_color=(1,1,1,1))
        layout.add_widget(self.port_input)
        
        # Rounded Start Button
        btn = RoundedButton(text="START ENGINE", font_size=30, bg_col=(0, 0.4, 0.8, 1), size_hint=(1, 0.3))
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

        # TOUCHPAD (Now Rounded)
        tp = TouchPad(text="TOUCHPAD", color=(1,1,1,0.3), 
                      pos_hint={'center_x': 0.5, 'center_y': 0.55}, 
                      size_hint=(0.25, 0.35))
        
        with tp.canvas.before:
            Color(0.15, 0.15, 0.18, 1)
            self.tp_rect = RoundedRectangle(pos=tp.pos, size=tp.size, radius=[20])
            
        def update_tp(instance, value):
            self.tp_rect.pos = instance.pos
            self.tp_rect.size = instance.size
        tp.bind(pos=update_tp, size=update_tp)
        self.layout.add_widget(tp)

        # MOUSE BUTTONS
        def make_btn(text, pos, size, cmd, bg_col=(0.25, 0.25, 0.28, 1), txt_col=(1,1,1,1)):
            btn = RoundedButton(text=text, pos_hint=pos, size_hint=size, bg_col=bg_col, text_col=txt_col)
            btn.bind(on_press=lambda x: send_msg(f"{cmd}:DOWN"))
            btn.bind(on_release=lambda x: send_msg(f"{cmd}:UP"))
            self.layout.add_widget(btn)

        make_btn("LMB", {'right': 0.49, 'top': 0.36}, (0.12, 0.12), "LMB")
        make_btn("RMB", {'x': 0.51, 'top': 0.36}, (0.12, 0.12), "RMB")

        # CONTROLS
        # Rounded Pedals
        make_btn("BRAKE", {'x': 0.02, 'top': 0.98}, (0.3, 0.25), "BTN_LB", bg_col=(0.6, 0.1, 0.1, 1))
        make_btn("GAS", {'right': 0.98, 'top': 0.98}, (0.3, 0.25), "BTN_RB", bg_col=(0.1, 0.5, 0.2, 1))

        # Rounded ABXY
        make_btn("Y", {'right': 0.85, 'y': 0.45}, (0.08, 0.15), "BTN_Y", txt_col=(1, 1, 0.4, 1))
        make_btn("A", {'right': 0.85, 'y': 0.10}, (0.08, 0.15), "BTN_A", txt_col=(0.4, 1, 0.4, 1))
        make_btn("X", {'right': 0.94, 'y': 0.28}, (0.08, 0.15), "BTN_X", txt_col=(0.4, 0.6, 1, 1))
        make_btn("B", {'right': 0.76, 'y': 0.28}, (0.08, 0.15), "BTN_B", txt_col=(1, 0.4, 0.4, 1))

        # Rounded DPAD
        make_btn("U", {'x': 0.13, 'y': 0.45}, (0.08, 0.15), "BTN_UP")
        make_btn("D", {'x': 0.13, 'y': 0.10}, (0.08, 0.15), "BTN_DOWN")
        make_btn("L", {'x': 0.04, 'y': 0.28}, (0.08, 0.15), "BTN_LEFT")
        make_btn("R", {'x': 0.22, 'y': 0.28}, (0.08, 0.15), "BTN_RIGHT")
        
        # Rounded Start/Select
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
