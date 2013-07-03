
#----------------------------------------------------------
import numpy as np
import struct
import time
import usb.core
import warnings
from _defines import OceanOpticsError as _OOError
from _defines import OceanOpticsModelConfig as _OOModelConfig
from _defines import OceanOpticsVendorId as _OOVendorId
from _defines import OceanOpticsSpectrumConfig as _OOSpecConfig
#----------------------------------------------------------

class OceanOpticsUSBComm(object):

    def __init__(self, model):
        self._usb_init_connection(model)

    def _usb_init_connection(self, model):
       
        if model not in _OOModelConfig.keys():
            raise _OOError('Unkown OceanOptics spectrometer model: %s' % model)

        vendorId, productId = _OOVendorId, _OOModelConfig[model]['ProductId']
        self._EPout = _OOModelConfig[model]['EPout']
        self._EPin0 = _OOModelConfig[model]['EPin0']
        self._EPin1 = _OOModelConfig[model]['EPin1']
        self._EPin0_size = _OOModelConfig[model]['EPin0_size']
        self._EPin1_size = _OOModelConfig[model]['EPin1_size']

        devices = usb.core.find(find_all=True, 
                        custom_match=lambda d: (d.idVendor==vendorId and
                                                d.idProduct in productId))
        
        try:
            self._dev = devices.pop(0)
        except AttributeError:
            raise _OOError('No OceanOptics %s spectrometer found!' % model)
        else:
            if devices: 
                warnings.warn('Currently the first device matching the '
                              'Vendor/Product id is used')
        
        self._dev.set_configuration()
        self._USBTIMEOUT = self._dev.default_timeout * 1e-3

    def _usb_send(self, data, epo=None):
        """ helper """
        if epo is None:
            epo = self._EPout
        self._dev.write(epo, data)

    def _usb_read(self, epi=None, epi_size=None):
        """ helper """
        if epi is None:
            epi = self._EPin0
        if epi_size is None:
            epi_size = self._EPin0_size
        return self._dev.read(epi, epi_size)

    def _usb_query(self, data, epo=None, epi=None, epi_size=None):
        """ helper """
        self._usb_send(data, epo)
        return self._usb_read(epi, epi_size)



class OceanOpticsBase(OceanOpticsUSBComm):
    """ This class implements functionality that is common
    among all supported spectrometers.

    """

    def __init__(self, model):
        super(OceanOpticsBase, self).__init__(model)
        self._initialize()

        status = self._init_robust_status()
        self._usb_speed = status['usb_speed']
        self._integration_time = status['integration_time']
        self._pixels = status['pixels']
        self._EPspec = self._EPin1 if self._usb_speed == 0x80 else self._EPin0
        self._packet_N, self._packet_size, self._packet_func = (
                _OOSpecConfig[model][self._usb_speed] )
        self._init_robust_spectrum()

        # XXX: differs for some spectrometers...
        #self._sat_factor = 65535.0/float(
        #      stuct.unpack('<h', self._query_information(17, raw=True)[6:8])[0])
        self._wl_factors = [float(self._query_information(i)) for i in range(1,5)]
        self._nl_factors = [float(self._query_information(i)) for i in range(6,14)]
        self._wl = sum( self._wl_factors[i] *
              np.arange(self._pixels)**i for i in range(4) )

    #---------------------
    # High level functions
    #---------------------

    def wavelengths(self):
        return self._wl

    def spectrum(self, raw=False):
        data = np.array(self._request_spectrum(), dtype=np.float)
        if not raw:
            data = data / sum( self._nl_factors[i] * data**i for i in range(8) )
            # XXX: differs for some spectrometers
            #data *= self._sat_factor
        return data

    def integration_time(self, time_us=None):
        if not (time_us is None):
            self._set_integration_time(time_us)
        self._integration_time = self._query_status()['integration_time']*1e-6
        return self._integration_time

    #---------------------
    # Low level functions.
    #---------------------

    def _init_robust_status(self):
        for i in range(10):
            try:
                status = self._query_status()
                break
            except usb.core.USBError: pass
        else: raise _OOError('Initialization USBCOM')
        return status
        
    def _init_robust_spectrum(self):
        self.integration_time(1000)
        for i in range(10):
            try:
                self._request_spectrum()
                break
            except: raise
        else: raise _OOError('Initialization SPECTRUM')

    def _initialize(self):
        """ send command 0x01 """
        self._usb_send(struct.pack('<B', 0x01))
        
    def _set_integration_time(self, time_us):
        """ send command 0x02 """
        self._usb_send(struct.pack('<BI', 0x02, int(time_us)))

    def _query_information(self, address, raw=False):
        """ send command 0x05 """
        ret = self._usb_query(struct.pack('<BB', 0x05, int(address)))
        if bool(raw): return ret
        if ret[0] != 0x05 or ret[1] != int(address)%0xFF:
            raise _OOError('query_information: Wrong answer')
        return ret[2:ret[2:].index(0)+2].tostring()

    def _write_information(self):
        raise NotImplementedError

    def _request_spectrum(self):
        self._usb_send(struct.pack('<B', 0x09))
        time.sleep(max(self._integration_time - self._USBTIMEOUT, 0))
        ret = [ self._usb_read(epi=self._EPspec, epi_size=self._packet_size) 
                            for _ in range(self._packet_N) ]
        ret = sum( ret[1:], ret[0] )
        sync = self._usb_read(epi=self._EPspec, epi_size=1)
        if sync[0] != 0x69:
            raise _OOError('request_spectrum: Wrong sync byte')
        spectrum = struct.unpack('<'+'h'*self._pixels, ret)
        spectrum = map(self._packet_func, spectrum)
        return spectrum

    def _query_status(self):
        """ 0xFE query status """
        ret = self._usb_query(struct.pack('<B', 0xFE))
        data = struct.unpack('<HLBBBBBBBBBB', ret[:])
        ret = { 'pixels' : data[0],
                'integration_time' : data[1],
                'lamp_enable' : data[2],
                'trigger_mode' : data[3],
                'acquisition_status' : data[4],
                'packets_in_spectrum' : data[5],
                'power_down' : data[6],
                'packets_in_endpoint' : data[7],
                'usb_speed' : data[10] }
        return ret




class OceanOpticsSerialNum(OceanOpticsUSBComm):

    def _write_serial_number(self,):
        raise NotImplementedError

    def _get_serial_number(self,):
        raise NotImplementedError



class OceanOpticsShutdown(OceanOpticsUSBComm):

    def _set_shutdown_mode(self):
        raise NotImplementedError


class OceanOpticsTrigger(OceanOpticsUSBComm):

    def _set_trigger_mode(self):
        raise NotImplementedError
















