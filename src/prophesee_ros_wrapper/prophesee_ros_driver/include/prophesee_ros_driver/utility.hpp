#ifndef DATASET_TOOLBOX_UTILITY_HPP_
#define DATASET_TOOLBOX_UTILITY_HPP_

#include <boost/filesystem.hpp>
#include <geometry_msgs/PoseStamped.h>
#include <prophesee_event_msgs/Event.h>
#include <prophesee_event_msgs/EventArray.h>
#include <prophesee_event_msgs/Event_custom.h>
#include <prophesee_event_msgs/EventArray_custom.h>

#include <ros/package.h>
#include <ros/ros.h>
#include <sensor_msgs/Image.h>
#include <sensor_msgs/Imu.h>
#include <sensor_msgs/PointCloud2.h>
#include <string>

#define IMU_PERIOD    0.005000000  // 200Hz
#define CAM_PERIOD    0.033333333  // 30Hz
#define KINECT_PERIOD 0.033333333  // 30Hz
#define LIDAR_PERIOD  0.100000000  // 10Hz
#define GT_PERIOD     0.008333333  // 120Hz (small-scale) or 10Hz (large-scale)

using IMU         = sensor_msgs::Imu;
using Event       = prophesee_event_msgs::Event;
using EventArray  = prophesee_event_msgs::EventArray;
using Event_custom       = prophesee_event_msgs::Event_custom;
using EventArray_custom  = prophesee_event_msgs::EventArray_custom;

using Image       = sensor_msgs::Image;
using PointCloud  = sensor_msgs::PointCloud2;
using PoseStamped = geometry_msgs::PoseStamped;

// ------------------------------------------------------------------------- //

namespace colorful_char {

std::string info(std::string input_str) {
  return "\033[1;32m>> " + input_str + " \033[0m";
}

std::string warning(std::string input_str) {
  return "\033[1;35m>> WARNING: " + input_str + " \033[0m";
}

std::string error(std::string input_str) {
  return "\033[1;31m>> ERROR: " + input_str + " \033[0m";
}

}  // namespace colorful_char

// ------------------------------------------------------------------------- //


#endif  // DATASET_TOOLBOX_UTILITY_HPP_
