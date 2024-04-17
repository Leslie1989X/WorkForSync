import time

score = int(input("Please input int: "))
start = time.time()
if 0 <= score <= 100:
    if score == 100:
        print("A+")
    elif 100 > score >= 90:
        print("A")
    elif 90 > score >=80:
        print("B")
    elif 80 > score >=70:
        print("C")
    elif 70 > score >=60:
        print("D")
    else:
        print("E")
else:
    print("Wrong input...")
end = time.time()
print(f"{end-start}s")