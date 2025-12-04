# -*- coding: utf-8 -*-

def classFactory(iface):
    """
    QGIS ruft diese Funktion auf, um das Plugin zu erstellen.
    """
    from .tilda_jump import TildaJumpPlugin
    return TildaJumpPlugin(iface)
