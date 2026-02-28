# game.py
import random


class Card:
    SUITS = ['♥', '♦', '♣', '♠']
    RANKS = [('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6), 
             ('7', 7), ('8', 8), ('9', 9), ('10', 10), 
             ('J', 10), ('Q', 10), ('K', 10), ('A', 11)]
    
    def __init__(self):
        r, self.value = random.choice(self.RANKS)
        self.rank = r
        self.suit = random.choice(self.SUITS)
        self.is_red = self.suit in ['♥', '♦']
    
    def to_dict(self):
        return {'r': self.rank, 's': self.suit, 'v': self.value, 'red': self.is_red}


class Game:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.p1_balance = 1000
        self.p2_balance = 1000
        self.p1_cards = []
        self.p2_cards = []
        self.p1_bet = 0
        self.p2_bet = 0
        self.state = 'WAITING'
        self.winner = None
        self.message = 'Ожидание...'
        self.my_player = 1
    
    def get_value(self, cards):
        total = 0
        aces = 0
        for c in cards:
            if c.rank == 'A':
                aces += 1
                total += 11
            else:
                total += c.value
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total
    
    def deal(self):
        self.p1_cards = [Card(), Card()]
        self.p2_cards = [Card(), Card()]
        v1 = self.get_value(self.p1_cards)
        v2 = self.get_value(self.p2_cards)
        
        if v1 == 21 and v2 == 21:
            self.end_round(0, 'Оба BlackJack! Ничья!')
        elif v1 == 21:
            self.end_round(1, 'Игрок 1 - BlackJack!')
        elif v2 == 21:
            self.end_round(2, 'Игрок 2 - BlackJack!')
        else:
            self.state = 'PLAYER1_TURN'
            self.message = 'Ход Игрока 1'
    
    def place_bet(self, player, amount):
        if player == 1:
            if amount > self.p1_balance:
                return False
            self.p1_balance -= amount
            self.p1_bet = amount
        else:
            if amount > self.p2_balance:
                return False
            self.p2_balance -= amount
            self.p2_bet = amount
        
        if self.p1_bet > 0 and self.p2_bet > 0:
            self.deal()
        return True
    
    def hit(self, player):
        if player == 1:
            self.p1_cards.append(Card())
            if self.get_value(self.p1_cards) > 21:
                self.end_round(2, 'Игрок 1 перебрал!')
                return True
        else:
            self.p2_cards.append(Card())
            if self.get_value(self.p2_cards) > 21:
                self.end_round(1, 'Игрок 2 перебрал!')
                return True
        return False
    
    def stand(self, player):
        if player == 1:
            self.state = 'PLAYER2_TURN'
            self.message = 'Ход Игрока 2'
        else:
            self.showdown()
    
    def showdown(self):
        v1 = self.get_value(self.p1_cards)
        v2 = self.get_value(self.p2_cards)
        if v1 > v2:
            self.end_round(1, f'{v1} vs {v2}. Победа Игрока 1!')
        elif v2 > v1:
            self.end_round(2, f'{v1} vs {v2}. Победа Игрока 2!')
        else:
            self.end_round(0, f'Ничья! {v1}')
    
    def end_round(self, winner, message):
        self.winner = winner
        self.message = message
        if winner == 1:
            self.p1_balance += self.p1_bet * 2
        elif winner == 2:
            self.p2_balance += self.p2_bet * 2
        else:
            self.p1_balance += self.p1_bet
            self.p2_balance += self.p2_bet
        self.state = 'ROUND_END'
    
    def new_round(self):
        self.p1_cards = []
        self.p2_cards = []
        self.p1_bet = 0
        self.p2_bet = 0
        self.winner = None
        self.state = 'BETTING'
        self.message = 'Сделайте ставки!'
    
    def to_dict(self):
        return {
            'state': self.state,
            'p1_balance': self.p1_balance,
            'p2_balance': self.p2_balance,
            'p1_bet': self.p1_bet,
            'p2_bet': self.p2_bet,
            'p1_cards': [c.to_dict() for c in self.p1_cards],
            'p2_cards': [c.to_dict() for c in self.p2_cards],
            'p1_value': self.get_value(self.p1_cards),
            'p2_value': self.get_value(self.p2_cards),
            'winner': self.winner,
            'message': self.message
        }