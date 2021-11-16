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
MQTT_TOPIC = 'lib_jo_demo'
MQTT_IP = '192.168.1.108'
MQTT_PLANT = 'lib_demo'
# battery
UBAT_100 = 4.2
UBAT_0 = 3.6

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
    return

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
    print("Rhodo -> connected with result code " + str(rc))
    print('-----------------------------------------'  )
    client.subscribe(MQTT_TOPIC)

# This is the message manager
def on_message(client, userdata, msg):
    
    rx_msg = msg.payload.decode()
    print(rx_msg)
    plant = MQTT_PLANT
    
    rx_tupple = rx_msg.split(',')
    print(rx_tupple)
    for l in rx_tupple:
        if '=' in l:
            le = l.split('=')
            c_name = le[0]
            c_val = c[1]
            print('c_name=',c_name, 'c_val=', c_val)
        
    
    ubat100 = UBAT_100 # tension batterie li-ion a pleine charge
    ubat000 = UBAT_0 # tension batterie li-ion déchargée
    pente_decharge = (ubat100-ubat000)/100 # pente de décharge estimée comme linéaire
    charge_bat = str(int((float(rx_battery_voltage) - ubat000) / pente_decharge))
    
    str_now = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime())

    sql_txt = " ".join(["INSERT INTO soil (plant, sol_moist, sol_temp, air_temp, ubat, charge_bat) VALUES ('", \
                        plant, "',", rx_sol_moisture, ",", rx_sol_temperature, ",", \
                        rx_air_temperature, "," , \
                        rx_battery_voltage, "," , charge_bat, ")"])

    db_connection, err = get_db_connection("mqtt")
    db_cursor = db_connection.cursor()
    db_cursor.execute(sql_txt)
    db_connection.commit()

    sql_duree_debut = 'SELECT time_stamp FROM soil ORDER BY id ASC LIMIT 1;'
    db_cursor = db_connection.cursor()
    db_cursor.execute(sql_duree_debut)
    date_start = db_cursor.fetchall()
    
    sql_duree_fin = 'SELECT time_stamp FROM soil ORDER BY id DESC LIMIT 1;'
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
    
    soil_alarm_level = 950
    
    msg = str_now \
          + '\ntempérature terre:    ' + rx_sol_temperature + ' [°C]'\
          + '\nhumidité terre:       ' + rx_sol_moisture + ' [-]'\
          + '\ntempérature air:      ' + rx_air_temperature + ' [°C]'\
          + '\ntension batterie:     ' + rx_battery_voltage  + ' [V]'\
          + '\ncharge batterie:      ' + str(charge_bat) + ' [%]'\
          + '\nvie batterie (j-h:m): ' + '{:02d}'.format(int(d)) + '-' + '{:02d}'.format(int(h)) + ':' + '{:02d}'.format(int(m)) \
          + '\n-------------------------------------'  
    print(msg)
    
    if int(rx_sol_moisture) < soil_alarm_level:
        title = 'Rhodos: time to water the rhododendrons, moisture = ' + str(rx_sol_moisture) + ' [-]'
#         send_email(title, msg)
        
    if float(rx_battery_voltage) < ubat000:
        title = 'Rhodos: time to recharge battery, tension = ' + str(rx_battery_voltage) + ' [V]'
        send_email(title, msg)

if __name__ == '__main__':

    client = mqtt.Client()
    client.connect("192.168.1.108",1883,60)

    client.on_connect = on_connect
    client.on_message = on_message

    client.loop_forever()
