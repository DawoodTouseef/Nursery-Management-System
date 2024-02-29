PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS `Product` (
  `p_id` INTEGER PRIMARY KEY,
  `p_name` VARCHAR(25),
  `stock_available` INTEGER,
  `price` FLOAT,
   `Description` VARCHAR(25),
  `supplier_id` INTEGER,
  `image` VARCHAR(25),
  FOREIGN KEY (`supplier_id`) REFERENCES `supplier` (`s_id`)
);

CREATE TABLE IF NOT EXISTS `supplier` (
  `s_id` INTEGER PRIMARY KEY,
  `company_name` VARCHAR(45),
  `s_email` VARCHAR(25),
  `password_hash` VARCHAR(25),
  `s_contact` INTEGER(12),
  `s_address` VARCHAR(25)
);

CREATE TABLE IF NOT EXISTS `users` (
  `user_id` INTEGER PRIMARY KEY,
  `First_Name` VARCHAR(35),
  `last_Name` VARCHAR(35),
  `user_email` VARCHAR(25),
  `password_hash` VARCHAR(25)
);

CREATE TABLE IF NOT EXISTS  `Orders` (
  `order_id` INTEGER PRIMARY KEY,
  `reference` VARCHAR(45),
  `p_id` INTEGER,
  `u_id` INTEGER,
  `order_date` DATE,
  `Delivery_date` VARCHAR(45),
  `First_Name` VARCHAR(35),
  `last_Name` VARCHAR(35),
  `user_email` VARCHAR(25),
  `country`VARCHAR(25),
  `state`VARCHAR(25),
  `city` VARCHAR(25),
  `u_contact` VARCHAR(25),
  `u_address` VARCHAR(45),
  `status` VARCHAR(25),
  `total_amt` FLOAT,
  `PaymentType` VARCHAR(10),
  FOREIGN KEY (`p_id`) REFERENCES `Product` (`p_id`),
  FOREIGN KEY (`u_id`) REFERENCES `users` (`user_id`)

);

CREATE TABLE IF NOT EXISTS `order_item` (
  `order_item_id` INTEGER PRIMARY KEY,
  `p_id` INTEGER,
  `u_id` INTEGER,
  `order_id` INTEGER,
  `quantity` INTEGER,
   FOREIGN KEY (`order_id`) REFERENCES `Orders` (`order_id`),
  FOREIGN KEY (`p_id`) REFERENCES `Product` (`p_id`),
  FOREIGN KEY (`u_id`) REFERENCES `users` (`user_id`)
);
