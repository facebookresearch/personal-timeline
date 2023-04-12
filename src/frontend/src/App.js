import './App.css';

import React, { useEffect, useState, useRef } from 'react';
import { Terminal } from 'primereact/terminal';
import { TerminalService } from 'primereact/terminalservice';
import { Panel } from 'primereact/panel';
import { ProgressBar } from 'primereact/progressbar';
import { TabView, TabPanel } from 'primereact/tabview';
import { Card } from 'primereact/card';
import { Chip } from 'primereact/chip';
import { Button } from 'primereact/button';
import { Timeline } from 'primereact/timeline';
import { addDays } from './timeline/builders'
import { Tooltip } from 'primereact/tooltip';
import { Toast } from 'primereact/toast';
import { RadioButton } from 'primereact/radiobutton';
import { Image } from 'primereact/image';
import { Dialog } from 'primereact/dialog';
import { Calendar } from 'primereact/calendar';


import HeatMap from '@uiw/react-heat-map';
import GoogleMapComponent from './map/GoogleMapComponent';

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { coy } from 'react-syntax-highlighter/dist/esm/styles/prism';

import EpiTimeline from "./timeline/EpiTimeline"

import "video-react/dist/video-react.css"; // import css
import importDigitalData from './service/DigitalDataImportor';

import { config } from './Constants';

