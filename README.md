# SmartCushion-Rasp

This code is on the Raspberry Pi.

**14/06/2024:**

Influx and Node-RED are in images.

To execute the full project, you need to:

- Activate the virtual environment "cushion" with `conda activate cushion`.
- Run all the following commands :
  -cd /home/pi/smart_cushion/fsr
  -cd smartcushion
  -cd fsr
  -python ENV_DATA.py
  -python sedentary.py
  -python posture.py

- Run the `app.py` file in the "backend" folder in the "smartcushion" folder.

After that, you need to run the application "cushionv3":

```bash
cd cushionv3
npx expo start

```
