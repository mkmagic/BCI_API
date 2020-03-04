using System.Collections;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Threading;
using UnityEngine;
using System.Net;
using System.Text;
using System;
using System.IO;

public class NmsUdpReceiver : NmsSocketReceiver {

    private int dataPort;

    private UdpClient client;
    private Thread thread;

    TcpClient welcomeClient;

    protected override void cleanUp(bool onClose=true)
    {
        isConnected = false;
        if(thread != null && onClose)
        {
            thread.Join();
        }
        NmsProtocolHandler.closeTcpClient(welcomeClient);
        NmsProtocolHandler.closeUdpClient(client);
    }

    protected override bool connectAndListen()
    {
        if(client == null)
        {
            welcomeClient = NmsProtocolHandler.signUp(host, port);
            if(welcomeClient != null)
            {
                dataPort = ((IPEndPoint)welcomeClient.Client.LocalEndPoint).Port;
                client = new UdpClient(new IPEndPoint(IPAddress.Any, dataPort));
                client.Client.ReceiveTimeout = 1000;
                thread = new Thread(Read);
                thread.Start();
                return true;
            }
        }
        return false;
    }

    private void Read()
    {
        IPEndPoint remote = new IPEndPoint(IPAddress.Any, dataPort);
        try
        {
            while(isConnected)
            {
                if(client.Available > 0)
                {
                    int bytesRead = 0;
                    using (MemoryStream ms = new MemoryStream())
                    {
                        byte[] data;
                        int numBytesRead;
                        do
                        {
                            numBytesRead = 0;
                            if(client.Available > 0)
                            {
                                data = client.Receive(ref remote);
                                numBytesRead = data.Length;
                                if(numBytesRead > 0)
                                {
                                    bytesRead += data.Length;
                                    ms.Write(data, 0, data.Length);
                                }
                            }
                        }while (numBytesRead > 0);
                        String readData = Encoding.ASCII.GetString(ms.ToArray(), 0, (int)ms.Length);
                        if(bytesRead > 0)
                        {
                            foreach(String responses in readData.Split('\n'))
                            {
                                foreach(String response in responses.Split(new string[] {NmsProtocolHandler.NmsMessage.Suffix}, StringSplitOptions.None))
                                {
                                    if(response != "")
                                    {
                                        byte[] responseData = System.Text.Encoding.ASCII.GetBytes(response);
                                        appendMessage(new NmsProtocolHandler.NmsMessage(responseData));
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        catch(SocketException e)
        {
            Debug.Log(e);
            cleanUp(false);
        }
    }

    protected override void initialization()
    {

    }
}
