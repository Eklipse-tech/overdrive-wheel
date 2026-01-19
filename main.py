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
# Import vibrator safely
try:
    from plyer import vibrator
except:
    vibrator = None
from kivy.core.window import Window
from kivy.metrics import dp

# --- CONFIGURATION ---
Window.clearcolor = (0.1, 0.1, 0.1, 1)
# REMOVED: Window.rotation = 270 (Now runs in native Portrait)

# --- NETWORK SETUP ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_IP = "192.168.1.1" 
SERVER_PORT = 5000

def send_msg(msg):
    try:
        if SERVER_IP and len(SERVER_IP) > 7:
            sock.sendto(msg.encode('utf-8'), (SERVER_IP, int(SERVER_PORT)))
    except Exception as e:
        print(f"Network Error: {e}")

def safe_rumble(duration=0.05):
    try:
        if vibrator:
            vibrator.vibrate(duration)
    except:
        pass

# --- WIDGETS ---
class TouchPad(Label):
    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            # In portrait, coordinates might need 1.5x speed
            send_msg(f"MOUSE_MOVE:{touch.dx * 1.5},{touch.dy * 1.5}")

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Vertical Layout for Login
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))
        
        layout.add_widget(Label(text="OVERDRIVE", font_size='40sp', bold=True, color=(0, 0.9, 1, 1), size_hint=(1, 0.4)))
        
        self.ip_input = TextInput(text="192.168.", multiline=False, font_size='30sp', size_hint=(1, 0.15),
                                  background_color=(0.2, 0.2, 0.2, 1), foreground_color=(1,1,1,1), halign='center')
        layout.add_widget(self.ip_input)
        
        # Spacer
        layout.add_widget(Label(size_hint=(1, 0.1)))

        btn = Button(text="START ENGINE", font_size='25sp', background_color=(0, 0.8, 0, 1), size_hint=(1, 0.2))
        btn.bind(on_press=self.connect)
        layout.add_widget(btn)
        
        self.add_widget(layout)

    def connect(self, instance):
        global SERVER_IP
        SERVER_IP = self.ip_input.text
        safe_rumble(0.1)
        self.manager.current = 'game'

