using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ObservedHandler : ObjectHanlder {
    public NmsSocketTransmitter sender;
    public override void Proccess(List<GameObject> objects)
    {
        int count = 0;
        string reply = "Observed";
        foreach(GameObject observed in objects)
        {
            count++;
            reply += '#' + observed.name;
        }
        if(count > 0)
        {
            sender.appendMessage(new NmsProtocolHandler.NmsMessage(reply));
        }
    }

    // Use this for initialization
    void Start () {
		
	}
	
	// Update is called once per frame
	void Update () {
		
	}
}
