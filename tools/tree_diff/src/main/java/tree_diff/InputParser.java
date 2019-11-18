package tree_diff;

import eu.mihosoft.ext.apted.node.Node;
import eu.mihosoft.ext.apted.parser.*;

import java.io.StringReader;
import org.json.*;

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
        JSONObject inputNode = new JSONObject(s);
        for (String key : inputNode.keySet()) {
            System.out.println("Key is " + key);
        }
        System.out.println("Parsed string " + s);
        System.out.println("Input json is " + inputNode.toString());
        return null;
    }
}
