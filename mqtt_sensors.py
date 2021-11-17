#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
import sys
import socket
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# mysql
MYSQL_IP = '192.168.1.139'
MYSQL_USERNAME = 'pi'
MYSQL_PW = 'mablonde'
MYSQL_HOSTNAME = 'localhost'
# mail
MAIL_SENDER_ADRESS = 'esp32jmb@gmail.com'
MAIL_SENDER_PW = 'mablonde'
MAIL_RECEIVER_ADRESS = 'jmetra@outlook.com'
# Mosquitto MQTT
MQTT_TOPIC = 'temp_sensor_bme'
MQTT_IP = '192.168.1.108'
# MQTT_PLANT = 'lib_demo'
# battery
UBAT_100 = 4.2
UBAT_0 = 3.5

def get_db_connection(db):

    # get the local IP adress
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()

    database_username = MYSQL_USERNAME  # YOUR MYSQL USERNAME, USUALLY ROOT
    database_password = MYSQL_PW  # YOUR MYSQL PASSWORD
    host_name = MYSQL_HOSTNAME
    server_ip = MYSQL_IP


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
#     return

    #The mail initialisation
    sender_address = MAIL_SENDER_ADRESS
    sender_pass = MAIL_SENDER_PW
    receiver_address = MAIL_RECEIVER_ADRESS
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
    print('Mail Sent')


# This is the Subscriber
def on_connect(client, userdata, flags, rc):
    print("mqtt_sensors -> connected with result code " + str(rc))
    print('---------------------------------------------'  )
    client.subscribe('mqtt_sensors/bureau/#')

# This is the message manager
def on_message(client, userdata, msg):

    charge_bat = 0
    
    rx_topic_global = msg.topic
    topic = rx_topic_global.split("/")
    rx_topic = topic[0]
    rx_piece = topic[1]
    rx_grandeur = topic[2]
    rx_valeur = msg.payload.decode()
#     print(rx_topic, rx_piece, rx_grandeur, rx_valeur)

    if rx_grandeur == 'volt':
        ubat100 = UBAT_100 # tension batterie li-ion a pleine charge
        ubat000 = UBAT_0 # tension batterie li-ion déchargée
        pente_decharge = (ubat100-ubat000)/100 # pente de décharge estimée comme linéaire
        charge_bat = str(int((float(rx_valeur) - ubat000) / pente_decharge))

    str_now = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())

    sql_txt = "".join(["INSERT INTO home_sensors (topic, piece, grandeur, valeur) VALUES ('", \
                        rx_topic, "',", "'", rx_piece, "',", "'", rx_grandeur, "',", rx_valeur, ")"])

#     print(sql_txt)
    db_connection, err = get_db_connection("mqtt")
    db_cursor = db_connection.cursor()
    db_cursor.execute(sql_txt)
    db_connection.commit()

    sql_duree_debut = 'SELECT time_stamp FROM home_sensors ORDER BY id ASC LIMIT 1;'
    db_cursor = db_connection.cursor()
    db_cursor.execute(sql_duree_debut)
    date_start = db_cursor.fetchall()

    sql_duree_fin = 'SELECT time_stamp FROM home_sensors ORDER BY id DESC LIMIT 1;'
    db_cursor = db_connection.cursor()
    db_cursor.execute(sql_duree_fin)
    date_end = db_cursor.fetchall()

    db_cursor.close()
    db_connection.close()

    elapsed = ((date_end[0][0] - date_start[0][0]).total_seconds())
    d = elapsed // (24 * 3600)
    elapsed = elapsed % (24 * 3600)
    h = elapsed // 3600
    elapsed %= 3600
    m = elapsed // 60
    elapsed %= 60
    s = elapsed

    msg = rx_topic + '/' + rx_piece + '/' + rx_grandeur + ': ' + rx_valeur
    print(msg)
    if rx_grandeur == 'volt':
        battery_voltage = rx_valeur
        msg =  'charge batterie: ' + str(charge_bat) + ' [%]\n'
        msg += 'vie batterie (j-h:m): ' + '{:02d}'.format(int(d)) + '-' + '{:02d}'.format(int(h)) + ':' + '{:02d}'.format(int(m)) + '\n'
        msg += 'time stamp: ' + str(date_end[0][0])
        msg += '\n---------------------------------------------'
        print(msg)

        if float(battery_voltage) < ubat000:
            title = rx_topic + '/' + rx_piece + 'time to recharge battery, tension = ' + str(battery_voltage) + ' [V]'
            print('---------------------------------------------')
            print(title)
            print('---------------------------------------------')
            send_email(title, msg)

if __name__ == '__main__':

    client = mqtt.Client()
    client.connect("192.168.1.108",1883,60)

    client.on_connect = on_connect
    client.on_message = on_message

    client.loop_forever()