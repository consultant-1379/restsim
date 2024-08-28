#!/usr/bin/python -u

import os

from http.server import BaseHTTPRequestHandler, HTTPServer
from services import DoGetService,DoPutService
from response_writer import ResponseWriter
import utils
import sys
sys.path.append('/netsim_users/pms/bin')
import logger_utility


logger = logger_utility.LoggerUtilities()
response =  ResponseWriter()
script_dir = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(script_dir, 'config.ini')
config_map = utils.createConfigMap(config_file)



class Controller(BaseHTTPRequestHandler,DoGetService,DoPutService):

        def do_PUT(self):
            logger.print_info('File upload request acknowledged.')
            content_length = int(self.headers.get('Content-Length'))
            file_name = os.path.basename(self.path)
            read_request_data = self.rfile.read(content_length)
            self.file_upload(content_length,file_name,read_request_data,response,config_map)

        def do_GET(self):
            # Normal On-Demand (Hussain's init requirement).
            if (self.path.startswith('/api/v1/start-pm-generation')):
                logger.print_info('Received pm generation request')
                ROP_IN_SECONDS = int(config_map.get('TIME_PARAMS','ONE_MINUTE')) * int(config_map.get('TIME_PARAMS','ROP_IN_MIN'))
                epoch_token = utils.get_epoch_token(ROP_IN_SECONDS)
                self.support_on_demand_for_default_use_case(epoch_token,response,config_map,ROP_IN_SECONDS)

            # Enable replay mode in Netsim cfg
            elif (self.path.startswith('/api/v1/enable')):
                logger.print_info('Received enable request')
                self.change_modes(self.path,response,config_map,True)
                                            

            # Disbale replay mode in if netsim_cfg
            elif (self.path.startswith('/api/v1/disable')):
                logger.print_info('Received disable request')
                self.change_modes(self.path,response,config_map,False)
                                        

            # Future Rop data/ STATS Calculator (Joe Murphy use case)
            elif (self.path.startswith('/api/v1/start-future-pm-generation')):
                '''
                try:
                    print('INFO : Captured future rop generation request : {}.'.format(self.path))
                    query = urlparse(self.path).query
                    future_rop_value = '1'
                    if len(query) == 5:
                        query_components = parse_qs(query)
                        future_rop_value = query_components['rop'][0]
                    else:
                        print('INFO : Default value 1 has been considered for future rop count.')
                    if future_rop_value.isdigit():
                        future_rop_value = int(math.floor(float(future_rop_value)))
                    else:
                        return self.sendResponse('ERROR : Given future rop count is not digit.', 400, 'text/plain')
                    print('INFO : Captured Future rop count as {} from request.'.format(future_rop_value))
                    if 0 < future_rop_value <= 4:
                        return self.sendResponse('INFO : Call future generation script.', 200, 'text/plain')
                    else:
                        return self.sendResponse('ERROR : Invalid future rop count information given.', 400, 'text/plain')
                except Exception as e:
                    print(e)
                '''
                logger.print_info('Received future rop generation request.')
                ROP_IN_SECONDS = int(config_map.get('TIME_PARAMS','ONE_MINUTE')) * int(config_map.get('TIME_PARAMS','ROP_IN_MIN'))
                epoch_token = utils.get_epoch_token(ROP_IN_SECONDS)
                self.support_on_demand_for_future_rop_use_case(epoch_token,response,config_map,ROP_IN_SECONDS)

            elif (self.path.startswith('/api/v1/check-status')):
                logger.print_info('Received check status request')
                self.check_status(self.path,response,config_map)

            elif (self.path.startswith('/api/v1/check-server-status')):
                return response.sendResponse(self,'INFO : Server up and running', 200, 'text/plain')

            else:
                return response.sendResponse(self,'ERROR : Bad request.', 400, 'text/plain')

try:
    # Create a web server and define the handler to manage the incoming requests
    PORT_NUMBER = config_map.get('REQ_LIS','PORT_NUMBER')
    server = HTTPServer(('', int(PORT_NUMBER)),  Controller)
    logger.print_info('Started http server on port {}'.format(PORT_NUMBER))
    # Wait forever for incoming http requests
    server.serve_forever()
except KeyboardInterrupt:
    logger.print_info('^C received, Stopping server...')
    server.socket.close()