package tree_diff;

import eu.mihosoft.ext.apted.node.Node;
import eu.mihosoft.ext.apted.parser.*;

import java.io.StringReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

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
        HashMap<Integer, Node<NodeData>> indexToNodeMapping= new HashMap<>();
        HashMap<Integer, List<Integer>> parentToChildrenMapping = new HashMap<>();
        NodeData newNodeData = null;
        NodeData root = null;
        if (inputNode.keySet().contains("length")) {
            int length = inputNode.getInt("length");
            for(int i = 0; i < length; i++) {
                JSONObject currentObject = inputNode.getJSONObject(Integer.toString(i));
                newNodeData = new NodeData(currentObject.getInt("size"), currentObject.getString("type"));
                indexToNodeMapping.put(i, new Node<NodeData>(newNodeData));
                if (!parentToChildrenMapping.keySet().contains(i)) {
                    parentToChildrenMapping.put(i, new ArrayList<>());
                }
                for(Object child : currentObject.getJSONArray("children")) {
                    parentToChildrenMapping.get(i).add((int)child);
                }
            }

            for(int key : parentToChildrenMapping.keySet()) {
                for(int child : parentToChildrenMapping.get(key)) {
                    indexToNodeMapping.get(key).addChild(indexToNodeMapping.get(child));
                }
            }
            return indexToNodeMapping.get(0);
        } else {
            return null;
        }
    }
}
