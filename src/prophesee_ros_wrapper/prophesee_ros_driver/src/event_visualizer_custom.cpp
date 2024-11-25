#include <cv_bridge/cv_bridge.h>
#include <mutex>
#include <opencv2/opencv.hpp>
#include <utility.hpp>
#include <opencv2/videoio.hpp>  // For cv::VideoWriter

// ------------------------------------------------------------------------- //

std::mutex         mtx1, mtx2;
std::vector<Event> event_buffer1, event_buffer2;
int                cam1_width, cam1_height, cam2_width, cam2_height;

// ------------------------------------------------------------------------- //

void Event1Callback(const EventArray::ConstPtr & message, const std::string & topic_name) {
  ROS_INFO_ONCE("%s", colorful_char::info("Receive event messages under topic name: " + topic_name).c_str());
  mtx1.lock();
  for (const Event & event : message->events) event_buffer1.emplace_back(event);
  mtx1.unlock();
  cam1_width  = message->width;
  cam1_height = message->height;
}

void Event2Callback(const EventArray::ConstPtr & message, const std::string & topic_name) {
  ROS_INFO_ONCE("%s", colorful_char::info("Receive event messages under topic name: " + topic_name).c_str());
  mtx2.lock();
  for (const Event & event : message->events) event_buffer2.emplace_back(event);
  mtx2.unlock();
  cam2_width  = message->width;
  cam2_height = message->height;
}

// ------------------------------------------------------------------------- //

int main(int argc, char ** argv) {
  ros::init(argc, argv, "event_visualizer");
  ros::NodeHandle nh;

  // Read and validate the input parameters from config.
  std::vector<std::string> in_topics;
  int out_freq;
  ros::param::get("in_event_stream_topic", in_topics);
  ros::param::get("out_frequency", out_freq);
  if (in_topics.size() > 2) {
    ROS_ERROR("%s", colorful_char::error("The current version does not support more than two event cameras.").c_str());
    ros::shutdown();
    return -1;
  }
  int cam_num = in_topics.size();

  // Set up the subscribers according to the sensor setup (monocular or stereo).
  ros::Subscriber sub1, sub2;
  for (size_t idx = 0; idx < cam_num; ++idx) {
    if (idx == 0) {
      sub1 = nh.subscribe<EventArray>(in_topics[idx], 100000, boost::bind(Event1Callback, _1, in_topics[idx]));
    } else if (idx == 1) {
      sub2 = nh.subscribe<EventArray>(in_topics[idx], 100000, boost::bind(Event2Callback, _1, in_topics[idx]));
    }
  }

  // OpenCV VideoWriter setup for each topic.
  cv::VideoWriter video_writer1, video_writer2;

  // Wait for the first event buffer to populate before determining size
  ros::Rate rate(out_freq);
  while (ros::ok() && (event_buffer1.empty() || (cam_num == 2 && event_buffer2.empty()))) {
    ros::spinOnce();
    rate.sleep();
  }

  // Initialize the video writers once we have the camera dimensions.
  video_writer1.open("output_cam1.avi", cv::VideoWriter::fourcc('M','J','P','G'), out_freq, cv::Size(cam1_width, cam1_height));
  if (cam_num == 2) {
    video_writer2.open("output_cam2.avi", cv::VideoWriter::fourcc('M','J','P','G'), out_freq, cv::Size(cam2_width, cam2_height));
  }

  if (!video_writer1.isOpened() || (cam_num == 2 && !video_writer2.isOpened())) {
    ROS_ERROR("Could not open the output video files for writing.");
    return -1;
  }

  while (ros::ok()) {
    // Swap the events from the buffer to a temporary holder.
    std::vector<Event> event_holder1, event_holder2;
    mtx1.lock();
    event_holder1.swap(event_buffer1);
    mtx1.unlock();
    if (cam_num == 2) {
      mtx2.lock();
      event_holder2.swap(event_buffer2);
      mtx2.unlock();
    }

    // Skip if no new events.
    if ((cam_num == 1 && event_holder1.empty()) || (cam_num == 2 && (event_holder1.empty() || event_holder2.empty()))) {
      rate.sleep();
      ros::spinOnce();
      continue;
    }

    // Process and write the frames for camera 1.
    cv::Mat event_frame1 = cv::Mat(cam1_height, cam1_width, CV_8UC3, cv::Vec3b(255, 255, 255));
    for (auto & event : event_holder1) {
      if (event.polarity) event_frame1.at<cv::Vec3b>(event.y, event.x) = cv::Vec3b(0, 0, 0);  // positive - black
      else
        event_frame1.at<cv::Vec3b>(event.y, event.x) = cv::Vec3b(100, 100, 100);  // negative - gray
    }
    video_writer1.write(event_frame1);

    // If stereo, process and write the frames for camera 2.
    if (cam_num == 2) {
      cv::Mat event_frame2 = cv::Mat(cam2_height, cam2_width, CV_8UC3, cv::Vec3b(255, 255, 255));
      for (auto & event : event_holder2) {
        if (event.polarity) event_frame2.at<cv::Vec3b>(event.y, event.x) = cv::Vec3b(0, 0, 0);  // positive - black
        else
          event_frame2.at<cv::Vec3b>(event.y, event.x) = cv::Vec3b(100, 100, 100);  // negative - gray
      }
      video_writer2.write(event_frame2);
    }

    rate.sleep();
    ros::spinOnce();
  }

  video_writer1.release();
  if (cam_num == 2) {
    video_writer2.release();
  }

  ros::shutdown();
  return 0;
}

