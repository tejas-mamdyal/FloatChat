import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// Fix for default markers in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Component to handle map clicks
const MapClickHandler = ({ onMapClick }) => {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng);
    }
  });
  return null;
};

const MapComponent = ({ mapData, height = "600px" }) => {
  const [clickedLocation, setClickedLocation] = useState(null);
  const [mapCenter, setMapCenter] = useState([20, 77]); // Default to India
  const [mapZoom, setMapZoom] = useState(4);
  const [mapError, setMapError] = useState(null);

  // Update map center and zoom when mapData changes
  useEffect(() => {
    if (mapData && mapData.locations && mapData.locations.length > 0) {
      if (mapData.center_lat && mapData.center_lon) {
        setMapCenter([mapData.center_lat, mapData.center_lon]);
        setMapZoom(6);
      } else {
        // Calculate center from all locations
        const avgLat = mapData.locations.reduce((sum, loc) => sum + loc.latitude, 0) / mapData.locations.length;
        const avgLon = mapData.locations.reduce((sum, loc) => sum + loc.longitude, 0) / mapData.locations.length;
        setMapCenter([avgLat, avgLon]);
        setMapZoom(6);
      }
    }
  }, [mapData]);

  const handleMapClick = (latlng) => {
    setClickedLocation({
      lat: latlng.lat.toFixed(4),
      lng: latlng.lng.toFixed(4)
    });
  };

  // Create custom icon for ocean data points
  const oceanIcon = L.divIcon({
    className: 'custom-ocean-marker',
    html: '<div style="background-color: #3b82f6; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });

  // Error boundary for map rendering
  if (mapError) {
    return (
      <div className="space-y-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-red-500">
              <h3>Map Error</h3>
              <p>{mapError}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  let mapComponent;
  try {
    mapComponent = (
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ height: '100%', width: '100%' }}
        className="rounded-lg"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapClickHandler onMapClick={handleMapClick} />
        
        {/* Render data points from mapData */}
        {mapData && mapData.locations && mapData.locations.map((location, index) => (
          <Marker
            key={index}
            position={[location.latitude, location.longitude]}
            icon={oceanIcon}
          >
            <Popup>
              <div className="space-y-2">
                <div className="font-semibold text-blue-600">
                  {location.file_name || `Data Point ${index + 1}`}
                </div>
                <div className="text-sm space-y-1">
                  <div><strong>Latitude:</strong> {location.latitude.toFixed(4)}°</div>
                  <div><strong>Longitude:</strong> {location.longitude.toFixed(4)}°</div>
                  {location.depth && (
                    <div><strong>Depth:</strong> {location.depth}m</div>
                  )}
                  {location.date && (
                    <div><strong>Date:</strong> {new Date(location.date).toLocaleDateString()}</div>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Show clicked location */}
        {clickedLocation && (
          <Marker position={[parseFloat(clickedLocation.lat), parseFloat(clickedLocation.lng)]}>
            <Popup>
              <div className="space-y-2">
                <div className="font-semibold text-green-600">Clicked Location</div>
                <div className="text-sm">
                  <div><strong>Latitude:</strong> {clickedLocation.lat}°</div>
                  <div><strong>Longitude:</strong> {clickedLocation.lng}°</div>
                </div>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>
    );
  } catch (error) {
    console.error('Error rendering map:', error);
    return (
      <div className="space-y-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-red-500">
              <h3>Map Rendering Error</h3>
              <p>{error.message}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-0">
          <div style={{ height, width: '100%' }}>
            {mapComponent}
          </div>
        </CardContent>
      </Card>

      {/* Display clicked coordinates */}
      {clickedLocation && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold">Last Clicked Location</h4>
                <p className="text-sm text-muted-foreground">
                  Coordinates: {clickedLocation.lat}°N, {clickedLocation.lng}°E
                </p>
              </div>
              <Badge variant="outline">
                Click coordinates
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Map data summary */}
      {mapData && mapData.locations && mapData.locations.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold">Ocean Data Points</h4>
                <p className="text-sm text-muted-foreground">
                  {mapData.locations.length} locations displayed on map
                </p>
              </div>
              <Badge variant="default">
                {mapData.locations.length} points
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MapComponent;
