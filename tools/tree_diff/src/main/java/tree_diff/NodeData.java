package tree_diff;

public class NodeData {
    private double size;
    private String type;
    private int id;

    public NodeData() {
        this.size = -1;
        this.type = "none";
    }

    public NodeData(int id, double size, String type) {
        this.id = id;
        this.size = size;
        this.type = type;
    }

    public int getId() {
        return id;
    }

    public double getSize() {
        return size;
    }

    public void setId(int id) {
        this.id = id;
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
        return "id: " + this.id + ", type: " + this.type + ", size: " + this.size;
    }

}
