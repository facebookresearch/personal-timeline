import React, { useCallback, useEffect, useRef, useState } from "react";
import { GoogleMap, useLoadScript } from "@react-google-maps/api";
import PlaceInfo from "./PlaceInfo";

const libraries = ["places"];

const options = {
  disableDefaultUI: true,
  zoomControl: true
};

export default function GoogleMapComponent(props) {
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: "AIzaSyDs-aCGqXsGbPv_tIN8IgFqT0RbP_CPhY0",
    libraries
  });

  const [selectedCenter, setSelectedCenter] = useState(null);

  const mapRef = useRef();

  const onMapLoad = useCallback((map) => {
    mapRef.current = map;
  }, []);

  useEffect(() => { setSelectedCenter(null) }, [props.geo]);

  if (loadError) return "Error";
  if (!isLoaded) return "Loading...";

  return (
    <GoogleMap
      id="map"
      mapContainerStyle={{height: props.height, width: props.width || "100%"}}
      zoom={14}
      center={
        selectedCenter ? {
          lat: selectedCenter.lat,
          lng: selectedCenter.long
        } : (props.geo && props.geo.length > 0) ? {
          lat: props.geo[0].lat,
          lng: props.geo[0].long,
        } : {
          lat: 47.6062,
          lng: -122.3321
        }
    } // TODO: auto-select center based on props.geo
      options={options}
      onLoad={onMapLoad}
    >
      <PlaceInfo geo={props.geo} 
        setSelectedDateRange={props.setSelectedDateRange} 
        setSelectedCenter={setSelectedCenter}
        setSelectedIDs={props.setSelectedIDs}/>
    </GoogleMap>
  );
}
