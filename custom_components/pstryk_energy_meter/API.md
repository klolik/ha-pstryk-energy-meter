# Endpoints

Pstryk Energy Meter exposes local API on its Wifi interface.

```
$ curl -s http://hostname/info |jq .
{
  "device": {
    "deviceName": "Pstryk",
    "type": "multiSensor",
    "product": "PstrykEnergyMeter",
    "hv": "sMbB-1.0",
    "fv": "0.1143",
    "universe": 20,
    "categories": [
      4
    ],
    "apiLevel": "20241124",
    "id": "XXXXXXXXXXXX",
    "ip": "xxx.xxx.xxx.xxx",
    "availableFv": null
  }
}
```

```
$ curl -s http://hostname/state
{
  "multiSensor": {
    "periodicCounter": {
      "enabled": 0,
      "resetType": 3
    },
    "energyMeter": {
      "measureReverseEnergy": {
        "enabled": 1
      }
    },
    "sensors": [
      {
        "id": 0,
        "type": "activePower|apparentEnergy|apparentPower|current|forwardActiveEnergy|forwardReactiveEnergy|frequency|reactivePower|reverseActiveEnergy|reverseReactiveEnergy|voltage",
        "name": "", # not populated (yet?)
        "value": 586,
        "state": 2,
        "iconSet": 89
      },
      # ...
    ]
  }
}
```


```
Sensors:
Current 0: 1,145 mA
Current 1: 5,457 mA
Current 2: 5,413 mA
Current 3: 5,476 mA
Power 0: 3,842 W
Power 1: 1,282 W
Power 2: 1,272 W
Power 3: 1,287 W
Voltage 0: 237.0 V
Voltage 1: 237.0 V
Voltage 2: 237.2 V
Voltage 3: 237.6 V
```

```
Sensors:
Current 0: 1,319 mA
Current 1: 10,835 mA
Current 2: 10,750 mA
Current 3: 10,808 mA
Power 0: 7,640 W
Power 1: 2,552 W
Power 2: 2,537 W
Power 3: 2,550 W
Voltage 0: 236.1 V
Voltage 1: 236.1 V
Voltage 2: 236.5 V
Voltage 3: 236.7 V
```
