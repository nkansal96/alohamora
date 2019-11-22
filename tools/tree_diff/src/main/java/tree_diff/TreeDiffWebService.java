package tree_diff;

import com.sun.source.tree.Tree;
import eu.mihosoft.ext.apted.distance.APTED;
import eu.mihosoft.ext.apted.node.Node;
import org.json.JSONException;
import org.json.JSONObject;

import static spark.Spark.*;


public class TreeDiffWebService {
    public void parseAString() {
        System.out.println(("server should be running now"));
        InputParser parser = new InputParser();
        Node<NodeData> t1 = parser.fromString("{\"0\":{\"children\":[1,2],\"size\":100,\"type\":\"text/html\"},\"1\":{\"children\":[],\"size\":75,\"type\":\"image/jpeg\"},\"2\":{\"children\":[],\"size\":50,\"type\":\"text/css\"},\"length\":3}");
    }

    public String getDiffBetweenStrings(String treeData1, String treeData2) {
        InputParser parser = new InputParser();
        Node<NodeData> t1 = parser.fromString(treeData1);
        Node<NodeData> t2 = parser.fromString(treeData2);
        APTED<CostModel, NodeData> apted = new APTED<>(new CostModel());
        float result = apted.computeEditDistance(t1, t2);
        JSONObject jsonOutput = new JSONObject();
        jsonOutput.put("status", "success");
        jsonOutput.put("message", "none");
        jsonOutput.put("editDistance", result);
        return jsonOutput.toString();
    }

    public static void runServer(int serverPort) {
        TreeDiffWebService t = new TreeDiffWebService();
        port(serverPort);
        post("/getTreeDiff" , ((request, response) -> {
            JSONObject jsonOutput = new JSONObject();
            try {
                String incomingRequest = request.body();
                JSONObject jsonInput = new JSONObject(incomingRequest);
                JSONObject tree1 = (JSONObject)jsonInput.get("tree1");
                JSONObject tree2 = (JSONObject)jsonInput.get("tree2");
                return t.getDiffBetweenStrings(tree1.toString(), tree2.toString());
            } catch (JSONException e) {
                response.status(406);
                jsonOutput.put("status", "error");
                jsonOutput.put("editDistance", -1);
                jsonOutput.put("message", "Error: query was malformed. Please ensure it is a valid JSON.");
                return jsonOutput.toString();
            } catch (Exception e) {
                response.status(500);
                jsonOutput.put("status", "error");
                jsonOutput.put("editDistance", -1);
                jsonOutput.put("message", "Error: Unable to parse input query.");
                return jsonOutput.toString();
            }

        }));
        get("/getTreeDiff", (request, response) -> {
            JSONObject jsonOutput = new JSONObject();
            String treeData1 = request.queryMap().get("tree1").value();;
            String treeData2 = request.queryMap().get("tree2").value();;
            if (treeData1 == null || treeData2 == null) {
                response.status(406);
                jsonOutput.put("status", "error");
                jsonOutput.put("editDistance", -1);
                jsonOutput.put("message", "Error: query must include tree1 and tree2.");
                return jsonOutput.toString();
            } else {
                try {
                    return t.getDiffBetweenStrings(treeData1, treeData2);
                } catch (JSONException e) {
                    response.status(406);
                    jsonOutput.put("status", "error");
                    jsonOutput.put("editDistance", -1);
                    jsonOutput.put("message", "Error: query was malformed. Please ensure it is a valid JSON.");
                    return jsonOutput.toString();
                } catch (Exception e) {
                    response.status(500);
                    jsonOutput.put("status", "error");
                    jsonOutput.put("editDistance", -1);
                    jsonOutput.put("message", "Error: Unable to parse input query.");
                    return jsonOutput.toString();
                }

            }
        });

        post("/", (request, response) -> {
            return "Post root";
        });
    }

}
