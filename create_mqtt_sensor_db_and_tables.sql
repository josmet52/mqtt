-- Batch pour la création de la base de donnee arrose
-- 21.04.2021 Joseph Metrailler
-- ------------------------------------------------------------
-- si elle existe, supprimer la db mqtt existante et la recreer
DROP DATABASE IF EXISTS mqtt;
CREATE DATABASE mqtt;
USE mqtt;
-- ------------------------------------------------------------
-- table home_sensors pour les mesures
CREATE TABLE home_sensors
(
  id INT NOT NULL AUTO_INCREMENT,
  time_stamp TIMESTAMP NOT NULL,
  topic VARCHAR(20) NOT NULL;
  piece VARCHAR(20) NOT NULL;
  grandeur VARCHAR(20) NOT NULL
  valeur DOUBLE NOT NULL;
  PRIMARY KEY (id),
  INDEX i_date (time_stamp),
  INDEX i_id (id),
  UNIQUE(id)
);
