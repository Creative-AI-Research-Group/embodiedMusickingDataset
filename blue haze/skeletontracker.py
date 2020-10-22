import os
import platform
from cubemos.skeletontracking.core_wrapper import CM_TargetComputeDevice
from cubemos.skeletontracking.core_wrapper import initialise_logging, CM_LogLevel
from cubemos.skeletontracking.native_wrapper import Api, TrackingContext, SkeletonKeypoints
from cubemos.skeletontracking.native_wrapper import CM_SKEL_TrackingSimilarityMetric, CM_SKEL_TrackingMethod
import pyrealsense2 as rs
import numpy as np
from time import sleep


def default_log_dir():
    if platform.system() == "Windows":
        return os.path.join(os.environ["LOCALAPPDATA"], "Cubemos", "SkeletonTracking", "logs")
    elif platform.system() == "Linux":
        return os.path.join(os.environ["HOME"], ".cubemos", "skeleton_tracking", "logs")
    else:
        raise Exception("{} is not supported".format(platform.system()))


def default_license_dir():
    if platform.system() == "Windows":
        return os.path.join(os.environ["LOCALAPPDATA"], "Cubemos", "SkeletonTracking", "license")
    elif platform.system() == "Linux":
        return os.path.join(os.environ["HOME"], ".cubemos", "skeleton_tracking", "license")
    else:
        raise Exception("{} is not supported".format(platform.system()))


def check_license_and_variables_exist():
    license_path = os.path.join(default_license_dir(), "cubemos_license.json")
    if not os.path.isfile(license_path):
        raise Exception(
            "The license file has not been found at location \"" +
            default_license_dir() + "\". "
            "Please have a look at the Getting Started Guide on how to "
            "use the post-installation script to generate the license file")
    if "CUBEMOS_SKEL_SDK" not in os.environ:
        raise Exception(
            "The environment Variable \"CUBEMOS_SKEL_SDK\" is not set. "
            "Please check the troubleshooting section in the Getting "
            "Started Guide to resolve this issue." 
        )

class skeletontracker:
    def __init__(self, cloud_tracking_api_key = ""):
        check_license_and_variables_exist()

        # Get the path of the native libraries and ressource files
        sdk_path = os.environ["CUBEMOS_SKEL_SDK"]
        model_path = os.path.join(
            sdk_path, "models", "skeleton-tracking", "fp32", "skeleton-tracking.cubemos"
        )

        # Initialise the logging
        initialise_logging(sdk_path, CM_LogLevel.CM_LL_ERROR, True, os.path.join(default_log_dir(), "logs")) 

        # Initialise the api with a valid license key in default_license_dir()
        self.__api = Api(default_license_dir())

        # Load the neural network model to the CPU as the default device
        self.__api.load_model(CM_TargetComputeDevice.CM_CPU, model_path)

        # Initialise the edge tracker if the cloud tracker wasnt asked for
        if not cloud_tracking_api_key: 
            print("Initialising the Skeleton Tracking Pipeline with EDGE tracking.")
            self.__tracker = TrackingContext()
        else: 
            print("Initialising the Skeleton Tracking Pipeline with ReID based CLOUD tracking.")
            self.__tracker = TrackingContext( 
                similarity_metric = CM_SKEL_TrackingSimilarityMetric.CM_IOU,
                max_frames_id_keepalive = 25,
                tracking_method = CM_SKEL_TrackingMethod.CM_TRACKING_FULLBODY_CLOUD,
                cloud_tracking_api_key = cloud_tracking_api_key,
                min_body_percentage_visible = 0.85,
                min_keypoint_confidence = 0.7,
                num_teach_in_per_person_cloud_tracking = 6,
                force_cloud_tracking_every_x_frame = 0)

    
    def track_skeletons(self, color_image):
        # perform inference and update the tracking id
        skeletons = self.__api.estimate_keypoints(color_image, 256)
        try: 
            skeletons = self.__api.update_tracking(color_image, self.__tracker, skeletons, False)
        except Exception as ex:
            print("Exception occured while updating tracking IDs: \"{}\"".format(ex))

        return skeletons


class SkeletonReader():
    def __init__(self):
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
        print('Real Sense Depth Camera ready')

    def start(self):
        # Start the realsense pipeline
        self.pipeline = rs.pipeline()
        self.pipeline.start()

        # Create align object to align depth frames to color frames
        self.align = rs.align(rs.stream.color)

        # Get the intrinsics information for calculation of 3D point
        self.unaligned_frames = self.pipeline.wait_for_frames()
        self.frames = self.align.process(self.unaligned_frames)
        self.depth = self.frames.get_depth_frame()
        self.depth_intrinsic = self.depth.profile.as_video_stream_profile().intrinsics

        # Initialize the cubemos api with a valid license key in default_license_dir()
        self.skeletrack = skeletontracker(cloud_tracking_api_key="")
        self.joint_confidence = 0.2

    def read(self):
        # Create a pipeline object. This object configures the streaming camera and owns it's handle
        self.unaligned_frames = self.pipeline.wait_for_frames()
        self.frames = self.align.process(self.unaligned_frames)
        self.depth = self.frames.get_depth_frame()
        self.color = self.frames.get_color_frame()
        # if not self.depth or not self.color:
        #     continue

        # Convert images to numpy arrays
        depth_image = np.asanyarray(self.depth.get_data())
        color_image = np.asanyarray(self.color.get_data())

        # perform inference and update the tracking id
        self.skeletons = self.skeletrack.track_skeletons(color_image)

        return self.skeletons # removed self.depth, self.depth_intrinsic, self.joint_confidence

        # # render the skeletons on top of the acquired image and display it
        # color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        # cm.render_result(skeletons, color_image, joint_confidence)
        # render_ids_3d(
        #     color_image, skeletons, depth, depth_intrinsic, joint_confidence
        # )
        # cv2.imshow(window_name, color_image)
        # if cv2.waitKey(1) == 27:
        #     break

    def terminate(self):
        self.pipeline.stop()



if __name__ == '__main__':
    skeleton = SkeletonReader()

    skeleton.start()

    for i in range(10):
        data = skeleton.read()
        print(data)
        sleep(0.1)

    skeleton.terminate()