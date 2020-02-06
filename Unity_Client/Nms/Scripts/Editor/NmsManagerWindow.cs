using UnityEngine;
using UnityEditor;

public enum Protocol
{
	TCP,
	UDP
}

public class NsmManagerWindow : EditorWindow
{
	int tab = 0;
	Tab createTab = new TabCreate();

	[MenuItem("Window/NMS Manager")]
	public static void ShowWindow()
	{
		EditorWindow.GetWindow<NsmManagerWindow>();
		
	}

	void OnGUI()
	{
		tab = GUILayout.Toolbar (tab, new string[] {"Create NMS Object"});
		switch (tab) 
		{
			case 0:
				createTab.buildTab();
				break;
		}
	}

	abstract class Tab
	{
		public abstract void buildTab();
	}

	private class TabCreate : Tab
	{
		int objectTab;
		Tab createReceiver;
		Tab createTransmitter;
		Tab createObserver;

		public TabCreate()
		{
			createReceiver = new TabCreateReceiver();
			createTransmitter = new TabCreateTransmitter();
			createObserver = new TabCreateObserver();
		}

		public override void buildTab()
		{
			objectTab = GUILayout.Toolbar (objectTab, new string[] {"Receiver", "Transmitter", "Observer"});
			switch(objectTab)
			{
				case 0:
					createReceiver.buildTab();
					break;
				case 1:
					createTransmitter.buildTab();
					break;
				case 2:
					createObserver.buildTab();
					break;
			}
		}
	}

	private class TabCreateReceiver : Tab
	{
		Protocol protocol;
		string serverHost;
		int portIn;

		MessageHandler messageHandler;

		public TabCreateReceiver()
		{
			protocol = Protocol.TCP;
			serverHost = "";
			portIn = 0;
			messageHandler = null;
		}

		public override void buildTab()
		{
			messageHandler = (MessageHandler)EditorGUILayout.ObjectField("Message Handler:", messageHandler, typeof(MessageHandler), true);
			protocol = (Protocol)EditorGUILayout.EnumPopup("Network Protocol:", protocol);
			serverHost = EditorGUILayout.TextField("Server Host Address:", serverHost);
			portIn = EditorGUILayout.IntField("Receive Port [IN]:", portIn);

			if(GUILayout.Button("Create"))
			{
				foreach (GameObject obj in Selection.gameObjects)
				{
					GameObject prefab = null;
					switch(protocol)
					{
						case Protocol.TCP:
							prefab = Resources.Load("Nms/Base/NmsTcpReceiver") as GameObject;
							break;
						case Protocol.UDP:
							prefab = Resources.Load("Nms/Base/NmsUdpReceiver") as GameObject;
							break;
					}
					GameObject created = GameObject.Instantiate(prefab, obj.transform.position, obj.transform.rotation, obj.transform);
					created.name = "NmsReceiver";

					NmsSocketReceiver receiver = created.GetComponent<NmsSocketReceiver>();
					receiver.host = serverHost;
					receiver.port = portIn;
					receiver.processor = messageHandler;
				}
			}
		}
	}

	private class TabCreateTransmitter : Tab
	{
		Protocol protocol;
		string serverHost;
		int portIn;

		public TabCreateTransmitter()
		{
			protocol = Protocol.TCP;
			serverHost = "";
			portIn = 0;
		}

		public override void buildTab()
		{
			protocol = (Protocol)EditorGUILayout.EnumPopup("Network Protocol:", protocol);
			serverHost = EditorGUILayout.TextField("Server Host Address:", serverHost);
			portIn = EditorGUILayout.IntField("Transmission Port [OUT]:", portIn);

			if(GUILayout.Button("Create"))
			{
				foreach (GameObject obj in Selection.gameObjects)
				{
					GameObject prefab = null;
					switch(protocol)
					{
						case Protocol.TCP:
							prefab = Resources.Load("Nms/Base/NmsTcpTransmitter") as GameObject;
							break;
						case Protocol.UDP:
							prefab = Resources.Load("Nms/Base/NmsUdpTransmitter") as GameObject;
							break;
					}
					GameObject created = GameObject.Instantiate(prefab, obj.transform.position, obj.transform.rotation, obj.transform);
					created.name = "NmsTransmitter";

					NmsSocketTransmitter transmitter = created.GetComponent<NmsSocketTransmitter>();
					transmitter.host = serverHost;
					transmitter.port = portIn;
				}
			}
		}
	}

	private class TabCreateObserver : Tab
	{
		string tagToObserve;
		bool transmiteChangesOnly;
		string serverHost;
		int eyeFocusPortIn;
		int observedObejctsPortOut;

		public TabCreateObserver()
		{
			tagToObserve = "";
			transmiteChangesOnly = true;
			serverHost = "";
			eyeFocusPortIn = 0;
			observedObejctsPortOut = 0;
		}

		public override void buildTab()
		{
			EditorGUIUtility.labelWidth = 200;
			tagToObserve = EditorGUILayout.TextField("Tag To Observe:", tagToObserve);
			transmiteChangesOnly = EditorGUILayout.Toggle("Transmite Changes Only", transmiteChangesOnly);
			serverHost = EditorGUILayout.TextField("Server Host Address:", serverHost);
			eyeFocusPortIn = EditorGUILayout.IntField("Eye Focus Port [IN]:", eyeFocusPortIn);
			observedObejctsPortOut = EditorGUILayout.IntField("Observed Objects Port [OUT]:", observedObejctsPortOut);

			if(GUILayout.Button("Create"))
			{
				foreach (GameObject obj in Selection.gameObjects)
				{
					var prefab = Resources.Load("Nms/Observer/NmsObserver") as GameObject;
					GameObject created = GameObject.Instantiate(prefab, obj.transform.position, obj.transform.rotation, obj.transform);
					created.name = "NmsObserver	";

					NmsSocketReceiver receiver = created.GetComponentInChildren<NmsSocketReceiver>();
					receiver.host = serverHost;
					receiver.port = eyeFocusPortIn;

					NmsSocketTransmitter transmitter = created.GetComponentInChildren<NmsSocketTransmitter>();
					transmitter.host = serverHost;
					transmitter.port = observedObejctsPortOut;

					Observe observer = created.GetComponentInChildren<Observe>();
					observer.tagToObserve = tagToObserve;
					observer.ChangesOnly = transmiteChangesOnly;
				}
			}
		}
	}
}
