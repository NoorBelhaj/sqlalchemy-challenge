# Import the dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

import numpy as np
import pandas as pd
import datetime as dt
from dateutil.parser import parse




#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
# Might be a better idea to open the session only when user requests something from a table
# and close it right after
# session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

# Main = / 
# Start at the homepage.
# List all the available routes.
# Route 1 /api/v1.0/precipitation
# Route 2 : /api/v1.0/stations
# # Route 3: /api/v1.0/tobs
# Route 4: /api/v1.0/<start> and /api/v1.0/<start>/<end>
@app.route('/')
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to Hawaii Weather Stations<br/>"
        f"You have access to the following information<br/>"
        f"--------------------------------------------<br/>"
        f"Precipitations: /api/v1.0/precipitation<br/>"
        f"-----------------------<br/>"
        f"List of our Stations:  /api/v1.0/stations<br/>"
        f"-----------------------<br/>"
        f"Temperatures Observed: /api/v1.0/tobs<br/>"
        f"-----------------------<br/>"
        f"Min, Average, Max Temperature since a given date (YYYY-MM-DD): /api/v1.0/start <br/>"
        f"------------------------------------------------------------------------------------<br/>"
        f"Min, Average, Max Temperature for given dates (YYYY-MM-DD): /api/v1.0/start/end <br/>"
        f"--------------------------------------------------------------------------------<br/>"
    )

# Route 1 : /api/v1.0/precipitation
# Convert the query results from your precipitation analysis (i.e. retrieve only the last 
# 12 months of data) to a dictionary using date as the key and prcp as the value.
# Return the JSON representation of your dictionary.

@app.route('/api/v1.0/precipitation')
def precipitation():

# Create our session (link) from Python to the DB
    session = Session(engine)

# Find the most recent date in the data set.
    date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    year_ago = pd.to_datetime(date[0]) - dt.timedelta(days=365)
    yearago = year_ago.date()
    yearago_data = session.query(Measurement.date,Measurement.prcp).filter(Measurement.date >= yearago)
    yearago_df = pd.DataFrame(yearago_data)
    yearago_df.rename(columns={0:"Date",1:"prcp"},inplace=True)
    yearago_df.sort_index(ascending = True,inplace=True)
    precip_dict = yearago_df.to_dict('index')
    return jsonify(precip_dict)

# Close Session
    session.close()

# Route 2 : /api/v1.0/stations
# Return a JSON list of stations from the dataset.
@app.route('/api/v1.0/stations')
# Create our session (link) from Python to the DB
def station_list():
    session = Session(engine)

    station_inventory = session.query(Station.station).all()

    # Close Session
    session.close()

    all_stations = list(np.ravel(station_inventory))
    return jsonify(all_stations)



# Route3: /api/v1.0/tobs
# Query the dates and temperature observations of the most-active station for the 
# previous year of data.
# Return a JSON list of temperature observations for the previous year.
@app.route('/api/v1.0/tobs')
def temp_most_active_station():
# Create our session (link) from Python to the DB
    session = Session(engine)
    date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    year_ago = pd.to_datetime(date[0]) - dt.timedelta(days=365)
    yearago = year_ago.date()
    most_act_st_id = session.query(Measurement.station,func.count(Measurement.station)).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]
    yearago_tobs = session.query(Measurement.date,Measurement.tobs).filter(Measurement.date >= yearago).filter(Measurement.station == most_act_st_id)
    tobs_yearago_df = pd.DataFrame(yearago_tobs)
    tobs_yearago_df.rename(columns={0:"Date",1:"tobs"},inplace=True) 
    tobs_yearago_sorted = tobs_yearago_df.sort_values(by="Date")
    
# Close Session
    session.close()
    tobs_yearago_list = list(np.ravel(tobs_yearago_sorted.to_dict('index')))
    return jsonify(tobs_yearago_list)

def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


# Route 4: /api/v1.0/<start> and /api/v1.0/<start>/<end>
# Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature
# for a specified start or start-end range.
# For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.
# For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates
#  from the start date to the end date, inclusive.
@app.route('/api/v1.0/<start>')
@app.route('/api/v1.0/<start>/<end>')
def min_max_temp_start(start,end=None):
# Create our session (link) from Python to the DB
    if  (is_date(start) == True):
        session = Session(engine)
        if not end:
            end_date = session.query(func.max(Measurement.date)).all()
            for row in end_date:
                end = row[0]

        measures = session.query(func.min(Measurement.tobs),func.avg(Measurement.tobs),func.max(Measurement.tobs)).filter(Measurement.date <=end ).all()
# Close Session
        session.close()
        for row in measures:
            results = [{"Min Temp":row[0], "Average Temp":row[1], "Max Temp":row[2]}]
        
        return jsonify(results)
    else:
        error_date = "Please enter a valid date YYYY-MM-DD"
        return error_date
    


if __name__ == "__main__":
    app.run(debug=True)
