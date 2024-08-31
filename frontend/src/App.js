import React from "react";
import Search from "./components/Search";
import { BrowserRouter as Router, Route, Routes, useNavigate } from "react-router-dom";
import { objectDetection } from "./pages/position";
// import Images from "./components/Images";

function App() {
	return (
		<Router>
			<Routes>
				<Route path="/" element={<Search />} />
				<Route path="/position" element={<objectDetection />} />
			</Routes>
		</Router>
	);
}

export default App;
