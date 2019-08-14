import time
import datetime
import json
import requests
import pypyodbc
from influxdb import InfluxDBClient

def loadconfig():
    '''load config.json file'''
    with open('config.json', 'r') as configfile:
        configjson = json.load(configfile)
    return configjson

def postresults(config, results):
    '''insert results to influxdb'''
    client = InfluxDBClient(host=config["InfluxDB"]["Host"], port=config["InfluxDB"]["Port"])
    dbexists = False
    listofdb = client.get_list_database()
    for db in listofdb:
        if db['name'] == config["InfluxDB"]["DB"]:
            dbexists = True
    if not dbexists:
        client.create_database(config["InfluxDB"]["DB"])
    client.switch_database(config["InfluxDB"]["DB"])
    client.write_points(results)

def wanlatencytest(config, results):
    '''Tests download speed of test file from multiple urls'''
    if config["Tests"]["Internal"]:
        internal_start = time.time()
        try:
            r_i = requests.get(config["Internal"]["URL"], stream=True)
            r_i.content
            if not r_i.status_code == config["Internal"]["StatusCode"]:
                raise
        except:
            results["fields"]["internal"] = 0.0
        else:
            results["fields"]["internal"] = time.time() - internal_start
    if config["Tests"]["External"]:
        external_start = time.time()
        try:
            r_e = requests.get(config["External"]["URL"], stream=True)
            r_e.content
            if not r_e.status_code == config["Internal"]["StatusCode"]:
                raise
        except:
            results["fields"]["external"] = 0.0
        else:
            results["fields"]["external"] = time.time() - external_start
    if config["Tests"]["Proxy"]:
        proxy_start = time.time()
        try:
            r_p = requests.get(config["External"]["URL"], stream=True, proxies=config["Proxy"])
            r_p.content
            if not r_p.status_code == config["Internal"]["StatusCode"]:
                raise
        except:
            results["fields"]["proxy"] = 0.0
        else:
            results["fields"]["proxy"] = time.time() - proxy_start

def sqllatencytest(config, results):
    '''Test latency of SQL server'''
    sql_start = time.time()
    try:
        # this is horrible but i cannot find another way to build this string up
        connstring = ""
        connstring += "Driver={ODBC Driver 17 for SQL Server};Server="
        connstring += config["SQL"]["Server"]
        connstring += "\\"
        connstring += config["SQL"]["Instance"]
        connstring += ";"
        connstring += "Port="
        connstring += config["SQL"]["Port"]
        connstring += ";"
        connstring += "Database="
        connstring += config["SQL"]["Database"]
        connstring += ";"
        connstring += "uid="
        connstring += config["SQL"]["UID"]
        connstring += ";"
        connstring += "pwd="
        connstring += config["SQL"]["PWD"]
        connstring += ";"
        conn = pypyodbc.connect(connstring)
        cursor = conn.cursor()
        cursor.execute(config["SQL"]["Query"])
        if not cursor.fetchone()[0] > 1:
            raise
    except:
        results["fields"]["sql"] = 0.0
    else:
        results["fields"]["sql"] = time.time() - sql_start

def coresiteaccesstest(config, results):
    '''Test access to core sites'''
    for site in config["Core"]:
        start_time = time.time()
        try:
            resp = requests.get(config["Core"][site]["URL"], stream=True)
            resp.content
            if not resp.status_code == config["Core"][site]["StatusCode"]:
                raise
            if "Test" in config["Core"][site]:
                if not resp.text[0:6] == config["Core"][site]["Test"]:
                    raise
        except:
            results["fields"][site] = 0.0
        else:
            results["fields"][site] = time.time() - start_time

if __name__ == "__main__":
    starttime = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    config = loadconfig()
    resultarray = []
    results = {}
    results["measurement"] = config["InfluxDB"]["Measurement"]
    results["tags"] = {}
    results["tags"]["site"] = config["Site"]
    results["time"] = starttime
    results["fields"] = {}
    wanlatencytest(config, results)
    if config["Tests"]["SQL"]:
        sqllatencytest(config, results)
    if config["Tests"]["Core"]:
        coresiteaccesstest(config, results)
    resultarray.append(results)
    if config["Debug"]:
        print(json.dumps(resultarray))
    postresults(config, resultarray)
