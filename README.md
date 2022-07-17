# lighTag
An UWB Positioning System Integrated in Lighting System and its Applications

<img src="https://github.com/lighTag-UWB/lighTag/blob/main/lighTag_Logo_2.png" width="50%"></img>

---

A project supported by [**The Hong Kong Polytechnic University**](https://www.polyu.edu.hk/) and [**MIT Hong Kong Innovation Node**](https://hkinnovationnode.mit.edu/),

made by [Haley Kwok](https://github.com/HaleyKwok), [Mike Zhang](https://github.com/zhangwengyu999) and [Xavier Pan](https://github.com/X3vvv).


This project mainly focused on the research of the Ultra-wideband (UWB) technology and Internet of Things as well as their applications.

---

# Problem Statements
- 1. Users can not easily find their place in a multi-storey mall;
- 2. Visitor recording during Covid-19 is not smart and detailed;
- 3. It is not smart to turn off surplus and excessive lighting along the corridors due to the photocell sensors or occupancy sensors canonly detect movement rather than people.

---

# lighTag Features
- 1. Solution to Power Issue: lighTag integrated with lighting system in the building, UBW bases cn receive continuous power;
- 2. 3D Indoor Positioning: with 4 lighTag Base Station, lighTag can get the x,y and z coordinates of the lighTag Tag integrated in user'sdevices;
- 3. High Accuracy: lighTag has 5cm ranging accuracy, 10cm 2D accuracy, and 20cm 3D accuracy, which provides a accurate position ofuser;
- 4. Area of Interest Detection: lighTag can detect the presence of user in an specific area inside a building.

---

# Project Contents
- 1. lighTag Base&Tag: Using the BP-TWR-50 UWB Module from bphero Inc. with Two Way Ranging (TWR) distancing algorithm. Based onthe TWR open source firmware, we set 4 base stations for the 3D positioning. ESP8266-01S WI-FI Module is used to do thecommunication between UWB module and the PC via TCP/IP, which sends the distance data from based station to backend program;
- 2. lighTag Algorithm API: Using Python to implement the Multilateration Positioning Algorithm, which calculates the coordinates fromdistance data. The Python library sympy and numpy are used to solve the Euclidean metric to get the coordinates. After the algorithmoptimisation, we packaged all functions into Python API for further UI uasge;
- 3. lighTag User Interface: The UI is implemented by the Python's Kivy library. The lighTag UI can do the real-time plotting of user'sposition, add AOI area by the administrator, as well as detect whether user is in the area on not. The Kivy UI can be further packaged intomobile App. The AOI detection is realized by the optimized Ray Method.

---

# Applications to Problem Statements:
- 1. lighTag can enable 3D Indoor Navigation in shopping mall, airport, and factory with floor number indicated;
- 2. Working with LeaveHomeSafe App, lighTag can automatically record arrival & leaving, record detailed location information, andmeasure social distance;
- 3. lighTag can adjust indoor lights state including ON/OFF, brightness based on the position and number of people.
