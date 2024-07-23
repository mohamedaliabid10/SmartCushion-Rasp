import os
from flask import Flask, jsonify,request
from flask_socketio import SocketIO, emit
from influxdb_client import InfluxDBClient
import time
from threading import Thread
from datetime import datetime,timedelta
app = Flask(__name__)
socketio = SocketIO(app)

# InfluxDB connection details
influxdb_url = "http://192.168.43.134:8087"
influxdb_token = "IqkNTA6RHNJC8Q3O6OJXytKil_zteUXpFKP2-bw8JZKuoiZZbvgwBTV-nq-ClafVK-fHizGHrKd7xg4gHyeAjg=="
influxdb_org = "sofrecom"
influxdb_bucket = "cushiondb"

client = InfluxDBClient(url=influxdb_url, token=influxdb_token)

def execute_posture_query(query):
    try:
        tables = client.query_api().query(query, org=influxdb_org)
        posture_counts = {}
        for table in tables:
            for record in table.records:
                posture = record.get_value()
                if posture not in posture_counts:
                    posture_counts[posture] = 0
                posture_counts[posture] += 1
        return [{"posture": posture, "count": count} for posture, count in posture_counts.items()]
    except Exception as e:
        return {"error": str(e)}


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
            posture_query = f"""
                from(bucket: "{influxdb_bucket}")
                    |> range(start: -1d)
                    |> filter(fn: (r) => r._measurement == "posture")
                    |> filter(fn: (r) => r._field == "posture")
                    |> last()
            """
            
            dht11_tables = client.query_api().query(dht11_query, org=influxdb_org)
            fsr_tables = client.query_api().query(fsr_query, org=influxdb_org)
            posture_tables = client.query_api().query(posture_query, org=influxdb_org)

            results = {"dht11": {}, "fsr": {}, "posture": {}}

            for table in dht11_tables:
                for record in table.records:
                    results["dht11"][record["_field"]] = record.get_value()

            for table in fsr_tables:
                for record in table.records:
                    results["fsr"][record["_field"]] = record.get_value()
            
            for table in posture_tables:
                for record in table.records:
                    results["posture"][record["_field"]] = record.get_value()

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
        posture_query = f"""
            from(bucket: "{influxdb_bucket}")
                |> range(start: -1d)
                |> filter(fn: (r) => r._measurement == "posture")
                |> filter(fn: (r) => r._field == "posture")
                |> last()
        """
        
        dht11_tables = client.query_api().query(dht11_query, org=influxdb_org)
        fsr_tables = client.query_api().query(fsr_query, org=influxdb_org)
        posture_tables = client.query_api().query(posture_query, org=influxdb_org)

        results = {"dht11": {}, "fsr": {}, "posture": {}}

        for table in dht11_tables:
            for record in table.records:
                results["dht11"][record["_field"]] = record.get_value()

        for table in fsr_tables:
            for record in table.records:
                results["fsr"][record["_field"]] = record.get_value()

        for table in posture_tables:
            for record in table.records:
                results["posture"][record["_field"]] = record.get_value()

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/history/daily", methods=["GET"])
def get_daily_posture_history():
    today = datetime.now()
    start_of_day = today.strftime('%Y-%m-%dT00:00:00Z')
    end_of_day = today.strftime('%Y-%m-%dT23:59:59Z')
    query = f"""
        from(bucket: "{influxdb_bucket}")
            |> range(start: {start_of_day}, stop: {end_of_day})
            |> filter(fn: (r) => r._measurement == "posture")
            |> filter(fn: (r) => r._field == "posture")
    """
    result = execute_posture_query(query)
    return jsonify({'data': result, 'date_range': today.strftime('%d-%m-%Y')})


@app.route("/history/weekly", methods=["GET"])
def get_weekly_posture_history():
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=4)
    query = f"""
        from(bucket: "{influxdb_bucket}")
            |> range(start: {start_of_week.strftime('%Y-%m-%dT00:00:00Z')}, stop: {end_of_week.strftime('%Y-%m-%dT23:59:59Z')})
            |> filter(fn: (r) => r._measurement == "posture")
            |> filter(fn: (r) => r._field == "posture")
    """
    result = execute_posture_query(query)
    return jsonify({'data': result, 'date_range': f"{start_of_week.strftime('%d-%m-%Y')} to {end_of_week.strftime('%d-%m-%Y')}"})

@app.route("/history/monthly", methods=["GET"])
def get_monthly_posture_history():
    start_of_month = datetime.now().replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    query = f"""
        from(bucket: "{influxdb_bucket}")
            |> range(start: {start_of_month.strftime('%Y-%m-%dT00:00:00Z')}, stop: {end_of_month.strftime('%Y-%m-%dT23:59:59Z')})
            |> filter(fn: (r) => r._measurement == "posture")
            |> filter(fn: (r) => r._field == "posture")
    """
    result = execute_posture_query(query)
    return jsonify({'data': result, 'date_range': f"{start_of_month.strftime('%d-%m-%Y')} to {end_of_month.strftime('%d-%m-%Y')}"})

@app.route("/history/range", methods=["GET"])
def get_posture_history_range():
    date_range = request.args.get('date_range')  # Expects 'DD/MM/YYYY to DD/MM/YYYY'
    if not date_range:
        return jsonify({"error": "No date range provided"}), 400

    try:
        start_date_str, end_date_str = date_range.split(' to ')
        # Convert date strings from DD/MM/YYYY to YYYY-MM-DD
        start_date = datetime.strptime(start_date_str, '%d/%m/%Y').strftime('%Y-%m-%dT00:00:00Z')
        end_date = datetime.strptime(end_date_str, '%d/%m/%Y').strftime('%Y-%m-%dT23:59:59Z')

        query = f"""
            from(bucket: "{influxdb_bucket}")
                |> range(start: {start_date}, stop: {end_date})
                |> filter(fn: (r) => r._measurement == "posture")
                |> filter(fn: (r) => r._field == "posture")
        """
        result = execute_posture_query(query)
        return jsonify({'data': result, 'date_range': f"{start_date_str} to {end_date_str}"})
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use DD/MM/YYYY to DD/MM/YYYY format."}), 400


@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("fetch_data")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=3003, debug=True)
