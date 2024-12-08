import os
import dotenv
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

dotenv.load_dotenv()


ACCUWEATHER_API_KEY = os.getenv("ACCUWEATHER_API_KEY")

def get_location_key(city):
    base_url = 'http://dataservice.accuweather.com/locations/v1/cities/search'
    params = {
        'apikey': ACCUWEATHER_API_KEY,
        'q': city
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200 and response.json():
        return response.json()[0]['Key']
    return None

def get_weather_forecast(location_key):
    base_url = f'http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}'
    params = {
        'apikey': ACCUWEATHER_API_KEY,
        'metric': 'true'
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        forecast = response.json()
        daily_forecast = forecast['DailyForecasts'][0]
        return {
            'temperature_min': daily_forecast['Temperature']['Minimum']['Value'],
            'temperature_max': daily_forecast['Temperature']['Maximum']['Value'],
            'day_precipitation': daily_forecast['Day']['HasPrecipitation'],
            'night_precipitation': daily_forecast['Night']['HasPrecipitation'],
            'precipitation_type_day': daily_forecast['Day'].get('PrecipitationType', 'None'),
            'precipitation_type_night': daily_forecast['Night'].get('PrecipitationType', 'None'),
            'precipitation_intensity_day': daily_forecast['Day'].get('PrecipitationIntensity', 'None'),
            'precipitation_intensity_night': daily_forecast['Night'].get('PrecipitationIntensity', 'None'),
            'headline': forecast['Headline']['Text']
        }
    return None

def check_bad_weather(weather_data):
    bad_weather_conditions = [
        weather_data['temperature_min'] < -2,  # Very cold
        weather_data['temperature_max'] > 30,  # Very hot
        weather_data['day_precipitation'] or weather_data['night_precipitation'],  # Any precipitation
        'Snow' in weather_data['precipitation_type_day'] or 'Snow' in weather_data['precipitation_type_night'],
        'Freezing' in weather_data['precipitation_type_day'] or 'Freezing' in weather_data['precipitation_type_night']
    ]
    
    return any(bad_weather_conditions)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_city = request.form['start_city']
        end_city = request.form['end_city']

        try:
            start_location_key = get_location_key(start_city)
            end_location_key = get_location_key(end_city)

            if not start_location_key or not end_location_key:
                return render_template('index.html', error='Could not find location information')

            start_weather = get_weather_forecast(start_location_key)
            end_weather = get_weather_forecast(end_location_key)

            if not start_weather or not end_weather:
                return render_template('index.html', error='Could not retrieve weather information')

            start_bad_weather = check_bad_weather(start_weather)
            end_bad_weather = check_bad_weather(end_weather)

            result = {
                'start_city': start_city,
                'end_city': end_city,
                'start_weather': start_weather,
                'end_weather': end_weather,
                'start_bad_weather': start_bad_weather,
                'end_bad_weather': end_bad_weather
            }

            return render_template('result.html', result=result)

        except Exception as e:
            return render_template('index.html', error=str(e))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)