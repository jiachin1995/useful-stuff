class Node():
    def __init__(self, start=0, end=None, indexes=[], branches=None):
        self.branches = branches if branches else [None] * 27 # lowercase letters + '$' only

        # labels start & end idx
        self.start = start
        self.end = end

        # source text matching indexes
        self.indexes=indexes
        self.suffix_link = None

    def custom_repr(self, depth=0):
        labels = SuffixTree.text[self.start:self.get_end()]
        # labels += str(self.start) + str(self.end)
        myrepr =  f"{labels=}, indexes={self.indexes}, suffix={self.suffix_link.indexes if self.suffix_link else None}"
        list_of_node_repr = [myrepr] + [node.custom_repr(depth+1) for node in self.branches if node]

        separator = "\n"
        for i in range(depth):
            separator+="-"

        return separator.join(list_of_node_repr)
    
    def __repr__(self):
        return self.custom_repr()

    def get_end(self):
        # Rule 1: Point all leaf nodes at SuffixTree.END to automatically update edges.
        return SuffixTree.END if self.end is None else self.end

    def reset_branches(self):
        self.branches = [None] * 27  # lowercase letters + '$' only

    def extend(self, char_idx, active_len=0, prev_parent=None):
        branch_idx = max(ord(SuffixTree.text[char_idx]) - 97, -1)

        if self.start+active_len < self.get_end():
            if SuffixTree.text[self.start+active_len] == SuffixTree.text[char_idx]:
                # Rule 3: char exists. Do nothing. Update active point
                node, _, _ = SuffixTree.active_point
                SuffixTree.active_point = (node, self, active_len+1)
                return
            else:
                # Rule 2: char does not exist. Split label to create 2 new nodes. Clear remainder stack, if any.
                # Extend old node
                split_idx = self.start+active_len
                old_branch_idx = max(ord(SuffixTree.text[split_idx]) - 97, -1)
                replace_node = Node(self.start, split_idx, indexes=self.indexes.copy())
                replace_node.branches[old_branch_idx] = self

                # relink from active node
                node, _, _ = SuffixTree.active_point
                old_branch_idx = max(ord(SuffixTree.text[self.start]) - 97, -1)
                node.branches[old_branch_idx] = replace_node
                
                # create new node
                last_idx = self.indexes.pop(-1)
                replace_node.branches[branch_idx] = Node(char_idx, indexes=[last_idx])
                SuffixTree.remainder -= 1
                if prev_parent:
                    prev_parent.suffix_link = replace_node

                SuffixTree.clear_remainder(replace_node, char_idx)
                return


        edge_node = self.branches[branch_idx]
        if edge_node:
            # Rule 3: char exists. Do nothing. Update active point
            edge_node.indexes.append(char_idx)

            # update active point
            node, _, _ = SuffixTree.active_point
            SuffixTree.active_point = (node, edge_node, 1)
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

class SuffixTree():
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
            SuffixTree.END +=1
            
            # print(self)
            # print(SuffixTree.remainder)
            # input("==== give input====\n\n")

    @classmethod
    def clear_remainder(cls, prev_parent, char_idx):
        if SuffixTree.remainder > 0:
            # print(cls.instance)
            # print(SuffixTree.remainder)
            # input("==== give input2====\n\n")

            # reset active_point
            cls.active_point = (cls.root, None, 0) 

            for i in range(char_idx-SuffixTree.remainder+1, char_idx+1):
                curr_node, edge_node, length = cls.active_point
                edge_node.extend(i, length, prev_parent=prev_parent) if edge_node else curr_node.extend(i, prev_parent=prev_parent)


if __name__ == "__main__":
    text = "banananana"
    st = SuffixTree(text)
    print(st)