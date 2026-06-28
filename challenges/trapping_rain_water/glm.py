def trap(height: list[int]) -> int:
    """
    Calculate how much water can be trapped after raining.

    This implementation uses dynamic programming approach:
    - Precompute left_max and right_max arrays
    - For each position, water trapped is determined by the minimum of the
      maximum heights to the left and right

    Time Complexity: O(n)
    Space Complexity: O(n)
    """
    n = len(height)

    # Edge cases: no water can be trapped
    if n == 0 or n == 1:
        return 0

    # Precompute left_max: maximum height seen from left to current position
    left_max = [0] * n
    left_max[0] = height[0]
    for i in range(1, n):
        left_max[i] = max(left_max[i - 1], height[i])

    # Precompute right_max: maximum height seen from right to current position
    right_max = [0] * n
    right_max[n - 1] = height[n - 1]
    for i in range(n - 2, -1, -1):
        right_max[i] = max(right_max[i + 1], height[i])

    # Calculate trapped water at each position
    water = 0
    for i in range(n):
        water += min(left_max[i], right_max[i]) - height[i]

    return water