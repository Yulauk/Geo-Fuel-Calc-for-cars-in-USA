import pytest
from main import get_route

@pytest.mark.asyncio
async def test_get_route():
    # Replace with known start and end coordinates
    start = '37.7749,-122.4194'  # Example: San Francisco
    end = '34.0522,-118.2437'    # Example: Los Angeles

    # Get the route
    route = await get_route(start, end)

    # Check that the route was received
    assert route is not None
    assert isinstance(route, list)
    assert len(route) > 0  # Make sure the route is not empty

    # Additionally, you can check that the route has the expected structure
    assert isinstance(route[0], list)  # The first direction must be a list of coordinates
