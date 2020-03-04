using System.Collections;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Threading;
using UnityEngine;
using System;

public abstract class NmsSocketTransmitter : MonoBehaviour {

    public int port;
    public string host;

    protected volatile bool isConnected;
    protected volatile bool isOpened;

    // Fields for message handling
    private List<NmsProtocolHandler.NmsMessage> messages;
    private Mutex msgLock;

    protected abstract void initialization();
    protected abstract void cleanUp(bool onClose=true);

    protected abstract bool connect();
    public abstract bool sendMessage(NmsProtocolHandler.NmsMessage msg);

    public void appendMessage(NmsProtocolHandler.NmsMessage msg)
    {
        this.msgLock.WaitOne();
        this.messages.Add(msg);
        this.msgLock.ReleaseMutex();
    }

    public void pushMessage(NmsProtocolHandler.NmsMessage msg)
    {
        this.msgLock.WaitOne();
        this.messages.Insert(0, msg);
        this.msgLock.ReleaseMutex();
    }

    // Use this for initialization
    protected void Start () {
        this.messages = new List<NmsProtocolHandler.NmsMessage>();
        this.msgLock = new Mutex();
        this.isConnected = false;
        this.isOpened = true;
        this.initialization();
	}
	
	// Update is called once per frame
	protected void Update() {
        if(!this.isConnected && this.isOpened)
        {
            this.isConnected = this.connect();
        }
        if(this.isConnected)
        {
            NmsProtocolHandler.NmsMessage msg;
            if((msg = this.getNextMessage()) != null)
            {
                if(msg.Message != "")
                {
                    if(!this.sendMessage(msg))
                    {
                        pushMessage(msg);
                    }
                }
            }
        }
    }

    protected NmsProtocolHandler.NmsMessage getNextMessage()
    {
        NmsProtocolHandler.NmsMessage msg = null;
        if(messages.Count > 0)
        {
            this.msgLock.WaitOne();
            msg = this.messages[0];
            this.messages.RemoveAt(0);
            this.msgLock.ReleaseMutex();
        }
        
        return msg;
    }

    protected void OnDestroy()
    {
        this.isOpened = false;
        this.isConnected = false;
        this.cleanUp();
    }

}
