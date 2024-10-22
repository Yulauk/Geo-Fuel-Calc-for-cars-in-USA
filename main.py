import asyncio
import time

from math import radians, cos, sin, sqrt, atan2, ceil
import aiohttp
import folium
import matplotlib.pyplot as plt

def measure_time(func):
    if asyncio.iscoroutinefunction(func):  # Check if the function is asynchronous
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)  # Asynchronous function execution
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Function {func.__name__} took {elapsed_time:.6f} seconds")
            return result
    else:
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)  # Synchronous function execution
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Function {func.__name__} took {elapsed_time:.6f} seconds")
            return result
    return wrapper


# Function to calculate the distance between two coordinates (haversine formula)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


# Interpolate additional points between two coordinates
def interpolate_points(point1, point2, num_points):
    lat1, lon1 = point1
    lat2, lon2 = point2
    interpolated_points = []

    for i in range(1, num_points + 1):
        fraction = i / (num_points + 1)
        lat = lat1 + (lat2 - lat1) * fraction
        lon = lon1 + (lon2 - lon1) * fraction
        interpolated_points.append((lat, lon))

    return interpolated_points


# Interpolation of additional points based on distance
def interpolate_points_distance_based(route, max_distance_per_point=0.1):
    detailed_route = [route[0]]  # Start with the first point of the route

    for i in range(1, len(route)):
        point1 = route[i - 1]
        point2 = route[i]

        lat1, lon1 = point1
        lat2, lon2 = point2

        distance = haversine(lat1, lon1, lat2, lon2)  # Distance between points in km
        num_points = int(distance / max_distance_per_point)  # Number of points on the segment

        # Add interpolated points
        interpolated_points = interpolate_points(point1, point2, num_points)
        detailed_route.extend(interpolated_points)

    detailed_route.append(route[-1])  # Add the last point
    return detailed_route


# Route visualization on the map
def visualize_route(route):
    # Create a map centered on the first point of the route
    m = folium.Map(location=[route[0][1], route[0][0]], zoom_start=10)

    # Add the route to the map
    # Change the order of coordinates from (longitude, latitude) to (latitude, longitude)
    folium.PolyLine([(lat, lon) for lon, lat in route], color="blue", weight=2.5, opacity=1).add_to(m)

    # Add markers for the start and end of the route
    folium.Marker([route[0][1], route[0][0]], tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker([route[-1][1], route[-1][0]], tooltip="End", icon=folium.Icon(color="red")).add_to(m)

    # Save the map to a file
    m.save("route_map.html")
    print("Map saved to 'route_map.html'")


async def get_route(start, end):
    start_lat, start_lon = start.split(",")
    end_lat, end_lon = end.split(",")

    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if 'routes' in data:
                return data['routes'][0]['geometry']['coordinates']
            else:
                print(f"Error: {data}")
                return None


# Fetching elevations by coordinates
async def get_elevations_batch(session, coordinates):
    locations = "|".join([f"{lat},{lon}" for lon, lat in coordinates])
    url = f"https://api.opentopodata.org/v1/ned10m?locations={locations}"
    async with session.get(url) as response:
        data = await response.json()
        return [result.get('elevation') for result in data.get('results', [])]


# Function is responsible for the number of coordinates (points) sent in a single request to the API,
# limited to 100 points per request (batch_size=100)
@measure_time
async def fetch_elevations(coordinates, batch_size=100):
    elevations = []
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(coordinates), batch_size):
            batch = coordinates[i:i + batch_size]
            heights = await get_elevations_batch(session, batch)
            elevations.extend(heights)
            await asyncio.sleep(1.01)  # Delay between requests
    return elevations


# Route distance calculation
def get_route_distance(route):
    total_distance = 0
    for i in range(1, len(route)):
        lon1, lat1 = route[i-1]
        lon2, lat2 = route[i]
        distance = haversine(lat1, lon1, lat2, lon2)
        total_distance += distance
    return total_distance


