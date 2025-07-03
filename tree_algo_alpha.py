import pandas as pd

class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []
        self.parent = None
        self.visible_nodes = set()

    def add_child(self, child_node):
        child_node.parent = self
        self.children.append(child_node)

    def compute_visibility(self):
        # Add all immediate children
        self.visible_nodes.update(child.value for child in self.children)
        
        # Traverse upward to compute visibility
        current_node = self
        while current_node.parent:
            parent = current_node.parent
            self.visible_nodes.update(child.value for child in parent.children if child != current_node)
            current_node = parent

        # Compute visibility for children
        for child in self.children:
            child.compute_visibility()

    def print_tree(self, level=0):
        print(" " * level * 4 + str(self.value))
        for child in self.children:
            child.print_tree(level + 1)

    def get_visible_nodes(self):
        return list(self.visible_nodes)


def create_sample_tree(print_tree = False):
    root = TreeNode("root")
    child1 = TreeNode("child1")
    child2 = TreeNode("child2")
    child3 = TreeNode("child3")
    child4 = TreeNode("child4")
    child5 = TreeNode("child5")

    root.add_child(child1)
    root.add_child(child2)
    child1.add_child(child3)
    child1.add_child(child4)
    child2.add_child(child5)
    
    if print_tree:
        root.print_tree()

    root.compute_visibility()
    return root


def create_complex_tree(print_tree = False):
    root = TreeNode("root")
    child1 = TreeNode("child1")
    child2 = TreeNode("child2")
    child3 = TreeNode("child3")
    child4 = TreeNode("child4")
    child5 = TreeNode("child5")
    child6 = TreeNode("child6")
    child7 = TreeNode("child7")
    child8 = TreeNode("child8")
    child9 = TreeNode("child9")
    child10 = TreeNode("child10")

    root.add_child(child1)
    root.add_child(child2)
    child1.add_child(child3)
    child1.add_child(child4)
    child2.add_child(child5)
    child2.add_child(child6)
    child3.add_child(child7)
    child4.add_child(child8)
    child5.add_child(child9)
    child6.add_child(child10)
    
    if print_tree:
        root.print_tree()

    root.compute_visibility()
    return root


def create_complex_n_tree(print_tree=False):
    root = TreeNode("child0")

    # Level 1
    n1 = TreeNode("child1")
    n2 = TreeNode("child2")
    n3 = TreeNode("child3")
    root.add_child(n1)
    root.add_child(n2)
    root.add_child(n3)

    # Level 2
    n4 = TreeNode("child4")
    n5 = TreeNode("child5")
    n6 = TreeNode("child6")
    n1.add_child(n4)
    n1.add_child(n5)
    n1.add_child(n6)

    n7 = TreeNode("child7")
    n8 = TreeNode("child8")
    n9 = TreeNode("child9")
    n2.add_child(n7)
    n2.add_child(n8)
    n2.add_child(n9)

    n10 = TreeNode("child10")
    n11 = TreeNode("child11")
    n12 = TreeNode("child12")
    n3.add_child(n10)
    n3.add_child(n11)
    n3.add_child(n12)

    # Level 3
    n13 = TreeNode("child13")
    n14 = TreeNode("child14")
    n15 = TreeNode("child15")
    n4.add_child(n13)
    n4.add_child(n14)
    n4.add_child(n15)

    n16 = TreeNode("child16")
    n17 = TreeNode("child17")
    n18 = TreeNode("child18")
    n8.add_child(n16)
    n8.add_child(n17)
    n8.add_child(n18)

    n19 = TreeNode("child19")
    n20 = TreeNode("child20")
    n21 = TreeNode("child21")
    n12.add_child(n19)
    n12.add_child(n20)
    n12.add_child(n21)

    if print_tree:
        root.print_tree()

    root.compute_visibility()
    return root


def print_visible_nodes(node):
    print(f"Node {node.value} sees: {node.get_visible_nodes()}")
    for child in node.children:
        print_visible_nodes(child)


def check_visibility(tree, expected_results):
    data = []
    nodes_to_check = []

    def collect_nodes(node):
        nodes_to_check.append(node)
        for child in node.children:
            collect_nodes(child)

    collect_nodes(tree)

    for node in nodes_to_check:
        if node.value in expected_results:
            actual = set(node.get_visible_nodes())
            expected = set(expected_results[node.value])
            match = actual == expected
            data.append([node.value, expected, actual, match])

    df = pd.DataFrame(data, columns=["Source Node", "Expected Results", "Computed Results", "Match"])
    return df




if __name__ == "__main__":
    
    
    #Bool to print tree testing algorithm on
    print_tree = True
    # Set this to either "sample" or "complex"
    tree_type = "complex_n"

    if tree_type == "sample":
        tree = create_sample_tree(print_tree)
        expected_results = {
            "root": ["child1", "child2"],
            "child1": ["child3", "child4", "child2"],
            "child2": ["child1", "child5"],
            "child3": ["child4", "child2"],
            "child4": ["child3", "child2"],
            "child5": ["child1"]
        }
    elif tree_type == "complex":
        tree = create_complex_tree(print_tree)
        expected_results = {
            "root": ["child1", "child2"],
            "child1": ["child3", "child4", "child2"],
            "child2": ["child5", "child6", "child1"],
            "child3": ["child7", "child4", "child2"],
            "child4": ["child8", "child3", "child2"],
            "child5": ["child9", "child6", "child1"],
            "child6": ["child10", "child5", "child1"],
            "child7": ["child4", "child2"],
            "child8": ["child3", "child2"],
            "child9": ["child6", "child1"],
            "child10": ["child5", "child1"]
        }
        
    elif tree_type == "complex_n":
        tree = create_complex_n_tree(print_tree)
        expected_results = {
        "child0": ["child1", "child2", "child3"],
        "child1": ["child4", "child5", "child6", "child2", "child3"],
        "child2": ["child7", "child8", "child9", "child1", "child3"],
        "child3": ["child10", "child11", "child12", "child1", "child2"],
        "child4": ["child13", "child14", "child15", "child5", "child6", "child2", "child3"],
        "child5": ["child4", "child6", "child2", "child3"],
        "child6": ["child4", "child5", "child2", "child3"],
        "child7": ["child8", "child9", "child1", "child3"],
        "child8": ["child16", "child17", "child18", "child7", "child9", "child1", "child3"],
        "child9": ["child7", "child8", "child1", "child3"],
        "child10": ["child11", "child12", "child2", "child1"],
        "child11": ["child10", "child12", "child2", "child1"],
        "child12": ["child19", "child20", "child21", "child10", "child11", "child2", "child1"],
        "child13": ["child14", "child15", "child5", "child6", "child2", "child3"],
        "child14": ["child13", "child15", "child5", "child6", "child2", "child3"],
        "child15": ["child13", "child14", "child5", "child6", "child2", "child3"],
        "child16": ["child17", "child18", "child7", "child9", "child1", "child3"],
        "child17": ["child16", "child18", "child7", "child9", "child1", "child3"],
        "child18": ["child16", "child17", "child7", "child9", "child1", "child3"],
        "child19": ["child20", "child21", "child10", "child11", "child1", "child2"],
        "child20": ["child19", "child21", "child10", "child11", "child1", "child2"],
        "child21": ["child19", "child20", "child10", "child11", "child1", "child2"]
    }


    else:
        raise ValueError("Invalid tree type. Use 'sample' or 'complex'.")

    df = check_visibility(tree, expected_results)
    print(df)
