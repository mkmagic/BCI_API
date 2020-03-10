from tkinter import *
from tkinter import simpledialog
from tkinter import filedialog
from GUIObject import GUIObject
from threading import Thread
import time


class GUI:

    def __init__(self, master):
        self.master = master
        master.title("BMI Lab")

        self.SessionObject = None  # SessionObject is the GUIObject for the session
        self.SessionThread = None  # SessionThread will be the main thread for running the experiment
        self.file_location = 'Documents'  # file_location will hold the desired location
                                            # to save the data files.
        # Build GUI layout #
        self.header = Label(self.master,
                       justify=CENTER,
                       text=""" Welcome to P300 training game!""",
                       font="helvetica 16 bold").grid(row=0, columnspan=2)

        Label(self.master, text="isiTime in seconds: ", ).grid(row=1)
        Label(self.master, text="Stimulus Duration in ms: ", ).grid(row=2)
        Label(self.master, text="High Beep frequency: ", ).grid(row=3)
        Label(self.master, text="Low Beep frequency: ", ).grid(row=4)
        Label(self.master, text="Number of trials per block: ").grid(row=5)
        Label(self.master, text="Oddball Frequency: ").grid(row=6)

        self.isiTime_entry = Entry(self.master)
        self.Beep_Duration_entry = Entry(self.master)
        self.freq1_entry = Entry(self.master)
        self.freq2_entry = Entry(self.master)
        self.n_trials_per_block_entry = Entry(self.master)
        self.pFreq_entry = Entry(self.master)

        self.isiTime_entry.grid(row=1, column=1)
        self.Beep_Duration_entry.grid(row=2, column=1)
        self.freq1_entry.grid(row=3, column=1)
        self.freq2_entry.grid(row=4, column=1)
        self.n_trials_per_block_entry.grid(row=5, column=1)
        self.pFreq_entry.grid(row=6, column=1)

        # Insert default values to entry fields #
        self.isiTime_entry.insert(0, '1')
        self.Beep_Duration_entry.insert(0, '130')
        self.freq1_entry.insert(0, '1000')
        self.freq2_entry.insert(0, '1263')
        self.n_trials_per_block_entry.insert(0, '240')
        self.pFreq_entry.insert(0, '0.3')

        # Control Buttons #
        self.quit_button = Button(self.master,
                             text="QUIT",
                             fg="red", width=25,
                             command=quit).grid(row=7, column=0)

        self.start_button = Button(self.master,
                              text="START",
                              fg="green", width=25,
                              command=self.start).grid(row=7, column=1)
        self.Stimulus_button = Button(self.master,
                                 text = "ADD STIMULUS",
                                 fg="blue", width = 25,
                                 command = self.send_stimulus).grid(row = 8, column = 0)
        self.save_button = Button(self.master,
                                 text = "SAVE DATA",
                                 fg="red", width = 25,
                                 command = self.save_data).grid(row = 8, column = 1)
        self.save_location_button = Button(self.master,
                                           text = 'OPEN LOCATION TO SAVE FILES',
                                           command = self.open_location).grid(row = 9, columnspan = 2)


    # Function to start session #
    def start(self):
        self.SessionObject = GUIObject(float(self.isiTime_entry.get()),
                                        float(self.Beep_Duration_entry.get()),
                                        float(self.freq1_entry.get()),
                                        float(self.freq2_entry.get()),
                                        int(self.n_trials_per_block_entry.get()),
                                        [float(s) for s in self.pFreq_entry.get().split()],
                                        self.file_location)

        # Start session on a thread
        self.SessionThread = Thread(target=self.SessionObject.start)
        self.SessionThread.daemon = True # Thread will stop if main thread ends
        self.SessionThread.start()


    def send_stimulus(self):
        self.SessionObject.SendStimulus()

    def save_data(self):
        file_name = time.strftime('%Y-%m-%d_%H:%M:%S_', time.localtime()) + \
                    'Oddball_response_time_' + simpledialog.askstring('Save Data',
                                                                 'Enter a name for the data file:',
                                                                 parent=self.master)
        try:
            self.SessionObject.SaveData(file_name)
        except AttributeError:
            print('Session has not yet started!')

    def open_location(self):
        self.file_location = filedialog.askdirectory(title = 'Select folder where data files will be saved')
def main():
        root = Tk()
        app = GUI(root)
        root.mainloop()

if __name__ == '__main__':
    main()