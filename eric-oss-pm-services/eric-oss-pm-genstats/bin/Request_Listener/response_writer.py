
class ResponseWriter:
    def sendResponse(self,responseWriter,res , status,type):
        responseWriter.send_response(status)
        responseWriter.send_header('Content-type',type)
        responseWriter.end_headers()
        responseWriter.wfile.write(bytes(res + '\n', 'utf-8'))

response_writer_instance = ResponseWriter()
