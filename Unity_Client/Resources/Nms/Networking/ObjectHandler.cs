using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public abstract class ObjectHanlder : MonoBehaviour
{
    public abstract void Proccess(List<GameObject> objects);
}

