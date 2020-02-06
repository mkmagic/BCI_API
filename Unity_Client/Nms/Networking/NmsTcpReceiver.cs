using System.Collections;
using System.Collections.Generic;
using System.Net.Sockets;
using System.IO;
using System.Text;
using System.Threading;
using UnityEngine;
using System;

public class NmsTcpReceiver : NmsSocketReceiver {


    private TcpClient client;

    private Thread thread;

    private void Read()
    {
        try
        {
            using (NetworkStream stream = client.GetStream())
            {
                do
                {
                    if(stream.CanRead && stream.DataAvailable)
                    {
                        byte[] data = new byte[1024];
                        int bytesRead = 0;
                        using (MemoryStream ms = new MemoryStream())
                        {
                            int numBytesRead;
                            do
                            {
                                numBytesRead = 0;
                                if(stream.CanRead && stream.DataAvailable)
                                {
                                    numBytesRead = stream.Read(data, 0, data.Length);
                                    if(numBytesRead > 0)
                                    {
                                        bytesRead += numBytesRead;
                                        ms.Write(data, 0, numBytesRead);
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
                } while (isConnected && isOpened);
            }
        }
        catch(Exception e)
        {
            print(e.ToString());
            cleanUp(false);
        }
    }

    protected override bool connectAndListen()
    {
        if(client == null)
        {
            client = NmsProtocolHandler.signUp(host, port);
            if(client != null) 
            { 
                thread = new Thread(Read);
                thread.Start();
                return true;
            }
        }
        return false;
    }

    protected override void cleanUp(bool onClose=true)
    {
        isConnected = false;
        if(thread != null && onClose)
        {
            thread.Join();
        }
        NmsProtocolHandler.closeTcpClient(client);
    }

    protected override void initialization() { }
}
