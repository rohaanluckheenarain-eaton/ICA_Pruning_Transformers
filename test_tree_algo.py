import networkx as nx
import matplotlib.pyplot as plt


class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []
        self.parent = None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)
        
        
def visualize_tree(root):
    """Visualizes the tree using networkx."""
    graph = nx.DiGraph()
    
    def add_edges(node):
        for child in node.children:
            graph.add_edge(node.value, child.value)
            add_edges(child)
    
    add_edges(root)

    #plt.figure(figsize=(8, 5))
    pos = nx.spring_layout(graph)  # Layout for visualization
    nx.draw(graph, pos, with_labels=True, node_color="lightblue", edge_color="gray", node_size=2500, font_size=12)
    plt.show()


def find_matched_nodes(node):
    """Finds direct children, cousins, and recursively moves up to add parent cousins."""
    matched_set = set()

    # Step 1: Add direct children
    matched_set.update(node.children)

    # Step 2: Initialize traversal upwards
    current_node = node
    while current_node.parent:
        parent = current_node.parent

        # Step 3: Add cousins at the same level (siblings of current node)
        for sibling in parent.children:
            if sibling != current_node:
                matched_set.add(sibling)

        # Step 4: Move up and add parent's cousins (siblings of parent)
        if parent.parent:
            for uncle in parent.parent.children:
                if uncle != parent:
                    matched_set.add(uncle)

        # Move up the tree
        current_node = parent

    return {n.value for n in matched_set}


# Example Usage
if __name__ == "__main__":
    # Constructing the Tree
    A = TreeNode("A")
    B = TreeNode("B")
    C = TreeNode("C")
    D = TreeNode("D")
    E = TreeNode("E")
    F = TreeNode("F")
    G = TreeNode("G")
    H = TreeNode("H")
    I = TreeNode("I")
    J = TreeNode("J")
    K = TreeNode("K")

    A.add_child(B)
    A.add_child(C)
    B.add_child(D)
    B.add_child(E)
    C.add_child(F)
    C.add_child(G)
    D.add_child(H)
    D.add_child(I)
    G.add_child(J)
    G.add_child(K)

    
    for node in [A, B, C, D, E, F, G, H, I, J, K]:
        print(f"Node {node.value} has matched nodes: {find_matched_nodes(node)}")

    
    
    
