
classdef MsgClient
    properties
        serverHost;
        serverPort;
        name;
        
        isAsyncRead;
        
        TCPSocket;
        UDPSocket;
        
        
        TIMEOUT = 0.1; %Checks if there is new data in the tcp buffer every 0.1 time.
    end
    
    
    
    
    methods
        %**
        % function constructor.
        %**
        function obj = MsgClient(sHost, sPort, cname, isAsyncRead)
            obj.serverHost = sHost;
            obj.serverPort = sPort;
            obj.name = cname;
            
            % Check if object is set to read data Asynchronously
            if exist('isAsynceRead', 'var')
                obj.isAsyncRead = isAsyncRead;
            else
                obj.isAsyncRead = 0;
            end
            
%             availablePort = hdldaemon('socket', 0); % new available port
%             
%             LocalPort = str2num(availablePort.ipc_id); % convert port to scalar
            
            obj.TCPSocket = tcpip(sHost, sPort);
            
            obj.UDPSocket = udp(sHost, sPort);
            
            set(obj.UDPSocket, 'TimeOut',10);
        end
        
        %**
        % function destructor. Destructs all the object sockets
        %**
        function close(obj)
            
            echotcpip('off');
            fclose(obj.TCPSocket);
            delete(obj.TCPSocket);
            
            echoudp('off');
            fclose(obj.UDPSocket);
            delete(obj.UDPSocket);
        end
        
        
        %**
        % the function connect to the server that it's settings were given
        % in the object constructor.
        %**
        function connectToClient(obj)
            try
                fopen(obj.TCPSocket); %Connect to TCP server
                fopen(obj.UDPSocket); %Connect to UDP server
                
                welcomeMessage = strcat(datestr(now,'yyyy-mm-dd HH:MM:SS.FFF') ,strcat('000;',obj.name));
                fwrite(obj.TCPSocket,uint8(welcomeMessage)); %sends the welcome message
                
                disp('message written');
                
                while(1) %waits for data messages
                    if(obj.TCPSocket.BytesAvailable)
                        message = fscanf(obj.TCPSocket); % waiting until get connesction success message
                        disp(char(message));
                        break;
                    end
                end
                disp('CONNECTION SUCCEEDED');
            catch e
                obj.close()
                throw(e);
            end
            
            % Set object to read data Asynchronously if it is set to do so
            if obj.isAsyncRead
                obj.UDPSocket.ReadAsyncMode = 'continuous';
                obj.UDPSocket.readasync;
            end
            
        end % connectToClient function
        
        
        %**
        % the function listen to the server that it's settings were given
        % in the object constructor only if this object is connected.
        %**
        function listen(obj,handlerFunc)
            % try
            while(1)
                if(obj.UDPSocket.BytesAvailable) %Wait for message and convert it to a string
                    message = fread(obj.UDPSocket);
                    message2string = cellstr(char(message)');
                    message2string = message2string{1};
                    
                    % parse message and stop if the message is close
                    messageArr = strsplit(message2string,';');
                    messageTime = messageArr{1}; % Extract the time the message was sent
                    messageData = strsplit(messageArr{2},'$');
                    messageData = messageData{1}; % Extract only the message data
                    
                    % Stop listening if message is 'close'
                    if(strcmp(messageData,'close'))
                        break;
                    end
                    
                    % Send the message data to the handler function and
                    % display it on the screen
                    handlerFunc(messageData);
                    % fprintf('message received: %s \n', messageData);
                    break;
                end
            end
            
        end
        
        %**
        % the function sends data to the server only if this object is
        % connected to it.
        % @return logical boolean value. true in success and false
        % otherwise.
        %**
        function sendData(obj, data, protocol)
            msg = strcat(datestr(now,'yyyy-mm-dd HH:MM:SS.FFF') ,strcat('000;',data),'$@$');
            if exist('protocol','var') % Check if protocl is set
                if strcmp(protocol, 'TCP') % to TCP
                    fwrite(obj.TCPSocket,uint8(msg));
                else
                    fwrite(obj.UDPSocket,uint8(msg)); % else send using UDP
                end
            else
                fwrite(obj.UDPSocket,uint8(msg));    % else send using UDP   
            end
            
            disp(strcat(msg));
        end % send data function
        
        
        
        % Function to check if data is available
        function data = listenAsync(obj)
            try
                if obj.UDPSocket.BytesAvailable
                    % Parse message
                    message = fscanf(obj.UDPSocket);
                    message_data = strsplit(message, ';');
                    message_data = strsplit(message_data{2},'$');
                    
                    data = message_data{1};
                else
                    data = 0;
                end
            catch
                obj.close();
                throw(e);
            end
        end
    end % method
end % class