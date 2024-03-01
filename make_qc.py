import clr
import os
import sys
from tqdm import tqdm
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import warnings
warnings.filterwarnings('ignore')



sys.path.append("/usr/bin/mono")  # Adjust this path to Mono's installation directory

import pythonnet
pythonnet.set_runtime("/usr/bin/mono") 

# Set the base path to where the RawFileReader repository is cloned in the Docker container
base_path = '/RawFileReader'

# Update the paths to the DLL files based on the RawFileReader repository location in the Docker container
clr.AddReference(os.path.join(base_path, 'Libs/Net471/ThermoFisher.CommonCore.Data.dll'))
clr.AddReference(os.path.join(base_path, 'Libs/Net471/ThermoFisher.CommonCore.RawFileReader.dll'))
clr.AddReference(os.path.join(base_path, 'Libs/Net471/ThermoFisher.CommonCore.BackgroundSubtraction.dll'))
clr.AddReference(os.path.join(base_path, 'Libs/Net471/ThermoFisher.CommonCore.MassPrecisionEstimator.dll'))

# Continue with the rest of your script imports
from System import *
from System.Collections.Generic import *
from ThermoFisher.CommonCore.Data import ToleranceUnits, Extensions
from ThermoFisher.CommonCore.Data.Business import ChromatogramSignal, ChromatogramTraceSettings
from ThermoFisher.CommonCore.Data.Business import DataUnits, Device, GenericDataTypes, SampleType, Scan, TraceType
from ThermoFisher.CommonCore.Data.FilterEnums import IonizationModeType, MSOrderType
from ThermoFisher.CommonCore.Data.Interfaces import IChromatogramSettings, IScanEventBase, IScanFilter, RawFileClassification
from ThermoFisher.CommonCore.MassPrecisionEstimator import PrecisionEstimate
from ThermoFisher.CommonCore.RawFileReader import RawFileReaderAdapter


def ReadScanInformation(rawFile, firstScanNumber, lastScanNumber):
    print('extract data')
    time_ms, current_ms, ms_type = [], [], []
    #time_ms2, current_ms2 = [], []
    for scanIndex, scan in enumerate(tqdm(range(firstScanNumber, lastScanNumber))):
        time = rawFile.RetentionTimeFromScanNumber(scan)
        scanFilter = IScanFilter(rawFile.GetFilterForScanNumber(scan))

        # Common operations for both MS1 and MS2
        scanStatistics = rawFile.GetScanStatsForScanNumber(scan)
        segmentedScan = rawFile.GetSegmentedScanFromScanNumber(scan, scanStatistics)
        total_current = np.sum(segmentedScan.Intensities)

        time_ms.append(time)
        current_ms.append(total_current)
        ms_type.append(scanFilter.MSOrder)
    print('end extract data')
    return time_ms, current_ms, ms_type


def plot_ms_cycle_time_and_total_current(df, out_path, instrument_name=None):

    # Set up the plot layout
    fig, axes = plt.subplots(figsize=(16, 8), ncols=2, nrows=2)
    axes = axes.flatten()

    # Filter the DataFrame for MS1 and MS2 data and calculate cycle times
    ms1 = df[df['MS'] == 'Ms'].copy()
    ms1.loc[:, 'cycle_time'] = ms1['RT'] - ms1['RT'].shift(1)

    ms2 = df[df['MS'] == 'Ms2'].copy()
    ms2.loc[:, 'cycle_time'] = ms2['RT'] - ms2['RT'].shift(1)

    # Plot cycle time by RT_bin for MS1 and MS2
    ms1.groupby('RT_bin')['cycle_time'].mean().reset_index().plot(kind='line', x='RT_bin', y='cycle_time', ax=axes[0], label='MS1')
    ms2.groupby('RT_bin')['cycle_time'].mean().reset_index().plot(kind='line', x='RT_bin', y='cycle_time', ax=axes[1], label='MS2')

    # Plot total current by RT_bin for MS1 and MS2
    ms1.groupby('RT_bin')['total_current'].mean().reset_index().plot(kind='line', x='RT_bin', y='total_current', ax=axes[2], label='MS1')
    ms2.groupby('RT_bin')['total_current'].mean().reset_index().plot(kind='line', x='RT_bin', y='total_current', ax=axes[3], label='MS2')

    # Optionally print the instrument name if provided
    if instrument_name:
        plt.title('Instrument name: {}'.format(instrument_name))
    plt.savefig(os.path.join(out_path+'.png'))




if __name__ == '__main__':
    # The first argument after the script name is the path to the RAW file
    raw_file_path = sys.argv[1]
    rawFile = RawFileReaderAdapter.FileFactory(raw_file_path)
    rawFile.SelectInstrument(Device.MS, 1)

    firstScanNumber = rawFile.RunHeaderEx.FirstSpectrum
    lastScanNumber = rawFile.RunHeaderEx.LastSpectrum

    startTime = rawFile.RunHeaderEx.StartTime
    endTime = rawFile.RunHeaderEx.EndTime
    print('startTime':, startTime, 'endTime:', endTime, 'RAW file')
    time_list = ReadScanInformation(rawFile, firstScanNumber, lastScanNumber)

    df = pd.DataFrame()
    df['RT']=time_list[0]
    df['total_current']=time_list[1]
    df['MS']=time_list[2]
    df['MS']=df['MS'].astype(str)
    df['RT_bin']=df['RT'].astype(int)

    instrument_name = rawFile.GetInstrumentData().Name
    plot_ms_cycle_time_and_total_current(df, raw_file_path, instrument_name=instrument_name)
    print('All done')