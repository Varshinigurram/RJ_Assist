

Experience
In week five we studied binary search trees. The lecture described the rule that each left child holds a smaller value and each right child holds a larger value. We covered insertion, which adds a new key while preserving this order; searching, which compares the target with nodes and moves left or right; and deletion, which removes a node and may replace it with its in‑order successor. The class also introduced three traversal methods: inorder, preorder, and postorder.

Feelings
I think the BST concept is logical but requires practice to visualize. The rule of smaller left and larger right makes sense, yet I find insertion and deletion a bit confusing at first. Searching feels straightforward because each comparison guides the path, but deletion still seems tricky because the tree must stay ordered. Overall, the topic is interesting and I want to work on more examples.

Learning
The core principle is the ordering invariant: for any node, all keys in its left subtree are smaller and all keys in its right subtree are larger. This property allows each operation to reduce the search space by about half. Insertion follows the rule to place a new key at the correct leaf. Searching uses the same comparison to walk down the tree. Deletion must keep the invariant, so removing a node with two children often replaces it with its in‑order successor. Inorder traversal outputs keys in sorted order, while preorder and postorder give different sequences for specific tasks.

Application
A practical example is a simple contact manager that needs fast lookups by name. Storing each contact in a binary search tree keyed by name allows the program to find a contact in O(log n) time on average, which is much quicker than scanning a list. Adding a new contact uses insertion to place it correctly, and removing a contact uses deletion while preserving the order. An inorder traversal can list all contacts alphabetically, which is useful for display.

Conclusion
The main takeaway is that the BST ordering invariant enables efficient insertion, deletion, and search, and that traversal methods provide different ways to access the data. I also learned that deletion requires careful handling, often using the in‑order successor. To improve, I will write code that implements these operations and test it with various inputs. Understanding balancing techniques would be a logical next step.