import sys
import os
sys.path.insert(0, '/'.join(os.getcwd().split('\\')[:-2])) # Add 'unity_smi_bci' to the PATH
import time
from Python_Client.Client import Transmitter, Receiver # Import server API
from Generate_Sequence import *  # Import functions to generate oddball sequence




#________________________________ connection paths  ________________________________#

EXPERIMENT_CONTROL_PATH_HOST, EXPERIMENT_CONTROL_PATH_PORT = '10.0.0.1', 4010
STIMULUS_PATH_HOST, STIMULUS_PATH_PORT = '10.0.0.1', 8010
USER_CONTROL_PATH_HOST, USER_CONTROL_PATH_PORT = '10.0.0.1', 7011
SUBJECTS_RESPONSE_PATH_HOST, SUBJECTS_RESPONSE_PATH_PORT = '10.0.0.1', 9011


class GUIObject:

    def __init__(self, isiTime, Beep_Duration, freq1, freq2, n_trials_per_block, pFreq, file_location):
        # Data Sockets
        self.GuiControlSender = Transmitter(EXPERIMENT_CONTROL_PATH_HOST,
                                            EXPERIMENT_CONTROL_PATH_PORT,
                                            'GUI Control Sender',
                                            'UDP')
        self.SendStimulus = Transmitter(STIMULUS_PATH_HOST,
                                        STIMULUS_PATH_PORT,
                                        'Sound and Trigger Sender',
                                        'UDP')
        self.PauseReceiver = Receiver(USER_CONTROL_PATH_HOST,
                                      USER_CONTROL_PATH_PORT,
                                      'Sound and Trigger Sender',
                                      'UDP')
        self.UserDataRecord = Receiver(SUBJECTS_RESPONSE_PATH_HOST,
                                       SUBJECTS_RESPONSE_PATH_PORT,
                                       'User Data Record',
                                       'UDP')

        # Generate Sequence Data and Stimulus Info
        self.stimulus_info, self.sequence_data = generate_sequence(isiTime, Beep_Duration, freq1, freq2, n_trials_per_block, pFreq)

        # Set flag to wait for start command from Unity player
        self.startCommand = False

        # Create list to save User's response time
        self.ResponseTimeList = []

        # Set location in which Response Time file will be saved
        self.file_location = file_location

    def start(self):
        # Connect Data Sockets
        self.GuiControlSender.connect(True)
        self.SendStimulus.connect(True)
        self.PauseReceiver.connect(True)
        self.UserDataRecord.connect(True)

        # Get sequence and time to wait between beeps from sequence data
        sequence = self.sequence_data[1]
        time_between_beeps = self.stimulus_info[0] + (self.stimulus_info[1] / 1000)
        nTrialsperBlock = self.sequence_data[2][0]

        # Open UserDataRecord and listen for data entries
        self.UserDataRecord.listen(self.RecordUserResponse)

        # Wait for start message and then send command to start experiment
        self.PauseReceiver.listen(self.StartReceived)
        while not self.startCommand:
            pass

        self.GuiControlSender.send('VariablePassing StimulusDuration ' + str(self.stimulus_info[1]))
        self.GuiControlSender.send('start')
        print('start')
        time.sleep(20)

        # Run through sequence
        for i in range(len(sequence)):
            if sequence[i] == 0:  # Not oddball
                self.SendStimulus.send('10')
                print('1')
            elif sequence[i] == 1:  # Oddball, send trigger
                self.SendStimulus.send('20')
                print('0')

            if (i+1) % nTrialsperBlock == 0 and (i+1) != len(sequence):
                # Pause after each block and wait for user to continue
                self.GuiControlSender.send('EndOfBlock')
                self.startCommand = False
                self.PauseReceiver.listen(self.HandlerFunc)
                while not self.startCommand:
                    pass
                continue

            time.sleep(time_between_beeps)

        self.GuiControlSender.send('EndOfExperiment')
        self.SaveData(time.strftime('%Y-%m-%d_%H:%M:%S_', time.localtime()) + 'oddball_response_time_' + input('Enter file name for Response Time data: '))

    def HandlerFunc(self,data):
        print('Next Block')
        self.startCommand = True
        self.GuiControlSender.send('start')
        time.sleep(3)

    def StartReceived(self,data):
        self.startCommand = True

    def SendStimulus(self):
        print('Sending Stimulus')
        self.SendStimulus.send('Stimulus')

    def RecordUserResponse(self,data):
        srt = [float(x) for x in data[1].split()]
        self.ResponseTimeList.append(srt)


    def SaveData(self,file_name):
        f = open(self.file_location + file_name + '.txt', 'w+')
        total = 0
        count = 0
        for data in self.ResponseTimeList:
            # Write to Response Time file
            line = ' '.join([str(i) for i in data]) + '\n'
            f.write(line)

            # Track average Response Time
            if data[1] != -1:
               total += data[1]
               count += 1

        print('The average Response time was: ' + str(total / count))
        f.close()
