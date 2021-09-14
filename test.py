from http.server import BaseHTTPRequestHandler, HTTPServer
from queue import Queue
from threading import Thread



class handler(BaseHTTPRequestHandler):
    t_status = False
    def do_GET(self):
        checked = (lambda x:["checked",""] if x else ["","checked"])(self.t_status)
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        display = '<html><body>'
        display += '<h1>Choix<h1>'
        display += '<p><h3><form method="POST" enctype="multipart/form-data" action="/">'
        display += '<div><input name= "OnOff" type="radio" value="On"{}>ON</div>'.format(checked[0])
        display += '<div><input name= "OnOff" type="radio" value="Off"{}>OFF</div>'.format(checked[1])
        display += '<input type="submit">'
        display += '</form></h3></p></body></html>'
        

        self.wfile.write(bytes(display, "utf8"))
        
    def do_POST(self):
        
        content_len = int(self.headers.get('Content-Length'))
        post_body = str(self.rfile.read(content_len))
        post = post_body.split("OnOff")[1]
        if "On" in post:
            self.t_status = True
        elif "Off" in post:
            self.t_status = False
        q.put(self.t_status)
        self.do_GET()
        #self.wfile.write(bytes(post_body, "utf8"))





# A thread that produces data
def server(out_q):
    with HTTPServer(('localhost', 800), handler) as server:
        print ("serving at port 8000")
        server.serve_forever()
          
# A thread that consumes data
def automation(in_q):
    while True:
        print(in_q.get())
          
# Create the shared queue and launch both threads
q = Queue()
t1 = Thread(target = server, args =(q, ))
t2 = Thread(target = automation, args =(q, ))
t1.start()
t2.start()