function App() {

  // today's date
  const today = new Date();

  // answer for QA
  const [answer, setAnswer] = useState("Empty")

  // whether the query is running
  const [running, setRunning] = useState(false);

  // aria + digital data tracks
  const [tracks, setTracks] = useState([]);

  // the list of geo locations
  const [geo, setGeo] = useState([]);

  // for heatmap calendar
  const [dayCount, setDayCount] = useState([]);

  // endDay is always today
  const [startDay, setStartDay] = useState(today);

  // number of days to be shown in the heatmap
  const [dayLength, setDayLength] = useState(700);

  // selected start/end date
  const [selectedDateRange, setSelectedDateRange] = useState(null);

  // zoom-level
  const [zoom, setZoom] = useState(2);

  // world-state
  const [worldState, setWorldState] = useState({
    'gaia_id': 'none',
    'some_attribute': 'val',
    'actions': ['a1', 'a2']
  });

  // images
  const [images, setImages] = useState(null);

  // events to be shown in the timeline
  const [events, setEvents] = useState([]);

  // selected event ID's
  const [selectedIDs, setSelectedIDs] = useState(null);

  // selected view's index (timeline, map, etc.)
  const [activeIndex, setActiveIndex] = useState(0);

  // for displaying the speech dialog
  const [showSpeech, setShowSpeech] = useState(false);

  const [currentSpeech, setCurrentSpeech] = useState("");

  // qa engine
  const [qa, setQA] = useState(null);

  // different qa methods
  const qa_methods = ["ChatGPT", "Retrieval-based", "View-based"]

  // mapping names of the different maps to indices
  // const view_name_mp = {
  //   "timeline": 0, "query_result": 1, "video": 2,
  //   "retrieval_result": 3, "heatmap": 4,
  //   "map": 5, "details": 6
  // }
  const view_name_mp = {
    "timeline": 0, "query_result": 1,
    "retrieval_result": 2, "heatmap": 3,
    "map": 4, "details": 5
  }

  // Toast
  const toast = useRef(null);

  /**
   * useEffect hooks for updating heatmap, geo based on tracks
   */
  useEffect(() => {
    let dates = [];
    let new_geo = [];
    let counter = {};

    for (let track_id = 0; track_id < tracks.length; track_id++) {
      let track = tracks[track_id];
      for (let i = 0; i < track.elements.length; i++) {
        let elem = track.elements[i]; // id, title, start, end
        let date_str = elem.start.toDateString();
        dates.push(date_str);
        if (!(date_str in counter)) {
          counter[date_str] = { date: date_str, count: 0 };
        }

        if (!(track.title in counter[date_str])) {
          counter[date_str][track.title] = 0;
        }
        counter[date_str].count += 1;
        counter[date_str][track.title] += 1;

        if (elem.lat && elem.long) {
          new_geo.push(elem);
        }
      }
    }

    // counter
    setDayCount(Object.values(counter));

    // set start day and length
    dates = dates.map((d) => { return new Date(d); });
    let maxDate = new Date(Math.max.apply(null, dates));
    let minDate = new Date(Math.min.apply(null, dates));
    setStartDay(minDate);
    setDayLength(Math.max((maxDate - minDate) / 60 / 60 / 24 / 1000 * 3.6, 700));

    // set geo locations
    setGeo(new_geo);
  }, [tracks]);

  /**
   * Icons for displaying episodes in the vertical timeline
   */
  const icon_map = {
    purchase: 'pi pi-amazon',
    books: 'pi pi-book',
    streaming: 'pi pi-youtube',
    places: 'pi pi-map',
    exercise: 'pi pi-heart-fill',
    trips: 'pi pi-car',
    photos: 'pi pi-instagram'
  }

  /**
   * Icon colors from https://coolors.co/palette/ffbe0b-fb5607-ff006e-8338ec-3a86ff
   */
  const icon_color_map = {
    purchase: '#ffbe0b',
    books: '#3a86ff',
    streaming: '#ff006e',
    places: '#8338ec',
    trips: '#ff006e',
    exercise: '#fb5607',
    photos: '#3a86ff'
  }

  /**
   * Map an element (episode) to an event in the vertical timeline.
   * @param {String} track_name - name of the track
   * @param {Object} element - the episode (digital / aria)
   * @returns A timeline event
   */
  const element_to_event = (track_name, element) => {
    let data = element.data;
    let event = {
      title: element.title, date: element.start.toString(),
      icon: icon_map[track_name],
      color: icon_color_map[track_name]
    };

    // summarization
    if (data.instructions) {
      event.summary = data.instructions;
    }

    if (data.summary) {
      event.summary = data.summary;
    }

    if (data.video_url) {
      event.video = data.video_url;
    }

    // Digital data: kindle and spotify
    if (data.img_url) { 
      event.image = data.img_url; 
    } else if (data.start_lat && data.start_long) {
      event.lat = data.start_lat;
      event.long = data.start_long;
    }

    if (data.spotify_link && data.spotify_link !== "") { event.spotify = data.spotify_link; }

    event.data = data;
    return event;
  }

  const compute_offset = (tracks, start, end) => {
    let time_zones = [0];

    for (let tid = 0; tid < tracks.length; tid++) {
      for (let eid = 0; eid < tracks[tid].elements.length; eid++) {
        let element = tracks[tid].elements[eid];
        if (element.start.getTime() >= start.getTime() && element.start.getTime() <= end.getTime()) {
          if (element.lat && element.long) {
            time_zones.push(Math.floor(element.lat / 15));
          }
        }
      }
    }
    return time_zones.sort((a, b) =>
      arr.reduce((acu, cur) => (cur === a ? (acu += 1) : cur)) -
      arr.reduce((acu, cur) => (cur === b ? (acu += 1) : cur))).pop();
  }

  /**
   * useEffect hooks for updating the events to be shown on the timeline
   * when selected data range changes.
   */
  useEffect(() => {
    let new_events = [];
    let new_geo = [];
    let [start, end] = [startDay, today];
    if (selectedDateRange && selectedDateRange.length == 2) {
      [start, end] = selectedDateRange;
      if (end === null) {
        end = addDays(start, 1);
      }
    }

    for (let tid = 0; tid < tracks.length; tid++) {
      for (let eid = 0; eid < tracks[tid].elements.length; eid++) {
        let element = tracks[tid].elements[eid];
        if (element.start.getTime() >= start.getTime() && element.start.getTime() <= end.getTime()) {
          let event = element_to_event(tracks[tid].title, element);
          new_events.push(event);

          // update geo
          if (element.lat && element.long) {
            new_geo.push(element);
          }
        }
      }
    }

    // update vertical timeline view
    // no more than 500 events
    new_events.sort((a, b) => {
      let a_time = new Date(a.date).getTime();
      let b_time = new Date(b.date).getTime();
      return a_time - b_time;
    });
    // setEvents(new_events.slice(0, 500));
    setEvents(new_events);

    // update geo view
    setGeo(new_geo);
  }, [selectedDateRange]);

  /**
   * Handler for user entering command.
   *
   * @param {String} text - the input question or command (e.g., clear)
   */
  const commandHandler = (text) => {
    let argsIndex = text.indexOf(' ');
    let command = argsIndex !== -1 ? text.substring(0, argsIndex) : text;

    switch (command) {
      case 'clear':
        TerminalService.emit('clear');
        break;

      default:
        TerminalService.emit('response', 'Running...');
        setRunning(true);
        let data_source = 'digital';

        // send queries to the backend
        fetch(config.API_URL + "/query?" + new URLSearchParams({
          query: text,
          source: data_source,
          qa: qa
        })).then((response) => response.json())
          .then((data) => {
            console.log(data);
            setAnswer(data);

            if (data.sources) {
              let new_selected_ids = []
              for (let i = 0; i < data.sources.length; i++) {
                let source = data.sources[i];
                if (source.id) {
                  new_selected_ids.push(source.id);
                }
              }
              setSelectedIDs(new_selected_ids);
            }

            TerminalService.emit('response', (data.answer ? data.method + ": " + data.answer : 'Done!'));
            setActiveIndex(view_name_mp["retrieval_result"]);
            setRunning(false);
          });
        break;
    }
  }

  /**
   * useEffect hooks for the QA dialog box.
   */
  useEffect(() => {
    TerminalService.on('command', commandHandler);
    return () => {
      TerminalService.off('command', commandHandler);
    };
  }, [qa]);

  /**
   * For displaying counts (for different episode types) on the heatmap view.
   * @param {Object} data
   * @returns {String} the count string
   */
  const showCount = (data) => {
    let res = `${data.date}`;
    for (let key in data) {
      if (!(['row', 'column', 'index', 'count'].includes(key)) &&
        Number.isInteger(data[key]) &&
        data[key] > 0) {
        res += ` ${key}: ${data[key]}`;
      }
    }
    return res
  }

  /**
   * For showing markers on the vertical timeline.
   * @param {Object} item
   * @returns
   */
  const customizedMarker = (item) => {
    return (
      <span className="flex w-2rem h-2rem align-items-center justify-content-center text-white border-circle z-1 shadow-1" style={{ backgroundColor: item.color }}>
        <i className={item.icon}></i>
      </span>
    );
  };

  /**
   * The show more button for summaries
   * @param {Text} prop.summary - the summary
   * @returns
   */
  const ShowMore = (prop) => {
    let summary = prop.summary;
    const [more, setMore] = useState(false);

    return <div className='p-chip p-chip-text overflow-x-auto' style={{ width: '100%', maxHeight: '160px' }}>
      {summary.length >= 200 && !more ? <p> {summary.slice(0, 200) + ' '} <Button size="sm" className="m-0 p-0 text-black-alpha-80" label="... See More" link onClick={() => {
        setMore(true);
      }} /> </p> : summary}
    </div>;
  }

  /**
   * The lazy loading video class.
   */
  const Video_ = (props) => {
    const videoRef = useRef(props.video_path);

    const useIntersectionObserver = (ref, options) => {
      const [isIntersecting, setIsIntersecting] = React.useState(false);

      React.useEffect(() => {
        const observer = new IntersectionObserver(([entry]) => {
          setIsIntersecting(entry.isIntersecting);
        }, options);

        if (ref.current) {
          observer.observe(ref.current);
        }

        return () => {
          try {
            observer.unobserve(ref.current);
          } catch (e) {
            console.log(e);
          }
        };
      }, []);

      return isIntersecting;
    };

    const shouldLoadVideo = useIntersectionObserver(videoRef, { threshold: 0.5 });
      return (
            <div ref={videoRef}>
              {shouldLoadVideo && (
                          <video className="my-2" width="100%" autoPlay>
                          <source src={props.video_path} type="video/mp4" />
                        </video>
              )}
            </div>
          );
  };

  /**
   * For displaying the speech records.
   * @param {String} content - the content to be displayed
   * @param {boolean} visible - show the dialog if true
   * @param {String} setVisible - setter of showDialog
   */
  const SpeechDialog = (props) => {
    return (
      <Dialog header="Details" visible={props.visible} style={{ width: '50vw' }} onHide={() => props.setVisible(false)}>
          <pre className="m-0">
          {props.content.replace("the following conversation: ", "the following conversation:\n\n")}
          </pre>
      </Dialog>
    )
  }

  /**
   * Displaying one episode in the timeline.
   * @param {Object} item - the event to be displayed
   * @returns
   */
  const customizedContent = (item) => {
    return (
      <Card title={item.title} subTitle={item.date}>
        {item.summary && <ShowMore summary={item.summary} />}
        {item.image && <Image src={`${item.image}`} alt={item.name} width={200} className="shadow-1" />}
        {item.spotify &&
          <iframe style={{ "borderRadius": "12px" }} src={item.spotify.replace('/track/', '/embed/track/')}
            width="100%" height="380" frameBorder="0" allow="autoplay;
                clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"
          />
        }
        {item.video && events.length <= 100 &&
          <Video_ video_path={item.video}/>}

        {item.data.speech && item.data.speech.length >= 100 &&
          <Button className="my-2" label="Conversation" link onClick={() => {
            setShowSpeech(true);
            setCurrentSpeech(item.data.speech);}}/>
        }

        {item.lat && item.long && <GoogleMapComponent geo={[item]} height="20vh"
          setSelectedDateRange={setSelectedDateRange} setSelectedIDs={setSelectedIDs} />
        }

        {item.data.exercise_text &&
          <Button className="my-2" label="Exercise" link onClick={() => {
            setShowSpeech(true);
            setCurrentSpeech(item.data.exercise_text);}}/>
        }

        <Button className="my-2" label="More details" link onClick={() => {
          setWorldState(item.data);
          setActiveIndex(view_name_mp["details"]);
        }} />
      </Card>
    );
  };

  /**
   * For QA, given the array of episode ID's, select and display episodes from different tracks.
   * @param {Array} sources - ID's of the supporting episodes
   * @returns The events ready to be displayed.
   */
  const source_to_events = (sources) => {
    let res = []
    let source_ids = []
    for (let i = 0; i < sources.length; i++) {
      source_ids.push(sources[i].id);
    }

    for (let i = 0; i < tracks.length; i++) {
      for (let j = 0; j < tracks[i].elements.length; j++) {
        if (source_ids.includes(tracks[i].elements[j].id)) {
          res.push(element_to_event(tracks[i].title, tracks[i].elements[j]));
        }
      }
    }
    return res;
  }

  useEffect(() => { importDigitalData(tracks, setTracks, setSelectedDateRange, toast); }, []);

  return (
    <div className="App">
      <h1 className="title">Personal Timeline</h1>
      {/* For message (success, fail) display */}
      <Toast ref={toast}></Toast>

      {/* For selecting date range */}
      <span className="p-float-label">
      <Calendar className="mr-4" inputId="date_range" value={selectedDateRange} onChange={(e) => {
          setSelectedDateRange(e.value);
        }} selectionMode="range" readOnlyInput />
      <label htmlFor="date_range">Date Range</label>

      {/* Showing the start and end date of the selected date range */}
      {selectedDateRange && <Chip label={
          selectedDateRange[1] !== null ?
          `From ${selectedDateRange[0].toDateString()} to ${selectedDateRange[1].toDateString()}` :
          `On ${selectedDateRange[0].toDateString()}`
        }
        removable onRemove={() => {
          setSelectedDateRange(null);
          setZoom(2);
        }} />}
      </span>

      {/* The horizontal timeline for navigation */}
      <Panel className="my-5" header="Timeline" toggleable style={{ maxWidth: '1000px' }}>
        <EpiTimeline
          startDay={startDay}
          selectedDateRange={selectedDateRange}
          setSelectedDateRange={setSelectedDateRange}
          zoom={zoom}
          setZoom={setZoom}
          tracks={tracks}
          set_tracks={setTracks} />
      </Panel>


      {/* QA dialog box */}
      <p>Enter a question or "<strong>clear</strong>" to clear all commands.</p>
      <div className="flex flex-wrap gap-3 my-3">
        {qa_methods.map((method) => {
          return <div className="flex align-items-center">
            <RadioButton value={method} onChange={(e) => { setQA(e.value) }} checked={qa === method} />
            <label className="ml-2">{method}</label>
          </div>;
        })}
        {/* <div className="flex align-items-center">
                    <RadioButton value="View-based" onChange={(e) => setQA(e.value)} checked={qa === 'View-based'} />
                    <label className="ml-2">View-based</label>
                </div> */}
      </div>
      <Terminal className="text-lg line-height-3" style={{ maxWidth: '1000px', height: '200px' }} welcomeMessage="Welcome to TL-QA" prompt="TL-QA $" />
      <ProgressBar mode="indeterminate" style={{ maxWidth: '1000px', height: '6px', display: running ? '' : 'none' }}></ProgressBar>

      {/* Showing the episode ID's included in the answer */}
      {/* {selectedIDs && <Chip className="my-5" label={`Showing: ${selectedIDs}`} style={{ maxWidth: '1000px' }}
        removable onRemove={() => {
          setSelectedIDs(null);
          //  setZoom(2);
        }} />} */}

      {/* Dialog box for speech/conversation */}
      <SpeechDialog content={currentSpeech} visible={showSpeech} setVisible={setShowSpeech}/>

      {/* Container for all the detailed views */}
      <TabView className="my-3" style={{ maxWidth: '1000px' }}
        activeIndex={activeIndex} onTabChange={(e) => setActiveIndex(e.index)}>

        {/* The vertical timeline */}
        <TabPanel header="Timeline Events" style={{ maxWidth: '1000px', maxHeight: '1000px' }}>
          <div className='card overflow-auto' style={{ maxHeight: '1000px' }}>
            {events.length <= 1000 && <Timeline value={events} align="alternate" className="customized-timeline" marker={customizedMarker} content={customizedContent} />}
          </div>
        </TabPanel>

        {/* QA result */}
        <TabPanel header="Query result" style={{ maxWidth: '1000px' }}>
          <p className="m-0">
            <SyntaxHighlighter language="javascript" style={coy}>
              {JSON.stringify(answer, null, 2)}
            </SyntaxHighlighter>
          </p>
        </TabPanel>

        {/* Result video clips (Not used for now) */}
        {/* <TabPanel header="Video clip" style={{ maxWidth: '1000px' }}>
          <Player
            playsInline
            // poster="/assets/poster.png"
            src={(selectedIDs && selectedIDs.length > 0) ? `data/videos/movie_${selectedIDs[0]}.mp4` : video_url}
          // can be a local mp4 from public/
          />
        </TabPanel> */}

        {/* Retrieval results (for supporting evidence) */}
        <TabPanel header="Retrieval Results" style={{ maxWidth: '1000px' }}>
          {answer.sources && <div className='card overflow-auto' style={{ maxHeight: '1000px' }}>
            <Timeline value={source_to_events(answer.sources)} align="alternate" className="customized-timeline" marker={customizedMarker} content={customizedContent} />
          </div>}
        </TabPanel>

        {/* Heatmap */}
        <TabPanel header="Heatmap" toggleable style={{ maxWidth: '1000px' }}>
          <div className='card overflow-x-auto'>
            <HeatMap
              className='text-sm'
              value={dayCount}
              width={dayLength}
              startDate={selectedDateRange ? addDays(selectedDateRange[0], -120) : startDay}
              endDate={selectedDateRange ? addDays(selectedDateRange[1] ? selectedDateRange[1] : selectedDateRange[0], 120) : today}
              // startDate={startDay}
              // endDate={today}
              rectSize={20}
              space={4}
              legendCellSize={0}
              rectRender={(props, data) => {
                return (
                  <rect className={'rect' + data.date.replaceAll('/', '_')} {...props} onClick={() => {
                    let start = new Date(data.date);
                    let end = addDays(start, 1);
                    setZoom(256);
                    setSelectedDateRange([start, end]);
                  }}>
                    {data.count > 0 && <Tooltip target={'.rect' + data.date.replaceAll('/', '_')} placement="top" content={showCount(data)} />}
                  </rect>
                );
              }}
              style={{ height: 200 }}
            />
          </div>
        </TabPanel>

        {/* Displaying geo locations on GoogleMap */}
        <TabPanel header="Map" style={{ maxWidth: '1000px' }}>
          <GoogleMapComponent geo={geo} height="60vh" setSelectedDateRange={setSelectedDateRange} setSelectedIDs={setSelectedIDs} />
        </TabPanel>

        {/* Displaying the raw JSON object for an episode */}
        <TabPanel header="Details" style={{ maxWidth: '1000px' }}>
          <SyntaxHighlighter language="javascript" style={coy}>
            {JSON.stringify(worldState, null, 2)}
          </SyntaxHighlighter>
        </TabPanel>

      </TabView>

    </div>
  );
}

export default App;
