import random
import string

nums = string.digits
letters = string.ascii_letters
symbol = string.punctuation
symbol1 = '@#*'
alphabet = list(nums+letters+symbol1)


random.shuffle(alphabet)


N = int(input('password long: '))
N2 = random.randint(0,int(N/2))
N3 = random.randint(0,N-N2)
password = ''.join(alphabet[:N])
print(password)
print(N2,N3)