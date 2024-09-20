import React from "react";
import Search from "./components/Search";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
// import Position from "./pages/position";

function App() {

	return (
		<Router>
			<Routes>
				<Route path="/" element={<Search />} />
				{/* <Route path="/position" element={<Position />} /> */}
			</Routes>
		</Router>
	);
}

export default App;
