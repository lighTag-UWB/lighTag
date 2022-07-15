import socket
import codecs
from mpmath.functions.functions import re
import sympy
import numpy as np
from numpy import *
import serial
import serial.tools.list_ports
import time

tmp = 0


class lighTagAlgo:
    """
    Four Default Base Station Coordinates

    Note that if all four z-coordinates are the same,
    then the x, y and z of the fourth point can be directly implied,
    so the fourth z should be different in order to form a 3D-perceived environment
    """

    # (x,y,z) for base A
    xA, yA, zA = 0.0, 0.0, 2.0

    # (x,y,z) for base B
    xB, yB, zB = 0.0, 8.6, 2.0

    # (x,y,z) for base C
    xC, yC, zC = 5.6, 8.6, 2.0

    # (x,y,z) for base D
    xD, yD, zD = 5.6, 0.0, 2.37

    # (TA, TB, TC, TD) for four distances
    disArr = [0.0, 0.0, 0.0, 0.0]

    # (x,y,z) for the target
    coorArr = [0.0, 0.0, 0.0]

    # For WIFI
    c = None
    client = None
    address = None

    # For serial port
    ser = None

    def __init__(self):
        pass

    def wifiConnect(self):
        """
        For WIFI connection
        """
        print("Starts to connect socket.")

        self.c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.c.bind(("192.168.0.110", 8234))
        self.c.listen(10)
        self.client, self.address = self.c.accept()

        print("Socket connected.")
        return True

    def serialConnect(self):
        """
        For serial port connection
        """
        self.ser = serial.Serial("/dev/cu.usbserial-110", 115200)
        if self.ser.isOpen():
            print("Serial port connected.")
            print(self.ser.name)
        else:
            print("Serial port failed to connect.")

        self.ser = serial.Serial(
            port="/dev/cu.usbserial-110",
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.5,
        )
        return True

    def wifiDisconnect(self):
        """
        For WIFI disconnection
        """
        self.client.close()
        self.c.close()
        return True

    def serialDisconnect(self):
        """
        For serial port disconnection
        """
        self.ser.close()
        return True

    def getWifiData(self):
        """
        For WIFI data
        """
        global tmp

        bytes = self.client.recv(1024)

        new_tmp = time.time()
        print("(interval: {:.1f}s)".format(new_tmp - tmp), end=" ")
        tmp = time.time()
        # print(
        #     "[{}.{}]: ".format(
        #         time.strftime("%H:%M:%S", time.localtime()), int(time.time() * 10) % 10
        #     ),
        #     end="",
        # )
        return bytes.hex()

    def getSerialData(self):
        """
        For serial port data
        """
        bytes = self.ser.read(16)
        return bytes.hex()

    def convertDistance(self, inStr):
        """Convert hex string to distance data, assign the converted result to self.disArr

        Args:
            inStr (String): received hex string from WIFI
            32 Bytes data from WIFI

        Returns:
            arr (float[]): An array of length 4 containing distance data: [TA, TB, TC, TD]
            or -1 if error: wrong format or received 0000
        """
        # Check if the string is valid, start with "6d72" and end with "0a0d"
        if ((inStr[0:2] == "6d") and (inStr[2:4] == "72")) and (
            (inStr[28:30] == "0a") and (inStr[30:32] == "0d")
        ):
            arr = []
            for i in range(0, len(inStr), 2):
                str_1 = inStr[i : i + 2]
                # m r
                if i == 0 or i == 2:
                    binary_str = codecs.decode(str_1, "hex")  # hex to ASCII code
                    arr.append(str(binary_str, "utf-8"))
                # S/N, TAG ID, Frame
                if i == 4 or i == 6 or i == 8 or i == 10:
                    arr.append(inStr[i : i + 2])

                # dis 1.hex -> dec 2. dec/100
                if (
                    i == 12
                    or i == 14
                    or i == 16
                    or i == 18
                    or i == 20
                    or i == 22
                    or i == 24
                    or i == 26
                ):  # High 8 bits (2 bytes)
                    s = inStr[i : i + 2]  # Get the 2 bytes
                    inInt = int(s, 16)  # hex to dec
                    out = inInt / 100  # Get real distance

                    if i == 14 or i == 18 or i == 22 or i == 26:  # Low 8 bits (2 bytes)
                        val = inInt << 8  # Shift 8 bits to left
                        val = val / 100  # Get real distance
                        out = (
                            val + arr[int(i / 2 - 1)]
                        )  # Add the high 8 bits distance to the low 8 bits distance to get the real distance
                        if out == 0:
                            return -1
                    arr.append(out)

            self.disArr = arr[7::2]
            return arr[
                7::2
            ]  # Return the real distance data (high 8 bits distance + low 8 bits distance)
        else:
            return -1

    def setDistance(self, inArr):
        """set the distance data list for debug

        Args:
            inArr (float): a list of 4 distances

        Returns:
            Boolean: True for success
        """
        self.disArr = inArr
        return True

    def getDistance(self):
        """return the distance data list

        Returns:
            list: [TA,TB,TC,TD]
        """
        return self.disArr

    def calculateTriPosition(self):
        """Calculate the coordinates of the tag using the three base stations coordinates and the distance data, assign the result to self.coorArr

        Args:
            xP (float): x coordinate of the base station P
            yP (float): y coordinate of the base station P
            dP (float): distance between the tag and the base station P
            ...

        Returns:
            arr (float[]): An array of length 2 containing the coordinates of the tag: [x, y]
        """
        xa, ya, da, xb, yb, db, xc, yc, dc = (
            self.xA,
            self.yA,
            self.disArr[0],
            self.xB,
            self.yB,
            self.disArr[1],
            self.xC,
            self.yC,
            self.disArr[2],
        )

        x, y = sympy.symbols("x y")

        # List of equations
        f1 = (
            2 * x * (xa - xc)
            + np.square(xc)
            - np.square(xa)
            + 2 * y * (ya - yc)
            + np.square(yc)
            - np.square(ya)
            - (np.square(dc) - np.square(da))
        )
        f2 = (
            2 * x * (xb - xc)
            + np.square(xc)
            - np.square(xb)
            + 2 * y * (yb - yc)
            + np.square(yc)
            - np.square(yb)
            - (np.square(dc) - np.square(db))
        )

        # Solve the equations
        result = sympy.solve([f1, f2], [x, y])
        locx, locy = result[x], result[y]
        self.coorArr = [locx, locy, None]
        return [locx, locy]

    def calculateQuartPosition(self):
        [a, b] = self.calculateTriPosition()
        z1 = sympy.symbols("z1")
        f1 = (
            np.square(a - self.xD)
            + np.square(b - self.yD)
            + np.square(z1 - self.zD)
            - np.square(self.disArr[3])
        )
        rst1 = sympy.solve(f1, z1)

        z2 = sympy.symbols("z2")
        f2 = (
            np.square(a - self.xB)
            + np.square(b - self.yB)
            + np.square(z2 - self.zB)
            - np.square(self.disArr[1])
        )
        rst2 = sympy.solve(f2, z2)

        sol1 = list(rst1)
        sol2 = list(rst2)

        if complex(sol1[0]).real > complex(sol1[1]).real:
            sol1[0], sol1[1] = sol1[1], sol1[0]

        if complex(sol2[0]).real > complex(sol2[1]).real:
            sol2[0], sol2[1] = sol2[1], sol2[0]

        min1 = abs(sol1[0] - sol2[0])
        min2 = abs(sol1[1] - sol2[1])

        min0 = min(min1, min2)

        out = 0

        if min0 == min1:
            out = (sol1[0] + sol2[0]) / 2
        elif min0 == min2:
            out = (sol1[1] + sol2[1]) / 2

        out = complex(out).real

        self.coorArr = [a, b, out]
        return [a, b, out]

    def getCoor(self):
        """return the coordinates of the tag

        Returns:
            list: [x, y, z]
        """
        return self.coorArr

    def setBaseACoor(self, x, y, z):
        """set the coordinates of the base station A

        Args:
            x (float): x coordinate of the base station A
            y (float): y coordinate of the base station A
            z (float): z coordinate of the base station A

        Returns:
            Boolean: True for success
        """
        self.xA = x
        self.yA = y
        self.zA = z
        return True

    def setBaseBCoor(self, x, y, z):
        """set the coordinates of the base station B

        Args:
            x (float): x coordinate of the base station B
            y (float): y coordinate of the base station B
            z (float): z coordinate of the base station B

        Returns:
            Boolean: True for success
        """
        self.xB = x
        self.yB = y
        self.zB = z
        return True

    def setBaseCCoor(self, x, y, z):
        """set the coordinates of the base station C

        Args:
            x (float): x coordinate of the base station C
            y (float): y coordinate of the base station C
            z (float): z coordinate of the base station C

        Returns:
            Boolean: True for success
        """
        self.xC = x
        self.yC = y
        self.zC = z
        return True

    def setBaseDCoor(self, x, y, z):
        """set the coordinates of the base station D

        Args:
            x (float): x coordinate of the base station D
            y (float): y coordinate of the base station D
            z (float): z coordinate of the base station D

        Returns:
            Boolean: True for success
        """
        self.xD = x
        self.yD = y
        self.zD = z
        return True

    def getFourBaseCoor(self):
        """return the coordinates of the four base stations

        Returns:
            list: [xa, ya, za, xb, yb, zb, xc, yc, zc, xd, yd, zd]
        """
        return [
            self.xA,
            self.yA,
            self.zA,
            self.xB,
            self.yB,
            self.zB,
            self.xC,
            self.yC,
            self.zC,
            self.xD,
            self.yD,
            self.zD,
        ]

    def run(self):
        """The main entrance of the function, step 4 to 6, wait to be called repeatedly

        !!!!!
        Instantiate an lighTagAlgo object (Step 1),
        Wifi/Serial connection (Step 2), and
        Set coordinates of four base stations (Step 3)
        should be called once BEFORE using this function.
        !!!!!

        Returns:
            out[2D list]: [[distance_AT, distance_BT, distance_CT, distance_DT],[coor_x, coor_y, coor_z]]
            or, -1 for error, need to be checked and skipped
        """

        str = self.getWifiData()
        dis = self.convertDistance(str)

        if dis != -1:  # check if the distance is valid
            return self.calculateQuartPosition()  # calculate the coordinates of the tag
        return -1


def test():
    """
    Referenced SOP
    Below are Step 1 to 3, need to be called only once before using the function run(),
    Step 4 to 6 are in the function run(), need to be called repeatedly
    """

    # 1. Instantiate an lighTagAlgo object
    lt = lighTagAlgo()

    # 2. Wifi connection
    lt.wifiConnect()

    # 2. Or Serial connection
    # lt.serialConnect()

    # 3. Set the coordinates of four base stations
    lt.setBaseACoor(0, 0, 2.0)
    lt.setBaseBCoor(0, 8.535, 2.0)
    lt.setBaseCCoor(5.86, 8.535, 2.0)
    lt.setBaseDCoor(5.86, 0.0, 2.355)

    # for debug only
    # arr = [4.04,6.05,6.78,5.4]
    # lt.setDistance(arr)
    # lt.calculateTriPosition()
    # lt.calculateQuartPosition()
    # print(lt.getCoor())

    # Loop
    while True:
        print(lt.run())
        # lt.run()


if __name__ == "__main__":
    test()
