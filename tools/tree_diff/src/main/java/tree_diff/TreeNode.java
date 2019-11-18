package tree_diff;

import eu.mihosoft.ext.apted.node.*;

class NodeDataStructure {
    private String resourceURL;
}

public class TreeNode extends Node<NodeDataStructure> {
    /**
     * Constructs a new node with the passed node data and an empty list of
     * children.
     *
     * @param nodeData instance of node data (node label).
     */
    public TreeNode(NodeDataStructure nodeData) {
        super(nodeData);
    }
}
