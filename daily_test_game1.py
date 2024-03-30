class MyClass:
    i = 12345
    def __init__(self,i) -> None:
        self.i=i
    def f(self):
        return 'hello'
x = MyClass # x为一个类对象的引用，而不是类的实例
print(x.i)  
print(x.f(12))
print('________')
y = MyClass(12) # y为类的实例，会调用__init__()方法进行初始化并传递参数i = 12
print(y.i)
print(y.f())

class 新类别:
    名字 = ''
    性别 = ''
人=新类别()

import random
class role:
    level = 1
    experience_value = 0
    HP = 500
    AP = 200
    def __init__(self,name,age) -> None:
        self.name =  name
        self.age = age
        pass
    def move(self):
        print(f'{self.name}向敌人发起了冲刺!')
    def watch(self):
        print(f'{self.name}观察了四周')
    def defense(self,order):
        if order == '格挡':
            print(f'{self.name}使用了格挡')
            return 0.5
        if order == '闪避':
            return random.choice([0,1])
        pass
class warrior(role):
    def fight(self):
        print(f'{self.name}发起了一次攻击!')
player1 = warrior('OV',18)
player1.move()
player1.fight()