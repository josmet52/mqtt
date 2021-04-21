-- Batch pour la création de la base de donnee arrose
-- 21.04.2021 Joseph Metrailler
-- --------------------------------------------------------------
-- si elle existe, supprimer la db mqtt existante et la recreer
DROP DATABASE IF EXISTS mqtt;
CREATE DATABASE mqtt;
USE mqtt;
-- --------------------------------------------------------------
-- table soil pour l'humidite de la terre 
CREATE TABLE soil
(
  id int NOT NULL AUTO_INCREMENT,
  time_stamp timestamp NOT NULL,
  plant varchar(10) NOT NULL,
  moist double NOT NULL,
  temp_soil double NOT NULL,
  temp_ds18b20 double NOT NULL,
  temp_dht11 double NOT NULL,
  humidity_dht11 double NOT NULL,
  ubat double NOT NULL,
  INDEX i_date (time_stamp),
  INDEX i_id (id),
  UNIQUE(id)
);
-- table reduit pour les temperature congelo et reduit
-- --------------------------------------------------------------
CREATE TABLE reduit
(
  id int NOT NULL AUTO_INCREMENT,
  time_stamp timestamp NOT NULL,
  PRIMARY KEY (id),
  INDEX i_date (time_stamp),
  INDEX i_id (id),
  UNIQUE(id),
  sensorid varchar(20) NOT NULL,
  sensorval double NOT NULL
);
