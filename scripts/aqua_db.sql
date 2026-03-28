-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 28, 2026 at 02:54 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `aqua_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `id` int(11) NOT NULL,
  `username` varchar(80) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`id`, `username`, `password_hash`, `created_at`) VALUES
(1, 'admin', 'scrypt:32768:8:1$xc6wNlB8CU7wrkYZ$4d49481bf97d3d9ea13fd8b66e34699ac1a7b4c04f4fc744b88592e34d8d056c4d7ae1486202df6176878b1054f3f5fe03ea0f6dc01d38c8cf71f90869fd00d0', '2026-02-04 21:27:22');

-- --------------------------------------------------------

--
-- Table structure for table `contact_messages`
--

CREATE TABLE `contact_messages` (
  `id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `email` varchar(255) NOT NULL,
  `subject` varchar(300) NOT NULL,
  `message` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `contact_messages`
--

INSERT INTO `contact_messages` (`id`, `name`, `email`, `subject`, `message`, `created_at`) VALUES
(1, 'Praveen Pitawala', 'praveenpitawalajob@gmail.com', 'sdfdf', 'sdfsdfsdf', '2026-02-09 15:13:40'),
(2, 'sdfdsf', 'sfsdf@gmail.com', 'sdfsdf', 'sfsdf', '2026-02-09 15:19:58'),
(3, 'sfsdf', 'sfsdf@gmail.com', 'sfsdf', 'sdfsdf', '2026-02-09 15:20:03'),
(4, 'sdfsdf', 'sfsdf@gmail.com', 'sdfsf', 'sdfsdfdf', '2026-02-09 15:20:08'),
(5, 'sdfsdf', 'sfsdf@gmail.com', 'sfsdf', 'sdfsdfdf', '2026-02-09 15:20:14'),
(6, 'fghfghfgh', 'sfsdf@gmail.com', 'sfsdf', 'sdfsf', '2026-02-09 15:20:49'),
(7, 'sdfsf', 'sfsdf@gmail.com', 'sdfsdf', 'sdfdsf', '2026-02-09 15:20:54'),
(8, 'sdfsdf', 'sfsdfsfsdf@gmail.com', 'sdf', 'sdf', '2026-02-09 15:20:59'),
(9, 'sfsd', 'sfsdf@gmail.com', 'sdfg', 'sdfsdf', '2026-02-09 15:21:03'),
(10, 'sfsdf@gmail.com', 'sdfsdfsfsdf@gmail.com', 'sdfsdf', 'sdfsdf', '2026-02-09 15:21:10'),
(11, 'sdfsdf', 'sdfsfsdf@gmail.com', 'sdf', 'sdf', '2026-02-09 15:21:15'),
(12, 'sfdfgfd', 'sfsdf@gmail.com', 'sdf', 'sdfsd', '2026-02-09 15:21:20'),
(13, 'dfdfgfdg', 'sfsdf@gmail.com', 'sdfsdf', 'sdf', '2026-02-09 15:21:30'),
(14, 'sdfdgfdfg', 'sfsdf@gmail.com', 'sdf', 'sdfsdf', '2026-02-09 15:21:35');

-- --------------------------------------------------------

--
-- Table structure for table `delivery_base_per_kg`
--

CREATE TABLE `delivery_base_per_kg` (
  `id` int(11) NOT NULL,
  `max_weight_kg` decimal(10,2) NOT NULL DEFAULT 1.50,
  `base_price` decimal(10,2) NOT NULL DEFAULT 450.00,
  `extra_per_kg` decimal(10,2) NOT NULL DEFAULT 100.00,
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `delivery_base_per_kg`
--

INSERT INTO `delivery_base_per_kg` (`id`, `max_weight_kg`, `base_price`, `extra_per_kg`, `updated_at`) VALUES
(1, 1.53, 450.00, 100.00, '2026-02-09 15:13:15');

-- --------------------------------------------------------

--
-- Table structure for table `foods`
--

CREATE TABLE `foods` (
  `id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `category` varchar(80) NOT NULL,
  `weight` varchar(80) DEFAULT NULL,
  `image1` longblob DEFAULT NULL,
  `image1_type` varchar(20) DEFAULT NULL,
  `image2` longblob DEFAULT NULL,
  `image2_type` varchar(20) DEFAULT NULL,
  `image3` longblob DEFAULT NULL,
  `image3_type` varchar(20) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `plants`
--

CREATE TABLE `plants` (
  `id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `category` varchar(80) NOT NULL,
  `weight` varchar(80) DEFAULT NULL,
  `image1` longblob DEFAULT NULL,
  `image1_type` varchar(20) DEFAULT NULL,
  `image2` longblob DEFAULT NULL,
  `image2_type` varchar(20) DEFAULT NULL,
  `image3` longblob DEFAULT NULL,
  `image3_type` varchar(20) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `tools`
--

CREATE TABLE `tools` (
  `id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `category` varchar(80) NOT NULL,
  `weight` varchar(80) DEFAULT NULL,
  `image1` longblob DEFAULT NULL,
  `image1_type` varchar(20) DEFAULT NULL,
  `image2` longblob DEFAULT NULL,
  `image2_type` varchar(20) DEFAULT NULL,
  `image3` longblob DEFAULT NULL,
  `image3_type` varchar(20) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `contact_messages`
--
ALTER TABLE `contact_messages`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `delivery_base_per_kg`
--
ALTER TABLE `delivery_base_per_kg`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `foods`
--
ALTER TABLE `foods`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `plants`
--
ALTER TABLE `plants`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tools`
--
ALTER TABLE `tools`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admins`
--
ALTER TABLE `admins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `contact_messages`
--
ALTER TABLE `contact_messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT for table `delivery_base_per_kg`
--
ALTER TABLE `delivery_base_per_kg`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `foods`
--
ALTER TABLE `foods`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `plants`
--
ALTER TABLE `plants`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `tools`
--
ALTER TABLE `tools`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
