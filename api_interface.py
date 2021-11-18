import requests

# constants of connection to Netatmo (Legrand) API
API_URL = "https://api.netatmo.com/api/"
CLIENT_ID  =""
CLIENT_SECRET = ""
GRANT_TYPE = ""
API_USERNAME = ""
API_PASSWORD = ""
HOME_ID = ""
BRIDGE_ID = ""
CONTACTORS_ID = []

class API_Interface():
    def __init__(self):
        self.session = requests.Session()
        self.__token = ""
        self.__refresh_token = ""
        self.get_token()

    def get_token(self):
        data = {'client_id':CLIENT_ID,"client_secret":CLIENT_SECRET,\
            "grant_type":GRANT_TYPE,"username":API_USERNAME,\
                "password":API_PASSWORD}
        response = self.session.post("https://api.netatmo.com/oauth2/token",params=data)
        self.__token = response["access_token"]
        self.__refresh_token = response["refresh_token"]
        self.session.headers.update({'Authorization':'Bearer {}'.format(self.__token)})

    
    def refresh_token(self):
        data = {'client_id':CLIENT_ID,"client_secret":CLIENT_SECRET,\
            "grant_type":GRANT_TYPE,"refresh_token":self.__refresh_token}
        response = self.session.post("https://api.netatmo.com/oauth2/token",params=data)
        self.__token = response["access_token"]
        self.__refresh_token = response["refresh_token"]
        self.session.headers.update({'Authorization':'Bearer {}'.format(self.__token)})


    def send_request(self,data,endpoint_url):
        response = self.session.get(API_URL + endpoint_url, params=data)
        return self.status_code_analyse(response),response.json()

    def send_post(self,data,endpoint_url):
        response = self.session.post(API_URL + endpoint_url,params=data)
        return self.status_code_analyse(response), response.json()

    def status_code_analyse(self,response):
        try:
            response.raise_for_status()
            return True
        except requests.exceptions as e:
            print(e)
            self.__refresh_token()
            return False
    
    def get_modules(self):
        return self.send_request({'home_id':HOME_ID})["body"]["home"]["modules"]
    
    def set_module(self,id,new_state):
        data = {"home":{"id":HOME_ID,\
            "modules":[{"id":id,"on":new_state,"bridge":BRIDGE_ID}]}}
        return self.send_post(data,"setstate")