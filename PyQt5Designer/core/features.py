"""
Hand-landmark feature extraction for the sign-language classifier.

Extracts exactly 84 features from a single hand's landmarks:
  42  normalized x/y coordinates
  21  normalized z coordinates
   5  fingertip-to-wrist distances
   4  angles between adjacent fingers (arctan2)
   4  distances between adjacent fingertips (2-D)
   8  finger curvature angles (2 per non-thumb finger)
"""

import numpy as np

import config

_FINGERTIPS = config.FINGERTIP_INDICES  # [4, 8, 12, 16, 20]


def extract_features(hand_landmarks) -> list | None:
    """Return a list of 84 features from *hand_landmarks*, or ``None`` on failure."""
    lm = hand_landmarks.landmark
    xs = [p.x for p in lm]
    ys = [p.y for p in lm]
    zs = [p.z for p in lm]
    min_x, min_y, min_z = min(xs), min(ys), min(zs)

    data: list[float] = []

    # 1. Normalized x, y (42 features)
    for p in lm:
        data.append(p.x - min_x)
        data.append(p.y - min_y)

    # 2. Normalized z (21 features)
    for p in lm:
        data.append(p.z - min_z)

    # 3. Fingertip-to-wrist Euclidean distance (5 features)
    wrist = lm[config.WRIST_INDEX]
    for idx in _FINGERTIPS:
        tip = lm[idx]
        dist = ((tip.x - wrist.x) ** 2
                + (tip.y - wrist.y) ** 2
                + (tip.z - wrist.z) ** 2) ** 0.5
        data.append(dist)

    # 4. Angle between adjacent fingertips via arctan2 (4 features)
    for i in range(4):
        p1 = lm[_FINGERTIPS[i]]
        p2 = lm[_FINGERTIPS[i + 1]]
        data.append(np.arctan2(p2.y - p1.y, p2.x - p1.x))

    # 5. Distance between adjacent fingertips – 2D (4 features)
    for i in range(4):
        p1 = lm[_FINGERTIPS[i]]
        p2 = lm[_FINGERTIPS[i + 1]]
        data.append(((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) ** 0.5)

    # 6. Finger curvature (8 features – 2 per non-thumb finger)
    for i in range(4):
        base = lm[_FINGERTIPS[i] - 3]
        mid = lm[_FINGERTIPS[i] - 1]
        tip = lm[_FINGERTIPS[i]]
        data.append(np.arctan2(mid.y - base.y, mid.x - base.x))
        data.append(np.arctan2(tip.y - mid.y, tip.x - mid.x))

    if len(data) != config.NUM_FEATURES:
        return None
    return data
