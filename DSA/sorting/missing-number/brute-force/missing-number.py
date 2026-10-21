class Solution:
    def missingNumber(self, nums: list[int]) -> int:
        sorted_nums = sorted(nums)
        n = len(sorted_nums)

        for i in range(n):
            if sorted_nums[i] != i:
                return i
        return n