#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import time
import sys
import socket
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SENSOR_ID_TEMP_CONGELATEUR = '28-fe258316039f'
SENSOR_ID_TEMP_REDUIT = '28-f0298316032f'
CONGELATEUR_ALARM_LEVEL = -12

MYSQL_SERVER_IP = '192.168.1.139'
MYSQL_DB_USERNAME = 'pi'
MYSQL_DATABASE_PW = 'mablonde'
MYSQL_HOST_NAME = 'localhost'

MQTT_TOPIC_SUB = 'reduit_temp'
MQTT_SERVER_IP = '192.168.1.108'
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

GMAIL_MAIL_SENDER_ADRESS = 'esp32jmb@gmail.com'
GMAIL_MAIL_RECEIVER_ADRESS = 'joseph.metrailler@bluewin.ch'
GMAIL_MAIL_SEND_PW = 'mablonde'
GMAIL_SMTP_ADRESS = 'smtp.gmail.com'
GMAIL_SMTP_PORT = '587'

def get_db_connection(db):
    
    # get the local IP adress
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    
    database_username = MYSQL_DB_USERNAME  # YOUR MYSQL USERNAME, USUALLY ROOT
    database_password = MYSQL_DATABASE_PW  # YOUR MYSQL PASSWORD
    host_name = MYSQL_HOST_NAME
    server_ip = MYSQL_SERVER_IP

    # verify if the mysql server is ok and the db avaliable
    try:
        if local_ip == server_ip: # if we are on the RPI with mysql server (RPI making temp acquis)
            # test the local database connection
            con = mysql.connector.connect(user=database_username, password=database_password, host=host_name, database=db)
        else:
            # test the distant database connection
            con = mysql.connector.connect(user=database_username, password=database_password, host=server_ip, database=db)
        return con, sys.exc_info()
    
    except:
        return False, sys.exc_info()

def send_email(title, msg):

    #The mail addresses and password
    sender_address = GMAIL_MAIL_SENDER_ADRESS
    sender_pass = GMAIL_MAIL_SEND_PW
    receiver_address = GMAIL_MAIL_RECEIVER_ADRESS
    #Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = title
    #The body and the attachments for the mail
    message.attach(MIMEText(msg, 'plain'))
    #Create SMTP session for sending the mail
    session = smtplib.SMTP(GMAIL_SMTP_ADRESS, GMAIL_SMTP_PORT) #use gmail with port
    session.starttls() #enable security
    session.login(sender_address, sender_pass) #login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()

# This is the Subscriber
def on_connect(client, userdata, flags, rc):
    print("MQTT reduit -> connected with result code " + str(rc) + ' on topic: ' + MQTT_TOPIC_SUB)
    print('-----------------------------------------------------------------')
    client.subscribe(MQTT_TOPIC_SUB)

# This is the message manager
def on_message(client, userdata, msg):
    
    str_now = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
    # initialise database access
    mysql_ip = MYSQL_SERVER_IP

    db_connection, err = get_db_connection("mqtt")
    db_cursor = db_connection.cursor()
    sql_txt = "DELETE FROM reduit;"
    db_cursor.execute(sql_txt)
    
    rx_msg = msg.payload.decode()[:-1]
    rx_tupple = rx_msg.split(',')
    for rx_item in rx_tupple:
        mes = rx_item.split(':')
        sql_txt = "".join(["INSERT INTO reduit (sensorid, sensorval) VALUES ('", mes[0].strip(), "',", mes[1], ")"])
        db_cursor.execute(sql_txt)
        if mes[0].strip() == SENSOR_ID_TEMP_CONGELATEUR and float(mes[1].replace('"','')) > CONGELATEUR_ALARM_LEVEL:
            title = 'ALARME CONGELATEUR'
            msg = 'La température du congélateur aumente. Elle atteint maintenant: ' + mes[1].replace('"','') + '°C'
            print(mes[1])
            print('\n', title, '\n', msg, '\n')
            send_email(title, msg), 
        print(str_now, sql_txt)
    print('----------------------------------------------------------------------------------------------------')
            
    db_connection.commit()
    db_cursor.close()
    db_connection.close()

client = mqtt.Client()
client.connect(MQTT_SERVER_IP, MQTT_PORT, MQTT_KEEPALIVE)

client.on_connect = on_connect
client.on_message = on_message

client.loop_forever()