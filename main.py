import socket
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.clock import Clock
from plyer import accelerometer
from kivy.core.window import Window
from kivy.metrics import dp

# --- CONFIGURATION ---
Window.clearcolor = (0.1, 0.1, 0.1, 1)

# --- NETWORK ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_IP = "192.168.1.1" 
SERVER_PORT = 5000

def send_msg(msg):
    try:
        sock.sendto(msg.encode('utf-8'), (SERVER_IP, int(SERVER_PORT)))
    except: pass

# --- WIDGETS ---
class TouchPad(Label):
    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            send_msg(f"MOUSE_MOVE:{touch.dx},{touch.dy}")

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        layout.add_widget(Label(text="OVERDRIVE", font_size='40sp', bold=True, color=(0, 0.9, 1, 1)))
        
        self.ip_input = TextInput(text="192.168.", multiline=False, font_size='30sp', size_hint=(1, 0.2),
                                  background_color=(0.2, 0.2, 0.2, 1), foreground_color=(1,1,1,1))
        layout.add_widget(self.ip_input)
        
        btn = Button(text="START ENGINE", font_size='25sp', background_color=(0, 0.8, 0, 1), size_hint=(1, 0.3))
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
        # We rotate the entire screen content to match the phone held sideways
        self.rotation_layout = RelativeLayout()
        
        # Apply 90 degree rotation if phone is portrait
        if Window.width < Window.height:
            self.rotation_layout.canvas.before.clear()
            with self.rotation_layout.canvas.before:
                from kivy.graphics import Rotate, PushMatrix, PopMatrix, Translate
                PushMatrix()
                # Rotate around the center
                Rotate(angle=-90, origin=self.center)
                # Since we rotated, we need to swap width/height logic visually, 
                # but Kivy makes this hard. 
                # instead, we will just design for LANDSCAPE and let the user rotate the phone.
            self.rotation_layout.canvas.after.add(PopMatrix())
        
        # --- THE MAIN LAYOUT ---
        # We use a FloatLayout that assumes LANDSCAPE (Width > Height)
        self.layout = FloatLayout()

        # 1. TOP BAR (Pedals & Toggle)
        # Gas (Right/Top side)
        btn_gas = Button(text="GAS", pos_hint={'right': 0.98, 'center_y': 0.7}, size_hint=(0.25, 0.4), 
                         background_color=(0,0.7,0,1), font_size='20sp', bold=True)
        btn_gas.bind(on_press=lambda x: send_msg("BTN_RB:DOWN"))
        btn_gas.bind(on_release=lambda x: send_msg("BTN_RB:UP"))
        self.layout.add_widget(btn_gas)

        # Brake (Left/Top side)
        btn_brake = Button(text="BRAKE", pos_hint={'x': 0.02, 'center_y': 0.7}, size_hint=(0.25, 0.4), 
                           background_color=(0.7,0,0,1), font_size='20sp', bold=True)
        btn_brake.bind(on_press=lambda x: send_msg("BTN_LB:DOWN"))
        btn_brake.bind(on_release=lambda x: send_msg("BTN_LB:UP"))
        self.layout.add_widget(btn_brake)

        # Gyro Toggle (Middle Top)
        sw = Switch(active=True, size_hint=(None, None), size=(dp(100), dp(50)), 
                    pos_hint={'center_x': 0.5, 'top': 0.98})
        sw.bind(active=self.toggle_gyro)
        self.layout.add_widget(sw)


        # 2. CENTER ZONE (Touchpad & Mouse)
        # Touchpad
        tp = TouchPad(text="TOUCHPAD", color=(1,1,1,0.2), 
                      pos_hint={'center_x': 0.5, 'center_y': 0.5}, 
                      size_hint=(0.3, 0.4))
        with tp.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.15, 0.15, 0.15, 1)
            self.tp_rect = Rectangle(pos=tp.pos, size=tp.size)
        tp.bind(pos=lambda instance, value: setattr(self.tp_rect, 'pos', instance.pos))
        tp.bind(size=lambda instance, value: setattr(self.tp_rect, 'size', instance.size))
        self.layout.add_widget(tp)

        # Mouse Buttons (Below Touchpad)
        btn_lmb = Button(text="LMB", pos_hint={'right': 0.49, 'top': 0.28}, size_hint=(0.14, 0.12))
        btn_lmb.bind(on_press=lambda x: send_msg("LMB:DOWN"), on_release=lambda x: send_msg("LMB:UP"))
        self.layout.add_widget(btn_lmb)

        btn_rmb = Button(text="RMB", pos_hint={'x': 0.51, 'top': 0.28}, size_hint=(0.14, 0.12))
        btn_rmb.bind(on_press=lambda x: send_msg("RMB:DOWN"), on_release=lambda x: send_msg("RMB:UP"))
        self.layout.add_widget(btn_rmb)


        # 3. D-PAD ZONE (Bottom Left) -> FIXED SQUARE CONTAINER
        # We create a RelativeLayout to hold the D-Pad buttons together
        dpad_zone = RelativeLayout(pos_hint={'x': 0.05, 'y': 0.05}, size_hint=(None, None), size=(dp(180), dp(180)))
        
        def make_dpad(text, px, py, cmd):
            btn = Button(text=text, pos_hint={'center_x': px, 'center_y': py}, size_hint=(0.3, 0.3), background_color=(0.2,0.2,0.2,1))
            btn.bind(on_press=lambda x: send_msg(f"{cmd}:DOWN"))
            btn.bind(on_release=lambda x: send_msg(f"{cmd}:UP"))
            dpad_zone.add_widget(btn)

        make_dpad("U", 0.5, 0.85, "BTN_UP")
        make_dpad("D", 0.5, 0.15, "BTN_DOWN")
        make_dpad("L", 0.15, 0.5, "BTN_LEFT")
        make_dpad("R", 0.85, 0.5, "BTN_RIGHT")
        self.layout.add_widget(dpad_zone)


        # 4. ABXY ZONE (Bottom Right) -> FIXED SQUARE CONTAINER
        face_zone = RelativeLayout(pos_hint={'right': 0.95, 'y': 0.05}, size_hint=(None, None), size=(dp(180), dp(180)))

        def make_face(text, px, py, cmd, col):
            btn = Button(text=text, pos_hint={'center_x': px, 'center_y': py}, size_hint=(0.3, 0.3), 
                         background_color=col, background_normal='', font_size='20sp', bold=True)
            btn.bind(on_press=lambda x: send_msg(f"{cmd}:DOWN"))
            btn.bind(on_release=lambda x: send_msg(f"{cmd}:UP"))
            face_zone.add_widget(btn)

        make_face("Y", 0.5, 0.85, "BTN_Y", (1,1,0,1))
        make_face("A", 0.5, 0.15, "BTN_A", (0,1,0,1))
        make_face("X", 0.15, 0.5, "BTN_X", (0,0,1,1))
        make_face("B", 0.85, 0.5, "BTN_B", (1,0,0,1))
        self.layout.add_widget(face_zone)

        # Start/Select (Tiny buttons in bottom center)
        btn_sel = Button(text="SLCT", pos_hint={'center_x': 0.4, 'y': 0.02}, size_hint=(None, None), size=(dp(60), dp(40)))
        btn_sel.bind(on_press=lambda x: send_msg("BTN_SELECT:DOWN"), on_release=lambda x: send_msg("BTN_SELECT:UP"))
        self.layout.add_widget(btn_sel)

        btn_str = Button(text="STRT", pos_hint={'center_x': 0.6, 'y': 0.02}, size_hint=(None, None), size=(dp(60), dp(40)))
        btn_str.bind(on_press=lambda x: send_msg("BTN_START:DOWN"), on_release=lambda x: send_msg("BTN_START:UP"))
        self.layout.add_widget(btn_str)

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
            tilt = (val[1] / 9.81) * 90
            send_msg(f"STEER:{tilt:.2f}")
        except: pass

class OverdriveApp(App):
    def build(self):
        # Force the app to act like it's landscape 
        # (This helps on some devices, but user should still rotate phone)
        Window.rotation = 270 
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    OverdriveApp().run()
