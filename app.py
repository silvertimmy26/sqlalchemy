# Import the dependencies
import numpy as np
import pandas as pd
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

#################################################
# Database Setup
#################################################

# Create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    return (
        f"Hi! Welcome to my climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"Enter a start date in the format 'YYYY-MM-DD' to get the minimum, average, and maximum temperature from that date:<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"Enter a start date and an end date in the format 'YYYY-MM-DD' to get the minimum, average, and maximum temperature between those dates:<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt"
    )

# Return precipitation data for the last year
@app.route("/api/v1.0/precipitation")
def precipitation():
    most_recent_date = session.query(func.max(Measurement.date)).scalar() # .first() was throwing errors so I switched to .scalar()
    most_recent_date_dt = datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = (most_recent_date_dt - timedelta(days=365)).strftime('%Y-%m-%d')

    precipitation_data = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= one_year_ago).all()
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    return jsonify(precipitation_dict)

# Return data of ALL stations in the database
@app.route("/api/v1.0/stations")
def stations():
    stations_query = session.query(Station.station).all()
    stations_list = [station[0] for station in stations_query]
    return jsonify(stations_list)

# Return data for the most active station for the last year
@app.route("/api/v1.0/tobs")
def tobs():
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date_dt = datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = (most_recent_date_dt - timedelta(days=365)).strftime('%Y-%m-%d')

    most_active_station = session.query(Measurement.station).group_by(
        Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]

    tobs_data = session.query(Measurement.date, Measurement.tobs).filter(
        Measurement.station == most_active_station).filter(
        Measurement.date >= one_year_ago).all()
    return jsonify([temp for date, temp in tobs_data])

# Return the temperature min, avg, and max for dates between the specified start and end
@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end):
    results = (
        session.query(
            func.min(Measurement.tobs),
            func.max(Measurement.tobs),
            func.avg(Measurement.tobs)
        )
        .filter(Measurement.date >= start)
        .filter(Measurement.date <= end)
        .all()
    )
    stats = {"MIN": results[0][0], "MAX": results[0][1], "AVG": results[0][2]}
    return jsonify(stats)

# Return min, avg, and max for all dates starting at the start date
@app.route("/api/v1.0/<start>")
def start_date(start):
    results = (
        session.query(
            func.min(Measurement.tobs),
            func.max(Measurement.tobs),
            func.avg(Measurement.tobs)
        )
        .filter(Measurement.date >= start)
        .all()
    )
    stats = {"MIN": results[0][0], "MAX": results[0][1], "AVG": results[0][2]}
    return jsonify(stats)

@app.teardown_appcontext
def shutdown_session(exception=None):
    session.close()
