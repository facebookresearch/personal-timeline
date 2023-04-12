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
            <Button className="justify-content-center p-1 border-noround" label={selected.start.toDateString()} link 
              onClick={() => {
                let start = addDays(new Date(selected.start.toDateString()), -selected.start.getDay());
                let end = addDays(start, 7);
                // props.setSelectedDateRange([start, end]);
                props.setSelectedCenter(selected);

                // the ID is not auto-generated
                if (selected.id && !String(selected.id).includes('-el-')) {
                  props.setSelectedIDs([selected.id]);
                }
              }} />
          </div>
        </InfoWindowF>
      ) : null}
    </>
  );
}
