import api_interface as a
import sql

def parse_new_command(new_command, force_status, thermostat_status, thermostat_temp):
    if "Force" in new_command:
        arg = new_command.split(" ")[1]
        if arg == "On":
            force_status = True
        elif arg == "Off":
            force_status = False
        elif arg == "Auto":
            force_status = None
    elif "Thermostat" in new_command:
        arg,thermostat_temp = new_command.split(" ")[1:3]
        if arg == "On":
            thermostat_status = True
        elif arg == "Off":
            thermostat_status = False
    return force_status, thermostat_status, thermostat_temp

def test_thermostat(thermostat_status, thermostat_temp):
    last_temp = float(sql.get_last_record('deux')[0])
    if last_temp < int(thermostat_temp):
        return True
    else: 
        return False

def thermostat(in_q,out_q):
    thermostat_status = False
    force_status = False
    thermostat_temp = None
    last_current_state = False

    #api_interface = a.API_Interface()

    while True:
        new_command = in_q.get()
        if sql.VERBOSE : print("new command:",new_command)
        if new_command:
            force_status, thermostat_status, thermostat_temp = parse_new_command(new_command, force_status, thermostat_status, thermostat_temp)
            
        if not force_status is None:
            current_state = force_status
            
        elif thermostat_status:
            current_state = test_thermostat(thermostat_status, thermostat_temp)

        if last_current_state != current_state:
            if sql.VERBOSE : print("current state",current_state)
            last_current_state = current_state
            #call_successful, response = api_interface.set_module(a.CONTACTORS_ID[0],current_state)
            call_successful, response = True, {"status":"ok","time_exec":"0.060059070587158","time_server":"1553777827","body":{"errors":[]}}
            if call_successful:
                http_response = "API call successful - {}".format(sql.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            else:
                http_response = str(response) + str(sql.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            if sql.VERBOSE : print(http_response)
            out_q.put(http_response)
        else:
            http_response = "No call to API - {}".format(sql.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            if sql.VERBOSE : print(http_response)
            out_q.put(http_response)
