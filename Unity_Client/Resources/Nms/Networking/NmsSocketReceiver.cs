using System.Collections;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Threading;
using UnityEngine;
using System;

public abstract class NmsSocketReceiver : MonoBehaviour {

    public int port;
    public string host;

    protected volatile bool isConnected;
    protected volatile bool isOpened;

    // Fields for message handling
    private List<NmsProtocolHandler.NmsMessage> messages;
    public MessageHandler processor;
    private Mutex msgLock;

    protected abstract void initialization();
    protected abstract void cleanUp(bool onClose=true);
    protected abstract bool connectAndListen();

    protected void appendMessage(NmsProtocolHandler.NmsMessage msg)
    {
        print(port + " : " + msg.Message);
        this.msgLock.WaitOne();
        this.messages.Add(msg);
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
            this.isConnected = this.connectAndListen();
        }
        if(messages.Count > 0)
        {
            this.msgLock.WaitOne();
            try
            {
                this.processor.Proccess(messages[0]);
                this.messages.RemoveAt(0);
            }
            catch(Exception e)
            {
                Debug.Log(e);
            }
            this.msgLock.ReleaseMutex();
        }
    }

    protected void OnDestroy()
    {
        this.isOpened = false;
        this.isConnected = false;
        this.cleanUp();
    }

}
