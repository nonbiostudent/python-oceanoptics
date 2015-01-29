import usb.core
from oceanoptics.defines import OceanOpticsSupportedModels as _OOSupMod
from oceanoptics.defines import OceanOpticsModelConfig as _OOModConf
from oceanoptics.defines import OceanOpticsVendorId as _OOVendorId
from oceanoptics.defines import OceanOpticsError as _OOError

import oceanoptics.spectrometers
from oceanoptics.spectrometers.XXX2000 import USB2000, HR2000, USB650
from oceanoptics.spectrometers.XXX2000plus import USB2000plus, HR2000plus
from oceanoptics.spectrometers.XXX4000 import USB4000, HR4000
from oceanoptics.spectrometers.MAYA import MAYA
from oceanoptics.spectrometers.MAYA2000pro import MAYA2000pro
from oceanoptics.spectrometers.APEX import APEX
from oceanoptics.spectrometers.QE65xxx import QE65000, QE65pro
from oceanoptics.spectrometers.TORUS import TORUS
from oceanoptics.spectrometers.STS import STS

_models = {
    "USB2000"    : USB2000,
    "USB650"    : USB650,
    "HR2000"    : HR2000,
    "USB2000+"    : USB2000plus,
    "HR2000+"    : HR2000plus,
    "USB4000"    : USB4000,
    "HR4000"    : HR4000,
    "MAYA"    : MAYA,
    "MAYA2000pro"    : MAYA2000pro,
    "APEX"    : APEX,
    "QE65000"    : QE65000,
    "QE65pro"    : QE65pro,
    "TORUS"    : TORUS,
    "STS"    : STS,
        }


def get_available_spectrometers():
    """
    Returns a dict of all available spectrometers with their serial numbers as
    keys.
    
    Note that an "available" spectrometer is one which is plugged in, but is not
    currently connected to. This means that unless the spectrometer objects 
    returned by this function are disposed of, subsequent calls to the function 
    will return an empty dict.
    
    Returns
    -------
    spectrometers : dict {string: OceanOpticsBase object,...}
        dict of spectrometer objects with their serial numbers as keys
    
    """
    
    ProductId = {}
    for model in _OOSupMod:
        pid = _OOModConf[model]['ProductId']
        ProductId.update(zip(pid, [model] * len(pid)))

    devices = usb.core.find(find_all=True,
                            custom_match=lambda d: (d.idVendor == _OOVendorId and
                                                    d.idProduct in ProductId.keys()))
    
    spectrometers = {}
    
    for d in devices:
        mod = ProductId[d.idProduct]
    
        spec_class = _models[mod]
        
        try:
            spectro = spec_class(device=d)
            spectrometers[spectro.serial_number] = spectro
            
        except usb.core.USBError:
            #the spectrometer is already connected - skip it
            continue
    
    return spectrometers
    

def get_spectrometer(serial_num=None):
    """
    If serial_num is specified, then returns the object corresponding to that 
    particular spectrometer, otherwise the first available spectrometer is 
    returned.
    
    Parameters
    ----------
    serial_num : string, optional
        the serial number of the spectrometer that you want to connect to
    
    Returns
    -------
    spectrometer : OceanOpticsBase object
        the spectrometer with the requested serial number, or the first 
        available spectrometer if serial_num=None
    
    Raises
    ------
        OceanOpticsError: 
            if the requested spectrometer is not available.
    """
    
    spectrometers = get_available_spectrometers()
    
    if not spectrometers:
        raise _OOError('no available spectrometers found')
    
    if serial_num is None:
        #then just return the first spectrometer in the list
        serial_num = spectrometers.keys()[0]

    try:
        selected_spectro = spectrometers.pop(serial_num)
    except KeyError:
        raise _OOError('Spectrometer %s is not available'%serial_num)
    finally:
        for s in spectrometers.values():
            s.dispose()
    
    return selected_spectro


def list_available_spectrometers():
    """
    Returns a list of spectrometer serial numbers (strings) for all the currently
    available spectrometers.
    
    Note that an "available" spectrometer is one which is plugged in, but is not
    currently connected to.
    
    Returns
    -------
    serial numbers : list of strings
        the serial numbers of all the available spectrometers
    """
    spectros = get_available_spectrometers()
    
    spectro_ids = spectros.keys()
    
    for s in spectros.values():
        s.dispose()
    
    return spectro_ids
    
    


def get_a_random_spectrometer():
    ProductId = {}
    for model in _OOSupMod:
        pid = _OOModConf[model]['ProductId']
        ProductId.update(zip(pid, [model] * len(pid)))

    devices = usb.core.find(find_all=True,
                            custom_match=lambda d: (d.idVendor == _OOVendorId and
                                                    d.idProduct in ProductId.keys()))
    # TODO: ??? usb.core.find can also return a generator ???
    devices = list(devices)

    if devices:
        print '> found:'
    else:
        raise _OOError('no supported spectrometers found')
    for d in devices:
        print '>  - %s' % ProductId[d.idProduct]

    mod = ProductId[devices[0].idProduct]
    print '>'
    print '> returning first %s as OceanOpticsSpectrometer' % mod

    spec_class = _models[mod]
    return spec_class()
