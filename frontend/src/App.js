import React from "react";
// import Search from "./components/Search";
import SearchExtra from "./components/SearchExtra";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

function App() {

	return (
		<Router>
			<Routes>
				{/* <Route path="/" element={<Search />} /> */}
				<Route path="/" element={<SearchExtra />} />

			</Routes>
		</Router>
	);
}

export default App;
