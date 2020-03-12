import cv2
from tools import ImageTools


def run():
    # grab the reference to the web cam
    vs = cv2.VideoCapture(0)
    # keep looping
    frames = []
    while True:
        # grab the current frame
        ret, frame = vs.read()
        # if we are viewing a video and we did not grab a frame,
        # then we have reached the end of the video
        if frame is None:
            break
        cv2.imshow("Video", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("c"):
            frames.append(frame)
        elif key == ord("s"):
            if len(frames) > 0:
                ImageTools.run_save_image_object_to_ftp(frames)
            else:
                pass
        elif key == ord("a"):
            frames.clear()
    # close all windows
    cv2.destroyAllWindows()
