import http.server
import os
from queue import Empty
import socket

import plot
import sql


def getIPAdress():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

def server(q,in_q):
    IP = getIPAdress()
    with http.server.HTTPServer((IP, sql.PORT), make_custom_handler(q,in_q)) as server:
        print ("server started at {0} port {1}".format(getIPAdress(),sql.PORT))
        server.serve_forever()

def make_custom_handler(q,in_q):
    
    class handler(http.server.BaseHTTPRequestHandler):
        force_status = None
        thermostat_status = False
        thermostat_temp = 20

        def __init__(self, *args, **kwargs):
            self.last_api_call = "No changes"
            super(handler, self).__init__(*args, **kwargs)
            
        def do_GET(self):
            self.send_response(200)

            if self.path.endswith(".png"):
                mimetype='image/png'
            elif self.path.endswith(".mp4"):
                mimetype = 'video/mp4'
            else:
                mimetype='text/html'
            self.send_header('Content-type',mimetype)
            self.end_headers()


            if self.path == "/":
                for filename in os.listdir(os.path.abspath('graphs')):
                    file_path = os.path.join(os.path.abspath('graphs'), filename)
                    os.unlink(file_path)
                plot.plt.close('all')
                c_variables = sql.get_last_record('deux')
                f_checked = (lambda x:"AUTO" if x is None else("CURRENTLY ON " if x else "CURRENTLY OFF"))(handler.force_status)
                t_checked = (lambda x:"CURRENTLY ON" if x else "CURRENTLY OFF")(handler.thermostat_status)
                f_color = (lambda x: 'orange' if x is None else('green' if x else 'red'))(handler.force_status)
                t_color = (lambda x: 'green' if x else 'red')(handler.thermostat_status)

                
                display = '<html><body>'
                

                display += '<h3>Current temperature is {} C, humidity {}%, last refresh was {} ago </h3><br/>'.format(\
                    c_variables[0],c_variables[1],c_variables[2])
                display += '<p><b><FONT face="arial"><form method="POST" enctype="multipart/form-data" action="/">'
                display += '<label for="OnOff">FORCE RADIATOR STATUS</label>'
                display += '<input type="hidden" id="OnOff" name="OnOff">'
                display += '<input type="submit" value="{}" style ="background-color:{}"> </form>'.format(f_checked,f_color)

                display += '<form method="POST" enctype="multipart/form-data" action="/">'
                display += '<label for="Thermostat">THERMOSTAT STATUS</label>'
                display += '<input type="hidden" id="Thermostat" name="Thermostat">'
                display += '<input type="submit" value="{}" style ="background-color:{}">'.format(t_checked,t_color)
                display += '<label for="Thermostat">CHOOSE TEMPERATURE : </label>'
                display += '<input type="number" id="Temperature" name="Temperature" min="0" max="40" placeholder="{}"> </form>'.format(\
                    handler.thermostat_temp)
                
                display += '<i>'+self.last_api_call+'</i>'

                display += '<form method="POST" enctype="multipart/form-data" action="/">'
                display += '<input type="datetime-local" id="date-inf" name="date-inf" value="2021-09-10T00:00"> '
                display += '<input type="datetime-local" id="date-sup" name="date-sup" value="2021-10-01T00:00"> '
                display += ' <input type="submit"> </form> <br/>'

                display  += '<a href=\"/graphs/quatre_last.png\">4 dernieres heures quatre</a> <a href=\"/graphs/deux_last.png\">4 dernieres heures deux</a> '
                display += '<a href=\"/graphs/zero_last.png\">4 dernieres heures zero</a> <br/>'

                display += ' <a href="/graphs/quatre_last_step_3.png">12 dernieres heures quatre</a> <a href="/graphs/deux_last_step_3.png">12 dernieres heures deux</a> '
                display += ' <a href="/graphs/zero_last_step_3.png">12 dernieres heures zero</a> <br/>'
                
                display += ' <a href="/graphs/quatre_last_step_12.png">50 dernieres heures quatre</a> <a href="/graphs/deux_last_step_12.png">50 dernieres heures deux</a> '
                display += ' <a href="/graphs/zero_last_step_12.png">50 dernieres heures zero</a> <br/>'

                display += '</FONT></b></p></body></html>'

                self.wfile.write(bytes(display, "utf8"))
            
            elif 'last' in self.path:
                split = self.path.split('_')
                if len(split) == 2:
                    table_name = split[0][8:]
                    plot.make_recent_plot(table_name,50)
                    with open('graphs/{}_last.png'.format(table_name),'rb') as f:
                        self.wfile.write(f.read())
                
                elif len(split) == 4:
                    table_name = split[0][8:]
                    step = int(split[3].split(".")[0])
                    plot.make_recent_step_plots(table_name,step,50)
                    with open('graphs/{0}_last_step_{1}.png'.format(table_name,step),'rb') as f:
                        self.wfile.write(f.read())
            
            elif 'period' in self.path:
                split = self.path.split('_')
                date_sup,date_inf = split[2], split[3][:-4]
                table_name = split[0][1:]
                plot.make_period_plot(table_name,date_sup,date_inf,100)
                with open('graphs/{0}_period_{1}.png'.format(table_name,date_sup),'rb') as f:
                    self.wfile.write(f.read())
            
            elif 'anniv' in self.path:
                with open('Papa_anniv.mp4','rb') as f:
                    self.wfile.write(f.read())


        def do_POST(self):
            content_len = int(self.headers.get('Content-Length'))
            post_body = str(self.rfile.read(content_len))
            if  "OnOff" in post_body:
                if sql.VERBOSE: print("Server handling OnOff")
                if handler.force_status is None:
                    handler.force_status = True
                    q.put("Force On")
                elif handler.force_status:
                    handler.force_status = False
                    q.put("Force Off")
                else:
                    handler.force_status = None
                    q.put("Force Auto")
            elif "Thermostat" in post_body:
                if sql.VERBOSE: print("Server handling Thermostat")
                handler.thermostat_status = not handler.thermostat_status
                try:
                    new_temp = int(post_body.split('Temperature"')[1][8:10])
                    handler.thermostat_temp = new_temp
                except ValueError:pass


                if handler.thermostat_status:
                    q.put("Thermostat On " + str(handler.thermostat_temp))
                else:
                    q.put("Thermostat Off " + str(handler.thermostat_temp))
             
            else:
                date_inf = "20"+post_body.split("\\n20")[1][:14].replace('T',' ')+":00"
                date_sup = "20"+post_body.split("\\n20")[2][:14].replace('T',' ')+":00"
                self.path = "/deux_period_{0}_{1}.png".format(date_sup,date_inf)

            if sql.VERBOSE : print("Server retreving API response")
            try:
                self.last_api_call = in_q.get(timeout=1)
            except Empty:
                self.last_api_call = "Error : no response from thermostat thread"

            if sql.VERBOSE : print("API response : {}".format(self.last_api_call))
            self.do_GET()
    return handler

