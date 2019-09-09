#!/usr/local/bin/python3

import paramiko, os, time, subprocess, getpass
from PySide2 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QCheckBox
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QFileDialog, QTextEdit
from ui import Ui_main

version = 'Build 10'
serversFile = 'servers.txt'
user = getpass.getuser()

try:
    servers = [line.rstrip('\n') for line in open(serversFile,'r')]
except FileNotFoundError:
    servers = None

def sshBackup(server, user, passwd, command):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_key = '/Users/'+user+'/.ssh/cisco.key'

    try:
        open(ssh_key, 'r')
        ssh.connect(server, username=user, key_filename=ssh_key, allow_agent=True, look_for_keys=True, passphrase=None)
        _, stdout, _ = ssh.exec_command(command)
        result = stdout.read().decode('ascii').strip("\n")
        ssh.close()    
        return result
    except FileNotFoundError:
        ssh.connect(server, username=user, password=passwd, allow_agent=True, look_for_keys=True, passphrase=None)
        _, stdout, _ = ssh.exec_command(command)
        result = stdout.read().decode('ascii').strip("\n")
        ssh.close()    
        return result
    except paramiko.AuthenticationException:
        result = "Authentication failed, please verify your credentials"
        return result
    except paramiko.SSHException as sshException:
        return sshException

def sshConnect(server, user, passwd, command):
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_key = '/Users/'+user+'/.ssh/cisco.key'

    try:
        open(ssh_key, 'r')
        ssh.connect(server, username=user, key_filename=ssh_key, allow_agent=True, look_for_keys=True, passphrase=None)
        channel = ssh.invoke_shell()
        channel.send(command+"\n")
        time.sleep(1)
        result = channel.recv(9999).decode('ascii').strip("\n")
        ssh.close()    
        return result
    except FileNotFoundError:
        ssh.connect(server, username=user, password=passwd, allow_agent=True, look_for_keys=True, passphrase=None)
        channel = ssh.invoke_shell()
        channel.send(command)
        time.sleep(1)
        result = channel.recv(9999).decode('ascii').strip("\n")
        ssh.close()    
        return result
    except paramiko.AuthenticationException:
        result = "Authentication failed, please verify your credentials"
        return result
    except paramiko.SSHException as sshException:
        return sshException

class App(Ui_main.Ui_MainWindow, QtWidgets.QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        
        if servers is None:
            QtWidgets.QMessageBox().warning(self, "Server File Not Found", "The Server's file was not found in the path; Exiting now",QtWidgets.QMessageBox.Ok)
            exit()
        else:
            self.setupUi(self)
            self.setWindowTitle("GPVA - "+version)
            self.populateUser()
            self.populateServer()
            self.actionReloadServerList.triggered.connect(self.reloadServersList)
            self.reloadServers.clicked.connect(self.reloadServersList)
            self.send.clicked.connect(self.submitBotton)
            self.exit.clicked.connect(self.exitBotton)
            self.clear.clicked.connect(self.clearBotton)
            self.actionClose.triggered.connect(self.exitBotton)
            self.actionOpen.triggered.connect(self.openFile)
            self.actionSave.triggered.connect(self.fileSave)
            self.actionBackup.triggered.connect(self.confBackup)
            self.actionNotes.triggered.connect(self.openReadme)
            self.actionEditServer.triggered.connect(self.editServer)    
    
    def populateUser(self):
        self.username.setText(user)
        
    def populateServer(self):
        self.server_list.clear()
        self.server_list.addItems(servers)

    def reloadServersList(self):
        global servers
        try:
            servers = [line.rstrip('\n') for line in open(serversFile,'r')]
            self.populateServer()
        except FileNotFoundError:
            servers = None

    def submitBotton(self):
        server = str(self.server_list.currentText())
        user = self.username.text()
        passwd = self.password.text()
        argument = self.argument.toPlainText()
        if not user:
            QtWidgets.QMessageBox.about(self, "Username Required", "You must provide a Username")    
        elif not argument:
            QtWidgets.QMessageBox.about(self, "Argument Required", "You must provide an argument or command")    
        else:
            status = self.all.isChecked()
            if (status == True):
                self.output.clear()
                for e in servers:
                    command = sshConnect(e,user,passwd,argument)
                    self.output.insertPlainText("Server: "+e)
                    self.output.insertPlainText(command)
                    self.output.insertPlainText("\n\n")
            else:
                self.output.clear()
                command = sshConnect(server,user,passwd,argument)
                self.output.insertPlainText(command)
    
    def clearBotton(self):        
        self.output.clear()
        
    def exitBotton(self):
        exit()
    
    def openFile(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '/Users/')
        if filename[0]:
            name = open(filename[0],'r')
            with name:
                text = name.read()
                self.argument.insertPlainText(text)    
    
    def fileSave(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File')
        if filename[0]:
            name = open(filename[0],'w')
            text = self.output.toPlainText()
            name.write(text)
            name.close()
    
    def confBackup(self):
        self.output.clear()
        self.output.insertPlainText("Attempting to create backup directory..."+'\n')
        
        try:
            os.mkdir("backup")
        except FileExistsError:
            self.output.insertPlainText("Backup directory already exists \n\n")
        now = time.strftime("%m-%d-%Y_%H-%M")
        try:
            os.mkdir("backup/"+now)
        except FileExistsError:
            self.output.insertPlainText(now+" directory already exists \n\n")
        
        user = self.username.text()
        password = self.password.text()
        
        if not user:
            QtWidgets.QMessageBox.about(self, "Username Required", "You must provide a Username")    
        else:
            for e in servers:
                backup = sshBackup(e,user,password,"show running-config")
                if backup is not None:
                    self.output.insertPlainText("Backup done in Network Device "+e+"\n")
                    name = open("backup/"+now+"/"+e+'.txt','w')
                    name.write(backup)
                    name.close()
                else:
                    self.output.insertPlainText("Backup failed in Network Device "+e+"\n")

    def editServer(self):
        global servers
        subprocess.call(['open','-a','TextEdit',serversFile])
        servers = [line.rstrip('\n') for line in open(serversFile,'r')]
        
    def openReadme(self):
        name = open('README.MD','r')
        if name is not None:
            text = name.read()
            self.output.insertPlainText(text) 
        else:
            text = "Fail to read README file"
            self.output.insertPlainText(text) 
    
if __name__ == '__main__':
    app = QtWidgets.QApplication()
    qt_app = App()
    qt_app.show()
    app.exec_()