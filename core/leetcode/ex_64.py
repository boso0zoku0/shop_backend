# def minPathSum(grid):
#     m, n = len(grid), len(grid[0])
#
#     # Используем первую строку как dp
#     dp = grid[0][:]  # копируем первую строку
#
#     # Заполняем первую строку
#     for j in range(1, n):
#         dp[j] += dp[j - 1]
#
#     # Обрабатываем остальные строки
#     for i in range(1, m):
#         dp[0] += grid[i][0]  # первый элемент текущей строки
#         for j in range(1, n):
#             dp[j] = min(dp[j], dp[j - 1]) + grid[i][j]
#
#     return dp[n - 1]
#
#
# print(minPathSum(input))
from collections import defaultdict
from itertools import count


# def partition_list(head: list, x: int):
#     before = []
#     after = []
#     for i, el in enumerate(head):
#         if el >= x:
#             after.insert(i, el)
#         elif el < x:
#             before.insert(i, el)
#     return before + after
#
#
# print(partition_list([1, 4, 3, 2, 5, 2], 3))


# def merge(nums1: list, m: int, nums2: list, n: int):
#     before = []
#     after = []
#
#     for i, el in enumerate(nums1):
#         if i == m:
#             break
#         before.insert(i, el)
#     for i, el in enumerate(nums2):
#         if i == n:
#             break
#         after.insert(i, el)
#     new_list = sorted(before + after)
#     nums1.clear()
#
#     for i, el in enumerate(new_list):
#         nums1.insert(i, el)
#     return nums1
#
#
# print(merge(nums1=[1, 2, 3, 0, 0, 0], m=3, nums2=[2, 5, 6], n=3))


# def subsets_with_dup(nums: list[int]):
#     new_arr = []
#     for i, el in enumerate(range(len(nums) + 1)):
#         n = nums[:i]
#         new_arr.append(n)
#         if len(n) == len(nums):
#             for j, e in enumerate(reversed(nums)):
#                 if j == 0:
#                     continue
#                 n = nums[j:]
#                 new_arr.append(n)
#
#     return new_arr
#
#
# print(subsets_with_dup([1, 2, 2]))


# def reverse_between(head: list, left: int, right: int):
#     if left + right <= 2:
#         return head
#     i_section: list = []
#     for i, el in enumerate(head):
#         if i == left:
#             i_section.append(i)
#         if i == right:
#             i_section.append(i)
#             i_s = abs(i_section[0] - i_section[1])
#
#             head[i_s : len(i_section)] = head[len(i_section) : i_s]
#         return head
#
#


def max_profit(prices: list[int]):
    s = 0
    for i, v in enumerate(prices):
        if i >= 1:
            print(f"f {prices[i] < prices[i - 1]}")
            if prices[i] < prices[i - 1]:

                return 0
            else:
                s += prices[i] - prices[i - 1]
    return s


print(max_profit([3, 33, 333]))
