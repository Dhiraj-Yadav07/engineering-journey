class Solution:
    def intersection(self, nums1: list[int], nums2: list[int]) -> list[int]:
        set1 = set(nums1)
        result = set()

        for num in nums2:
            if num in set1:
                result.add(num)

        return list(result)