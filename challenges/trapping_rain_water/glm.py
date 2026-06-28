def trap(height: list[int]) -> int:
    """
    Calculate trapped rain water using a stack-based approach.

    The algorithm uses a stack to keep track of indices of bars in increasing order.
    When we encounter a bar that is lower than the bar at the top of the stack,
    we pop the stack and calculate water trapped at that position.

    The key insight:
    - For any position i, water trapped depends on the nearest higher bar to the left and right
    - The stack helps us efficiently find these boundaries by maintaining a monotonic increasing sequence

    Time Complexity: O(n)
    Space Complexity: O(n)
    """
    stack = []  # Store indices of bars in increasing order of height
    water = 0

    for current_index, current_height in enumerate(height):
        # Process while current bar is higher than bar at stack top
        while stack and current_height > height[stack[-1]]:
            top_index = stack.pop()  # Pop the bar that will be the "water level"

            if not stack:  # No left boundary found
                break

            # Calculate distance between current index and the new top
            distance = current_index - stack[-1] - 1

            # Calculate the height of water that can be trapped
            bounded_height = min(current_height, height[stack[-1]]) - height[top_index]

            water += distance * bounded_height

        stack.append(current_index)

    return water