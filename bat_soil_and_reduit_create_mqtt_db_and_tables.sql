-- Batch pour la création de la base de donnee arrose
-- 21.04.2021 Joseph Metrailler
-- --------------------------------------------------------------
-- si elle existe, supprimer la db mqtt existante et la recreer
-- DROP DATABASE IF EXISTS mqtt;
-- CREATE DATABASE mqtt;
USE mqtt;
-- --------------------------------------------------------------
-- table soil pour l'humidite de la terre 
DROP TABLE IF EXISTS soil;
DROP TABLE IF EXISTS reduit;
CREATE TABLE soil
(
  id INT NOT NULL AUTO_INCREMENT,
  time_stamp TIMESTAMP NOT NULL,
  plant VARCHAR(10) NOT NULL,
  sol_moist DOUBLE NOT NULL,
  sol_temp DOUBLE NOT NULL,
  ubat double NOT NULL,
  charge_bat DOUBLE NOT NULL,
  PRIMARY KEY (id),
  INDEX i_date (time_stamp),
  INDEX i_id (id),
  UNIQUE(id)
);
-- table reduit pour les temperature congelo et reduit
-- --------------------------------------------------------------
CREATE TABLE reduit
(
  id INT NOT NULL AUTO_INCREMENT,
  time_stamp TIMESTAMP NOT NULL,
  sensorid VARCHAR(20) NOT NULL,
  sensorval DOUBLE NOT NULL,
  PRIMARY KEY (id),
  INDEX i_date (time_stamp),
  INDEX i_id (id),
  UNIQUE(id)
);
