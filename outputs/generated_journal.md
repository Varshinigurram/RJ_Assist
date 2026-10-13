Experience
In week 5 we studied binary search trees. We learned the BST property—left subtree holds smaller values, right subtree larger—and examined the core operations insertion, deletion, and searching. We also covered three traversal methods: inorder, preorder, and postorder. The material emphasized that the tree’s structure determines how each operation behaves and that traversal offers different ways to visit nodes.

Feelings
Initially the idea that changing a tree’s shape alters operation steps seemed abstract. Reflecting on the BST property showed me that left‑right ordering is the reason operations can navigate efficiently. I realized the same set of values can produce different trees depending on insertion order, which affects later steps. This shifted my view of trees from static containers to dynamic structures whose shape matters.

Learning
The BST property guarantees an ordered layout that guides insertion and search: each comparison sends the value left or right, preserving order without reshaping the whole tree. Deletion must locate a node and rearrange links while keeping the left‑smaller, right‑larger rule intact, showing how execution depends on existing structure. Traversal methods do not modify the tree; they define visitation sequences—inorder yields ascending order, preorder visits root before subtrees, postorder visits children before root. Seeing the same tree walked in three ways clarified why traversal serves different purposes such as sorted output or prefix expressions.

Application
Imagine a system that stores user IDs and must support insertions, deletions, and range queries. Keeping IDs in a BST lets the BST property maintain order, so an inorder traversal gives the IDs sorted. To find all IDs between two bounds, the tree can be traversed, visiting only nodes that fall within the range. Insertion and deletion use the same left‑right comparisons, updating the structure efficiently while preserving the ordering needed for fast queries.

Conclusion
My takeaway is that the BST’s strength lies in connecting its ordering property to how operations work and how traversal visits nodes. Understanding that shape influences performance highlights why balanced trees matter in practice. Next I will implement a simple BST, try different insertion orders to observe resulting shapes, and use inorder traversal to check that the output stays sorted.