class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()

        # --- 1. TOP SECTION (PEDALS) ---
        # Brake (Red) - Top Left
        btn_brake = Button(text="BRAKE", pos_hint={'x': 0.02, 'top': 0.98}, size_hint=(0.47, 0.25), 
                           background_color=(0.8,0,0,1), font_size='24sp', bold=True)
        btn_brake.bind(on_press=lambda x: self.btn_action("BTN_LB:DOWN"))
        btn_brake.bind(on_release=lambda x: self.btn_action("BTN_LB:UP"))
        self.layout.add_widget(btn_brake)

        # Gas (Green) - Top Right
        btn_gas = Button(text="GAS", pos_hint={'right': 0.98, 'top': 0.98}, size_hint=(0.47, 0.25), 
                         background_color=(0,0.8,0,1), font_size='24sp', bold=True)
        btn_gas.bind(on_press=lambda x: self.btn_action("BTN_RB:DOWN"))
        btn_gas.bind(on_release=lambda x: self.btn_action("BTN_RB:UP"))
        self.layout.add_widget(btn_gas)


        # --- 2. MIDDLE SECTION (TOUCHPAD) ---
        # A bit lower now
        tp = TouchPad(text="TOUCHPAD", color=(1,1,1,0.2), 
                      pos_hint={'center_x': 0.5, 'top': 0.70}, size_hint=(0.9, 0.25))
        with tp.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.15, 0.15, 0.15, 1)
            self.tp_rect = Rectangle(pos=tp.pos, size=tp.size)
        tp.bind(pos=lambda instance, value: setattr(self.tp_rect, 'pos', instance.pos))
        tp.bind(size=lambda instance, value: setattr(self.tp_rect, 'size', instance.size))
        self.layout.add_widget(tp)


        # --- 3. UTILITY ROW (Mouse & Toggle) ---
        # LMB
        btn_lmb = Button(text="LMB", pos_hint={'x': 0.05, 'top': 0.43}, size_hint=(0.2, 0.08))
        btn_lmb.bind(on_press=lambda x: self.btn_action("LMB:DOWN"), on_release=lambda x: self.btn_action("LMB:UP"))
        self.layout.add_widget(btn_lmb)

        # RMB
        btn_rmb = Button(text="RMB", pos_hint={'x': 0.27, 'top': 0.43}, size_hint=(0.2, 0.08))
        btn_rmb.bind(on_press=lambda x: self.btn_action("RMB:DOWN"), on_release=lambda x: self.btn_action("RMB:UP"))
        self.layout.add_widget(btn_rmb)
        
        # Gyro Toggle Switch (Right side)
        sw = Switch(active=True, size_hint=(None, None), size=(dp(80), dp(40)), 
                    pos_hint={'right': 0.95, 'center_y': 0.39})
        sw.bind(active=self.toggle_gyro)
        self.layout.add_widget(sw)
        
        self.layout.add_widget(Label(text="STEER", pos_hint={'right': 0.75, 'center_y': 0.39}, font_size='12sp', color=(0.5,0.5,0.5,1)))


        # --- 4. BOTTOM SECTION (CONTROLS) ---
        
        # D-PAD (Bottom Left)
        dpad_zone = RelativeLayout(pos_hint={'x': 0.02, 'y': 0.02}, size_hint=(None, None), size=(dp(160), dp(160)))
        def make_dpad(text, px, py, cmd):
            btn = Button(text=text, pos_hint={'center_x': px, 'center_y': py}, size_hint=(0.32, 0.32), background_color=(0.25,0.25,0.25,1))
            btn.bind(on_press=lambda x: self.btn_action(f"{cmd}:DOWN"))
            btn.bind(on_release=lambda x: self.btn_action(f"{cmd}:UP"))
            dpad_zone.add_widget(btn)
        
        make_dpad("U", 0.5, 0.85, "BTN_UP")
        make_dpad("D", 0.5, 0.15, "BTN_DOWN")
        make_dpad("L", 0.15, 0.5, "BTN_LEFT")
        make_dpad("R", 0.85, 0.5, "BTN_RIGHT")
        self.layout.add_widget(dpad_zone)

        # ABXY (Bottom Right)
        face_zone = RelativeLayout(pos_hint={'right': 0.98, 'y': 0.02}, size_hint=(None, None), size=(dp(160), dp(160)))
        def make_face(text, px, py, cmd, col):
            btn = Button(text=text, pos_hint={'center_x': px, 'center_y': py}, size_hint=(0.32, 0.32), 
                         background_color=col, background_normal='', font_size='20sp', bold=True)
            btn.bind(on_press=lambda x: self.btn_action(f"{cmd}:DOWN"))
            btn.bind(on_release=lambda x: self.btn_action(f"{cmd}:UP"))
            face_zone.add_widget(btn)
            
        make_face("Y", 0.5, 0.85, "BTN_Y", (1,1,0,1))
        make_face("A", 0.5, 0.15, "BTN_A", (0,1,0,1))
        make_face("X", 0.15, 0.5, "BTN_X", (0,0,1,1))
        make_face("B", 0.85, 0.5, "BTN_B", (1,0,0,1))
        self.layout.add_widget(face_zone)

        # START/SELECT (Tiny buttons in the very middle bottom)
        btn_sel = Button(text="SLCT", pos_hint={'center_x': 0.5, 'y': 0.12}, size_hint=(0.15, 0.06), font_size='10sp')
        btn_sel.bind(on_press=lambda x: self.btn_action("BTN_SELECT:DOWN"), on_release=lambda x: self.btn_action("BTN_SELECT:UP"))
        self.layout.add_widget(btn_sel)
        
        btn_str = Button(text="STRT", pos_hint={'center_x': 0.5, 'y': 0.05}, size_hint=(0.15, 0.06), font_size='10sp')
        btn_str.bind(on_press=lambda x: self.btn_action("BTN_START:DOWN"), on_release=lambda x: self.btn_action("BTN_START:UP"))
        self.layout.add_widget(btn_str)

        self.add_widget(self.layout)
        
        # --- SENSORS ---
        self.gyro_active = True
        try:
            accelerometer.enable()
            Clock.schedule_interval(self.update_gyro, 1.0 / 60.0)
        except Exception as e:
            print(f"Gyro Error: {e}")

    def btn_action(self, msg):
        safe_rumble(0.02)
        send_msg(msg)

    def toggle_gyro(self, instance, value):
        self.gyro_active = value
        if not value: send_msg("STEER:0")

    def update_gyro(self, dt):
        if not self.gyro_active: return
        try:
            val = accelerometer.acceleration
            if val is None: return
            if val[0] is None: return 
            
            # PORTRAIT MODE UPDATE:
            # When holding phone vertically, "Tilt" is the X-axis (val[0]), not Y.
            # 9.81 = 90 degrees
            tilt = (val[0] / 9.81) * 90
            
            # We might need to invert this depending on how you hold it.
            # If left is right, uncomment the next line:
            # tilt = -tilt
            
            send_msg(f"STEER:{tilt:.2f}")
        except:
            pass

class OverdriveApp(App):
    def build(self):
        # REMOVED ROTATION LOCK
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    OverdriveApp().run()
