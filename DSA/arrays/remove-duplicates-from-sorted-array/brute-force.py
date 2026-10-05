class Solution:
    def removeDuplicates(self, nums: list[int]) -> int:
        n = len(nums)
        freq_map = {}
        for i in range(0,n):
            freq_map[nums[i]] = 0
            i = i+1
        j=0
        for k in freq_map:
            nums[j] = k
            j = j+1
        return j