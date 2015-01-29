# XXX: untested
#----------------------------------------------------------
from oceanoptics.base import OceanOpticsBase as _OOBase
#----------------------------------------------------------


class APEX(_OOBase):

    def __init__(self, **kwargs):
        super(APEX, self).__init__('Apex', **kwargs)


