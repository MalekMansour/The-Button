using UnityEngine;

public class ThirdPersonCamera : MonoBehaviour
{
    public Transform target;

    [Header("Offset")]
    public Vector3 offset = new Vector3(0f, 3f, -6f);

    [Header("Mouse Look")]
    public float mouseSensitivity = 3f;
    public float minPitch = -30f;
    public float maxPitch = 60f;

    [Header("Follow")]
    public float followSmoothness = 12f;

    private float yaw;
    private float pitch = 15f;

    void Start()
    {
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;

        if (target != null)
        {
            yaw = target.eulerAngles.y;
        }
    }

    void LateUpdate()
    {
        if (target == null) return;

        yaw += Input.GetAxis("Mouse X") * mouseSensitivity;
        pitch -= Input.GetAxis("Mouse Y") * mouseSensitivity;
        pitch = Mathf.Clamp(pitch, minPitch, maxPitch);

        Quaternion rotation = Quaternion.Euler(pitch, yaw, 0f);
        Vector3 desiredPosition = target.position + rotation * offset;

        transform.position = Vector3.Lerp(
            transform.position,
            desiredPosition,
            followSmoothness * Time.deltaTime
        );

        transform.LookAt(target.position + Vector3.up * 1.5f);
    }
}using UnityEngine;

public class ThirdPersonCamera : MonoBehaviour
{
    public Transform target;

    [Header("Offset")]
    public Vector3 offset = new Vector3(0f, 3f, -6f);

    [Header("Mouse Look")]
    public float mouseSensitivity = 3f;
    public float minPitch = -30f;
    public float maxPitch = 60f;

    [Header("Follow")]
    public float followSmoothness = 12f;

    private float yaw;
    private float pitch = 15f;

    void Start()
    {
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;

        if (target != null)
        {
            yaw = target.eulerAngles.y;
        }
    }

    void LateUpdate()
    {
        if (target == null) return;

        yaw += Input.GetAxis("Mouse X") * mouseSensitivity;
        pitch -= Input.GetAxis("Mouse Y") * mouseSensitivity;
        pitch = Mathf.Clamp(pitch, minPitch, maxPitch);

        Quaternion rotation = Quaternion.Euler(pitch, yaw, 0f);
        Vector3 desiredPosition = target.position + rotation * offset;

        transform.position = Vector3.Lerp(
            transform.position,
            desiredPosition,
            followSmoothness * Time.deltaTime
        );

        transform.LookAt(target.position + Vector3.up * 1.5f);
    }
}
