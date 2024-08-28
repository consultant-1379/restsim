package eric.oss.pm.genstats.updator;

import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.nio.file.Paths;

import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.ContentType;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.HttpClients;

/**
 * @author xjaimah
 *
 */
public class DataBaseUpdatorService {
	
	/**
	 * @param args
	 * @throws URISyntaxException
	 */
	public static void main(String args[]) throws URISyntaxException {
		try {
			if (args[0].trim().equalsIgnoreCase("add")) {
				dataBaseOpration(args);
			} else if (args[0].trim().equalsIgnoreCase("delete")) {
				dataBaseOpration(args);
			}else {
				dataBaseOpration(args);
			}
		} catch (Exception ex) {
			ex.printStackTrace();
		}
	}

	/**
	 * @param args
	 * @throws IOException
	 */
	public static void dataBaseOpration(String args[]) throws IOException {
		HttpClient httpclient = HttpClients.createDefault();
		String content = new String(Files.readAllBytes(Paths.get(args[1].trim())));
		StringEntity requestEntity = new StringEntity(content, ContentType.APPLICATION_JSON);
		System.out.println("http://" + args[2].trim() + ":" + args[3].trim() + "/"+args[0].trim());
		HttpPost postMethod = new HttpPost(
				"http://" + args[2].trim() + ":" + args[3].trim() + "/"+args[0].trim());
		postMethod.setEntity(requestEntity);
		httpclient.execute(postMethod);
	}
}
