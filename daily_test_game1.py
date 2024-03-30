import random

class role:
    level = 1
    experience_value = 0
    HP = 500
    AP = 200
    age = 18
    def __init__(self,name) -> None:
        self.name = name
        pass
    def move(self):
        print(f'{self.name}向敌人冲刺！')
        pass
    def defense(self,order):
        if order == 1:
            print(f'{self.name}发起了一次格挡')
            return 0.5
        elif order == 2:
            print(f'{self.name}尝试闪避')
            return random.choice([0,1])
class warrior(role):
    def fight(self,order):
        if order == 1:
            print(f'{self.name}发起了一次普通攻击')
            return 200
        elif order == 2:
            print(f'{self.name}发起了一次暴击')
            return random.choice([50,300])
class monster(role):
    def fight(self,order):
        if order == 1:
            print(f'{self.name}发起了一次利刃攻击')
            return 200
        elif order == 2:
            print(f'{self.name}发起了一次暴怒攻击')
            return random.choice([100,350])
yourname = input('please input your name: ')
you = warrior(yourname)
enemy = monster('暴龙君')

round = 0
while True:
    round += 1
    your_fight_order = int(input('Please input your fight order: 1.普通攻击    2.暴击\n'))
    fight = you.fight(your_fight_order)
    enemy_defense_order = random.choice([1,2])
    HP_loss = float(enemy.defense(enemy_defense_order))*fight
    enemy.HP -= HP_loss
    if enemy.HP <= 0:
        print(f'{enemy.name}was dead, {you.name} win!')
        print(f'round_{round}')
        break
    elif enemy.HP > 0:
        print(f'{enemy.name}受到{HP_loss}点伤害, 剩余{enemy.HP}点生命')
        print('')

    you_defense_order = int(input('Please input your defense order: 1.格挡    2.闪避\n'))
    enemy_fight_order = random.choice([1,2])
    fight = enemy.fight(enemy_fight_order)
    HP_loss = float(you.defense(you_defense_order))*fight
    you.HP -= HP_loss
    if you.HP <= 0:
        print(f'{you.name} was dead, {enemy.name} win!')
        print(f'round_{round}')
        break
    elif you.HP > 0:
        print(f'{you.name}受到{HP_loss}点伤害, 剩余{you.HP}点生命')
        print('')