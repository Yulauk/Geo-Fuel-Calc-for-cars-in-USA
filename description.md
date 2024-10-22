# Project: Route Distance and Fuel Consumption Calculation Considering Terrain

This project provides a tool for calculating routes between two points, interpolating intermediate points, obtaining elevation data, calculating distance, and estimating fuel consumption while considering the terrain of the route. An important aspect of the system is the visualization of the route on a map and the construction of an elevation graph for a clearer understanding of the terrain.

## Advantages of the Project

- **Accuracy of Calculation:** Using terrain data for fuel consumption estimation allows for a more precise assessment of trip costs, especially in hilly or mountainous areas.

- **Route Interpolation:** Additional points along the route improve detail, which is important for analyzing complex routes.

- **Flexibility:** The system allows for various input parameters, such as fuel prices and base consumption rates, making it adaptable to different scenarios.

- **Visualization:** Creating a map of the route and an elevation graph allows clients to better understand the route and anticipate potential challenges.

- **Cost Optimization:** The system takes into account not only fuel expenses but also driver salaries, providing a complete picture of trip costs.

## Key Features

- **Route Distance Calculation:** Uses the Haversine formula to calculate the distance between points. The program can obtain routes between two points using the OSRM API.

- **Point Interpolation:** To increase calculation accuracy, the system interpolates additional points along the route at intervals of 0.1 miles.

- **Elevation Data Retrieval:** The opentopodata.org API is used to obtain elevation data based on coordinates, allowing for the consideration of terrain when calculating fuel consumption.

- **Fuel Consumption Calculation:** The program evaluates fuel consumption while accounting for gradients (ascents and descents), enabling a more accurate estimation of fuel costs.

- **Route Visualization:** A map with the route is created, along with an elevation graph to display heights from the starting to the endpoint.

- **Trip Cost Estimation:** The system calculates fuel costs and total trip expenses considering driver salaries and distance.

## Disadvantages of the Project

- **Limit of 100 Points per API Request:** 
  - **Description:** The system uses the opentopodata.org API to obtain elevation data. However, due to the limitation on the number of points per request, only 100 points can be requested at a time.
  - **Problem:** If the route is long, the number of points can easily exceed 100. For example, a 100-mile route with a step of 0.1 miles requires 1000 points. This means the request will be split into 10 separate batches, increasing the total number of requests and processing time.

- **Impact:**
  - **Slowed Data Processing:** The more points that need processing, the more requests must be executed. For long routes or highly detailed routes, this can significantly increase the time needed to obtain elevation data.
  - **Risk of API Quota Overflow:** Many external APIs have limits on the number of requests per day. For example, if the API usage quota is 1000 requests per day, requests for a single long route can quickly deplete this limit when processing a large number of points.

- **Complexity in Data Processing:** Handling very long routes requires managing large datasets in stages. This demands additional logic and can introduce errors if some batches fail to process or return errors.

- **Delay of 1.01 Seconds Between Requests (Rate Limit):**
  - **Description:** To prevent overloading the API server, a pause of 1.01 seconds must be added between requests. This is common in free or public APIs to limit server load and ensure fair resource usage among all users.
  - **Problem:** This delay significantly increases the total waiting time with a large number of requests. For example, a route with 1000 points would require 10 requests, resulting in approximately 10 seconds of total delay. For routes with thousands of points, the overall waiting time can extend to minutes.

## How to Use

1. Clone the repository:

   ```bash
   git clone https://github.com/Yulauk/Geo-Fuel-Calc-for-cars-in-USA.git
   
2. Navigate to the project directory


3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   
4. Run the application:
   ```bash
   flask main.py
   

## Author
The project is developed by Yulauk, a Python Full Stack Developer with experience in web development and process automation. I hope this application has been useful for you, and I would be happy to collaborate in the future.

