#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: mqtt_airsens.py 

author: jom52
email: jom52.dev@gmail.com
github: https://github.com/jom52/esp32-airsens

data management for the project airsens esp32-mqtt-mysql

v0.1.0 : 15.02.2022 --> first prototype
"""
VERSION = '0.1.0'

import paho.mqtt.client as mqtt
import time
import sys
import socket
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# battery
UBAT_100 = 4.2
UBAT_0 = 3.5

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
        return False, sys.exc_info()

def send_email(title, msg):
#     return

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
    print('Mail Sent')

def decode_msg(msg):
    jmb_id = msg[0:3]
    piece = msg[3:5]
    temp = int(msg[6:9])/10
    hum = int(msg[9:11])
    pres = int(msg[11:14])
    ubat = int(msg[14:17])/100
    rx_crc = msg[17:19]
    return jmb_id, piece, temp, hum, pres, ubat, rx_crc

def crc(msg):
    crc_0 = 0
    crc_1 = 0
    for i, char in enumerate(msg):
        if (i %2) == 0:
            crc_0 += ord(char)
        else:
            crc_1 += ord(char)
    v_crc = crc_0 + crc_1 * 3
    if v_crc < 10 : v_crc *= 10
    return str(v_crc)[-2:]

# This is the Subscriber
def on_connect(client, userdata, flags, rc):
#     print('client, userdata, flags, rc:', client, userdata, flags, rc)
    print("airsens -> connected with result code " + str(rc))
    print('-----------------------------------------'  )
    client.subscribe("airsens_test")
    
def record_data_in_db(rx_msg):
    
    _, local, temp, hum, pres, ubat, __ = decode_msg(rx_msg)
    charge_bat = int((float(ubat) - UBAT_0) / ((UBAT_100 - UBAT_0)/100))
    str_now = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
    sql_txt = "".join(["INSERT INTO airsens (local, temp, hum, pres, ubat, charge_bat) VALUES ('",
                       local, "',",
                       "'", str(temp), "',",
                       "'", str(hum), "',",
                       "'", str(pres), "',",
                       "'", str(ubat), "',",
                       "'", str(charge_bat), "');"])

    db_connection, err = get_db_connection("airsens")
    db_cursor = db_connection.cursor()
    db_cursor.execute(sql_txt)
    db_connection.commit()
    db_cursor.close()
    db_connection.close()

def get_now_and_elapsed(local):
    
    db_connection, err = get_db_connection("airsens")
    db_cursor = db_connection.cursor()

    sql_duree_debut = 'SELECT time_stamp FROM airsens WHERE local="' + local + '" ORDER BY id ASC LIMIT 1;'
    db_cursor.execute(sql_duree_debut)
    date_start = db_cursor.fetchall()

    sql_duree_fin = 'SELECT time_stamp FROM airsens WHERE local="' + local + '" ORDER BY id DESC LIMIT 1;'
    db_cursor.execute(sql_duree_fin)
    date_end = db_cursor.fetchall()

    db_cursor.close()
    db_connection.close()

    str_now = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
    elapsed = ((date_end[0][0] - date_start[0][0]).total_seconds())
    d = elapsed // (24 * 3600)
    elapsed = elapsed % (24 * 3600)
    h = elapsed // 3600
    elapsed %= 3600
    m = elapsed // 60
    elapsed %= 60
    s = elapsed
    str_elapsed = '{:02d}'.format(int(d)) + '-' + '{:02d}'.format(int(h)) + ':' + '{:02d}'.format(int(m))
    return str_now, str_elapsed

# This is the message manager
def on_message(client, userdata, msg):
    
    # initialise database access
    mysql_ip = "192.168.1.139"
    
    rx_msg = msg.payload.decode()
    rx_crc = rx_msg[-2:]
    ctrl_crc = crc(rx_msg[:-2])
    if rx_crc == ctrl_crc:
        idx, local, temp, hum, pres, ubat, crc_v = decode_msg(rx_msg)
        record_data_in_db(rx_msg)
        
#         db_connection, err = get_db_connection("airsens")
#         db_cursor = db_connection.cursor()
# 
#         sql_duree_debut = 'SELECT time_stamp FROM airsens WHERE local="' + local + '" ORDER BY id ASC LIMIT 1;'
#         db_cursor.execute(sql_duree_debut)
#         date_start = db_cursor.fetchall()
# 
#         sql_duree_fin = 'SELECT time_stamp FROM airsens WHERE local="' + local + '" ORDER BY id DESC LIMIT 1;'
#         db_cursor.execute(sql_duree_fin)
#         date_end = db_cursor.fetchall()
# 
#         db_cursor.close()
#         db_connection.close()
# 
#         str_now = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())
#         elapsed = ((date_end[0][0] - date_start[0][0]).total_seconds())
#         d = elapsed // (24 * 3600)
#         elapsed = elapsed % (24 * 3600)
#         h = elapsed // 3600
#         elapsed %= 3600
#         m = elapsed // 60
#         elapsed %= 60
#         s = elapsed

        str_now, str_elapsed = get_now_and_elapsed(local)
        charge_bat = int((float(ubat) - UBAT_0) / ((UBAT_100 - UBAT_0)/100))
        room = local

        if local == 'bu' or local == 'ex' or local == 'sa' or local == 'B9':
#             if local == 'bu' : room = 'office    '
#             elif local == 'sa': room = 'salon    '
#             elif local == 'ex': room = 'outside  '
#             elif local == 'B9': room = 'office b9'
            
            msg = 'room:' + room + ' - temp:' + '{:.1f}'.format(temp) + '°C - hum:' + '{:.0f}'.format(hum)
            msg += '% - pres:' + '{:.0f}'.format(pres) + 'hPa - bat:' + '{:.2f}'.format(ubat) + 'V'
            msg += ' - battery load:' + str(charge_bat) + '%'
#             msg += ' - battery life(j-h:m):' + '{:02d}'.format(int(d)) + '-' + '{:02d}'.format(int(h)) + ':' + '{:02d}'.format(int(m))
            msg += ' - battery life(j-h:m):' + str_elapsed
            msg += ' - measure time:' + str_now
            print(msg)

            if float(ubat) < UBAT_0:
                title = local  + ' --> time to recharge battery, tension = ' + str(ubat) + ' [V]'
                print(title)
                print('---------------------------------------------')
                send_email(title, msg)
        else:
            print('room:' + local
                  + ' - temp:' + '{:.1f}'.format(temp) + '°C'
                  + ' - hum:' + '{:.0f}'.format(hum) + '%'
                  + ' - pres:' + '{:.0f}'.format(pres) + 'hPa'
                  + ' - bat:' + '{:.2f}'.format(ubat) + 'V')

client = mqtt.Client()
client.connect("192.168.1.108",1883,60)

client.on_connect = on_connect
client.on_message = on_message

client.loop_forever()