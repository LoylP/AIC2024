import React, { useRef, useState } from "react";
import Search from "./components/Search";
import { BrowserRouter as Router, Route, Routes, useNavigate } from "react-router-dom";
// import Images from "./components/Images";
import Position from "./pages/position";

function App() {
	// const videoRef = useRef(null);
	// const [time, setTime] = useState("");

	// const handleSeek = () => {
	// 	if (videoRef.current) {
	// 		videoRef.current.currentTime = parseFloat(time)/25; 
	// 	}
	// };

	return (
		<Router>
			<Routes>
				<Route path="/" element={<Search />} />
				<Route path="/position" element={<Position />} />
			</Routes>
		</Router>
		// <div>
		// 	<input
		// 		type="text"
		// 		value={time}
		// 		onChange={(e) => setTime(e.target.value)} // Update state on input change
		// 		placeholder="Enter time in seconds"
		// 	/>
		// 	<button onClick={handleSeek}>Seek</button>
		// 	<video
		// 		ref={videoRef}
		// 		width="600"
		// 		controls
		// 		preload="auto"
		// 		muted
		// 		crossOrigin="anonymous"
		// 		autoPlay
		// 	>
		// 		<source src="http://localhost:8000/videos/Videos_L05/L05_V001.mp4" type="video/mp4" />
		// 		Your browser does not support the video tag.
		// 	</video>
		// </div>
	);
}

export default App;
