"""Gets metrics from endpoints via SSH, parses to spec; sends to Influx

    Uses a provided inventory.yaml file which defines the devices and
    commands to process.  Then references the environment
    optionsconfig.yaml which contains management IP addresses and
    credentials.  Once the commands are efficiently extracted via SSH
    it references the parse-specs.yaml file which defines the regex
    matching rules, measurement name, tags, keys, and data types.
    Finally the script forms the output into Influx write line protocol
    for injection to InfluxDB.

    Args:
        var_TBD: Description_TBD

    Inputs/Reference files:
        parameters.yaml - (optional name) contains inventory, command,
            regex pattern and influx key/tag specs in YAML format
            (See parameters-example.yaml for formatting guidance)
        optionsconfig.yaml - contains secret credential information

    Returns:
        Description TBD

    Raises:
        RaiseNameTBD: Description_TBD


    Version: 5 2022-0420
    normalized to take any command input
    Version: 6 2023-0605
        Added capability to specify target Influx server in YAML file
    Version: 7 2023-0629
        Updates to documentation
"""

# Credits:
__version__ = '2'
__author__ = 'Jason Davis - jadavis@cisco.com'
__license__ = 'Cisco Sample Code License, Version 1.1 - ' \
    'https://developer.cisco.com/site/license/cisco-sample-code-license/'


import asyncio
import asyncssh
import sys
import time
import yaml
import re
import argparse
import os
import pprint
import datetime
import schedule
import threading
import GetEnv
import requests


class SSHTarget:
    def __init__(self, info):
        self.alias = info["hostalias"]
        self.mgmt = info["host"]
        self.username = info["username"]
        self.password = info["password"]
        self.commands = info["commands"]
        # print(f'\n\n=====Learning device: {self.alias}')
        self.server_version, self.prompt = self.get_prompt(self.mgmt,
            self.username,
            self.password)
        print(f'{self.alias} initialized')
        if DEBUG: print(f'prompt is [{self.prompt}]\n'
              f'SSH server type is [{self.server_version}]')
        #if DEBUG: print(self)

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def __exit__(self, exc_type, exc_value, traceback):
        print("exited")

    async def _get_prompt(self, device, username, password):
        async with asyncssh.connect(device, username=username,
                                    password=password,
                                    client_keys=None,
                                    known_hosts=None) as conn:
            server_version = conn.get_extra_info(name='server_version')
            #if DEBUG: print(f'DEBUG: Socket connection info:\n'
            #                f'{conn.get_extra_info("socket")}')
            if 'Cisco' in server_version:
                # Yeah - got a Cisco device
                async with conn.create_process(term_type="vt100") as process:
                    process.stdin.write('!test\n!test')
                    #process.stdin.write("w\n")
                    while True:
                        line = await process.stdout.readline()
                        if line:
                            if DEBUG: print(f'DEBUG: Got line [{line}]')
                            match = re.search(r'(\S+)!test', line, re.S | re.M)
                            if match:
                                prompt = match.group(1)
                                if DEBUG: print(f'DEBUG: Got prompt: [{prompt}]')
                                break
                    process.close()
                    conn.close()
                    return server_version, prompt
            elif 'Ubuntu' in server_version:
                # OK - we got an Ubuntu endpoint
                return server_version, ':~$'
            else:
                # OK - something else
                return server_version, '$'

    def get_prompt(self, device, username, password):
        if DEBUG: print('Starting get_prompt')
        try:
            return asyncio.run(self._get_prompt(device, username,
                                                password))
        except (OSError, asyncssh.Error) as exc:
            sys.exit('SSH connection failed: ' + str(exc))

    async def _run_command(self):
        async with asyncssh.connect(self.mgmt, username=self.username,
                                    password=self.password,
                                    client_keys=None,
                                    known_hosts=None) as conn:
            print(f'Connection made to {self.alias} / '
                  f'{conn.get_extra_info("peername")[0]}:'
                  f'{conn.get_extra_info("peername")[1]} with prompt '
                  f'<{self.prompt}>')
            result = ''
            process = await conn.create_process(request_pty='force',
                                                term_type="vt100")
            process.stdin.write("\n")
            try:
                result += await asyncio.wait_for(
                            process.stdout.readuntil(self.prompt),
                            timeout=10)
            except Exception as e:
                print(f'prompt timeout step {e}')
            if DEBUG: print(f'Session prompt output: [{result}]')

            if 'Cisco' in self.server_version:
                # Prep env with 'term len 0'
                command = 'terminal length 0'
                if DEBUG: print(f'Working command - [{command}]')
                await asyncio.wait_for(process.stdout.readuntil(self.prompt),
                                       timeout=5)
                process.stdin.write(command + "\n")
                process.stdin.write("\n")
                result = ''
                try:
                    result += await asyncio.wait_for(
                                process.stdout.readuntil(self.prompt),
                                timeout=10)
                except Exception as e:
                    print(f'prompt timeout step {e}')

                if DEBUG: print(f'Command [{command}] output:\n[{result}]')

            # Start specific command collection
            output_records = []
            if DEBUG: print(f'DEBUG: Commands to execute are:\n{self.commands}')
            for item in self.commands:
                command=item['cmd']
                parsespec=item['parsespec']
                if DEBUG: print(f'DEBUG: Working command - <{command}> '
                                f'and parsespec <{parsespec}>')
                await asyncio.wait_for(process.stdout.readuntil(self.prompt),
                                       timeout=10)
                process.stdin.write(command + "\n")
                process.stdin.write("\n")
                result = ''
                try:
                    result += await asyncio.wait_for(
                                process.stdout.readuntil(self.prompt),
                                timeout=10)
                except Exception as e:
                    print(f'prompt timeout step {e}')

                if DEBUG: print(f'Command specific [{command}] output:\n[{result}]')
                output_records.append((self.alias, command, parsespec,
                                       result))
            conn.close()
            return output_records

    def run_commands(self):
        #print(f'\n\n=====Collecting commands for device: {self.alias}')

        try:
            return asyncio.run(self._run_command())
        except Exception as exc:
            sys.exit('SSH connection failed: ' + str(exc))
        # except (OSError, asyncssh.Error, asyncio.exceptions.TimeoutError) as exc:
            # sys.exit('SSH connection failed: ' + str(exc))


