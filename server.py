#!/usr/bin/env python3
import socketserver
import urllib.parse
import db
import json


"""
Written by: Raymon Skjørten Hansen
Email: raymon.s.hansen@uit.no
Course: INF-2300 - Networking
UiT - The Arctic University of Norway
May 9th, 2019
"""

# Resources that may not be returned to client
blacklist = ["server.py", "test_client.py"]

# Database for REST API
database = db.Database("messages.db", "messages")


class MyTCPHandler(socketserver.StreamRequestHandler):
    """
    This class is responsible for handling a request. The whole class is
    handed over as a parameter to the server instance so that it is capable
    of processing request. The server will use the handle-method to do this.
    It is instantiated once for each request!
    Since it inherits from the StreamRequestHandler class, it has two very
    usefull attributes you can use:

    rfile - This is the whole content of the request, displayed as a python
    file-like object. This means we can do readline(), readlines() on it!

    wfile - This is a file-like object which represents the response. We can
    write to it with write(). When we do wfile.close(), the response is
    automatically sent.

    The class has three important methods:
    handle() - is called to handle each request.
    setup() - Does nothing by default, but can be used to do any initial
    tasks before handling a request. Is automatically called before handle().
    finish() - Does nothing by default, but is called after handle() to do any
    necessary clean up after a request is handled.
    """
    def handle(self):
        """
        This method is responsible for handling an http-request. You can, and should(!),
        make additional methods to organize the flow with which a request is handled by
        this method. But it all starts here!
        """
        # Read request headers
        req = {}
        line = self.rfile.readline().decode().split()
        req["type"] = line[0]
        req["url"] = line[1]

        # Remove initial '/' from url
        if req["url"] == '/':
            req["url"] = "index.html"
        elif req["url"][:1] == '/':
            req["url"] = req["url"][1:]

        while line:
            req[line[0]] = line[1]
            line = self.rfile.readline().decode().split()

        # Go to correct method handler
        if req["type"] == 'GET':
            self.handleGet(req)
        elif req["type"] == 'POST':
            self.handlePost(req)
        elif req["type"] == 'PUT' and req["url"] == 'messages':
            self.RESTput(req)
        elif req["type"] == 'DELETE' and req["url"] == 'messages':
            self.RESTdelete(req)

        

    def handleGet(self, req):
        """ Handle get request """

        # Handle request to REST API
        if req["url"] == "messages":
            self.RESTget()
            return

        # Check for forbidden requests
        if req["url"] in blacklist:
            self.retForbidden()
            return
        
        if req["url"][:3] == "../":
            self.retForbidden()
            return



        # Read file
        try:
            with open(req["url"], "rb") as f:
                body = f.read()
                length = str(len(body))
        except:
            self.retNotFound()
            return


        # Write response
        self.wfile.write(b"HTTP/1.1 200 OK\r\n" +
                        b"Content-Length: " + bytes(length,'utf8') + b"\r\n" +
                        b"Content-Type: text/html\r\n\r\n" + body)


    def handlePost(self, req):
        """ Handle post request """

        # Handle request to REST API
        if req["url"] == "messages":
            self.RESTpost(req)
            return

        # Must post to test.txt
        if not req["url"] == "test.txt":
            self.retForbidden()
            return

        # Read body
        rlen = int(req["Content-Length:"])
        rbody = self.rfile.read(rlen).decode()
        # Remove url encoding ("text=")
        rbody = urllib.parse.unquote_plus(rbody)[5:]

        # Append body to text file
        with open(req["url"], "a") as f:
            f.write(rbody)

        # Read text file for response
        with open("test.txt", "rb") as f:
            wbody = f.read()
            length = str(len(wbody))

        # Write response
        self.wfile.write(b"HTTP/1.1 200 OK\r\n" +
                        b"Content-Length: " + bytes(length,'utf8') + b"\r\n" +
                        b"Content-Type: text/html\r\n\r\n" + wbody)

    def RESTget(self):
        """ Get all messages and return them """
        data = database.get()
        # Apply correct formatting
        list = []
        for p in data:
            list.append({"id":p[0], "text":p[1]})
        body = json.dumps(list)

        length = str(len(body))

        # Write response
        self.wfile.write(b"HTTP/1.1 200 OK\r\n" +
                        b"Content-Length: " + bytes(length, 'utf8') + b"\r\n" +
                        b"Content-Type: application/json\r\n\r\n" + bytes(body, 'utf8'))

    def RESTpost(self, req):
        """ Insert a new message into database """

        # Read request body
        rlen = int(req["Content-Length:"])
        rbody = self.rfile.read(rlen).decode()
        obj = json.loads(rbody)

        # Return error on no message
        if not "text" in obj:
            self.wfile.write(b"HTTP/1.1 400 BAD REQUEST\r\n\r\n")
            return

        # Insert message into database
        msg = obj["text"]
        database.post(msg)

        # Get ID in database
        data = database.getid(msg)
        # Make sure it is the last added if identicals exist
        ID = data[-1]

        # Write object to return
        body = json.dumps({"id":ID, "text":msg})
        length = str(len(body))

        # Return success
        self.wfile.write(b"HTTP/1.1 201 CREATED\r\n" +
                        b"Content-Length: " + bytes(length, 'utf8') + b"\r\n" +
                        b"Content-Type: application/json\r\n\r\n" + bytes(body, 'utf8'))

    def RESTput(self, req):
        """ Update a message already in the database with a new value """

        # Read request body
        rlen = int(req["Content-Length:"])
        rbody = self.rfile.read(rlen).decode()
        obj = json.loads(rbody)

        # Return error on invalid input
        if not "id" in obj or not "text" in obj:
            self.wfile.write(b"HTTP/1.1 400 BAD REQUEST\r\n\r\n")
            return
        
        # Update message
        database.put(obj["id"], obj["text"])

        # Return success
        self.wfile.write(b"HTTP/1.1 200 OK\r\n\r\n")

    def RESTdelete(self, req):
        """ Delete message with given id """

        # Read request body
        rlen = int(req["Content-Length:"])
        rbody = self.rfile.read(rlen).decode()
        obj = json.loads(rbody)

        # Return error on no id
        if not "id" in obj:
            self.wfile.write(b"HTTP/1.1 400 BAD REQUEST\r\n\r\n")
            return

        # Return error if message does not exist
        if not database.exists(obj["id"]):
            self.wfile.write(b"HTTP/1.1 404 NOT FOUND\r\n\r\n")
            return
        
        # Delete message
        database.delete(obj["id"])

        # Return success
        self.wfile.write(b"HTTP/1.1 200 OK\r\n\r\n")

    def retForbidden(self):
        """ Return status 403 forbidden to client """
        with open("forbidden.html", "rb") as f:
            body = f.read()
            length = str(len(body))

        self.wfile.write(b"HTTP/1.1 403 FORBIDDEN\r\n" +
                        b"Content-Length: " + bytes(length,'utf8') + b"\r\n" +
                        b"Content-Type: text/html\r\n\r\n" + body)

    def retNotFound(self):
        """ Return status 404 not found to client """
        with open("notFound.html", "rb") as f:
            body = f.read()
            length = str(len(body))

        self.wfile.write(b"HTTP/1.1 404 NOT FOUND\r\n" +
                        b"Content-Length: " + bytes(length,'utf8') + b"\r\n" +
                        b"Content-Type: text/html\r\n\r\n" + body)






if __name__ == "__main__":
    HOST, PORT = "localhost", 8080
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        print("Serving at: http://{}:{}".format(HOST, PORT))
        server.serve_forever()
