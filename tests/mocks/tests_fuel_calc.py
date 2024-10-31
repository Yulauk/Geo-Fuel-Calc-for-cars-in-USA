import unittest
import asynctest
from main import kilometers_to_miles, get_coordinates_by_zip, get_route_by_zip, get_route
from datetime import datetime



class TestKilometersToMiles(unittest.TestCase):

    def test_conversion(self):
        # Testing conversion with a known value
        self.assertAlmostEqual(kilometers_to_miles(1), 0.621371, places=5)
        self.assertAlmostEqual(kilometers_to_miles(0), 0, places=5)
        self.assertAlmostEqual(kilometers_to_miles(10), 6.21371, places=5)

    def test_negative_value(self):
        # Check for negative value
        self.assertAlmostEqual(kilometers_to_miles(-5), -3.106855, places=5)

    def test_large_value(self):
        # Check for large value
        self.assertAlmostEqual(kilometers_to_miles(10000), 6213.71, places=2)


class TestGetCoordinatesByZip(asynctest.TestCase):

    async def test_valid_zip_code(self):
        # Mocking the response from aiohttp ClientSession
        with asynctest.patch("aiohttp.ClientSession.get") as mock_get:
            # Defining the behavior of a mock object
            mock_response = asynctest.Mock()
            mock_response.json = asynctest.CoroutineMock(
                return_value=[{'lat': '40.7128', 'lon': '-74.0060', 'display_name': 'New York, NY, USA'}]
            )
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await get_coordinates_by_zip("10001", "US")
            self.assertEqual(result, "40.7128,-74.0060")

    async def test_invalid_zip_code(self):
        with asynctest.patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = asynctest.Mock()
            mock_response.json = asynctest.CoroutineMock(return_value=[])
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await get_coordinates_by_zip("99999", "US")
            self.assertIsNone(result)


class TestGetRouteByZip(asynctest.TestCase):

    async def test_route_success(self):
        # Mock the function for getting coordinates
        with asynctest.patch("main.get_coordinates_by_zip") as mock_get_coords:
            mock_get_coords.side_effect = [
                "40.7128,-74.0060",  # Coordinates for the first ZIP
                "34.0522,-118.2437"  # Coordinates for the second ZIP
            ]

            # Mocking the response from aiohttp ClientSession
            with asynctest.patch("aiohttp.ClientSession.get") as mock_get:
                # Defining the behavior of a mock object for the response from OSRM
                mock_response = asynctest.Mock()
                mock_response.json = asynctest.CoroutineMock(
                    return_value={
                        'routes': [{
                            'geometry': {
                                'coordinates': [[-74.0060, 40.7128], [-118.2437, 34.0522]]
                            }
                        }]
                    }
                )
                mock_get.return_value.__aenter__.return_value = mock_response

                result = await get_route_by_zip("10001", "90001", "US")
                expected = [[-74.0060, 40.7128], [-118.2437, 34.0522]]
                self.assertEqual(result, expected)

    async def test_route_failure_due_to_coords(self):
        # Mock the coordinates function to return None
        with asynctest.patch("main.get_coordinates_by_zip") as mock_get_coords:
            mock_get_coords.side_effect = [None, "34.0522,-118.2437"]

            result = await get_route_by_zip("99999", "90001", "US")
            self.assertIsNone(result)

    async def test_route_failure_due_to_osrm(self):
        # Mock the function for getting coordinates
        with asynctest.patch("main.get_coordinates_by_zip") as mock_get_coords:
            mock_get_coords.side_effect = [
                "40.7128,-74.0060",
                "34.0522,-118.2437"
            ]

            # Mock response from aiohttp ClientSession for OSRM error
            with asynctest.patch("aiohttp.ClientSession.get") as mock_get:
                mock_response = asynctest.Mock()
                mock_response.json = asynctest.CoroutineMock(
                    return_value={'error': 'Some error occurred'}
                )
                mock_get.return_value.__aenter__.return_value = mock_response

                result = await get_route_by_zip("10001", "90001", "US")
                self.assertIsNone(result)


class TestGetRoute(asynctest.TestCase):

    async def test_route_success(self):
        start_coords = "40.7128,-74.0060"  # Coordinates for New York
        end_coords = "34.0522,-118.2437"    # Coordinates for Los Angeles

        with asynctest.patch("aiohttp.ClientSession.get") as mock_get:
            # Create a mock response for OSRM
            mock_response = asynctest.Mock()
            mock_response.json = asynctest.CoroutineMock(
                return_value={
                    'routes': [{
                        'geometry': {
                            'coordinates': [[-74.0060, 40.7128], [-118.2437, 34.0522]]
                        }
                    }]
                }
            )
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await get_route(start_coords, end_coords)
            expected = [[-74.0060, 40.7128], [-118.2437, 34.0522]]
            self.assertEqual(result, expected)

    async def test_route_failure(self):
        start_coords = "40.7128,-74.0060"  # Coordinates for New York
        end_coords = "34.0522,-118.2437"    # Coordinates for Los Angeles

        with asynctest.patch("aiohttp.ClientSession.get") as mock_get:
            # Create a mock response with an error
            mock_response = asynctest.Mock()
            mock_response.json = asynctest.CoroutineMock(
                return_value={'error': 'Some error occurred'}
            )
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await get_route(start_coords, end_coords)
            self.assertIsNone(result)

report_file = 'test_report.txt'

with open(report_file, 'w') as f:
    f.write(f"Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}\n\n")
    # Run tests with output to the specified file
    runner = unittest.TextTestRunner(stream=f, verbosity=2)
    # Find and run all tests in the 'tests' directory
    suite = unittest.defaultTestLoader.discover('tests')
    runner.run(suite)

if __name__ == "__main__":
    unittest.main()

    """
    python -m unittest discover -s tests
    python -m unittest discover -s tests -v 
    
    """
