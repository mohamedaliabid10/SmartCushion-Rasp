import os
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO, emit
from influxdb_client import InfluxDBClient
import time
from threading import Thread

app = Flask(__name__)
socketio = SocketIO(app)

# InfluxDB connection details
influxdb_url = "http://192.168.43.134:8087"
influxdb_token = "IqkNTA6RHNJC8Q3O6OJXytKil_zteUXpFKP2-bw8JZKuoiZZbvgwBTV-nq-ClafVK-fHizGHrKd7xg4gHyeAjg=="
influxdb_org = "sofrecom"
influxdb_bucket = "cushiondb"

client = InfluxDBClient(url=influxdb_url, token=influxdb_token)

def fetch_latest_data():
    while True:
        try:
            dht11_query = f"""
                from(bucket: "{influxdb_bucket}")
                    |> range(start: -1d)
                    |> filter(fn: (r) => r._measurement == "ENV_DATA")
                    |> filter(fn: (r) => r._field == "humidity" or r._field == "temperature" or r._field == "voc_index")
                    |> last()
            """
            fsr_query = f"""
                from(bucket: "{influxdb_bucket}")
                    |> range(start: -1d)
                    |> filter(fn: (r) => r._measurement == "sedentary")
                    |> filter(fn: (r) => r._field == "fsr_sum" or r._field == "elapsed_time")
                    |> last()
            """
            
            dht11_tables = client.query_api().query(dht11_query, org=influxdb_org)
            fsr_tables = client.query_api().query(fsr_query, org=influxdb_org)

            results = {"dht11": {}, "fsr": {}}

            for table in dht11_tables:
                for record in table.records:
                    results["dht11"][record["_field"]] = record.get_value()

            for table in fsr_tables:
                for record in table.records:
                    results["fsr"][record["_field"]] = record.get_value()

            socketio.emit("update_data", results)
        except Exception as e:
            print(f"Error fetching data: {e}")
        
        time.sleep(1)

fetch_thread = Thread(target=fetch_latest_data)
fetch_thread.daemon = True
fetch_thread.start()

@app.route("/get", methods=["GET"])
def get_latest_data():
    try:
        dht11_query = f"""
            from(bucket: "{influxdb_bucket}")
                |> range(start: -1d)
                |> filter(fn: (r) => r._measurement == "ENV_DATA")
                |> filter(fn: (r) => r._field == "humidity" or r._field == "temperature" or r._field == "voc_index")
                |> last()
        """
        fsr_query = f"""
            from(bucket: "{influxdb_bucket}")
                |> range(start: -1d)
                |> filter(fn: (r) => r._measurement == "sedentary")
                |> filter(fn: (r) => r._field == "fsr_sum" or r._field == "elapsed_time")
                |> last()
        """
        
        dht11_tables = client.query_api().query(dht11_query, org=influxdb_org)
        fsr_tables = client.query_api().query(fsr_query, org=influxdb_org)

        results = {"dht11": {}, "fsr": {}}

        for table in dht11_tables:
            for record in table.records:
                results["dht11"][record["_field"]] = record.get_value()

        for table in fsr_tables:
            for record in table.records:
                results["fsr"][record["_field"]] = record.get_value()

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("fetch_data")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=3003, debug=True)
