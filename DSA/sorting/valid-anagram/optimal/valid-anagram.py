class Solution:
    def isAnagram(self, s: str, t: str) -> bool:

        if len(s) != len(t):
            return False

        dict_s = {}
        dict_t = {}

        for char in s:
            if char not in dict_s:
                dict_s[char] = 1
            else:
                dict_s[char] = dict_s[char] + 1
        
        for char in t:
            if char not in dict_t:
                dict_t[char] = 1
            else:
                dict_t[char] = dict_t[char] + 1

        if dict_s == dict_t:
            return True
        return False