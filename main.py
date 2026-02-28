# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp

import socket
import threading
import json

from game import Game  # Импорт из game.py


Window.clearcolor = (0.05, 0.25, 0.1, 1)


class Network:
    PORT = 55555
    
    def __init__(self, app):
        self.app = app
        self.socket = None
        self.is_host = False
        self.connected = False
    
    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def host(self):
        try:
            self.is_host = True
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', self.PORT))
            self.socket.listen(1)
            threading.Thread(target=self._accept, daemon=True).start()
            return True
        except Exception as e:
            print(f"Host error: {e}")
            return False
    
    def _accept(self):
        try:
            client, addr = self.socket.accept()
            self.socket.close()
            self.socket = client
            self.connected = True
            Clock.schedule_once(lambda dt: self.app.on_connect(), 0)
            self._receive()
        except Exception as e:
            print(f"Accept error: {e}")
    
    def join(self, ip):
        try:
            self.is_host = False
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((ip, self.PORT))
            self.socket.settimeout(None)
            self.connected = True
            threading.Thread(target=self._receive, daemon=True).start()
            return True
        except Exception as e:
            print(f"Join error: {e}")
            return False
    
    def _receive(self):
        while self.connected:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                msg = json.loads(data)
                Clock.schedule_once(lambda dt, m=msg: self.app.on_message(m), 0)
            except Exception as e:
                print(f"Receive error: {e}")
                break
        self.connected = False
    
    def send(self, data):
        if self.connected and self.socket:
            try:
                self.socket.send(json.dumps(data).encode('utf-8'))
                return True
            except:
                pass
        return False


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        layout.add_widget(Label(text='♠ BlackJack PvP ♥', font_size=dp(36), color=(1, 0.85, 0, 1)))
        
        self.ip_label = Label(text='IP: ...', font_size=dp(16), color=(0.5, 0.9, 0.5, 1))
        layout.add_widget(self.ip_label)
        
        self.ip_input = TextInput(hint_text='Введите IP друга', multiline=False, size_hint_y=None, height=dp(50))
        layout.add_widget(self.ip_input)
        
        layout.add_widget(Button(text='🏠 Создать игру', font_size=dp(20), on_press=self.create))
        layout.add_widget(Button(text='🔗 Присоединиться', font_size=dp(20), on_press=self.join))
        
        self.status = Label(text='', color=(1, 0.85, 0, 1))
        layout.add_widget(self.status)
        
        self.add_widget(layout)
        Clock.schedule_once(self.update_ip, 0.5)
    
    def update_ip(self, dt):
        self.ip_label.text = f'Ваш IP: {self.manager.parent.network.get_ip()}'
    
    def create(self, instance):
        self.status.text = '⏳ Ожидание...'
        if self.manager.parent.network.host():
            self.status.text = '⏳ Ожидание игрока 2...'
        else:
            self.status.text = '❌ Ошибка!'
    
    def join(self, instance):
        ip = self.ip_input.text.strip()
        if not ip:
            self.status.text = '❌ Введите IP!'
            return
        self.status.text = '⏳ Подключение...'
        if self.manager.parent.network.join(ip):
            self.manager.parent.game.my_player = 2
            self.manager.parent.start_game()
        else:
            self.status.text = '❌ Не удалось!'


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main = FloatLayout()
        
        with self.main.canvas.before:
            Color(0.08, 0.4, 0.15, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.main.bind(pos=self.update_bg, size=self.update_bg)
        
        # UI элементы...
        self.main.add_widget(Label(text='♠ ПРОТИВНИК ♠', font_size=dp(20), color=(1, 0.85, 0, 1), pos_hint={'center_x': 0.5, 'top': 0.98}, size_hint=(None, None), size=(dp(200), dp(40))))
        
        self.opp_score = Label(text='?', font_size=dp(18), color=(1, 0.85, 0, 1), pos_hint={'center_x': 0.5, 'top': 0.9}, size_hint=(None, None), size=(dp(60), dp(30)))
        self.main.add_widget(self.opp_score)
        
        self.opp_cards = BoxLayout(orientation='horizontal', spacing=dp(5), pos_hint={'center_x': 0.5, 'top': 0.82}, size_hint=(None, None), size=(dp(300), dp(100)))
        self.main.add_widget(self.opp_cards)
        
        self.msg = Label(text='Ожидание...', font_size=dp(18), color=(1, 0.85, 0, 1), pos_hint={'center_x': 0.5, 'center_y': 0.6}, size_hint=(0.9, None), height=dp(50))
        self.main.add_widget(self.msg)
        
        # Панели управления...
        self.bet_panel = BoxLayout(orientation='horizontal', spacing=dp(10), pos_hint={'center_x': 0.5, 'center_y': 0.5}, size_hint=(None, None), size=(dp(250), dp(50)))
        self.bet_input = TextInput(text='100', multiline=False, input_filter='int')
        self.bet_btn = Button(text='СТАВКА', on_press=self.place_bet)
        self.bet_panel.add_widget(self.bet_input)
        self.bet_panel.add_widget(self.bet_btn)
        self.main.add_widget(self.bet_panel)
        
        self.game_panel = BoxLayout(orientation='horizontal', spacing=dp(10), pos_hint={'center_x': 0.5, 'center_y': 0.5}, size_hint=(None, None), size=(dp(220), dp(50)))
        self.hit_btn = Button(text='ЕЩЁ', on_press=self.hit)
        self.stand_btn = Button(text='СТОП', on_press=self.stand)
        self.game_panel.add_widget(self.hit_btn)
        self.game_panel.add_widget(self.stand_btn)
        self.main.add_widget(self.game_panel)
        self.game_panel.opacity = 0
        
        self.new_btn = Button(text='НОВЫЙ РАУНД', pos_hint={'center_x': 0.5, 'center_y': 0.5}, size_hint=(None, None), size=(dp(180), dp(50)), on_press=self.new_round)
        self.main.add_widget(self.new_btn)
        self.new_btn.opacity = 0
        
        self.balance = Label(text='$1000', font_size=dp(24), color=(1, 0.85, 0, 1), pos_hint={'center_x': 0.5, 'y': 0.35}, size_hint=(None, None), size=(dp(150), dp(40)))
        self.main.add_widget(self.balance)
        
        self.main.add_widget(Label(text='♥ ВЫ ♥', font_size=dp(20), color=(1, 0.85, 0, 1), pos_hint={'center_x': 0.5, 'y': 0.25}, size_hint=(None, None), size=(dp(200), dp(40))))
        
        self.player_score = Label(text='0', font_size=dp(18), color=(1, 0.85, 0, 1), pos_hint={'center_x': 0.5, 'y': 0.18}, size_hint=(None, None), size=(dp(60), dp(30)))
        self.main.add_widget(self.player_score)
        
        self.player_cards = BoxLayout(orientation='horizontal', spacing=dp(5), pos_hint={'center_x': 0.5, 'y': 0.05}, size_hint=(None, None), size=(dp(300), dp(100)))
        self.main.add_widget(self.player_cards)
        
        self.add_widget(self.main)
    
    def update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size
    
    def place_bet(self, instance):
        app = self.manager.parent
        try:
            amount = int(self.bet_input.text)
        except:
            return
        my_bal = app.game.p1_balance if app.game.my_player == 1 else app.game.p2_balance
        if amount > my_bal:
            self.msg.text = 'Недостаточно средств!'
            return
        app.game.place_bet(app.game.my_player, amount)
        app.network.send({'type': 'bet', 'player': app.game.my_player, 'amount': amount})
        self.update_ui()
    
    def hit(self, instance):
        app = self.manager.parent
        app.game.hit(app.game.my_player)
        app.network.send({'type': 'hit', 'player': app.game.my_player})
        self.update_ui()
    
    def stand(self, instance):
        app = self.manager.parent
        app.game.stand(app.game.my_player)
        app.network.send({'type': 'stand', 'player': app.game.my_player})
        self.update_ui()
    
    def new_round(self, instance):
        app = self.manager.parent
        app.game.new_round()
        app.network.send({'type': 'new_round'})
        self.update_ui()
    
    def update_ui(self):
        app = self.manager.parent
        g = app.game
        
        my_bal = g.p1_balance if g.my_player == 1 else g.p2_balance
        self.balance.text = f'${my_bal}'
        self.msg.text = g.message
        
        my_hand = g.p1_cards if g.my_player == 1 else g.p2_cards
        opp_hand = g.p2_cards if g.my_player == 1 else g.p1_cards
        
        self.player_score.text = str(g.get_value(my_hand))
        
        show_opp = g.state in ['ROUND_END', 'SHOWDOWN']
        self.opp_score.text = str(g.get_value(opp_hand)) if show_opp else '?'
        
        self.render_cards(self.player_cards, my_hand, False)
        self.render_cards(self.opp_cards, opp_hand, not show_opp)
        
        my_turn = (g.my_player == 1 and g.state == 'PLAYER1_TURN') or \
                  (g.my_player == 2 and g.state == 'PLAYER2_TURN')
        
        self.bet_panel.opacity = 1 if g.state == 'BETTING' else 0
        self.game_panel.opacity = 1 if my_turn else 0
        self.new_btn.opacity = 1 if g.state == 'ROUND_END' and g.my_player == 1 else 0
    
    def render_cards(self, container, cards, face_down):
        container.clear_widgets()
        for c in cards:
            if face_down:
                btn = Button(size_hint=(None, None), size=(dp(55), dp(85)), background_color=(0.6, 0.1, 0.1, 1))
            else:
                color = (0.9, 0.9, 0.9, 1) if not c.is_red else (1, 0.9, 0.9, 1)
                text_color = (0.8, 0.1, 0.1, 1) if c.is_red else (0.1, 0.1, 0.1, 1)
                btn = Button(text=f'{c.rank}\n{c.suit}', color=text_color, font_size=dp(16), size_hint=(None, None), size=(dp(55), dp(85)), background_color=color)
            container.add_widget(btn)


class BlackJackApp(App):
    def build(self):
        self.game = Game()
        self.network = Network(self)
        
        self.sm = ScreenManager()
        self.sm.add_widget(MenuScreen(name='menu'))
        self.sm.add_widget(GameScreen(name='game'))
        return self.sm
    
    def on_connect(self):
        self.start_game()
    
    def on_message(self, msg):
        if msg['type'] == 'bet':
            self.game.place_bet(msg['player'], msg['amount'])
        elif msg['type'] == 'hit':
            self.game.hit(msg['player'])
        elif msg['type'] == 'stand':
            self.game.stand(msg['player'])
        elif msg['type'] == 'new_round':
            self.game.new_round()
        self.sm.get_screen('game').update_ui()
    
    def start_game(self):
        if self.network.is_host:
            self.game.my_player = 1
            self.game.state = 'BETTING'
            self.game.message = 'Сделайте ставки!'
        self.sm.current = 'game'
        self.sm.get_screen('game').update_ui()


if __name__ == '__main__':
    BlackJackApp().run()