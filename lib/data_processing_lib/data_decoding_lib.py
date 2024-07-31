import numpy as np
import csv
import os

def valid_checksum(byte_object_in, flag):
    packetSum = 0
    cks = 0
    if flag == '04':
        cks = int(byte_object_in[42:44].hex(), 16)
        for index in range(0, 42):
            packetSum = packetSum + byte_object_in[index]
    elif flag == '05':
        cks = int(byte_object_in[56:58].hex(), 16)
        for index in range(0, 56):
            packetSum = packetSum + byte_object_in[index]
    elif flag == '06':
        cks = int(byte_object_in[44:46].hex(), 16)
        for index in range(0, 44):
            packetSum = packetSum + byte_object_in[index]
    elif flag == '07':
        cks = int(byte_object_in[54:56].hex(), 16)
        for index in range(0, 54):
            packetSum = packetSum + byte_object_in[index]
    if packetSum == cks:
        return True
    return False


def decode_serial_byte_stream_quad(byte_object_in, flag):
    # Function Definition: Decodes data read from serial port
    # Input: Byte Object, Well-Formatted
    # Output: String, comma seperated
    sss = byte_object_in.hex()
    return decode_raw_data_helper(sss, flag)

def decode_raw_data_file_quad(fn, flag):
    #def:
    #in:
    #out:
    fnr = fn + '_raw_data.txt'
    fr = open(fnr, 'r')
    ls = fr.readlines()
    fnw = fn + '_processed_data.txt'
    fw = open(fnw, 'w')
    for i,j in enumerate(ls) :
        j = j.strip() #remove newline
        if i < 2 :
            if i == 1 :
                fw.write(str(int(j[0:4],16)) + '\n')
                et = True if (ls[i+1][0:2] == '05' or ls[i+1][0:2] == '06') else False 
                ei = True if (ls[i+1][0:2] == '05' or ls[i+1][0:2] == '07') else False 
                if et and ei :
                    fw.write(
                        "\nPacket Flag, Syst-Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z, Acc-X, Acc-Y, Acc-Z, Gyr-X, Gyr-Y, Gyr-Z, Temp\n")
                elif not et and not ei :
                    fw.write(
                        "\nPacket Flag, Syst-Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z\n")
                elif ei :
                    fw.write(
                        "\nPacket Flag, Syst-Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z, Acc-X, Acc-Y, Acc-Z, Gyr-X, Gyr-Y, Gyr-Z\n")
                else:
                    fw.write(
                        "\nPacket Flag, Syst-Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z, Temp\n")
            else :
                fw.write(j + '\n')
        else :
            ws = decode_raw_data_helper(j[2:], j[0:2])
            fw.write(j[0:2] + ',' + ws[1] + '\n')


def decode_raw_data_helper(sss, flag) :
    #def:
    #in:
    #out:
    i = 0
    rsc = str(float(int(sss[i:i+8],16)) + (float(int(sss[i+8:i+12], 16)) * (1.00/32768.00))) + ","
    i = i + 12
    if flag == '01': #debug can be anything really, right now setup for one mag
        while i < 30:
            rsc = rsc + \
                str(decode_twos_comp(int(sss[i:i+6], 16), 24)) + ","
            i = i + 6
    elif flag == '04':
        while i < 84:
            rsc = rsc + \
                str(decode_twos_comp(int(sss[i:i+6], 16), 24)) + ","
            i = i + 6
    elif flag == '05':
        while i < 84:
            rsc = rsc + \
                str(decode_twos_comp(int(sss[i:i+6], 16), 24)) + ","
            i = i + 6
        while i < 108:
            rsc = rsc + \
                str(decode_twos_comp(int(sss[i:i+4], 16), 16)) + ","
            i = i + 4
        rsc = rsc + \
            str(int(sss[i:i+4], 16))
    elif flag == '06':
        while i < 84:
            rsc = rsc + \
                str(decode_twos_comp(int(sss[i:i+6], 16), 24)) + ","
            i = i + 6
        rsc = rsc + \
            str(int(sss[i:i+4], 16))
    elif flag == '07':
        while i < 84:
            rsc = rsc + \
                str(decode_twos_comp(int(sss[i:i+6], 16), 24)) + ","
            i = i + 6
        while i < 108:
            rsc = rsc + \
                str(decode_twos_comp(int(sss[i:i+4], 16), 16)) + ","
            i = i + 4
    # We discard the checksum
    return [sss, rsc]

def decode_twos_comp(ntc, nb):
    # Function Definition: Decodes twos complement input into a signed decimal number
    # Input: int twos complement number, int size of number in bits
    # Output: int converted signed decimal num
    if(ntc >> (nb - 1) & 1):
        return ntc - (1 << nb)
    return ntc