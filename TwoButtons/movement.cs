using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class PlayerMovement : MonoBehaviour
{
    [Header("Movement")]
    public float walkSpeed = 4f;
    public float sprintSpeed = 7f;
    public float strafeMultiplier = 0.75f;
    public float rotationSpeed = 180f;

    [Header("Jump")]
    public float jumpHeight = 1.2f;
    public float gravity = -25f;
    public float jumpCooldown = 0.5f;
    public float coyoteTime = 0.15f;
    public float jumpBufferTime = 0.15f;

    [Header("Sprint / Breath")]
    public float maxSprintTime = 3f;
    public float breathRecoveryTime = 2f;

    private CharacterController controller;
    private Animator animator;
    private Vector3 velocity;

    private float sprintTimer;
    private bool outOfBreath;

    private float jumpCooldownTimer;
    private float coyoteTimer;
    private float jumpBufferTimer;

    void Start()
    {
        controller = GetComponent<CharacterController>();
        animator = GetComponentInChildren<Animator>();
        sprintTimer = maxSprintTime;
    }

    void Update()
    {
        UpdateGroundedState();
        HandleMovement();
        HandleJumpInput();
        HandleJump();
        ApplyGravity();
        UpdateTimers();
        UpdateAnimation();
    }

    void UpdateGroundedState()
    {
        if (controller.isGrounded)
        {
            coyoteTimer = coyoteTime;

            if (velocity.y < 0f)
                velocity.y = -2f;
        }
        else
        {
            coyoteTimer -= Time.deltaTime;
        }
    }

    void HandleMovement()
    {
        float x = Input.GetAxisRaw("Horizontal"); // A / D
        float z = Input.GetAxisRaw("Vertical");   // W / S

        bool wantsToSprint = Input.GetKey(KeyCode.LeftShift);

        // Rotate with A / D
        if (x != 0f)
        {
            transform.Rotate(Vector3.up * x * rotationSpeed * Time.deltaTime);
        }

        bool isMovingForwardOrBack = Mathf.Abs(z) > 0.1f;
        bool sprinting = wantsToSprint && isMovingForwardOrBack && !outOfBreath && sprintTimer > 0f;

        float currentSpeed = sprinting ? sprintSpeed : walkSpeed;

        // Forward/back movement
        Vector3 forwardMove = transform.forward * z;

        // Left/right movement while also rotating
        Vector3 sidewaysMove = transform.right * x * strafeMultiplier;

        Vector3 moveDir = (forwardMove + sidewaysMove).normalized;

        controller.Move(moveDir * currentSpeed * Time.deltaTime);

        if (sprinting)
        {
            sprintTimer -= Time.deltaTime;
            if (sprintTimer <= 0f)
            {
                sprintTimer = 0f;
                outOfBreath = true;
            }
        }
        else
        {
            RecoverBreath();
        }
    }

    void HandleJumpInput()
    {
        if (Input.GetKeyDown(KeyCode.Space))
        {
            jumpBufferTimer = jumpBufferTime;
        }
    }

    void HandleJump()
    {
        if (jumpBufferTimer > 0f && coyoteTimer > 0f && jumpCooldownTimer <= 0f)
        {
            velocity.y = Mathf.Sqrt(jumpHeight * -2f * gravity);
            jumpCooldownTimer = jumpCooldown;
            jumpBufferTimer = 0f;
            coyoteTimer = 0f;
        }
    }

    void ApplyGravity()
    {
        velocity.y += gravity * Time.deltaTime;
        controller.Move(new Vector3(0f, velocity.y, 0f) * Time.deltaTime);
    }

    void UpdateTimers()
    {
        if (jumpCooldownTimer > 0f)
            jumpCooldownTimer -= Time.deltaTime;

        if (jumpBufferTimer > 0f)
            jumpBufferTimer -= Time.deltaTime;
    }

    void RecoverBreath()
    {
        if (sprintTimer < maxSprintTime)
        {
            sprintTimer += (maxSprintTime / breathRecoveryTime) * Time.deltaTime;

            if (sprintTimer >= maxSprintTime)
            {
                sprintTimer = maxSprintTime;
                outOfBreath = false;
            }
        }
        else
        {
            outOfBreath = false;
        }
    }

    void UpdateAnimation()
    {
        if (animator == null) return;

        float moveAmount = Mathf.Abs(Input.GetAxisRaw("Vertical")) + Mathf.Abs(Input.GetAxisRaw("Horizontal"));
        animator.speed = moveAmount > 0.1f ? 1f : 0f;
    }

    public float GetSprintPercent()
    {
        if (maxSprintTime <= 0f) return 0f;
        return sprintTimer / maxSprintTime;
    }
}
