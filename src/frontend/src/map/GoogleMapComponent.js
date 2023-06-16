/*
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import { GoogleMap, useLoadScript } from "@react-google-maps/api";
import PlaceInfo from "./PlaceInfo";

const libraries = ["places"];

const options = {
  disableDefaultUI: true,
  zoomControl: true
};

export default function GoogleMapComponent(props) {
  console.log(process.env);

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env["REACT_APP_GOOGLE_MAP_API"],
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
