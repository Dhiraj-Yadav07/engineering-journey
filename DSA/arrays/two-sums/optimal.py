class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        hashmap= {}
        n= len(nums)
        for i in range(0,n):
            remaining = target - nums[i]
            if remaining in hashmap:
                return [hashmap[remaining],i]
            hashmap[nums[i]] = i