# Fuel consumption calculation considering terrain
def calculate_fuel_consumption(elevations, base_fuel_consumption, total_distance):
    total_fuel = 0
    segment_distance = total_distance / (len(elevations) - 1)  # Distance between points

    # Slope limits
    min_slope = -0.20  # Descent no more than -20%
    max_slope = 0.20   # Ascent no more than 20%


    for i in range(1, len(elevations)):
        if elevations[i] is not None and elevations[i - 1] is not None:
            # Calculate slope
            slope = (elevations[i] - elevations[i - 1]) / segment_distance

            # Apply limits
            slope = max(min(slope, max_slope), min_slope)

            # Different slope levels for ascent and descent
            if slope > 0:  # Gentle ascent
                if 0 < slope <= 0.05:  # Gentle ascent
                    consumption_factor = 1 + slope * 0.10  # 10% increase per 1% ascent
                else:  # Steep ascent
                    consumption_factor = 1 + slope * 0.15  # 15% increase per 1% ascent
            else:  # Descent
                if -0.05 <= slope < 0:  # Gentle descent
                    consumption_factor = 1 + slope * 0.02  # 2% decrease per 1% descent
                else:  # Steep descent
                    consumption_factor = 1 + slope * 0.05  # 5% decrease per 1% descent

            # Calculate fuel consumption for the segment
            total_fuel += base_fuel_consumption * consumption_factor * segment_distance / 100
    return total_fuel


# Height accuracy calculation
def calculate_height_accuracy(elevations):
    total_heights = len(elevations)
    none_count = sum(1 for height in elevations if height is None)

    accuracy_percentage = ((total_heights - none_count) / total_heights) * 100 if total_heights > 0 else 0
    return total_heights, none_count, accuracy_percentage


# Function to convert kilometers to miles
def kilometers_to_miles(distance_km):
    # 1 км = 0.621371 мили
    miles_per_kilometer = 0.621371
    return distance_km * miles_per_kilometer


def calculate_price(distance, fuel_consumption, fuel_cost):
    profit_margin_short = 0.15      # 15% for up to 500 miles
    profit_margin_medium = 0.10     # 10% for 501-1500 miles
    profit_margin_long = 0.05       # 5% for 1500+ miles

    if distance <= 500:
        profit_margin = profit_margin_short
    elif 501 <= distance <= 1500:
        profit_margin = profit_margin_medium
    else:
        profit_margin = profit_margin_long

    total_fuel_cost = fuel_consumption * fuel_cost
    print('calculate_price>', total_fuel_cost)
    total_price = total_fuel_cost + (total_fuel_cost * profit_margin)
    print('total price>', total_price)

    return total_price


async def get_coordinates_by_zip(zip_code, country_code='US'):
    url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&countrycodes={country_code}&format=json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data:
                # Take the first found entry
                location = data[0]
                lat = location['lat']
                lon = location['lon']
                print(location['display_name'])  # Output the name associated with the ZIP code
                return f"{lat},{lon}"  # Return in 'latitude,longitude' format
            else:
                print(f"Could not find coordinates for ZIP code {zip_code}")
                return None


async def get_route_by_zip(start_zip, end_zip, country_code='US'):
    # If coordinates need to be passed instead of ZIP codes, obtain them using the coordinates retrieval function
    start_coords = await get_coordinates_by_zip(start_zip, country_code)
    end_coords = await get_coordinates_by_zip(end_zip, country_code)

    # If coordinates are successfully obtained
    if start_coords and end_coords:
        start_lat, start_lon = start_coords.split(",")
        end_lat, end_lon = end_coords.split(",")

        # URL for requesting a route to OSRM
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                if 'routes' in data:
                    return data['routes'][0]['geometry']['coordinates']
                else:
                    print(f"Error in the route: {data}")
                    return None
    else:
        print("Could not obtain coordinates for one of the points.")
        return None



