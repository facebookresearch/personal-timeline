import React, { useEffect, useState } from "react";
import Timeline from "react-timelines";

import "react-timelines/lib/css/style.css";

import { buildTimebar, addDays } from "./builders";


const MIN_ZOOM = 2;
const MAX_ZOOM = 512;

function EpiTimeline(props) {

  /**
   * Control whether a track is open or not (not in use for now)
   */
  const [open, setOpen] = useState(false);

  /**
   * Handling track toggling (not in use for now)
   */
  const handleToggleOpen = () => {
    setOpen(!open);
  };

  useEffect(() => {
    let [start, end] = [props.startDay, new Date()];
    if (props.selectedDateRange && props.selectedDateRange.length == 2) {
      [start, end] = props.selectedDateRange;
      if (end === null) {
        end = addDays(start, 1);
      }
    }
    
    let day_diff = (end.getTime() - start.getTime()) / 1000 / 60 / 60 / 24;
    if (day_diff <= 1) {
      props.setZoom(256);
    } else if (day_diff <= 7) {
      props.setZoom(64);
    } else if (day_diff <= 31) {
      props.setZoom(8);
    } else if (day_diff <= 125) {
      props.setZoom(2);
    } else {
      props.setZoom(2);
    }    
  }, [props.selectedDateRange]);

  /**
   * Control what happens when a cell (element) is clicked:
   * (1) zoom in the the next level
   * (2) set the start and end day to become the start/end of the clicked element
   * @param {Object} element
   */
  const clickElement = element => {
    props.setSelectedDateRange([element.start, element.end]);
  }

  /**
   * Adjust the top timebar for different zoom levels.
   * @param {Date} startDay
   * @param {int} zoom
   * @returns The two timebars (e.g., days+hours) that we want to display
   */
  const adjustTimebar = (startDay, zoom) => {
    const start_year = startDay.getFullYear() - 1;
    const all = Object.fromEntries(buildTimebar(start_year).map(x => [x.id, x]));
    if (zoom < 7) {
      return [all.quarters, all.months];
    } else if (zoom < 20) {
      return [all.months, all.weeks];
    } else if (zoom < 100) {
      return [all.weeks, all.days];
    } else {
      return [all.days, all.hours];
    }
  }

  /**
   * Zoom-in
   */
  const handleZoomIn = () => {
    props.setZoom(Math.min(props.zoom * 2, MAX_ZOOM));
  };

  /**
   * Zoom-out
   */
   const handleZoomOut = () => {
    props.setZoom(Math.max(props.zoom / 2, MIN_ZOOM));
  };

  /**
   * Opening a track (not in use now).
   * @param {Object} track
   */
  const handleToggleTrackOpen = track => {
    let new_tracks = [...props.tracks]
    for (let i = 0; i < new_tracks.length; i++) {
      if (new_tracks[i].id === track.id) {
        new_tracks[i].isOpen = !new_tracks[i].isOpen;
      }
    }
    props.set_tracks(new_tracks);
  };

  /**
   * Merge elements of a track into month/week/day/hour-level cells.
   * @param {Array} tracks - the tracks to be merged
   * @param {Function} getKey - a function that maps an element to month/week/day/hour
   * @returns the merged tracks
   */
  const mergeTracksByKey = (tracks, getKey) => {
    let new_tracks = [];
    // merge to month
    for (let i = 0; i < tracks.length; i++) {
      let track = tracks[i];
      let new_track = {...track};
      new_track.elements = [];

      for (let j = 0; j < track.elements.length; j++) {
        if (props.selectedDateRange) {
          let current_time = track.elements[j].start.getTime();
          const [start, end] = props.selectedDateRange || [props.startDay, new Date()];
          // const day_diff = Math.min(30, Math.max(1, (end.getTime() - start.getTime()) / 1000 / 60 / 60 / 24));
          // const start_time = addDays(start, -day_diff).getTime();
          // const end_time = addDays(end, +day_diff).getTime();
          if (current_time < start || (end !== null && current_time > end)) {
            continue;
          }
        }

        let start = track.elements[j].start;
        let key = getKey(start);
        if (new_track.elements.length === 0 ||
          getKey(new_track.elements[new_track.elements.length - 1].start) !== key) {
          let new_elem = {...track.elements[j]};
          let [start, end] = key.split('_');
          new_elem.start = new Date(start);
          new_elem.end = new Date(end); // addDays(new_elem.start, delta);
          new_elem.title = "1";
          new_track.elements.push(new_elem);
        } else {
          let val = parseInt(new_track.elements[new_track.elements.length - 1].title) + 1;
          new_track.elements[new_track.elements.length - 1].title = String(val);
        }
      }

      new_tracks.push(new_track);
    }
    return new_tracks;
  }

  /**
   * Merge tracks into month/week/day/hour-level cells depending on the zoom levels.
   * @param {Array} tracks
   * @param {int} zoom
   * @returns
   */
  const mergeTracksByZoom = (tracks, zoom) => {
    if (zoom < 7) {
      // merge to months
      let getKey = (date) => {
        let start = new Date(date);
        start.setDate(1);
        let end = new Date(start);
        end.setMonth(end.getMonth() + 1);
        // end.setDate(0);
        return `${start.toDateString()}_${end.toDateString()}`;
        // return date.getFullYear() * 100 + date.getMonth();
      }
      return mergeTracksByKey(tracks, getKey);
    } else if (zoom < 20) {
      // merge to week
      let getKey = (date) => {
        let start = addDays(date, -date.getDay());
        let end = addDays(date, 7 - date.getDay());
        return `${start.toDateString()}_${end.toDateString()}`;
      }
      return mergeTracksByKey(tracks, getKey);
    } else if (zoom < 100) {
      // merge to day
      let getKey = (date) => {
        let start = new Date(date);
        let end = addDays(start, 1);
        return `${start.toDateString()}_${end.toDateString()}`;
      }
      return mergeTracksByKey(tracks, getKey);
    } else {
      let getKey = (date) => {
        let start = new Date(date);
        let hour = (start.getHours() >> 1) << 1; // round to 2 hours
        return `${start.toDateString()} ${hour}:00_${start.toDateString()} ${hour+2}:00`;
      }

      return mergeTracksByKey(tracks, getKey);
    }
  };

  /**
   * start and end days (also when they are not specified)
   */
  // const [start, end] = props.selectedDateRange || [props.startDay, new Date()];
  const start = props.selectedDateRange ? props.selectedDateRange[0] : props.startDay;
  const end = props.selectedDateRange ? (props.selectedDateRange[1] || addDays(start, 1)) : new Date();
  /**
   * Difference between start and end
   */
  const day_diff = Math.min(30, Math.max(1, (end.getTime() - start.getTime()) / 1000 / 60 / 60 / 24));

  return (
    <div className="app" >
      <Timeline
        scale={{
          start: addDays(start, -day_diff),
          end: addDays(end, +day_diff),
          zoom: props.zoom,
          zoomMin: MIN_ZOOM,
          zoomMax: MAX_ZOOM
        }}
        isOpen={open}
        toggleOpen={handleToggleOpen}
        zoomIn={handleZoomIn}
        zoomOut={handleZoomOut}
        clickElement={clickElement}
        clickTrackButton={track => {
          // eslint-disable-next-line no-alert
          alert(JSON.stringify(track));
        }}
        timebar={adjustTimebar(props.startDay, props.zoom)}
        tracks={mergeTracksByZoom(props.tracks, props.zoom)}
        now={end}
        toggleTrackOpen={handleToggleTrackOpen}
        enableSticky
        // scrollToNow
      />
    </div>
  );
}

export default EpiTimeline;
