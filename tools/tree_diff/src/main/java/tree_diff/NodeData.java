package tree_diff;

public class NodeData {
    private double size;
    private String type;

    public NodeData() {
        this.size = -1;
        this.type = "none";
    }

    public NodeData(double size, String type) {
        this.size = size;
        this.type = type;
    }

    public double getSize() {
        return size;
    }

    public void setSize(double size) {
        this.size = size;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    @Override
    public String toString() {
        return "type: " + this.type + ", size: " + this.size;
    }

}
