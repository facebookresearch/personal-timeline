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


import React, { useState, useEffect } from "react";
import { MarkerF, InfoWindowF } from "@react-google-maps/api";
import { Button } from 'primereact/button';
import { addDays } from "../timeline/builders";

export default function PlaceInfo(props) {
  const [places, setPlaces] = useState([
    {
      start: new Date(),
      lat: 35.64860429083234, 
      long: 138.57693376912908
    },
    {
      start: new Date(),
      lat: 35.658687875856664, 
      long: 138.56954332425778
    },
    {
      start: new Date(),
      lat: 35.66014231235642, 
      long: 138.57494260883726
    }
  ]);

  useEffect(() => { setPlaces(props.geo.slice(0, 100)); }, [props.geo])

  const [selected, setSelected] = useState(null);

  return (
    <>
      {places.map((marker, index) => (
        <MarkerF
          key={`marker_${index}`}
          position={{
            lat: marker.lat,
            lng: marker.long
          }}
          onMouseOver={() => {
            setSelected(marker);
          }}
        />
      ))}

      {selected ? (
        <InfoWindowF
          position={{
            lat: selected.lat,
            lng: selected.long
          }}
          onCloseClick={() => {
            setSelected(null);
          }}
        >
          <div>
            <Button className="justify-content-center p-1 border-noround" label={selected.title} link 
              onClick={() => {
                return null;
              }} />
          </div>
        </InfoWindowF>
      ) : null}
    </>
  );
}
