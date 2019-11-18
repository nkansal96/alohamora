package tree_diff;

import eu.mihosoft.ext.apted.costmodel.*;
import eu.mihosoft.ext.apted.node.*;

public class CostModel implements eu.mihosoft.ext.apted.costmodel.CostModel {

    /**
     * Calculates the cost of deleting a node.
     *
     * @param n the node considered to be deleted.
     * @return the cost of deleting node n.
     */
    @Override
    public float del(Node n) {
        return 0;
    }

    /**
     * Calculates the cost of inserting a node.
     *
     * @param n the node considered to be inserted.
     * @return the cost of inserting node n.
     */
    @Override
    public float ins(Node n) {
        return 0;
    }

    /**
     * Calculates the cost of renaming (mapping) two nodes.
     *
     * @param n1 the source node of rename.
     * @param n2 the destination node of rename.
     * @return the cost of renaming (mapping) node n1 to n2.
     */
    @Override
    public float ren(Node n1, Node n2) {
        return 0;
    }
}
