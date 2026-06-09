import cv2
import numpy as np

# הנקודות כפי שנמדדו מענן הנקודות של ה-ZED (במטרים)
points_in_camera = np.array([ [x1,y1,z1], [x2,y2,z2], ... ], dtype=np.float32)

# הנקודות כפי שנקראו מהרובוט (במטרים)
points_in_robot = np.array([ [x1,y1,z1], [x2,y2,z2], ... ], dtype=np.float32)

# חישוב המטריצה התלת-ממדית (מחזיר מטריצה של 3x4 וקטור אינדיקציה ל-Inliers)
retval, affine_matrix, inliers = cv2.estimateAffine3D(points_in_camera, points_in_robot)

# נהפוך אותה למטריצה ריבועית של 4x4 (מטריצה הומוגנית סטנדרטית) לנוחות עבודה
transformation_matrix = np.vstack([affine_matrix, [0, 0, 0, 1]])

# שמירה לקובץ - זה הקובץ הקבוע שלך!
np.save("zed_to_robot_matrix.npy", transformation_matrix)