import { useEffect, useRef } from 'react'
import Plotly from 'plotly.js-basic-dist-min'
export default function Plot({ data, layout = {}, height = 280 }) {
  const ref = useRef(null)
  useEffect(() => {
    Plotly.react(ref.current, data, { height, margin: { t: 20, r: 10, b: 40, l: 50 }, paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)', legend: { orientation: 'h', y: -0.25 }, ...layout }, { displayModeBar: false, responsive: true })
  }, [data, layout, height])
  return <div ref={ref} className="w-full" />
}
