#!/usr/bin/python3
import sys
import smtplib, email
import time
import os
import pandas as pd
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

datestr = time.strftime("%Y%m%d")
sheet_date = time.strftime("%d-%m-%Y")
csvfilename = "vpnusers_"+datestr+".csv"
excel_file = "vpnusers_"+datestr+".xlsx"
sheet_name = "VPN Users {}".format(sheet_date)

df1 = pd.read_csv(csvfilename, index_col="Time")

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')
df1.to_excel(writer, sheet_name= sheet_name)

# Access the XlsxWriter workbook and worksheet objects from the dataframe.
workbook = writer.book
worksheet = writer.sheets[sheet_name]

# Create a chart object.
chart = workbook.add_chart({'type': 'line'})
#chart = workbook.add_chart({'type': 'area', 'subtype': 'stacked'})

# Configure the series of the chart from the dataframe data.
for i in range(2):
    col = i + 1
    chart.add_series({
        'name':       [sheet_name, 0, col],
        'categories': [sheet_name, 1, 0, df1.shape[0], 0],
        'values':     [sheet_name, 1, col, df1.shape[0], col],
    })

chart.set_legend({'position': 'top'})

# Configure the chart axes.
chart.set_x_axis({'name': 'Time of Day'})
chart.set_y_axis({'name': 'Value', 'major_gridlines': {'visible': False}})

# Insert the chart into the worksheet.
worksheet.insert_chart('E2', chart)

# Close the Pandas Excel writer and output the Excel file.
writer.save()

recipients = "user1@address, user2@address, user3@address"
subject = 'VPN users graph report for {}'.format(sheet_date)
bodytext= "This is the report in Excel Graph format for {} for VPN users and peak values per time of day. \n\nWith Compliments of the Network Section.".format(sheet_date)

# exchange Sign In
exchange_sender = 'user@address'
exchange_passwd = 'exchangepass'

message = MIMEMultipart()
message["From"] = exchange_sender
message["To"] = recipients
message["Subject"] = subject
#message["Bcc"] = recipients

message.attach(MIMEText(bodytext, "plain"))

# Open file in binary mode
with open(excel_file, "rb") as attachment:
    # Add file as application/octet-stream
    # Email client can usually download this automatically as attachment
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())

# Encode file in ASCII characters to send by email
encoders.encode_base64(part)

# Add header as key/value pair to attachment part
part.add_header(
    "Content-Disposition",
    f"attachment; filename= {excel_file}",
)

# Add attachment to message and convert message to string
message.attach(part)
text = message.as_string()

# Log in to server using secure context and send email
with smtplib.SMTP('smtpaddress', 25) as server:
    server.ehlo()
    server.starttls()
    server.login(exchange_sender, exchange_passwd)
    try:
        server.sendmail(exchange_sender, recipients, text)
        print ('email sent')
        if os.path.isfile(excel_file):
            #os.remove(excel_file)
            print(excel_file, "file deleted")
        else:
            print(f'Error: {excel_file} not a valid filename')

        if os.path.isfile(csvfilename):
            #os.remove(csvfilename)
            print(csvfilename, "file deleted")
        else:
            print(f'Error: {csvfilename} not a valid filename')

    except:
        print ('error sending mail')
