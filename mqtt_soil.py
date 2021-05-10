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
        return False, sys.exc_info()

def send_email(title, msg):
    return

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


# This is the Subscriber
def on_connect(client, userdata, flags, rc):
    print("Rhodo -> connected with result code " + str(rc))
    print('-----------------------------------------'  )
    client.subscribe("rhodo_all")

# This is the message manager
def on_message(client, userdata, msg):
    
    # initialise database access
    mysql_ip = "192.168.1.139"
    
    rx_msg = msg.payload.decode()
    
    plant = 'rhodo'
    
    rx_tupple = rx_msg.split(',')
    print(rx_tupple)
    rx_sol_moisture = rx_tupple[0]#.split(':')[1]
    rx_air_temperature = rx_tupple[2]#.split(':')[1]
    rx_sol_temperature = rx_tupple[1]#.split(':')[1]
    rx_battery_voltage = rx_tupple[3]#.split(':')[1]
    
    ubat100 = 4.1 # tension batterie li-ion a pleine charge
    ubat000 = 3.6 # tension batterie li-ion déchargée
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
        send_email(title, msg)
        
    if float(rx_battery_voltage) < ubat000:
        title = 'Rhodos: time to recharge battery, tension = ' + str(rx_battery_voltage) + ' [V]'
        send_email(title, msg)

client = mqtt.Client()
client.connect("192.168.1.108",1883,60)

client.on_connect = on_connect
client.on_message = on_message

client.loop_forever()