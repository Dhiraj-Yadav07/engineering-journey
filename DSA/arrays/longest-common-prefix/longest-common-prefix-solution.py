class Solution:
    def longestCommonPrefix(self, strs: list[str]) -> str:
        result = ""
        base = strs[0]
        for i in range(0,len(base)):
            for word in strs[1:]:
                if i == len(word) or base[i] != word[i]:
                    return result
            result =  result + base[i]
        return result