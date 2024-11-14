#n = int(input('n = '))
import math

def s(n):
    if n == 1:
        return 1
    elif n == 2:
        return 2
    else:
        return s(n-2) + s(n-1)

def ss(n):
    a, b = 1, 1
    for _ in range(n-1):
        a, b = b, a + b
        #print(a,b)
    return b

def sss(n):
    d = [1,1]
    for i in range(2,n+1):
        d.insert(i,d[i-1] + d[i-2])
        print(d)
    return d[n]

def minCostClimbingStairs2(cost: list[int]) -> int:
    n = len(cost)
    i = 0
    x = 0
    while i <= n-4:
        a,b,c = cost[i] + cost[i+2],cost[i+1] + cost[i+2],cost[i+3] + cost[i+1]
        if min(a,b,c) == a:
            i += 3
        elif min(a,b,c) == b:
            i += 3
        else:
            i += 4
        x += min(a,b,c)
    else:
        a,b,c = cost[i] + cost[i+1],cost[i] + cost[i+2],cost[i+1]
        x += min(a,b,c)
    return x
def minCostClimbingStairs(cost: list[int]) -> int:
        n = len(cost)
        dp = [0,0]
        for i in range(2,n+1):
            dp[i%2] = min(cost[i-1]+dp[0],cost[i-2]+dp[1])
        return max(dp)
class Solution:
    def rob(self, nums: list[int]) -> int:
        n = len(nums)
        dp = [0]*(n+2)
        for i in range(0,n):
            dp[i] = max(dp[i-1],dp[i-2]+nums[i])
        return dp[n-1]
    def deleteAndEarn(self, nums: list[int]) -> int:
        if len(nums) == 1:
            return nums[0]
        maxnum = max(nums) + 1
        coins = [0] * maxnum
        for num in nums:
            coins[num] = coins[num] + num
        dp = [0] * maxnum
        dp[0] = coins[0]
        dp[1] = max(coins[0], coins[1])

        for i in range(2, maxnum):
            dp[i] = max(dp[i - 2] + coins[i], dp[i - 1])
        return dp[maxnum - 1]
    def uniquePaths(self, m: int, n: int) -> int:
        if n == 1 or m == 1:
            return 1
        if n == 2:
            return m
        elif m == 2:
            return n
        d = [1]*min(n,m)
        p = [1]+[0]*(min(n,m)-1)
        for i in range(1,max(n,m)):
            for j in range(1,min(n,m)):
                p[j] = d[j] + p[j-1]
            d, p = p,d
        if math.comb(n+m-2,n-1) == d[j]:
            return d[j]
        else:
            print(d,p)
    
a = Solution()
a.uniquePaths(3,4)