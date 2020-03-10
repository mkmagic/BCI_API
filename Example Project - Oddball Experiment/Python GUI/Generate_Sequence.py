import numpy
import os

def generate_sequence(isiTime, BeepDuration, freq1, freq2, nTrialsPerBlock, pFreq):

    # Call create_oddball_sequence_data to generate sequence_data
    sequence_data = create_oddball_sequence_data(pFreq, nTrialsPerBlock)

    # Stimulus info is an array that contains the info of the Stimulus.
    # Stimulus_info[0] = isiTime - time to pause
    # Stimulus_info[1] = BeepDuration - 0.125
    # Stimulus_info[2] = [freq1, freq2] - right now is 1000, 1263
    stimulus_info = [isiTime, BeepDuration, freq1, freq2]

    # Save sequence_data and stimulus_info in files
    f = open('/'.join(os.getcwd().split('\\')[:-1] + ['Sequence_Data', 'Sequence_Data.txt']), 'w')
    data_to_string = ''
    for i in sequence_data:
        for j in i:
            data_to_string = data_to_string + str(j) + ''
        data_to_string = data_to_string + '\n'
    f.write(data_to_string)
    f.close();

    f = open('/'.join(os.getcwd().split('\\')[:-1] + ['Sequence_Data', 'Stimulus_Info.txt']), 'w')
    data_to_string = ''
    for i in stimulus_info:
            data_to_string = data_to_string + str(i) + '\n'
    f.write(data_to_string)
    f.close();

    return stimulus_info, sequence_data

def create_oddball_sequence_data(q1, nTrialsPerBlock):
    seq1 = []
    for OddballProbability in q1:
        OddballSequence = list(numpy.random.choice([1, 0], size=nTrialsPerBlock, p=[OddballProbability, 1 - OddballProbability]))
        seq1 = seq1 + OddballSequence
    sequence_data = [q1, seq1, [nTrialsPerBlock]]
    return sequence_data