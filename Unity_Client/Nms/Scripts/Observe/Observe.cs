using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Linq;

public class Observe : MonoBehaviour {

	public string tagToObserve;

	public bool ChangesOnly;

	private List<GameObject> alreadyObserved;

	private Vector3 lastEyePosition;
	// Use this for initialization
	void Start () {
		alreadyObserved = new List<GameObject>();
	}

	public Vector3 LastEyePosition
	{
		get {return lastEyePosition;}
	}

	public List<GameObject> observe(Vector3 position)
	{
		lastEyePosition = position;

		GameObject[] toObserve = GameObject.FindGameObjectsWithTag(tagToObserve);

		List<GameObject> currentlyObserved = getCurrentlyObserved(toObserve, position);
		
		List<GameObject> result;
		if(ChangesOnly)
		{
			result = currentlyObserved.Except(alreadyObserved).ToList();
		}
		else
		{
			result = currentlyObserved;
		}
		alreadyObserved = currentlyObserved;
		return result;
	}

	List<GameObject> getCurrentlyObserved(GameObject[] toObserve, Vector3 position)
	{
		position.y = Screen.currentResolution.height - position.y;
		Ray ray = Camera.main.ScreenPointToRay(position);
		RaycastHit[] hits = Physics.RaycastAll(ray);
		
		Debug.DrawRay(ray.origin, ray.direction*10000, Color.red);
		List<GameObject> result = new List<GameObject>();
		foreach(RaycastHit hit in hits)
		{	
			foreach(GameObject obj in toObserve)
			{
				if(hit.collider == obj.GetComponent<Collider>())
				{
					Debug.DrawRay(hit.point, hit.point + ray.direction*5, Color.green);
					result.Add(obj);
				}
			}
		}
		return result;
	}
}
