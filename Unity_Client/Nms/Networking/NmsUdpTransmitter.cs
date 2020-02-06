using System.Collections;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Threading;
using UnityEngine;
using System.Net;
using System;

public class NmsUdpTransmitter : NmsSocketTransmitter {

	private UdpClient client;
    private TcpClient welcomeClient;
    public override bool sendMessage(NmsProtocolHandler.NmsMessage msg)
    {
        try
        {
            client.Send(msg.Data, msg.Data.Length, host, port);
        }
        catch(SocketException e)
        {
            print(e.Message);
            return false;
        }
        return true;
    }

    protected override void cleanUp(bool onClose=true)
    {
		isConnected = false;
        NmsProtocolHandler.closeTcpClient(welcomeClient);
        NmsProtocolHandler.closeUdpClient(client);
    }

    protected override bool connect()
    {
        if(client == null)
        {
            welcomeClient = NmsProtocolHandler.signUp(host, port);
            if(welcomeClient != null)
            {
                client = new UdpClient();
                return true;
            }
        }
        return false;
    }

    protected override void initialization() { }
}
