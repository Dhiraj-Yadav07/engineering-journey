class Solution:
    def removeDuplicates(self, nums: list[int]) -> int:
        n = len(nums)

        if n == 1:
            return 1

        i = 0
        j = i+1

        while j < n:
            if nums[j] != nums[i]:
                i = i + 1
                nums[i], nums[j] = nums[j], nums[i]
            j = j + 1
            
        return i + 1