def get_arguments():
    # Obtain parameters yaml file from user/CLI
    parser = argparse.ArgumentParser(description='Obtain metrics from '
                                     'a device via SSH; parse and '
                                     'format for InfluxDB')
    parser.add_argument('-d', '--debug', action='store_const',
                        default=False,
                        const=True,
                        dest='debug',
                        help='Enables debug with copious console '
                        'output, but none to InfluxDB')
    parser.add_argument('-p', '--paramfile', metavar='paramfile',
                        required=True,
                        help='YAML file with inventory and parsing specs')
    parser.add_argument('-g', '--group', metavar='group',
                        default="device_inventory",
                        help=('Device group from optionsconfig.yaml '
                            '(default of "device_inventory")'))
    parser.add_argument('-f', '--frequency', metavar='frequency',
                        default=300,
                        type=int,
                        help='Frequency (in seconds) to repeat '
                             'collection (default of 300 seconds)')
    args = parser.parse_args()
    return args


def get_params(paramfile, params):
    # Read specifications file (YAML) that defines how to parse the
    #   CLI output - return to keep in memory for other processing
    with open(paramfile, 'r') as file:
        dictionary = yaml.safe_load(file)

    try:
        paramresults = eval(f'dictionary{params}')
    except KeyError:
        paramresults = None
    return paramresults


def get_work(workparams, devicecreds):
    # Get work - items, credentials and commands to execute
    # Start by getting list of environment devices from optionsconfig.yaml
    #   allow user to define device group that maps to optionconfig.yaml
    groupcommands = workparams.get('groupcommands', None)
    if groupcommands == None: groupcommands = list()
    default_cred_set = workparams['credential_set']
    default_creds = GetEnv.getparam(default_cred_set)

    if DEBUG: print(workparams['hosts'])
    worklist = []
    for item in workparams['hosts']:
        host = item.get("host")
        specificcommands = item.get("commands")
        if DEBUG: print(host, specificcommands)
        try:
            device = [device for device in devicecreds if device['alias'] == host][0]
        except IndexError:
            print(f'WARNING: device {host} is not found in '
                  'optionsconfig.yaml - skipping')
            continue
        if DEBUG: print(device)
        username = device.get('username', default_creds["username"])
        password = device.get('password', default_creds["password"])
        mgmthostnameip = device['mgmt_hostnameip']

        if specificcommands is None:
            commands = groupcommands
        else:
            commands = item['commands'] + groupcommands
        # print(username, password, commands)
        worklist.append({"hostalias": host,
                         "host": mgmthostnameip,
                         "username": username,
                         "password": password,
                         "commands": commands,
                         })
    if DEBUG: print(worklist)
    return worklist


