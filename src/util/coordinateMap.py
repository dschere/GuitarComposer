""" 
Generic object used to solve the problem of mapping a mouse coordinate to
a set graphic images (frets and strings) or a note on staff etc.
"""
import bisect


def find_nearest_match(arr, target):
    """Finds the nearest match to the target in a sorted array."""

    # Find the insertion point for the target
    idx = bisect.bisect_left(arr, target)

    # Check if the target is in the array
    if idx < len(arr) and arr[idx] == target:
        return arr[idx]

    # If target is less than the first element, return the first element
    if idx == 0:
        return arr[0]

    # If target is greater than the last element, return the last element
    if idx == len(arr):
        return arr[-1]

    # Otherwise, return the closest of the two neighboring elements
    return min(arr[idx - 1], arr[idx], key=lambda x: abs(x - target))


class CoordinateMap:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.bottom = bottom
        self.right = right

        self.data = {}
        self.x = []
        self.y = []

    def add(self, x, y, obj):
        self.data[(x, y)] = obj
        self.x.append(x)
        self.y.append(y)
        self.x.sort()
        self.y.sort()

    def match(self, x, y):
        if x >= self.left and x <= self.right:
            if y >= self.top and y < self.bottom:
                nearest_x = find_nearest_match(self.x, x)
                nearest_y = find_nearest_match(self.y, y)
                return self.data.get((nearest_x, nearest_y))


if __name__ == '__main__':
    cm = CoordinateMap(0, 0, 100, 100)
    cm.add(10, 10, "a")
    cm.add(15, 10, "b")
    cm.add(20, 10, "c")
    cm.add(10, 20, "d")
    cm.add(15, 20, "e")
    cm.add(20, 20, "f")

    import sys
    for y in range(10, 21):
        for x in range(10, 21):
            sys.stdout.write("%s " % cm.match(x, y))
        print("")
