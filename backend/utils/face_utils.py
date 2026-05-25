from scipy.spatial import distance

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def calculate_ear(eye_points):
    vertical_1 = distance.euclidean(eye_points[1], eye_points[5])
    vertical_2 = distance.euclidean(eye_points[2], eye_points[4])
    horizontal = distance.euclidean(eye_points[0], eye_points[3])
    return (vertical_1 + vertical_2) / (2.0 * horizontal)

def get_eye_points(landmarks, eye_indices, width, height):
    return [(int(landmarks[idx].x * width), int(landmarks[idx].y * height)) for idx in eye_indices]

def get_head_state(landmarks, w, h):
    nose = landmarks[1]
    chin = landmarks[152]
    left_eye = landmarks[33]
    right_eye = landmarks[263]

    nose_x, nose_y = nose.x * w, nose.y * h
    chin_y = chin.y * h
    eye_center_x = (left_eye.x + right_eye.x) / 2 * w
    eye_center_y = (left_eye.y + right_eye.y) / 2 * h

    face_height = chin_y - eye_center_y
    if face_height == 0: return "FRONT"

    pitch = (nose_y - eye_center_y) / face_height
    yaw = (nose_x - eye_center_x) / face_height

    if pitch > 0.59: return "DOWN"
    elif pitch < -0.05: return "UP"
    elif yaw > 0.27: return "RIGHT"
    elif yaw < -0.27: return "LEFT"
    return "FRONT"