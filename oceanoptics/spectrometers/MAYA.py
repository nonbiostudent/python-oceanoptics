# XXX: untested
#----------------------------------------------------------
from oceanoptics.base import OceanOpticsBase as _OOBase
#----------------------------------------------------------


class MAYA(_OOBase):

    def __init__(self, **kwargs):
        super(MAYA, self).__init__('Maya', **kwargs)