def get_run_specs(args):
    # Read Influx target, if needed
    altinflux = get_params(args.paramfile, "['InfluxDB']")
    if altinflux is None or DEBUG:
        influxenv = GetEnv.getparam("InfluxDB")
        print(f'Using project-wide Influx server: {influxenv["alias"]}')
    else:
        influxenv = GetEnv.getparam(altinflux)
        print(f'Using alternative Influx server: {influxenv["alias"]}')

    # Read inventory from job-specific parameters file to build work list
    inventory = get_params(args.paramfile, '["inventory"]')
    if DEBUG: print(f'\nDEBUG====Inventory specs\n{inventory}')
    # Read group parameters info from environment optionconfig.yaml to
    # map device IPs and creds
    deviceparams = GetEnv.getparam(args.group)
    if DEBUG: print(f'\nDEBUG=====Device Parameters\n{deviceparams}')

    worklist = get_work(inventory, deviceparams)
    if DEBUG: print(f'\nDEBUG=====Work list\n{worklist}')

    # Do initial connections and prompt determination with devices
    print('\n=====Learning device prompts')
    inventory = {item["hostalias"]: SSHTarget(item) for item in worklist}
    if DEBUG: print(f'\nDEBUG=====Inventory\n{inventory}')

    # Read the parsing specifications file containing regex matches and
    #   influx measurement/tag/key assignments
    parse_specs = get_params(args.paramfile, '["parsespecs"]')
    if DEBUG: print(f'\nDEBUG==== Pattern Matching Specs are:\n{parse_specs}')

    return worklist, inventory, parse_specs, influxenv


