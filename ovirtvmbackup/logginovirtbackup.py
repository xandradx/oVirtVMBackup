#!/bin/env python2

import logging

class LogBackup:
    def __init__(self, settings=None):
        self.settings = settings
        self.mensaje = None

    def printlog(self, codigo, mensaje=None):
        if codigo == "api":
            print("api message {}".format(mensaje))
        elif codigo == "stdout":
            print("stdout message {}".format(mensaje))
        elif codigo == "tsm":
            print("tsm message {}".format(mensaje))
        elif codigo == "all":
            print("api message {}".format(mensaje))
            print("stdout message {}".format(mensaje))
            print("tsm message {}".format(mensaje))
        else:
            print("codigo incorrecto")