class Solution:
    def romanToInt(self, s: str) -> int:
        n = len(s)
        result = 0
        letters = {
            "I": 1,
            "V": 5,
            "X": 10,
            "L": 50,
            "C": 100,
            "D": 500,
            "M": 1000
        }

        for i in range(0, n):
            if i < n-1 and letters[s[i]] < letters[s[i + 1]]:
                result = result - letters[s[i]]
            else:
                result =  result + letters[s[i]]
        
        return result