import pandas as pd
import numpy as np
import re
import math
import sys
import os
import calendar
from datetime import datetime
import get_dates

desired_width=320
pd.set_option('display.width', desired_width)
np.set_printoptions(linewidth=desired_width)
pd.set_option('display.max_columns',100)

#
# df = pd.read_csv("/home/nonu/Desktop/data_/BN_FUT/_2020-01-01/BANKNIFTY-I.csv")
# print(df)

def SLhit(SL,Low,High,typeoftrade):
    if typeoftrade == "B":
        return Low<=SL
    else:
        return High>=SL
def extract_time(timestamp):
    pattern = "(\d{2}:\d{2})"
    result = re.findall(pattern,timestamp)
    return result[0]


loc = "/home/nonu/Desktop/data_/BN_FUT/"
dates = get_dates.get_dates()

l=[]

type_of_trade = "N"
intrade = False
SL = 0
entry = 0
prev_week_high = 0
curr_week_high = 10000000
prev_week_low = 0
curr_week_low = 0
curr_week_number = 1
prev_week_number = 0
pnl = 0

for date in dates:
    df = pd.read_csv(loc+date+"/"+"BANKNIFTY-I.csv")
    Day = df.at[1,'day_of_week']
    isexpiry = get_dates.check_expiry(df.at[1,"datetime"],df.at[1,"expiry_date"])
    curr_week_number = df.at[1,"week_number"]

    metadata = {"Date":date,"Day":Day,"High":0,"Low":0,"Close":0,
                "PrevWeeKLow":prev_week_low,"PrevWeekHigh":prev_week_high,
                "InTrade":intrade,"TypeOfPosition":type_of_trade,
                "Entry":entry,"StopLoss":SL, "posValue":0,"BookedPNL":pnl,"NetVal":0}
    High = 0
    Low = 100000

    if curr_week_number!=prev_week_number:
        prev_week_number = curr_week_number
        prev_week_high = curr_week_high
        curr_week_high = 0
        prev_week_low = curr_week_low
        curr_week_low = 100000000000

    for idx,row in df.iterrows():
        Time = extract_time(row["datetime"])
        L = row["low"]
        H = row["high"]
        O = row["open"]
        C = row["close"]

        ###-------------exit conditions----------#####
        if intrade:
            if SLhit(SL,L,H,type_of_trade):########Stoploss Hit##########
                intrade = False
                if type_of_trade == "B":
                    if SL<O:
                        pnl+=SL-entry
                    else:
                        pnl+=O-entry
                elif type_of_trade == "S":
                    if SL>0:
                        pnl+=entry-O
                    else:
                        pnl+=entry-SL
                type_of_trade = "N"
                SL = 0
                entry = 0

            elif Day=="Friday" and Time=="15:29": ############ on friday the entry condition is met #############
                if type_of_trade=="B":
                    if C<prev_week_low:
                        pnl+=C-entry
                        type_of_trade = "S"
                        entry = C
                        SL = entry + entry*0.02
                elif type_of_trade=="S":
                    if C>prev_week_high:
                        pnl+=entry-C
                        type_of_trade = "B"
                        entry = C
                        SL = entry - entry*0.02

            elif isexpiry and Time=="15:29":  ###########rollover on thursday ###################3
                df2 = pd.read_csv(loc + date + "/" + "BANKNIFTY-II.csv")
                new_entry = df2["open"].iloc[-1]
                if type_of_trade == "S":
                    pnl+=new_entry-O
                elif type_of_trade == "B":
                    pnl+=O-new_entry

        elif not intrade:
            if Day=="Friday" and Time=="15:29":
                if C < prev_week_low:
                    type_of_trade = "S"
                    entry = C
                    SL = entry + entry * 0.02
                    intrade = True
                elif C>prev_week_high:
                    type_of_trade = "B"
                    entry = C
                    SL = entry - entry * 0.02
                    intrade = True

        curr_week_high = max(curr_week_high,H)
        curr_week_low = min(curr_week_low,L)
        High = max(H,High)
        Low = min(Low,L)
        metadata["Close"] = C
    metadata["BookedPNL"] = pnl
    metadata["High"] = High
    metadata["Low"] = Low
    metadata["InTrade"] = intrade
    metadata["TypeOfPosition"] = type_of_trade
    metadata["Entry"] = entry
    metadata["StopLoss"] = SL
    metadata["PrevWeeKLow"] = prev_week_low
    metadata["PrevWeekHigh"] = prev_week_high
    if type_of_trade == "N":
        metadata["posValue"] = 0
    elif type_of_trade == "B":
        metadata["posValue"] = metadata["Close"] - metadata["Entry"]
    else:
        metadata["posValue"] = metadata["Entry"] - metadata["Close"]

    metadata["NetVal"] = metadata["posValue"] + metadata["BookedPNL"]
    print(metadata)
    l.append(metadata)


print(pnl)
df = pd.DataFrame(l)
print(df)
df.to_excel("/home/nonu/Desktop/data_/"+"WeeklyPosSys.xlsx")



