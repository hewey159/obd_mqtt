from obd_connect import main
import os


if __name__ == "__main__":
    obd_port = os.environ.get('OBD_PORT', "/dev/ttyUSB0")
    main(port=obd_port)