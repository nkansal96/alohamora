package tree_diff;

import eu.mihosoft.ext.apted.node.Node;
import eu.mihosoft.ext.apted.parser.*;

import java.io.StringReader;
import org.json.*;

public class InputParser implements eu.mihosoft.ext.apted.parser.InputParser<NodeData> {
    /**
     * Converts the input tree passed as string (as a JSON)
     * into the tree structure.
     *
     * @param s input tree as JSON.
     * @return tree structure.
     */
    @Override
    public Node<NodeData> fromString(String s) {
        JSONObject inputNode = new JSONObject(s);
        NodeData newNodeData = null;
        NodeData root = null;
        if (inputNode.keySet().contains("length")) {
            int length = inputNode.getInt("length");
            for(int i = 0; i < length; i++) {
                JSONObject currentObject = inputNode.getJSONObject(Integer.toString(i));
                newNodeData = new NodeData(currentObject.getInt("size"), currentObject.getString("type"));
            }
            if (root == null) {
                root = newNodeData;
            }
        }

        return new Node<NodeData>(root);
    }
}
