class Node:
    def __init__(self, start=0, end=None, indexes=[]):
        self.branches = [None] * 27  # lowercase letters + '$' only

        # labels start & end idx
        self.start = start
        self.end = end

        # matching indexes for source text
        self.indexes = indexes
        self.suffix_link = None

    def get_labels(self):
        return SuffixTree.text[self.start : self.get_end()]

    def custom_repr(self, depth=0):
        labels = self.get_labels()
        # labels += str(self.start) + str(self.end)
        myrepr = f"{labels=}, indexes={self.indexes}, suffix={self.suffix_link.indexes if self.suffix_link else None}"
        list_of_node_repr = [myrepr] + [
            node.custom_repr(depth + 1) for node in self.branches if node
        ]

        separator = "\n"
        for i in range(depth):
            separator += "-"

        return separator.join(list_of_node_repr)

    def __repr__(self):
        return self.custom_repr()

    def get_end(self):
        # Rule 1: Point all leaf nodes at SuffixTree.END to automatically update edges.
        return SuffixTree.END if self.end is None else self.end

    # =================== builder functions ===================
    def reset_branches(self):
        self.branches = [None] * 27  # lowercase letters + '$' only

    def extend(self, char_idx, active_len=0, prev_parent=None):
        branch_idx = max(ord(SuffixTree.text[char_idx]) - 97, -1)

        if self.start + active_len < self.get_end():
            if SuffixTree.text[self.start + active_len] == SuffixTree.text[char_idx]:
                # Rule 3: char exists. Do nothing. Update active point
                node, _, _ = SuffixTree.active_point
                SuffixTree.active_point = (node, self, active_len + 1)
                return
            else:
                # Rule 2: char does not exist. Split label to create 2 new nodes. Clear remainder stack, if any.
                # Extend old node
                split_idx = self.start + active_len
                old_branch_idx = max(ord(SuffixTree.text[split_idx]) - 97, -1)
                replace_node = Node(self.start, split_idx, indexes=self.indexes.copy())
                replace_node.branches[old_branch_idx] = self

                # relink from active node
                old_branch_idx = max(ord(SuffixTree.text[self.start]) - 97, -1)
                SuffixTree.active_point[0].branches[old_branch_idx] = replace_node

                # fix start index
                self.start = split_idx

                # create new node
                last_idx = self.indexes.pop(-1)
                replace_node.branches[branch_idx] = Node(char_idx, indexes=[last_idx])
                SuffixTree.remainder -= 1
                if prev_parent:
                    prev_parent.suffix_link = replace_node

                print("split")
                print(replace_node.get_labels())
                print(self.get_labels())
                print(replace_node.branches[branch_idx].get_labels())
                print("----")
                # bug. active_len became 3 instead of 1

                SuffixTree.clear_remainder(replace_node, char_idx)
                return

        edge_node = self.branches[branch_idx]
        if edge_node:
            # Rule 3: char exists. Do nothing. Update active point
            if self.indexes:
                edge_node.indexes.append(self.indexes[-1])
            else:
                # self is root node
                edge_node.indexes.append(char_idx)

            # update active point
            SuffixTree.active_point = (self, edge_node, 1)
            return

        else:
            # Rules 2. char not found. create new node. Clear remainder stack, if any.
            indexes = [self.indexes[-1] if self.indexes else char_idx]
            self.branches[branch_idx] = Node(char_idx, indexes=indexes)
            self.end = char_idx if self.end is None else self.end
            SuffixTree.remainder -= 1
            if prev_parent and self.indexes:  # root have empty indexes
                prev_parent.suffix_link = self

            SuffixTree.clear_remainder(self, char_idx)
            return

    # =================== helper functions ===================
    def match(self, substring, idx):
        idx = idx
        for i in range(self.start, self.get_end()):
            if SuffixTree.text[i] != substring[idx]:
                # failed match. return empty list
                return []

            idx += 1
            if idx >= len(substring):
                return self.indexes

        branch_idx = max(ord(substring[idx]) - 97, -1)
        edge_node = self.branches[branch_idx]
        if edge_node:
            # char exists. continue matching
            return edge_node.match(substring, idx)
        else:
            return []

    def seek_n_extend(self, char_idx, first_idx, seek_len, prev_parent):
        if self.end is None or self.start + seek_len < self.end:
            # print("extend1")
            self.extend(char_idx, seek_len, prev_parent)
            return

        edge_len = self.end - self.start
        branch_idx = max(ord(SuffixTree.text[first_idx + edge_len]) - 97, -1)
        edge_node = self.branches[branch_idx]

        if not edge_node:
            # print("extend2")
            self.extend(char_idx, seek_len, prev_parent)
            return

        # print("splt_extend")
        edge_node.indexes.append(first_idx)
        seek_len_ = seek_len
        SuffixTree.active_point = (self, edge_node, seek_len_)
        return edge_node.seek_n_extend(
            char_idx, first_idx + edge_len, seek_len_, prev_parent
        )


class SuffixTree:
    def __init__(self, text):
        SuffixTree.instance = self
        SuffixTree.END = 0
        SuffixTree.root = Node()
        SuffixTree.text = text + "$"
        SuffixTree.active_point = (self.root, None, 0)  # node, edge (node), length
        SuffixTree.remainder = 0

        self.build_tree()

    def __repr__(self):
        return repr(self.root)

    def build_tree(self):
        # Ukkonen extension rules for building `new_path + new_char`
        # Rule 1: If new_path ends on a leaf node, new_char is simply appended to node label.
        # Rule 2: If new_path ends on (or in-between) a non-leaf node and new_char does not match existing edges, a new node with label 'new_char' is created ?with number j?
        # Rule 3: If new_path ends on (or in-between) a non-leaf node and new_char match existing edges, do nothing.
        text = SuffixTree.text

        for i in range(len(text)):
            SuffixTree.remainder += 1
            curr_node, edge_node, length = self.active_point
            edge_node.extend(i, length) if edge_node else curr_node.extend(i)
            SuffixTree.END += 1

            # print(self)
            # print(SuffixTree.remainder)
            # input("==== give input====\n\n")

    @classmethod
    def clear_remainder(cls, prev_parent, char_idx):
        # print(cls.instance)
        # print(SuffixTree.remainder)
        # input("==== give input2====\n\n")

        # reset active_point
        cls.active_point = (cls.root, None, 0)

        if SuffixTree.remainder > 0:
            cls.root.seek_n_extend(
                char_idx,
                char_idx - SuffixTree.remainder + 1,
                SuffixTree.remainder - 1,
                prev_parent,
            )

    def match_substring(self, substring):
        return self.root.match(substring, 0)


if __name__ == "__main__":
    # text = "banana"
    text = "lingmindraboofooowingdingbarrwingmonkeypoundcake"
    st = SuffixTree(text)
    print(st)

    # print(st.match_substring("fooo"))
    # print(st.match_substring("barr"))
    # print(st.match_substring("wing"))
    # print(st.match_substring("ding"))
