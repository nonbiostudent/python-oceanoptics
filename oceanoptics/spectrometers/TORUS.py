# XXX: untested
#----------------------------------------------------------
from oceanoptics.base import OceanOpticsBase as _OOBase
#----------------------------------------------------------


class TORUS(_OOBase):

    def __init__(self, **kwargs):
        super(TORUS, self).__init__('Torus', **kwargs)


