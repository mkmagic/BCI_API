using System.Collections;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Threading;
using UnityEngine;
using System.Net;
using System;

public class NmsTcpTransmitter : NmsSocketTransmitter {


    private TcpClient client;
    private NetworkStream stream;

    protected override bool connect()
    {
        if(client == null)
        {
            client = NmsProtocolHandler.signUp(host, port);
            if(client != null) 
            { 
                stream = client.GetStream(); 
                return true;
            }
        }
        return false;
    }

    protected override void cleanUp(bool onClose=true)
    {
        if(stream != null)
        {
            stream.Close();
        }
        NmsProtocolHandler.closeTcpClient(client);
    }

    public override bool sendMessage(NmsProtocolHandler.NmsMessage msg)
    {
        try
        {
            print("sending: " + msg.Message);
            stream.Write(msg.Data, 0, msg.Data.Length);
        }
        catch(SocketException e)
        {
            print(e.Message);
            return false;
        }
        return true;
    }

    protected override void initialization() { }
}
