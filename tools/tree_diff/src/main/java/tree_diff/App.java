/*
 * This Java source file was generated by the Gradle 'init' task.
 */

package tree_diff;

import eu.mihosoft.ext.apted.parser.*;


public class App {
    public String getGreeting() {
        return "Hello world.";
    }

    public static void main(String[] args) {
	BracketStringInputParser b = new BracketStringInputParser();
        System.out.println(new App().getGreeting());
    }
}
