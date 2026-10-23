
class Solution:
    def isSymmetric(self, root: TreeNode | None) -> bool:
        if root is None:
            return True

        return self.isMirror(root.left, root.right)

    def isMirror(self, left: TreeNode | None, right: TreeNode | None) -> bool:
        if left is None and right is None:
            return True

        if left is None or right is None:
            return False

        return (
            left.val == right.val
            and self.isMirror(left.left, right.right)
            and self.isMirror(left.right, right.left)
        )