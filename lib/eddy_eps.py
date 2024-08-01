###############################################################################
# Author: Justin Schachter (jschach@umich.edu)
###############################################################################
from lib.ads7828 import ADS7828
from enum import IntEnum, Enum
import math
from tabulate import tabulate

###########################################################################
# Main Class
###########################################################################
class EddyEps():
    
    ###########################################################################
    # MEMBER VARIABLES
    ###########################################################################
    _rev = None
    _i2c_bus_num = None
    _adc_0 = None
    _adc_1 = None
    _channels_per_adc = 8
    _channel_enum = None

    ###########################################################################
    # CONSTRUCTOR
    ###########################################################################
    def __init__(self, rev='A', smbus_num=1):
        """
        """
        self._rev = rev
        self._i2c_bus_num = smbus_num
        
        #setup ADCs
        self._adc_0 = ADS7828(address=0x48, smbus_num=smbus_num)
        self._adc_1 = ADS7828(address=0x49, smbus_num=smbus_num)

        #setup channel scope
        if self._rev == 'A':
            self._channel_enum = self.ChannelsRevA
        else:
            raise ValueError("Provided rev (revision) value invalid (available options: 'A')")


    ###########################################################################
    # MEMBER CLASSES
    ###########################################################################
    class ChannelsRevA(IntEnum):
        """
        Global scope ADC channel name/value assignment
        on Eddy (i.e. ADC_XX on output regulation schematic)
        Edits can be made here to match board revisions
        """
        LM20_3V3_REG = 7
        LM20_5V0_REG = 4 
        
        V_VBATT_RAW = 5
        I_VBATT_RAW = 6

        V_3V3 = 3
        I_3V3 = 2

        V_5V0 = 1
        I_5V0 = 0

        V_VBATT = 13
        I_VBATT = 14

    class AdcChannelScope(Enum):
        """
        Max value of global scope ADC channels on Eddy 
        (i.e. ADC_XX on output regulation schematic)
        """
        ADC_0 = range(0,8)  #ADC_0 to ADC_7
        ADC_1 = range(8,16) #ADC_8 to ADC_15

    
    ###########################################################################
    # PUBLIC MEMBER METHODS (PUBLIC API)
    ###########################################################################
    def get_voltage_vbatt_raw(self):
        channel = self._channel_enum.V_VBATT_RAW
        raw_adc_v = self._eps_read_channel_single_ended(channel)
        r1 = 100e3 #Ohms
        r2 = 12e3  #Ohms
        return self._voltage_divider_reversal(raw_adc_v, r1, r2)

    def get_current_vbatt_raw(self):
        channel = self._channel_enum.I_VBATT_RAW
        raw_adc_v = self._eps_read_channel_single_ended(channel)
        r_sense = 12e-3 #Ohms
        gain = 100      #V/V
        return self._voltage_divider_reversal(raw_adc_v, r_sense, gain)

    def get_voltage_3v3(self):
        channel = self._channel_enum.V_3V3
        raw_adc_v = self._eps_read_channel_single_ended(channel)
        r1 = 100e3   #Ohms
        r2 = 60.4e3  #Ohms
        return self._voltage_divider_reversal(raw_adc_v, r1, r2)

    def get_current_3v3(self):
        channel = self._channel_enum.I_3V3
        raw_adc_v = self._eps_read_channel_single_ended(channel)
        r_sense = 5e-3  #Ohms
        gain = 100      #V/V
        return self._voltage_divider_reversal(raw_adc_v, r_sense, gain)

    def get_voltage_5v0(self):
        channel = self._channel_enum.V_5V0
        raw_adc_v = self._eps_read_channel_single_ended(channel)
        r1 = 100e3   #Ohms
        r2 = 33.2e3  #Ohms
        return self._voltage_divider_reversal(raw_adc_v, r1, r2)

    def get_current_5v0(self):
        channel = self._channel_enum.I_5V0
        raw_adc_v = self._eps_read_channel_single_ended(channel)
        r_sense = 12e-3 #Ohms
        gain = 100      #V/V
        return self._voltage_divider_reversal(raw_adc_v, r_sense, gain)

    def get_voltage_vbatt(self):
        channel = self._channel_enum.V_VBATT
        raw_adc_v = self._eps_read_channel_single_ended(channel)
        r1 = 100e3 #Ohms
        r2 = 12e3  #Ohms
        return self._voltage_divider_reversal(raw_adc_v, r1, r2)

    def get_current_vbatt(self):
        channel = self._channel_enum.I_VBATT
        raw_adc_v = self._eps_read_channel_single_ended(channel)
        r_sense = 12e-3 #Ohms
        gain = 100      #V/V
        return self._voltage_divider_reversal(raw_adc_v, r_sense, gain)
    
    def get_temp_3v3_reg(self, unit='c'):
        channel = self._channel_enum.LM20_3V3_REG
        raw_adc_v = self._eps_read_channel_single_ended(channel)

        if unit.lower() == 'c':
            return self._lm20_transfer_func_deg_c(raw_adc_v)
        elif unit.lower() == 'f':
            return self._lm20_transfer_func_deg_f(raw_adc_v)
        else: 
            raise ValueError('Invalid temperature unit selected')
    
    def get_temp_5v0_reg(self, unit='c'):
        channel = self._channel_enum.LM20_5V0_REG
        raw_adc_v = self._eps_read_channel_single_ended(channel)

        if unit.lower() == 'c':
            return self._lm20_transfer_func_deg_c(raw_adc_v)
        elif unit.lower() == 'f':
            return self._lm20_transfer_func_deg_f(raw_adc_v)
        else: 
            raise ValueError('Invalid temperature unit selected')

    def print_measurement_table(self):
        header = ['CHANNEL', 'MEASUREMENT', 'UNIT']
        table = [ header,
                 ['V VBATT RAW', self.get_voltage_vbatt_raw(), 'V'],
                 ['I VBATT RAW', self.get_current_vbatt_raw(), 'A'],
                 ['V 3V3', self.get_voltage_3v3(), 'V'],
                 ['I 3V3', self.get_current_3v3(), 'A'],
                 ['V 5V0', self.get_voltage_5v0(), 'V'],
                 ['I 5V0', self.get_current_5v0(), 'A'],
                 ['V VBATT', self.get_voltage_vbatt(), 'V'],
                 ['I VBATT', self.get_current_vbatt(), 'A'],
                 ['3V3 REG TEMP', self.get_temp_3v3_reg(), 'C'],
                 ['3V3 REG TEMP', self.get_temp_3v3_reg(unit='f'), 'F'],
                 ['5V0 REG TEMP', self.get_temp_5v0_reg(), 'C'],
                 ['5V0 REG TEMP', self.get_temp_5v0_reg(unit='f'), 'F'],
                 ]
        print(tabulate(table,headers="firstrow", tablefmt="grid"))

    ###########################################################################
    # PRIVATE MEMBER METHODS
    ###########################################################################
    def _adc_read_channel_single_ended(self,adc=None,adc_ch=None):
        if adc is not None and adc_ch is not None:
            if adc_ch < 0 or adc_ch > self._channels_per_adc:
                raise ValueError('Invalid ch value provided')
            if adc == 'ADC_0' or adc == 0:
                return self._adc_0.read_channel_single_ended(adc_ch, internal_ref_on=True, ad_on=True)
            elif adc == 'ADC_1' or adc == 1:
                return self._adc_0.read_channel_single_ended(adc_ch, internal_ref_on=True, ad_on=True)
            else:
                raise ValueError('Invalid adc value provided')
        else:
            raise ValueError('Value provided for adc or ch is None')
    
    def _eps_read_channel_single_ended(self,eps_ch):
        adc_ch_mod = (eps_ch+1) % self._channels_per_adc - 1
        adc_ch = adc_ch_mod if adc_ch_mod >= 0 else (self._channels_per_adc -1)
        adc_num = None

        for adc in self.AdcChannelScope:
            if eps_ch in adc.value:
                adc_num = int(adc.name.replace('ADC_',''))
                return self._adc_read_channel_single_ended(adc=adc_num, adc_ch=adc_ch)
        #Error Handling:
        #print(f'EPS_CH: {eps_ch}, ADC_CH: {adc_ch}, ADC_NUM: {adc_num}')
        raise ValueError('Provided EPS ADC channel (in scope of EPS global scope assignments) did not match any of the assignments in AdcChannelScope(Enum)')

    def _lm20_transfer_func_deg_c(self, voltage):
        """
        converts LM20 voltage to temperature in degC
        """
        return (-1481.96 + math.sqrt(2.1962e6 + ((1.8639 - voltage)/3.88e-6)))

    def _lm20_transfer_func_deg_f(self, voltage):
        """
        converts LM20 voltage to temperature in degC
        """
        return (-1481.96 + math.sqrt(2.1962e6 + ((1.8639 - voltage)/3.88e-6)))*(9/5) + 32

    def _voltage_divider_reversal(self, v2, r1, r2):
        v1 = v2 * ((r1 + r2)/r2)
        return v1

    def _max9634_v_to_i(self, v_sense, r_sense, gain):
        return v_sense / (r_sense * gain)
