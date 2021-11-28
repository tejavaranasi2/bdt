from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
import dotenv

def uploadFile(filePath):
    dotenv.load_dotenv('../.env')
    GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = os.getenv("BASE_DIR") + "client_secrets.json"
    g_login = GoogleAuth()
    g_login.LoadCredentialsFile(os.getenv("BASE_DIR") + "creds.txt")
    
    if g_login.credentials is None:
        g_login.LocalWebserverAuth()
    else:
        g_login.Authorize()
    
    g_login.SaveCredentialsFile(os.getenv("BASE_DIR") + "/" + "creds.txt")
    
    drive = GoogleDrive(g_login)
    
    
    with open(filePath, "r") as myFile:
        file_drive = drive.CreateFile({'title': os.path.basename(myFile.name)})
        file_drive.SetContentString(myFile.read())
        file_drive.Upload()
    
    print("The file has been uploaded")

def downloadFile(fileName):
    #TODO: Complete this function
    print("Hello, World")
