package tree_diff;

import eu.mihosoft.ext.apted.node.Node;
import eu.mihosoft.ext.apted.parser.*;

public class InputParser implements eu.mihosoft.ext.apted.parser.InputParser<NodeData> {
    /**
     * Converts the input tree passed as string (e.g., bracket notation, XML)
     * into the tree structure.
     *
     * @param s input tree as string.
     * @return tree structure.
     */
    @Override
    public Node<NodeData> fromString(String s) {
        return null;
    }
}
