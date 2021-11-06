import sys, time
import usb
import usb.backend.libusb1
import libusbfinder

MAX_PACKET_SIZE = 0x800
def acquire_device(timeout=5.00, match=None, fatal=True):
  backend = usb.backend.libusb1.get_backend(find_library=lambda x:libusbfinder.libusb1_path())
  start = time.time()
  once = False
  while not once or time.time() - start < timeout:
      once = True
      for device in usb.core.find(find_all=True, idVendor=0x5AC, idProduct=0x1227, backend=backend):
          if match is not None and match not in device.serial_number:
              continue
          return device
      time.sleep(0.001)
  if fatal:
      print 'ERROR: No Apple device in DFU Mode 0x1227 detected after %0.2f second timeout. Exiting.' % timeout
      sys.exit(1)
  return None

def release_device(device):
    usb.util.dispose_resources(device)

def reset_counters(device):
    assert device.ctrl_transfer(0x21, 4, 0, 0, 0, 1000) == 0

def usb_reset(device):
    try:
        device.reset()
    except usb.core.USBError:
        pass

def send_data(device, data):
    index = 0
    while index < len(data):
        amount = min(len(data) - index, MAX_PACKET_SIZE)
        assert device.ctrl_transfer(0x21, 1, 0, 0, data[index:index + amount], 5000) == amount
        index += amount

def get_data(device, amount):
    data = str()
    while amount > 0:
        part = min(amount, MAX_PACKET_SIZE)
        ret = device.ctrl_transfer(0xA1, 2, 0, 0, part, 5000)
        assert len(ret) == part
        data += ret.tostring()
        amount -= part
    return data

def request_image_validation(device):
    assert device.ctrl_transfer(0x21, 1, 0, 0, '', 1000) == 0
    for i in range (1,4):
        device.ctrl_transfer(0xA1, 3, 0, 0, 6, 1000)
    usb_reset(device)
