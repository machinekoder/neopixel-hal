#!/usr/bin/env python
# coding=utf-8
import time
import sys
import threading
import logging

import board
import neopixel
from pymachinetalk.dns_sd import ServiceDiscovery, ServiceDiscoveryFilter
import pymachinetalk.halremote as halremote

SLEEP_TIME_S = 0.1
#MK_UUID=b'adfc1666-c8f8-4193-8ad8-3d689e69043f'
MK_UUID=b'd4960627-f722-4168-a57a-86eaf37b458a'

logger = logging.getLogger('NeoPixelHal')


class NeoPixelHal(object):
    """
    NeoPixel HAL Remote component.
    
    For docs on how to use the neopixel lib visit: https://github.com/adafruit/Adafruit_CircuitPython_NeoPixel
    """

    WHITE = (255,255,255)
    RED = (255,0,0)
    BLUE = (0,0,255)
    OFF = (0,0,0)

    def __init__(self, com_pin=board.D18, num_pixels=16, debug=False):
        self.pixels = neopixel.NeoPixel(com_pin, num_pixels)
        self._connected = False
        self._enabled = False
        self._update_light()
        
        rcomp = halremote.RemoteComponent('neopixel', debug=debug)
        rcomp.no_create = True
        enable_pin = rcomp.newpin('enable', halremote.HAL_BIT, halremote.HAL_IN)
        enable_pin.on_value_changed.append(self._enable_pin_changed)
        mode_pin = rcomp.newpin('mode', halremote.HAL_U32, halremote.HAL_IN)
        mode_pin.on_value_changed.append(self._mode_pin_changed)
        rcomp.on_connected_changed.append(self._connected_changed)

        self.rcomp = rcomp
        self.sd = ServiceDiscovery(filter_=ServiceDiscoveryFilter(txt_records={b'uuid': MK_UUID}))
        self.sd.register(rcomp)

    def _standby_light(self):
        self.pixels.fill(self.OFF)
        color = tuple(map(lambda x: int(x * 0.01), (self.BLUE if self._connected else self.RED)))
        self.pixels[0] = color
        self.pixels[1] = color

    def _update_light(self):
        if self._enabled and self._connected:
            self.pixels.fill(self.RED)
        else:
            self._standby_light()

    def _enable_pin_changed(self, value):
        logger.debug(f'Enable pin changed: {value}')
        self._enabled = value
        self._update_light()

    def _mode_pin_changed(self, value):
        pass

    def _connected_changed(self, connected):
        logger.debug(f'Remote component connected: {connected}')
        self._connected = connected
        self._update_light()

    def start(self):
        self.sd.start()

    def stop(self):
        self.sd.stop()

    def update(self):
        pass


def main():
    debug = False
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    comp = NeoPixelHal(debug=debug)

    logger.debug('starting')
    comp.start()

    try:
        while True:
            comp.update()
            time.sleep(SLEEP_TIME_S)
    except KeyboardInterrupt:
        pass

    logger.debug('stopping threads')
    comp.stop()

    # wait for all threads to terminate
    while threading.active_count() > 1:
        time.sleep(0.1)

    logger.debug('threads stopped')
    sys.exit(0)


if __name__ == "__main__":
    main()
