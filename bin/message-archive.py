#!/usr/bin/python3

from xml.dom import minidom
from shutil import rmtree, move
import datetime
import os
import sqlite3
import argparse

parser = argparse.ArgumentParser(
    description='Import Signal and Google Voice backups into Sqlite3.',
    formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=150, width=150))
parser.add_argument('-p', '--signal-pass', help='Password for signal backup', default='')
parser.add_argument('-s', '--signal-back', help='Path to signal-back', default='/usr/bin/signal-back')
requiredArguments = parser.add_argument_group('required arguments')
requiredArguments.add_argument('-m', '--my-number', help='Your phone number. Format: "12223334444"', required=True)
requiredArguments.add_argument('-d', '--data-dir', help='The data directory', required=True)
args = parser.parse_args()

def processVoicePeople(f, c):
    with open(f, mode='r', encoding="utf-8") as myfile:
            data=myfile.read()
    data = data.replace('<br>', '<br/>')
    xmldoc = minidom.parseString(data)
    address = ""
    axml = xmldoc.getElementsByTagName('a')
    for a in axml:
        if a.hasAttribute('class') and a.attributes['class'].value == 'tel':
            sender = a.attributes['href'].value.replace("tel:+", "")
            if sender != "" and sender != "tel:":
                if sender not in mynumbers and address == "":
                    address = sender
                    break
    fn = ""
    spanxml = xmldoc.getElementsByTagName('span')
    for span in spanxml:
        if span.hasAttribute('class') and span.attributes['class'].value == 'fn' and len(span.childNodes) > 0:
            tmpfn = span.childNodes[0].nodeValue
            if tmpfn != "" and "+" not in tmpfn and address != "":
                fn = tmpfn
            break
    if fn == "":
        c.execute("insert into people (source, fn, address) values ('voice', ?, ?);", (address, address))
    else:
        c.execute("insert or replace into people (id, source, fn, address) values ((select id from people where address = ?), 'voice', ?, ?);", (address, fn, address))

def processVoice(f, c):
    with open(f, mode='r', encoding="utf-8") as myfile:
            data=myfile.read()
    data = data.replace('<br>', '<br/>')
    xmldoc = minidom.parseString(data)
    addresses = []
    address = ""
    axml = xmldoc.getElementsByTagName('a')
    for a in axml:
        if a.hasAttribute('class') and a.attributes['class'].value == 'tel':
            sender = a.attributes['href'].value.replace("tel:+", "")
            if sender != "" and sender != "tel:":
                if sender not in mynumbers and sender not in addresses:
                    addresses.append(sender)
    if len(addresses) == 1:
        address = addresses[0]
    elif len(addresses) > 1:
        for a in sorted(addresses):
            if address != "":
                address = address + ", "
            address = address + a
    if address == "":
        address = os.path.basename(f).split(" - ")[0].replace("+","")
        c.execute("select address from people where fn=?", (address,))
        rows = c.fetchall()
        for row in rows:
            address = row[0]
    divxml = xmldoc.getElementsByTagName('div')
    for div in divxml:
        if div.hasAttribute('class') and div.attributes['class'].value == 'message':
            body = ""
            bodyxml = div.getElementsByTagName('q')
            if len(bodyxml) > 0 and len(bodyxml[0].childNodes) > 0:
                    body = bodyxml[0].childNodes[0].nodeValue
            date = div.getElementsByTagName('abbr')[0].attributes['title'].value
            date = datetime.datetime.strptime(''.join(date.rsplit(':', 1)), "%Y-%m-%dT%H:%M:%S.%f%z")
            utcoffset = date.strftime("%z").replace('0', '')
            date = date + datetime.timedelta(hours=0-int(utcoffset))
            date = date.strftime("%Y-%m-%d %H:%M:%S.%f")
            msgtype = 2
            sender = address;
            axml = div.getElementsByTagName('a')
            for a in axml:
                if a.hasAttribute('class') and a.attributes['class'].value == 'tel':
                    sender = a.attributes['href'].value.replace("tel:+", "")
            if sender not in mynumbers:
                msgtype = 1
            img = ""
            imgxml = div.getElementsByTagName('img')
            if len(imgxml) > 0:
                img = imgxml[0].attributes['src'].value + ".jpg"
            if body is not None and body != "":
                c.execute("insert into messages (source, address, sender, date, body, img, msgtype) values ('voice', ?, ?, ?, ?, '', ?);", (address, sender, date, body, msgtype))
            if img is not None and img != "":
                c.execute("insert into messages (source, address, sender, date, body, img, msgtype) values ('voice', ?, ?, ?, '', ?, ?);", (address, sender, date, img, msgtype))


def processVoiceMedia(d, c):
    encdir = os.fsencode(d)
    for file in os.listdir(encdir):
        img = os.fsdecode(file)
        if img.endswith(".jpg"):
            new = os.path.join(voiceimagesdir,img)
            if not os.path.exists(new):
                orig = os.path.join(d,img)
                move(orig, new)
    