def extract_matches(parsespecs, aggregate_output):
    # Use the specs input to do pattern matches against the output
    measurements = []
    print(f'\n\n=====Processing output of hosts...')

    if DEBUG:
        print('DEBUG: Aggregate output is:')
        pprint.pprint(aggregate_output)
    for device_results in aggregate_output:
        for output in device_results:
            print(f'Processing: {output[0]}')
            if DEBUG: print(f'\nDEBUG: Working on device <{output[0]}> '
                            f'for command <{output[1]}> '
                            f'with parsespec <{output[2]}>')
            parsespec = [parsespec for parsespec in parsespecs
                         if parsespec["parsespec"] == output[2]][0]
            if DEBUG:
                print('DEBUG: Match spec being used is:')
                pprint.pprint(parsespec)
            measurement = [output[0], parsespec["measurement"]]
            if DEBUG: print(f'DEBUG: Measurement currently: {measurement}')

            statictags = parsespec.get("statictags")
            if statictags:
                if DEBUG: print(f'DEBUG extract_matches(iterative): Static tags are: {statictags}')
                for statictag in statictags:
                    tagname = statictag.get("tagname")
                    tagvalue = statictag.get("tagvalue")
                    measurement.append((tagname, 'tag', 'string',
                                        tagvalue))

            if parsespec["matchtype"] == 'single':
                x = re.search(fr'{parsespec["regex"]}', output[3])
                if x:
                    if DEBUG: print(f'DEBUG: Matching groups -  {x.groups()}')
                    for index, item in enumerate(x.groups(), start=1):
                        matchname = f'parsespec["match{index}"]'
                        matchkeytype = f'parsespec["match{index}keytype"]'
                        matchvaluetype = f'parsespec["match{index}valuetype"]'
                        matchvalue = f'{item}'
                        # print(key, keytype)
                        if DEBUG: print(f'DEBUG: Tag |{eval(matchname)}|'
                                        f'is a |{eval(matchkeytype)}| '
                                        f'of type {eval(matchvaluetype)} '
                                        f'with value: |{matchvalue}|')
                        measurement.append((eval(matchname),
                                            eval(matchkeytype),
                                            eval(matchvaluetype),
                                            matchvalue))
                    measurements.append(measurement)

            elif parsespec["matchtype"] == 'multiple':
                if DEBUG: print(f'DEBUG: regex pattern is:\n{parsespec["regex"]}')
                if DEBUG: print(f'DEBUG: output to search is:\n{output[3]}')
                matches = re.findall(fr'{parsespec["regex"]}', output[3],
                               re.S | re.M)
                if DEBUG: print(f'DEBUG: Groups matching are:\n{matches}')
                for matcheditem in matches:
                    if DEBUG: print(f'DEBUG: Processing item: {matcheditem}')
                    # Reset measurement for each instance (only multiple)
                    measurement = [output[0], parsespec["measurement"]]
                    for index, item in enumerate(matcheditem, start=1):
                        # Get individual match data
                        matchname = f'parsespec["match{index}"]'
                        matchkeytype = f'parsespec["match{index}keytype"]'
                        matchvaluetype = f'parsespec["match{index}valuetype"]'
                        matchvalue = f'matcheditem[{index - 1}]'
                        # print(key, keytype)
                        if DEBUG: print(f'DEBUG:    Tag |{eval(matchname)}| '
                                        f'is a |{eval(matchkeytype)}| '
                                        f'of type {eval(matchvaluetype)} '
                                        f'with value: |{eval(matchvalue)}|')
                        measurement.append((eval(matchname),
                                            eval(matchkeytype),
                                            eval(matchvaluetype),
                                            eval(matchvalue)))
                    measurements.append(measurement)
                if DEBUG:
                    print('DEBUG: Current measurements are:')
                    pprint.pprint(measurements)
                            
            elif parsespec["matchtype"] == 'iterative':
                measurement = [output[0], parsespec["measurement"]]
                if DEBUG:
                    print(f'DEBUG extract_matches(iterative): Current measurement is:')
                    pprint.pprint(measurement)
                regexmatches = parsespec["regexmatches"]
                for groupspec in regexmatches:
                    if DEBUG:
                        print(f'DEBUG extract_matches(iterative): Current groupspec is:')
                        pprint.pprint(groupspec)
                    # See if we have a multimatch group - special handling
                    if "groups" in groupspec:
                        x = re.findall(fr'{groupspec["regex"]}',
                                       output[3])
                        # TO-DO: Add logic for no match
                        if DEBUG: print(f'DEBUG: group match(es) is/are:\n {x}')
                        # for groupmatch in groupspec["groups"]:
                        for count, match in enumerate(x):
                            measurement.append((groupspec["groups"][count]["groupname"],
                                                groupspec["groups"][count]["groupkeytype"],
                                                groupspec["groups"][count]["groupvaluetype"],
                                                match.strip()))
                    else:
                        # Regular processing
                        x = re.search(fr'{groupspec["regex"]}', 
                                          output[3])
                        if x == None:
                            print(f'WARNING: No match of [{groupspec["regex"]}] on {output[0]} - skipping')
                            continue
                        if DEBUG: print(f'DEBUG groupmatch is: {x.group(1)}')
                        measurement.append((groupspec["groupname"],
                                            groupspec["groupkeytype"],
                                            groupspec["groupvaluetype"],
                                            x.group(1).strip()))
                measurements.append(measurement)
    return measurements


