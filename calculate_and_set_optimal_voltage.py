import pdb

import paho.mqtt.client as mqtt
import time
import datetime
import requests
from range_key_dict import RangeKeyDict

charger_ip = "192.168.4.1"
set_to_charger = False

target_topics = ["solpiplog/pip/totalsolarw", 'solpiplog/pylon/soc']
last_calculated_key = "last_calculated_amp"

topic_keys = {
    "solpiplog/pip/totalsolarw": "total_solar_watt",
    "solpiplog/pylon/soc": "soc"
}

latest_values = {
    "total_solar_watt": 101,
    "soc": 0,
    "last_calculated_amp": 0
}

pause_amp = 2
tsw_to_solar_power_mode_matrix = RangeKeyDict({
    # What about > 800 and less than 100?
    (701, 801): "HIGH",
    (451, 701): "MEDIUM",
    (101, 451): "LOW"
})

soc_to_charging_pace_matrix = {
    "HIGH": RangeKeyDict({
        (76, 101): "FAST",
        (51, 76): "MEDIUM",
        (21, 51): "SLOW",
        (0, 21): "PAUSE"
    }),
    "MEDIUM": RangeKeyDict({
        (86, 101): "FAST",
        (61, 86): "MEDIUM",
        (21, 61): "SLOW",
        (0, 21): "PAUSE"
    }),
    "LOW": RangeKeyDict({
        (90, 101): "FAST",
        (71, 91): "MEDIUM",
        (21, 71): "SLOW",
        (0, 21): "PAUSE"
    })
}

charging_pace_to_optimal_amp_matrix = {
    "FAST": 15,
    "MEDIUM": 11,
    "SLOW": 6,
    "PAUSE": 2
}


def on_log(client, userdata, level, buf):
    k = 0


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("connected ok")
        print("TOTAL SOLAR WATT  |  SOC  |  CALCULATED_OPTIMAL_AMPERE  |  TIMESTAMP")
        print("-------------------------------------------------------------------------------------")
    else:
        print("not connected", rc)


def on_disconnect(client, userdata, flags, rc=0):
    print("disconnect result code " + str(rc))


def on_message(client, userdata, msg):
    global m_decode
    m_decode = str(msg.payload.decode("utf-8", "ignore"))
    time.sleep(1)

    msg_value = str(m_decode)
    topic_key = topic_keys[msg.topic]
    latest_values[topic_key] = int(msg_value)
    latest_calculated_amp = calculate_optimal_ampere(latest_values["total_solar_watt"], latest_values["soc"])
    latest_values[last_calculated_key] = latest_calculated_amp
    latest_tsw = latest_values["total_solar_watt"]
    latest_soc = latest_values["soc"]
    timestamp = datetime.datetime.now()
    key_value_row = \
        '{tsw}                   {soc}             {calculated_optimal_amp}                     {timestamp}'.format(
            tsw=latest_tsw, soc=latest_soc, calculated_optimal_amp=latest_calculated_amp, timestamp=timestamp
        )
    print(key_value_row)
    print("-------------------------------------------------------------------------------------")
    mqtt_test_file = open("mqtt_test.txt", "a")
    mqtt_test_file.write(key_value_row + "\n")
    mqtt_test_file.close()


def calculate_optimal_ampere(total_solar_watt, soc):
    solar_power_mode = tsw_to_solar_power_mode_matrix[total_solar_watt]
    charge_pace = soc_to_charging_pace_matrix[solar_power_mode][soc]
    optimal_amp = charging_pace_to_optimal_amp_matrix[charge_pace]
    return optimal_amp


def set_optimal_ampere(amp):
    if set_to_charger is False:
        return

    files = {
        'action': (None, str(amp)),
    }
    requests.post('http://192.168.4.1', files=files)


broker_address = "127.0.0.1:1883"
client = mqtt.Client("paca")
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_log = on_log
client.on_message = on_message

print("cnct to broker", broker_address)
client.connect("127.0.0.1", 1883, 60)
client.subscribe([("solpiplog/pip/totalsolarw", 2), ("solpiplog/pylon/soc", 2)])
client.loop_forever()
