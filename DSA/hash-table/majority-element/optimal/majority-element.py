class Solution:
    def majorityElement(self, nums: list[int]) -> int:
        element = None
        counts = 0

        for num in nums:
            if counts == 0:
                element = num

            if element == num:
                counts = counts + 1 
            else:
                counts = counts - 1
        
        return element