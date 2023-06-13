import { buildElement, addDays } from '../timeline/builders';
import { config } from '../Constants';

/**
 * Import digital data from local JSONs.
 */
const importDigitalData = (tracks, setTracks, setSelectedDateRange, toast) => {
    return Promise.resolve(_importDigitalData(tracks, setTracks, setSelectedDateRange, toast));
};

const _importDigitalData = async (tracks, setTracks, setSelectedDateRange, toast) => {
    let data_sources = ['books.json', 'exercise.json', 'purchase.json', 'streaming.json', 'places.json', 'trips.json', 'photos.json'];
    let new_tracks = [...tracks]
    let dates = [];

    for (let data_id = 0; data_id < data_sources.length; data_id++) {
      let data = null;

      try {
        data = await (
          await fetch('digital_data/' + data_sources[data_id])
        ).json();
      } catch (error) {
        data = await (
          await fetch('digital_data/' + data_sources[data_id].replace('.json', '.sampled.json'))
        ).json();
      }
      
      let track_name = data_sources[data_id].split('.')[0];
      let trackId = data_id + 5;
      let elements = [];

      for (let i = 0; i < data.length; i++) {
        // remove duplicate records
        if (data[i].textDescription === 'from Google Photo') {
          continue;
        }

        let start = null;
        let end = null;
        if (data[i].start_time) {
          start = new Date(data[i].start_time);
          end = new Date(data[i].end_time);
        } else {
          start = new Date(data[i].time);
          end = addDays(start, 0.25);
        }
        dates.push(start);

        let elem = buildElement({trackId, start, end, i});

        // copy key-values
        if (data[i].id) {
          elem.id = data[i].id;
        }
        elem.data = data[i];

        if ('book_name' in data[i]) {
          elem.title = data[i].book_name;
        } else if ('country' in data[i]) {
          elem.title = data[i].country + ' ' + data[i].states_provinces;
        } else if ('textDescription' in data[i]) {
          elem.title = data[i].textDescription;
        } else if ('productName' in data[i]) {
          elem.title = data[i].productName;
        } else if ('artist' in data[i]) {
          elem.title = data[i].artist;
        }
  
        if (data[i].start_lat && data[i].start_long) {
          elem.lat = parseFloat(data[i].start_lat);
          elem.long = parseFloat(data[i].start_long);
        } else if (data[i].lat && data[i].long) {
          elem.lat = parseFloat(data[i].lat);
          elem.long = parseFloat(data[i].long);
        }
        elements.push(elem);
      }

      // sort elements
      elements.sort((a, b) => { 
        let a_time = new Date(a.start).getTime();
        let b_time = new Date(b.start).getTime();
        return a_time - b_time;
      });

      let track = {
        id: trackId,
        title: track_name,
        elements: elements,
        tracks: null,
        isOpen: false
      };
      
      // const subtrack = { ...track };
      // subtrack.id = 'subtrack';
      // subtrack.name = 'subtrack';
      // track.tracks = [subtrack];
  
      if (new_tracks.filter(item => item.id === trackId).length === 0) {
        new_tracks.push(track);
      }  
    }

    let maxDate = new Date(Math.max.apply(null, dates));
    let minDate = new Date(Math.min.apply(null, dates));
    setSelectedDateRange([minDate, maxDate]);

    setTracks(new_tracks)
    toast.current.show({ severity: 'success', summary: 'Success', detail: 'Digital Data Uploaded' });
    // launch QA engine
    fetch(config.API_URL + "/launch?" + new URLSearchParams({dataset: "Digital"})).then((response) => response.json())
    .then((data) => {
      toast.current.show({ severity: 'success', summary: 'Success', detail: 'QA engine for Digital Data is ready!' });
    }).catch(error => {
      toast.current.show({ severity: 'error', summary: 'Error', detail: 'QA Engine not loaded.' });
    })
};

export default importDigitalData;
