// Copyright (c) Meta Platforms, Inc. and affiliates.
// All rights reserved.

// This source code is licensed under the license found in the
// LICENSE file in the root directory of this source tree.
import {
  MONTH_NAMES,
  MONTHS_PER_YEAR,
  QUARTERS_PER_YEAR,
  MONTHS_PER_QUARTER,
} from "./constants";
  
import {
  hexToRgb,
  colourIsLight,
  addMonthsToYear,
  addMonthsToYearAsDate,
  nextColor,
  randomTitle
} from "./utils";
  
export const buildQuarterCells = (START_YEAR, NUM_OF_YEARS) => {
  const v = [];
  for (let i = 0; i < QUARTERS_PER_YEAR * NUM_OF_YEARS; i += 1) {
    const quarter = (i % 4) + 1;
    const startMonth = i * MONTHS_PER_QUARTER;
    const s = addMonthsToYear(START_YEAR, startMonth);
    const e = addMonthsToYear(START_YEAR, startMonth + MONTHS_PER_QUARTER);
    v.push({
      id: `${s.year}-q${quarter}`,
      title: `Q${quarter} ${s.year}`,
      start: new Date(`${s.year}-${s.month}-01`),
      end: new Date(`${e.year}-${e.month}-01`)
    });
  }
  return v;
};

export const buildMonthCells = (START_YEAR, NUM_OF_YEARS) => {
  const v = [];
  for (let i = 0; i < MONTHS_PER_YEAR * NUM_OF_YEARS; i += 1) {
    const startMonth = i;
    const start = addMonthsToYearAsDate(START_YEAR, startMonth);
    const end = addMonthsToYearAsDate(START_YEAR, startMonth + 1);
    v.push({
      id: `m${startMonth}`,
      title: MONTH_NAMES[i % 12],
      start,
      end
    });
  }
  return v;
};

export const addDays = (date, days) => {
  var ms = new Date(date).getTime() + 86400000 * days;
  var result = new Date(ms);
  return result;
}

export const buildHourCells = (START_YEAR, NUM_OF_YEARS) => {
  const v = [];
  let start = addMonthsToYearAsDate(START_YEAR, 0);
  let end = addDays(start, 0.25);

  let last_year = START_YEAR + NUM_OF_YEARS - 1;

  while (start.getFullYear() <= last_year) {
    v.push({
      id: `h${start}`,
      title: `${start.getHours()}`,
      start,
      end
    });
    start = addDays(start, 0.25);
    end = addDays(end, 0.25);
  }
  return v;
};

export const buildDayCells = (START_YEAR, NUM_OF_YEARS) => {
  const v = [];
  let start = addMonthsToYearAsDate(START_YEAR, 0);
  let end = addDays(start, 1);

  let last_year = START_YEAR + NUM_OF_YEARS - 1;
  const weekday_names = 'UMTWRFS'

  while (start.getFullYear() <= last_year) {
    v.push({
      id: `d${start}`,
      title: `${weekday_names[start.getDay()]}`,
      start,
      end
    });
    start = addDays(start, 1);
    end = addDays(end, 1);
  }
  return v;
};

export const buildWeekCells = (START_YEAR, NUM_OF_YEARS) => {
  const v = [];
  let start = addMonthsToYearAsDate(START_YEAR, 0);
  let end = addDays(start, 7);

  let last_year = START_YEAR + NUM_OF_YEARS - 1;

  while (start.getFullYear() <= last_year) {
    v.push({
      id: `w${start}`,
      title: `${start.getMonth()+1}/${start.getDate()}`,
      start,
      end
    });
    start = addDays(start, 7);
    end = addDays(end, 7);
  }
  return v;
};


export const buildTimebar = (START_YEAR) => {
  let NUM_OF_YEARS = new Date().getFullYear() - START_YEAR + 1;
  return [
    {
      id: "quarters",
      title: "Quarters",
      cells: buildQuarterCells(START_YEAR, NUM_OF_YEARS),
      style: {}
    },
    {
      id: "months",
      title: "Months",
      cells: buildMonthCells(START_YEAR, NUM_OF_YEARS),
      useAsGrid: true,
      style: {}
    },
    {
      id: "weeks",
      title: "Weeks",
      cells: buildWeekCells(START_YEAR, NUM_OF_YEARS),
      // useAsGrid: true,
      style: {}
    },
    {
        id: "days",
        title: "Days",
        cells: buildDayCells(START_YEAR, NUM_OF_YEARS),
        // useAsGrid: true,
        style: {}
    },
    {
      id: "hours",
      title: "Hours",
      cells: buildHourCells(START_YEAR, NUM_OF_YEARS),
      // useAsGrid: true,
      style: {}
    }  
  ];
};

export const buildElement = ({ trackId, start, end, i }) => {
  const bgColor = nextColor(trackId);
  const color = colourIsLight(...hexToRgb(bgColor)) ? "#000000" : "#ffffff";
  return {
    id: `t-${trackId}-el-${i}`,
    title: randomTitle(),
    start,
    end,
    style: {
      backgroundColor: `#${bgColor}`,
      color,
      borderRadius: "4px",
      boxShadow: "1px 1px 0px rgba(0, 0, 0, 0.25)",
      textTransform: "capitalize"
    }
  };
};

// export const buildTrackStartGap = () =>
//   Math.floor(Math.random() * MAX_TRACK_START_GAP);
// export const buildElementGap = () =>
//   Math.floor(Math.random() * MAX_ELEMENT_GAP);

// export const buildElements = trackId => {
//   const v = [];
//   let i = 1;
//   let month = buildTrackStartGap();

//   while (month < NUM_OF_MONTHS) {
//     let monthSpan =
//       Math.floor(Math.random() * (MAX_MONTH_SPAN - (MIN_MONTH_SPAN - 1))) +
//       MIN_MONTH_SPAN;

//     if (month + monthSpan > NUM_OF_MONTHS) {
//       monthSpan = NUM_OF_MONTHS - month;
//     }

//     const start = addMonthsToYearAsDate(START_YEAR, month);
//     const end = addMonthsToYearAsDate(START_YEAR, month + monthSpan);
//     v.push(
//       buildElement({
//         trackId,
//         start,
//         end,
//         i
//       })
//     );
//     const gap = buildElementGap();
//     month += monthSpan + gap;
//     i += 1;
//   }

//   return v;
// };

// export const buildSubtrack = (trackId, subtrackId) => ({
//   id: `track-${trackId}-${subtrackId}`,
//   title: `Subtrack ${subtrackId}`,
//   elements: buildElements(subtrackId)
// });

// export const buildTrack = trackId => {
//   const tracks = fill(Math.floor(Math.random() * MAX_NUM_OF_SUBTRACKS) + 1).map(
//     i => buildSubtrack(trackId, i + 1)
//   );
//   return {
//     id: `track-${trackId}`,
//     title: `Track ${trackId}`,
//     elements: buildElements(trackId),
//     tracks,
//     // hasButton: true,
//     // link: 'www.google.com',
//     isOpen: false
//   };
// };
