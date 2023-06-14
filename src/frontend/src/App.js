// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.

// This source code is licensed under the license found in the
// LICENSE file in the root directory of this source tree.
import './App.css';

import React, { useEffect, useState, useRef } from 'react';
import { Terminal } from 'primereact/terminal';
import { TerminalService } from 'primereact/terminalservice';
import { ProgressBar } from 'primereact/progressbar';
import { TabView, TabPanel } from 'primereact/tabview';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { addDays } from './timeline/builders'
import { Tooltip } from 'primereact/tooltip';
import { Toast } from 'primereact/toast';
import { RadioButton } from 'primereact/radiobutton';
import { Image } from 'primereact/image';
import { Dialog } from 'primereact/dialog';
import { Calendar } from 'primereact/calendar';
import { Divider } from 'primereact/divider';
import { Dropdown } from 'primereact/dropdown';
import { Toolbar } from 'primereact/toolbar';


import HeatMap from '@uiw/react-heat-map';
import GoogleMapComponent from './map/GoogleMapComponent';

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { coy } from 'react-syntax-highlighter/dist/esm/styles/prism';

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

  // digital data tracks
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

  // selected track
  const [selectedTrack, setSelectedTrack] = useState(null);

  // world-state
  const [worldState, setWorldState] = useState({
    'id': 'none',
    'some_attribute': 'val'
  });

  // events to be shown in the timeline
  const [events, setEvents] = useState([]);

  // selected event ID's
  const [selectedIDs, setSelectedIDs] = useState(null);

  // selected view's index (timeline, map, etc.)
  const [activeIndex, setActiveIndex] = useState(0);

  // qa engine
  const [qa, setQA] = useState(null);

  // sample questions
  const [sampleQuestions, setSampleQuestions] = useState([
    "Show me some photos of plants in my neighborhood", 
    "Which cities did I visit when I traveled to Japan?",
    "How many books did I purchase in April?"]);

  // different qa methods
  const qa_methods = ["ChatGPT", "Retrieval-based", "View-based"]

  // mapping names of the different maps to indices
  // const view_name_mp = {
  //   "timeline": 0, "query_result": 1, "video": 2,
  //   "retrieval_result": 3, "heatmap": 4,
  //   "map": 5, "details": 6
  // }
  const view_name_mp = {
    "query_result": 0,
    "retrieval_result": 1, 
    "map": 2, "details": 3
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
   * @param {Object} element - the episode
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

  /**
   * useEffect hooks for updating the events to be shown on the timeline
   * when selected data range changes.
   */
  useEffect(() => {
    let new_events = [];
    let new_geo = [];
    let [start, end] = [startDay, addDays(startDay, 180)];
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
   * Displaying one episode in the timeline.
   * @param {Object} item - the event to be displayed
   * @returns
   */
  const customizedContent_v2 = (item) => {
    return (
      <Card title={item.title} subTitle={item.date} className='mb-3 shadow-3'>
        {item.summary && <ShowMore summary={item.summary} />}
        {item.image && <Image src={`${item.image}`} alt={item.name} height={200} width={200} className="shadow-1" preview />}
        {item.spotify &&
          <iframe style={{ "borderRadius": "12px" }} src={item.spotify.replace('/track/', '/embed/track/')}
            width="200" height="200" frameBorder="0" allow="autoplay;
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

        {item.lat && item.long && <GoogleMapComponent geo={[item]} height="13vh" width="13vh" 
          setSelectedDateRange={setSelectedDateRange} setSelectedIDs={setSelectedIDs} />
        }

        {item.data.exercise_text &&
          <Button className="my-2" label="Exercise" link onClick={() => {
            setShowSpeech(true);
            setCurrentSpeech(item.data.exercise_text);}}/>
        }

        <div>
        <Button className="my-2" label="More details" link onClick={() => {
          setWorldState(item.data);
          setActiveIndex(view_name_mp["details"]);
        }} />
        </div>
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

  const events_to_timeline = (tracks, selectedDateRange, selectedTrack, sources) => {

    let [start, end] = [startDay, today];
    if (selectedDateRange && selectedDateRange.length == 2) {
      [start, end] = selectedDateRange;
      if (end === null) {
        end = addDays(start, 1);
      }
    }

    // collect events
    // start/end dates
    let events = [];
    if (sources) {
      events = source_to_events(sources);
    } else {
      for (let i = 0; i < tracks.length; i++) {
        // console.log(selectedTrack);
        if (selectedTrack && tracks[i].title !== selectedTrack.name) {
          continue;
        }
        for (let j = 0; j < tracks[i].elements.length; j++) {
          let element = tracks[i].elements[j];
          if (element.start.getTime() >= start.getTime() && element.start.getTime() <= end.getTime()) {
            events.push(element_to_event(tracks[i].title, tracks[i].elements[j]));
          }
        }
      }

      events.sort((a, b) => {
        let a_time = new Date(a.date).getTime();
        let b_time = new Date(b.date).getTime();
        return a_time - b_time;
      });
    }

    // year, month, day
    let new_events = []
    for (let i = 0; i < events.length; i++) {
      // if not same year
      if (i === 0 || new Date(events[i].date).getFullYear() !== new Date(events[i-1].date).getFullYear()) {
        new_events.push({"year": new Date(events[i].date).getFullYear()});
      }

      if (i === 0 || new Date(events[i].date).getMonth() !== new Date(events[i-1].date).getMonth()) {
        new_events.push({"month": new Date(events[i].date).getMonth()});
      }

      if (i === 0 || new Date(events[i].date).getDate() !== new Date(events[i-1].date).getDate()) {
        new_events.push({"day": new Date(events[i].date).toDateString()});
      }

      new_events.push(events[i]);
    }

    let to_content = (_input) => {
      return <div>
      {"year" in _input &&  <> <h3> <i className='pi pi-calendar-plus' /> Year {_input.year}</h3></>}
      {"month" in _input && <><Divider className='my-3'/> <h3>{["January", "February", "March",
    "April", "May", "June",
    "July", "August", "September",
    "October", "November", "December"][_input.month]}</h3></>}
      {"day" in _input && <><Divider className='my-3'/><h3>{_input.day}</h3></>}
      {"title" in _input && customizedContent_v2(_input)}
      </div>;
    }

    // return <div>{events.map(customizedContent)} </div>
    return <div>{new_events.map(to_content)} </div>
    // to_content
  }

  const generate_summaries = (tracks) => {
    let [start, end] = [startDay, today];
    if (selectedDateRange && selectedDateRange.length == 2) {
      [start, end] = selectedDateRange;
      if (end === null) {
        end = addDays(start, 1);
      }
    }

    let purchase = [];
    let places = [];
    let books = [];
    let streaming = []

    for (let i = 0; i < tracks.length; i++) {
      for (let j = 0; j < tracks[i].elements.length; j++) {
        let element = tracks[i].elements[j];
        if (element.start.getTime() >= start.getTime() && element.start.getTime() <= end.getTime()) {
          let event = element_to_event(tracks[i].title, element);
          if (tracks[i].title === 'purchase') {
            purchase.push(event);
          } else if (tracks[i].title === 'streaming' && event.spotify) {
            streaming.push(event);
          } else if (tracks[i].title === 'places') {
            places.push(event);
          } else if (tracks[i].title === 'books') {
            books.push(event);
          }
        }
      }
    }

    // purchase
    return <>
    {places.length > 0 && <Card title="Places you visited" className='mb-3 shadow-3'>
      <div style={{width: "500px"}}><GoogleMapComponent geo={places} height="20vh" width="47vh" 
                setSelectedDateRange={setSelectedDateRange} setSelectedIDs={setSelectedIDs}/>
      </div>      
      {/* <div className="grid">
      {places.slice(0, 8).map((event) => {
        return <div className="col-fixed mx-3 my-3" style={{width: "150px"}}><GoogleMapComponent geo={[event]} height="10vh" width="10vh" 
                setSelectedDateRange={setSelectedDateRange} setSelectedIDs={setSelectedIDs}/>
               </div>;
      }
      )}      
      </div> */}
    </Card>}

    {books.length > 0 && <Card title="Books you read" className='mb-3 shadow-3'>
      <div className="grid">
      {books.slice(0, 12).map((item) => {
        return <div className="col-fixed mx-2 my-2" style={{width: "100px"}}>
        {item.image && <Image src={`${item.image}`} alt={item.name} height={100} width={100} className="shadow-1" preview />}
               </div>;
      }
      )}      
      </div>
    </Card>}

    {purchase.length > 0 && <Card title="Purchases you made" className='mb-3 shadow-3'>
      {purchase.slice(0, 7).map((event) => {return <><Divider/>
        {event.title}
      </>})}
    </Card>}

    {streaming.length > 0 && <Card title="Content you stream" className='mb-3 shadow-3'>
    <div className="grid">
      {streaming.slice(0, 9).map((item) => {
                return <div className="col-fixed mx-2 my-2" style={{width: "200px"}}>
                <iframe style={{ "borderRadius": "12px" }} src={item.spotify.replace('/track/', '/embed/track/')}
            width="200" height="200" frameBorder="0" allow="autoplay;
                clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"/>
                       </div>;
        })}
      </div>
    </Card>}

    </>;
  }

  const copyToClipboard = async (textToCopy) => {
    // Navigator clipboard api needs a secure context (https)
    if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(textToCopy);
    } else {
        // Use the 'out of viewport hidden text area' trick
        const textArea = document.createElement("textarea");
        textArea.value = textToCopy;

        // Move textarea out of the viewport so it's not visible
        textArea.style.position = "absolute";
        textArea.style.left = "-999999px";

        document.body.prepend(textArea);
        textArea.select();

        try {
            document.execCommand('copy');
        } catch (error) {
            console.error(error);
        } finally {
            textArea.remove();
        }
    };
  }

  useEffect(() => { importDigitalData(tracks, setTracks, setSelectedDateRange, toast); }, []);
  
  return (
    <div className="App">
      {/* For message (success, fail) display */}
      <Toast ref={toast}></Toast>

      <h1 className="my-0 title">Personal Timeline</h1>
      <h3 className="font-light">Research by Meta AI</h3>
      <Divider className='my-3'/>

      <h2 className="">Query your personal timeline</h2>
      {/* QA dialog box */}
      <div class="grid">
      <div class="col-fixed mr-6" style={{width: '800px'}}>
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
      <span className='my-2'> {sampleQuestions.map((q) => {return <Button className='mx-2 my-1 p-chip p-chip-text overflow-x-auto' label={q} onClick={() =>
        {
          if (qa === null) {
            setQA('Retrieval-based');
          }
          // navigator.clipboard.writeText(q);
          copyToClipboard(q);
          toast.current.show({ severity: 'success', summary: 'Success', detail: 'Copied to clipboard!' });
        }}/> }) } </span>
      <div class="terminal-demo">
      <Terminal className="text-lg line-height-3" style={{ maxWidth: '800px', height: '500px' }} welcomeMessage="Welcome to TL-QA" prompt="TL-QA $" />
      </div>
      <ProgressBar mode="indeterminate" style={{ maxWidth: '800px', height: '6px', display: running ? '' : 'none' }}></ProgressBar>
      </div>

      {/* Container for all the detailed views */}
      <div class="col-fixed" style={{width: '800px'}}>
      <TabView className="my-3" style={{ maxWidth: '800px' }}
        activeIndex={activeIndex} onTabChange={(e) => setActiveIndex(e.index)}>

        {/* QA result */}
        <TabPanel header="Query result" style={{ maxWidth: '800px' }}>
          <p className="m-0">
            <SyntaxHighlighter language="javascript" style={coy}>
              {JSON.stringify(answer, null, 2)}
            </SyntaxHighlighter>
          </p>
        </TabPanel>

        {/* Retrieval results (for supporting evidence) */}
        <TabPanel header="Retrieval Results" style={{ maxWidth: '800px' }}>
          {answer.sources && <div className='card overflow-auto' style={{ maxHeight: '700px' }}>
            {events_to_timeline(tracks, null, null, answer.sources)}
          </div>}
        </TabPanel>

        {/* Displaying geo locations on GoogleMap */}
        <TabPanel header="Map" style={{ maxWidth: '800px' }}>
          <GoogleMapComponent geo={geo} height="36vh" setSelectedDateRange={setSelectedDateRange} setSelectedIDs={setSelectedIDs} />
        </TabPanel>

        {/* Displaying the raw JSON object for an episode */}
        <TabPanel header="Details" style={{ maxWidth: '800px' }}>
          <SyntaxHighlighter language="javascript" style={coy}>
            {JSON.stringify(worldState, null, 2)}
          </SyntaxHighlighter>
        </TabPanel>

      </TabView>
      </div>
      </div>

      <Divider className='my-5'/>
      <h2 className="my-5">Your personal timeline</h2>

      <div class="grid">
      <div class="col-fixed mr-6" style={{width: '800px'}}>

      <Toolbar start={<span className="p-float-label">
      <Calendar className="mr-4" inputId="date_range" value={selectedDateRange} onChange={(e) => {
          setSelectedDateRange(e.value);
        }} selectionMode="range" readOnlyInput />
      <label htmlFor="date_range">Date Range</label>
      </span>} 
      
      end={      <Dropdown value={selectedTrack} onChange={(e) => setSelectedTrack(e.value)} options={ Object.keys(icon_map).map((option) => {return {name: option}}) } optionLabel="name" 
      placeholder="All Events" showClear className="w-full md:w-14rem" />} />

      {/* For selecting date range */}
      
              {/* The vertical timeline */}
        <Card className='card overflow-auto' >
          <div style={{ maxWidth: '800px', maxHeight: '2500px' }}>
            {/* {<Timeline value={events} align="alternate" className="customized-timeline" marker={customizedMarker} content={customizedContent} />} */}
            {events_to_timeline(tracks, selectedDateRange, selectedTrack, null)}
          </div>
        </Card>
      </div>

      <div class="col-fixed" style={{width: '800px'}}>
        {/* Summaries */}
        {generate_summaries(tracks)}
        
        <Card title="Heatmap" className='shadow-3'>
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
        </Card>
      </div>

      </div>
    </div>
  );
}

export default App;
