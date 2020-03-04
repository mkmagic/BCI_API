using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class HandlerObserver : MessageHandler
{
    public Observe observer;

    public ObservedHandler handler;

    public override void Proccess(NmsProtocolHandler.NmsMessage message)
    {
        string[] msg = message.Message.Split('#');
        if(msg.Length == 2 || msg.Length==3)
        {
            string description = message.Message;
            if(msg.Length == 2)
            {
                description += "#0";
            }
            handler.Proccess(observer.observe(extractFocus(description)));
        }
    }

    Vector3 extractFocus(string message)
    {
        Vector3 focus = new Vector3();
        string[] msg = message.Split('#');
        if(msg.Length == 3)
        {
            focus.x = float.Parse(msg[0]);
            focus.y = float.Parse(msg[1]);
        }
        return focus;
    }
}