def processSignal(f, c):
    with open(f, mode='r', encoding="utf-8") as myfile:
            data=myfile.read()
    conversationwith = ""
    xmldoc = minidom.parseString(data)
    smsxml = xmldoc.getElementsByTagName('sms')
    for sms in smsxml:
        body = sms.attributes['body'].value
        date = sms.attributes['date_sent'].value
        date = datetime.datetime.utcfromtimestamp(int(date)/1000)
        date = date.strftime("%Y-%m-%d %H:%M:%S.%f")
        address = sms.attributes['address'].value.replace("+", "")
        msgtype = int(sms.attributes['type'].value)
        sender = address
        if msgtype == 2:
            sender = mynumbers[0]
        c.execute("insert into messages (source, address, sender, date, body, img, msgtype) values ('signal', ?, ?, ?, ?, '', ?);", (address, sender, date, body, msgtype))


def processSignalMedia(d, c):
    encdir = os.fsencode(d)
    for file in os.listdir(encdir):
        img = os.fsdecode(file)
        date = os.path.splitext(img)


def loopFilesForPeople():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    directory = os.path.join(backupdir,"watch")
    encdir = os.fsencode(directory)
    for file in os.listdir(encdir):
        filename = os.fsdecode(file)
        fullpath = os.path.abspath(os.path.join(directory,filename))
        if filename.endswith(".zip") and len(mynumbers) > 0:
            print("Processing people: " + filename)
            os.makedirs(tmpdir)
            os.popen("cd " + tmpdir + "; unzip " + fullpath + " *' - Text - '*").read()
            voicedirectory = os.path.join(tmpdir,"Takeout/Voice/Calls")
            voiceencdir = os.fsencode(voicedirectory)
            for voicefile in os.listdir(voiceencdir):
                voicefilename = os.fsdecode(voicefile)
                if voicefilename.endswith(".html"):
                    voicefullpath = os.path.abspath(os.path.join(voicedirectory,voicefilename))
                    print(" - Processing people: " + voicefilename)
                    processVoicePeople(voicefullpath, c)
        if os.path.exists(tmpdir):
            rmtree(tmpdir)
    conn.commit()
    conn.close()


def loopFiles():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    directory = os.path.join(backupdir,"watch")
    encdir = os.fsencode(directory)
    for file in os.listdir(encdir):
        filename = os.fsdecode(file)
        fullpath = os.path.abspath(os.path.join(directory,filename))
        if filename.endswith(".backup") and signalpassword != "":
            print("Processing: " + filename)
            os.makedirs(os.path.join(tmpdir,"images"))
            os.popen("cd " + tmpdir + "; " + signalbackup + " format -f XML -p '" + signalpassword + "' " + fullpath + " > " + tmpdir + "/signal.xml").read()
            os.popen("cd " + tmpdir + "; " + signalbackup + " extract -o images -p '" + signalpassword + "' " + fullpath).read()
            processSignal(os.path.join(tmpdir,'signal.xml'), c)
        if filename.endswith(".zip") and len(mynumbers) > 0:
            print("Processing: " + filename)
            os.makedirs(tmpdir)
            os.popen("cd " + tmpdir + "; unzip " + fullpath + " *' - Text - '* *'Group Conversation - '*").read()
            voicedirectory = os.path.join(tmpdir,"Takeout/Voice/Calls")
            voiceencdir = os.fsencode(voicedirectory)
            for voicefile in os.listdir(voiceencdir):
                voicefilename = os.fsdecode(voicefile)
                if voicefilename.endswith(".html"):
                    voicefullpath = os.path.abspath(os.path.join(voicedirectory,voicefilename))
                    print(" - Processing: " + voicefilename)
                    processVoice(voicefullpath, c)
                    processVoiceMedia(voicedirectory, c)
        if os.path.exists(tmpdir):
            rmtree(tmpdir)
        archivedir = os.path.join(backupdir,"processed")
        move(fullpath, os.path.join(archivedir,filename))
    conn.commit()
    conn.close()


def makeDB():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, address TEXT NOT NULL, sender TEXT NOT NULL, date DATETIME NOT NULL, body TEXT NOT NULL, img TEXT NOT NULL, msgtype INTEGER NOT NULL, UNIQUE(source, address, sender, date, body, img, msgtype) ON CONFLICT IGNORE);")
    c.execute("CREATE TABLE people (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, fn TEXT NOT NULL, address TEXT NOT NULL, UNIQUE(source, fn, address) ON CONFLICT IGNORE);")
    conn.commit()
    conn.close()


def init():
    if os.path.exists(tmpdir):
        rmtree(tmpdir)
    if not os.path.exists(os.path.join(backupdir,"watch")):
        os.makedirs(os.path.join(backupdir,"watch"))
    if not os.path.exists(os.path.join(backupdir,"processed")):
        os.makedirs(os.path.join(backupdir,"processed"))
    if not os.path.exists(voiceimagesdir):
        os.makedirs(voiceimagesdir)
    if not os.path.exists(database):
        makeDB()

mynumbers = []
if args.my_number != "":
    mynumbers.append(args.my_number)
signalbackup = args.signal_back
signalpassword = args.signal_pass
datadir = args.data_dir
tmpdir = "/tmp/message-archive"
backupdir = os.path.join(datadir,"backups")
voiceimagesdir = os.path.join(datadir,"images/voice")
database = os.path.join(datadir,"messages.db")
if signalpassword == "":
    print("Skipping Signal files as signal-back and password were not provided.")
if len(mynumbers) == 0:
    print("Skipping Google Voice files as phone number was not provided.")
init()
loopFilesForPeople()
loopFiles()
