#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
import sys
import socket
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_db_connection(db):
    
    # get the local IP adress
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    
    database_username = "pi"  # YOUR MYSQL USERNAME, USUALLY ROOT
    database_password = "mablonde"  # YOUR MYSQL PASSWORD
    host_name = "localhost"
    server_ip = '192.168.1.139'


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
        # return error
        return False, sys.exc_info()

def send_email(title, msg):

    #The mail addresses and password
    sender_address = 'esp32jmb@gmail.com'
    sender_pass = 'mablonde'
    receiver_address = 'jmetra@outlook.com'
    #Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = title
    #The body and the attachments for the mail
    message.attach(MIMEText(msg, 'plain'))
    #Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
    session.starttls() #enable security
    session.login(sender_address, sender_pass) #login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
#     print('Mail Sent')


# This is the Subscriber
def on_connect(client, userdata, flags, rc):
    print("MQTT reduit -> connected with result code "+str(rc))
    client.subscribe("mqtt_temp_reduit")

# This is the message manager
def on_message(client, userdata, msg):
    
    str_now = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
    # initialise database access
    mysql_ip = "192.168.1.139"
    
#     db_connection, err = mysql_con.get_db_connection("mqtt")
    db_connection, err = get_db_connection("mqtt")
    db_cursor = db_connection.cursor()
    sql_txt = "DELETE FROM reduit;"
    db_cursor.execute(sql_txt)
    
    rx_msg = msg.payload.decode()
    rx_tupple = rx_msg.split(',')
    for i, rx_item in enumerate(rx_tupple):
        if i > 0:
            mes = rx_item.split(':')
            sql_txt = " ".join(["INSERT INTO reduit (sensorid, sensorval) VALUES ('", mes[0].strip(), "',", mes[1], ")"])
            db_cursor.execute(sql_txt)
            print(str_now, sql_txt)
    print('-----------------------------------------')
            
    db_connection.commit()
    db_cursor.close()
    db_connection.close()

client = mqtt.Client()
client.connect("192.168.1.108",1883,60)

client.on_connect = on_connect
client.on_message = on_message

client.loop_forever()