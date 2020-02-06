using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public abstract class MessageHandler : MonoBehaviour
{
    public abstract void Proccess(NmsProtocolHandler.NmsMessage message);
}