def assemble_influx_lp(measurements):
    # Take list of measurements and assemble into Influx Line Protocol
    if DEBUG: print(f'DEBUG assemble_influx_lp: Measurements to process:\n{measurements}')
    influxlines = ""
    for item in measurements:
        if DEBUG: print(f'DEBUG assemble_influx_lp: Working item:\n{item}')
        device = item.pop(0)
        measurement = item.pop(0)
        mtags = [x for x in item if x[1] == 'tag']
        mfields = [x for x in item if x[1] == 'field']
        if DEBUG: print(f'Tags: {mtags}\nKeys: {mfields}')
        influxline = f'{measurement},device={device},'
        for mtagitem in mtags:
            tagkey = f'{mtagitem[0]}={mtagitem[3]}'.replace(' ', '\ ')
            # print(f'|{tagkey}|')
            nonspacestr = re.sub(r'(\\\s){2,}', "", tagkey)
            if nonspacestr.endswith('\ '):
                nonspacestr = nonspacestr.replace('\ ', '')
            influxline += nonspacestr + ','
        influxline = influxline.rstrip(',')
        influxline += ' '
        for mfielditem in mfields:
            # if string
            if mfielditem[2] == 'string':
                influxline += f'{mfielditem[0]}="{mfielditem[3]}",'
            else:
                # if float, int, boolean, decimal
                influxline += f'{mfielditem[0]}={mfielditem[3]},'
        influxline = influxline.rstrip(',')
        if DEBUG: print(f'DEBUG assemble_influx_lp: current influxline - {influxline}')
        influxlines += influxline + '\n'
    if DEBUG: print(f'DEBUG assemble_influx_lp: influxlines are\n{influxlines}')
    return influxlines


def send_to_influx(influxenv, measurements):
    influxurl = (f'{influxenv["protocol"]}://'
                 f'{influxenv["host"]}:{influxenv["port"]}'
                 f'/api/v2/write?bucket={influxenv["bucket"]}'
                 f'&org={influxenv["org"]}&precision=s')

    headers = {
    'Accept': 'application/json',
    'Authorization': 'Token ' + influxenv["token"],
    'Content-Type': 'text/plain'
    }

    try:
        response = requests.request("POST", influxurl, headers=headers,
                                    data=measurements)
        response.raise_for_status()
        print(f'{response.status_code} - {response.reason} - {response.text}')
        if response.status_code == 204:
            print('Good data push to InfluxDB')
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting to InfluxDB server!  Error was:\n", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Oops: Something Else", err)
    
    print(f'\nFinished at: {str(time.ctime())}')


def main_loop(worklist, inventory, parse_specs, influxenv):
    # At this point we've built a list of workable items, we can now
    #   build an asynchronous work queue and execute as fast as they
    #   respond
    startTime = time.time()
    command_results = []
    print(f'\n=====Collecting commands for hosts...')
    for item in worklist:
        command_results.append(inventory[item['hostalias']].run_commands())

    # if DEBUG: print(command_results)
    measurements = extract_matches(parse_specs, command_results)
    if DEBUG: print(measurements)
    influx_lines = assemble_influx_lp(measurements)
    print(f'\nCOMPLETE with command processing - Final influx write line output is:\n{influx_lines}')
    
    # Send to Influx
    if not DEBUG:
        send_to_influx(influxenv, influx_lines)
    executionTime = (time.time() - startTime)
    print(f'Execution time in seconds: {executionTime:.3f}')
    
    print(f'\nWaiting {FREQUENCY} seconds until next poll.', end='', flush=True)


def run_threaded(job_func, worklist, inventory, parse_specs, influxenv):
    job_thread = threading.Thread(target=job_func, args=(worklist,
                                                         inventory,
                                                         parse_specs,
                                                         influxenv,))
    print(f'\nRunning thread {threading.current_thread()}')
    job_thread.start()


####
if __name__ == '__main__':
    execstartTime = datetime.datetime.now()

    # Get command-line arguments or warn and exit
    args = get_arguments()

    DEBUG = args.debug
    FREQUENCY = args.frequency
    print(f'Starting script {os.path.basename(__file__)} with '
          f'parameters file "{args.paramfile}" at {execstartTime} '
          f'with DEBUG {DEBUG}')

    # Run process manually first, then schedule per spec
    worklist, inventory, parse_specs, influxenv = get_run_specs(args)
    main_loop(worklist, inventory, parse_specs, influxenv)

    # If we're running in DEBUG mode we won't schedule repeated runs
    if DEBUG: sys.exit('\nCompleted debug run')

    schedule.every(args.frequency).seconds.do(run_threaded,
                                              main_loop,
                                              worklist,
                                              inventory,
                                              parse_specs,
                                              influxenv)

    try:
        while True:
            print('.', end='', flush=True)
            schedule.run_pending()
            time.sleep(5)
    except KeyboardInterrupt:
        print('\nUser initiated stop - shutting down...')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
