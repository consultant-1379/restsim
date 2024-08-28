package eric.oss.pm.genstats.updator;

import java.util.Objects;


/**
 * @author xjaimah
 *
 */
public class NodeInfo {

	/**
	 * The id
	 */
	private long id;
	/**
	 * The nodeName
	 */
	private String nodeName;
	/**
	 * The nodeType
	 */
	private String nodeType;
	/**
	 * The fileLocation
	 */
	private String fileLocation;
	/**
	 * The fileCreationTimeInOss
	 */
	private String fileCreationTimeInOss;
	/**
	 * The dataType
	 */
	private String dataType;
	/**
	 * The fileType
	 */
	private String fileType;
	/**
	 * The startRopTimeInOss
	 */
	private String startRopTimeInOss;
	/**
	 * The endRopTimeInOss
	 */
	private String endRopTimeInOss;
	/**
	 * The fileSize
	 */
	private long fileSize;
	
	
	public NodeInfo() {

	}

	/**
	 * @param nodeName
	 * @param nodeType
	 * @param fileLocation
	 * @param fileCreationTimeInOss
	 * @param dataType
	 * @param fileType
	 * @param startRopTimeInOss
	 * @param endRopTimeInOss
	 * @param fileSize
	 */
	public NodeInfo(String nodeName, String nodeType, String fileLocation, String fileCreationTimeInOss,
			String dataType, String fileType, String startRopTimeInOss, String endRopTimeInOss, long fileSize) {
		this.nodeName = nodeName;
		this.nodeType = nodeType;
		this.fileLocation = fileLocation;
		this.fileCreationTimeInOss = fileCreationTimeInOss;
		this.dataType = dataType;
		this.fileType = fileType;
		this.startRopTimeInOss = startRopTimeInOss;
		this.endRopTimeInOss = endRopTimeInOss;
		this.fileSize = fileSize;
	}

	/**
	 * @return
	 */
	public long getId() {
		return id;
	}

	/**
	 * @param id
	 */
	public void setId(long id) {
		this.id = id;
	}

	/**
	 * @return
	 */
	public String getNodeName() {
		return nodeName;
	}

	/**
	 * @param nodeName
	 */
	public void setNodeName(String nodeName) {
		this.nodeName = nodeName;
	}

	/**
	 * @return
	 */
	public String getNodeType() {
		return nodeType;
	}

	/**
	 * @param nodeType
	 */
	public void setNodeType(String nodeType) {
		this.nodeType = nodeType;
	}

	/**
	 * The hashCode
	 */
	@Override
	public int hashCode() {
		return Objects.hash(this.nodeName, this.nodeType, this.fileLocation, this.startRopTimeInOss,
				this.endRopTimeInOss);
	}

	/**
	 * The equals
	 */
	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		NodeInfo other = (NodeInfo) obj;
		if (id != other.id)
			return false;
		if (fileLocation == null) {
			if (other.fileLocation != null)
				return false;
		} else if (!fileLocation.equals(other.fileLocation))
			return false;
		if (nodeName == null) {
			if (other.nodeName != null)
				return false;
		} else if (!nodeName.equals(other.nodeName))
			return false;
		if (nodeType == null) {
			if (other.nodeType != null)
				return false;
		} else if (!nodeType.equals(other.nodeType))
			return false;
		if (startRopTimeInOss == null) {
			if (other.startRopTimeInOss != null)
				return false;
		} else if (!startRopTimeInOss.equals(other.startRopTimeInOss))
			return false;
		if (endRopTimeInOss == null) {
			if (other.endRopTimeInOss != null)
				return false;
		} else if (!endRopTimeInOss.equals(other.endRopTimeInOss))
			return false;
		return true;
	}

	public String getFileLocation() {
		return fileLocation;
	}

	public void setFileLocation(String fileLocation) {
		this.fileLocation = fileLocation;
	}

	public String getFileCreationTimeInOss() {
		return fileCreationTimeInOss;
	}

	public void setFileCreationTimeInOss(String fileCreationTimeInOss) {
		this.fileCreationTimeInOss = fileCreationTimeInOss;
	}

	public String getDataType() {
		return dataType;
	}

	public void setDataType(String dataType) {
		this.dataType = dataType;
	}

	public String getFileType() {
		return fileType;
	}

	public void setFileType(String fileType) {
		this.fileType = fileType;
	}

	public String getStartRopTimeInOss() {
		return startRopTimeInOss;
	}

	public void setStartRopTimeInOss(String startRopTimeInOss) {
		this.startRopTimeInOss = startRopTimeInOss;
	}

	public String getEndRopTimeInOss() {
		return endRopTimeInOss;
	}

	public void setEndRopTimeInOss(String endRopTimeInOss) {
		this.endRopTimeInOss = endRopTimeInOss;
	}

	public long getFileSize() {
		return fileSize;
	}

	public void setFileSize(long fileSize) {
		this.fileSize = fileSize;
	}
	
	@Override
	public String toString() {
		return "NodeInfo{" + "id:" + this.id + ", nodeName:'" + this.nodeName + '\'' + ", nodeType:'" + this.nodeType
				+ '\'' + ", fileLocation:'" + this.fileLocation + '\'' + ", dataType:'" + this.dataType + '\'' + '}';
	}

}