# Main steps
async def main():
    start = input("Enter the ZIP code of the START point: ")
    end = input("Enter the ZIP code of the END point: ")

    if start.isdigit():
        route = await get_route_by_zip(start, end)
    else:
        route = await get_route(start, end)

    # start = input("Enter the coordinates of the START point (latitude,longitude): ")
    # end = input("Enter the coordinates of the END point (latitude,longitude): ")

    # end = '39.739236,-104.984862'  # Denver
    # start = '34.053691,-118.242766'  # LA

    # start = '41.878113,-87.629799'  # Chicago
    # end = '40.712776,-74.005974'    # NY

    # start = '41.878113,-87.629799'  # Chicago
    # end = '29.758938,-95.367697'  # Houston

    # start = '41.878113,-87.629799'  # Chicago
    # end = '34.053691,-118.242766'  # LA

    # start = '38.895037,-77.036543'  # Washington
    # end = '32.776272,-96.796856'  # Dallas

    # start = '42.331551,-83.046640'  # Detroit
    # end = '39.739236,-104.984862'  # Denver

    # start = '29.618567,-95.537722'
    # end = '40.712728,-74.006015'

    # start = '39.739236,-104.984862'  # Denver
    # end = '31.760116,-106.487040'  # El Paso

    # start = '39.739236,-104.984862'  # Denver
    # end = '26.142198,-81.794294'  # Naples, FL

    # start = '34.053691,-118.242766'  # LA
    # end = '30.271129,-97.743700'  # Austin

    if route:
        # Increase the detail of the route
        detailed_route = interpolate_points_distance_based(route)
        visualize_route(detailed_route)

        # Get the total distance of the route in kilometers and convert it to miles
        total_distance = get_route_distance(detailed_route)
        total_distance_miles = total_distance * 0.621371
        print(f'Total distance: {total_distance_miles:.2f} miles')

        print(f'_______________\n'
              f'The program is running, please wait, it may take about 1 minute\n'
              f'_______________')

        # Get the elevations for the route and calculate fuel consumption
        elevations = await fetch_elevations(detailed_route, batch_size=100)
        # Output the number of points and elevations
        print(f"Total points: {len(detailed_route)}")
        # print(f"Elevations: {elevations}")

        base_fuel_consumption = 5.75  # Fuel consumption in gallons per 100 miles
        fuel_consumption = calculate_fuel_consumption(elevations, base_fuel_consumption, total_distance_miles)
        print(f'Fuel consumption: {fuel_consumption:.2f} gallons')

        # Calculate fuel cost
        fuel_cost_per_gallon = 3.50  # Price per gallon in $
        total_fuel_cost = fuel_consumption * fuel_cost_per_gallon
        print(f'Fuel cost: {total_fuel_cost:.2f} $')


        def calculator(distance, fuel_cost):
            hours = distance * 2 / 60  # speed 60 miles per hour
            driver_work_days = ceil(hours / 11)  # maximum number of days for the trip
            drivers_salary = (20 * 11) * driver_work_days  # driver’s salary per day
            fuel_cost_total = fuel_cost * 2  # fuel cost for a round trip
            total_expenses = drivers_salary + fuel_cost_total  # total road expenses

            return round(total_expenses * 0.75)  # return 75% of the total cost

        cost = calculator(total_distance_miles, total_fuel_cost)
        print(f"TOTAL COST FOR CLIENTS: ${cost}")

        choice = input('Print elevations? Press 0 or 1:  ')
        # print(elevations)
        if choice == '1':
            # import matplotlib.pyplot as plt

            # Your data
            # data = elevations
            # print(data)

            # Create a graph
            plt.figure(figsize=(12, 6))
            plt.plot(elevations, marker='o', linestyle=':', color='purple')  # Dotted line
            plt.title('Elevation visualization from start to finish')
            plt.xlabel(f'Number of points along the route\none point represents 0.1 mile*')
            plt.ylabel('Elevation above sea level')
            plt.grid()
            plt.show()

    else:
        print("Failed to get the route")


if __name__ == '__main__':

    # Start the program
    asyncio.run(main())

