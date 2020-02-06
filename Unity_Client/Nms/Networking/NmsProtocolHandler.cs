using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.Net;
using System.Net.Sockets;
using System.IO;

public class NmsProtocolHandler {

	public static TcpClient signUp(string host, int port, int timeout=1000)
	{
		TcpClient welcomeClient = new TcpClient();
		try
		{
			welcomeClient.Connect(host, port);
			NetworkStream welcomeStream = welcomeClient.GetStream();
			NmsMessage signupMsg = new NmsMessage("id, " + port);
			welcomeStream.Write(signupMsg.Data, 0, signupMsg.Data.Length);
			byte[] replyData = new byte[welcomeClient.ReceiveBufferSize];
			int tries = 0;
			while(!welcomeStream.DataAvailable && ++tries != timeout);
			welcomeStream.ReadTimeout = timeout;
			try
			{
				welcomeStream.Read(replyData, 0, replyData.Length);
			}
			catch (IOException e)
			{
				Debug.Log(e);
				closeTcpClient(welcomeClient);
				return null;
			}
			NmsMessage replyMsg = new NmsMessage(replyData);
			Debug.Log(replyMsg.Message);
			return welcomeClient;
		}
		catch(SocketException e)
		{
			Debug.Log("Exception on connection to '" + host + " : " + port + "'");
			Debug.Log(e);
			closeTcpClient(welcomeClient);
		}

		return null;
	}

	public static void closeTcpClient(TcpClient client)
	{
		if(client != null)
		{
			if(client.Connected)
			{
				client.GetStream().Close();
			}
			client.Close();
		}
	} 

	public static void closeUdpClient(UdpClient client)
	{
		if(client != null)
		{
			client.Close();
		}
	}

	public class NmsMessage
	{
		private char sep = ';';
		private static string suffix = "$@$";
		private static string timeFormat = "yyyy-MM-dd HH:mm:ss.ffffff";

		private string msg;
		private System.DateTime time;

		public string Message
		{
			get { return msg;  }
			set { msg = value; }
		}

		public System.DateTime TimeValue
		{
			get { return time;  }
			set { time = value; }
		}

		public byte[] Data
		{
			get { return System.Text.Encoding.ASCII.GetBytes(Time + sep + Message + suffix); }
			set {
				string[] rawData = System.Text.Encoding.ASCII.GetString(value).Split(new[] {sep}, 2);
				Time = rawData[0];
				int cut = rawData[1].IndexOf(suffix);
				if (cut == -1)
				{
					Message = rawData[1];
				}
				else
				{
					Message = rawData[1].Substring(0, cut);
				}
			}
		}

		public string Time
		{
			get { return time.ToString(timeFormat);  }
			set { time = DateTime.ParseExact(value, timeFormat, System.Globalization.CultureInfo.InvariantCulture); }
		}

		public NmsMessage(string message, System.DateTime time)
		{
			TimeValue = time;
			Message = message;
		}

		public NmsMessage(string message)
		{
			TimeValue = System.DateTime.Now;
			Message = message;
		}

		public NmsMessage(byte[] data)
		{
			Data = data;
		}

		public static string Suffix { get {return suffix;}}
	}
}
