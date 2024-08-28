package eric.oss.pm.genstats.updator;


import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

/**
 *
 * @author postgresqltutorial.com
 */
public class App{


    /**
     * Connect to the PostgreSQL database
     *
     * @return a Connection object
     */
    public Connection connect(String arg[]) {
        Connection conn = null;
        try {
            conn = DriverManager.getConnection(arg[0], arg[1], arg[2]);
            System.out.println("Connected to the PostgreSQL server successfully.");
        } catch (SQLException e) {
            System.out.println(e.getMessage());
            e.printStackTrace();        }

        return conn;
    }

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) {
        App app = new App();
        app.connect(args);
    }
}

