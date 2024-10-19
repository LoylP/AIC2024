import React, { useState, useRef, useEffect } from "react";
import { Spin, Collapse, Input, Button, message } from "antd";
import "./Search.css";


const API_BASE_URL = "http://127.0.0.1:8080"

const { Panel } = Collapse;

const Search = () => {
	const [inputType, setInputType] = useState("text");
	const [searchValue, setSearchValue] = useState("");
	const [nextQueries, setNextQueries] = useState([""]);
	const [results, setResults] = useState([]);
	const [currentPage, setCurrentPage] = useState(1);
	const [ocrDescription, setOcrDescription] = useState("");
	const [selectedFile, setSelectedFile] = useState(null);
	const [selectedImage, setSelectedImage] = useState(null);
	const [showModal, setShowModal] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const modalRef = useRef(null);
	const [useExpandedPrompt, setUseExpandedPrompt] = useState(false);
	const [isOcrDisabled, setIsOcrDisabled] = useState(false);
	const [showVideo, setShowVideo] = useState(false); 
	const [surroundingImages, setSurroundingImages] = useState([]); 

	const itemsPerPage = 25;

	const indexOfLastItem = currentPage * itemsPerPage;
	const indexOfFirstItem = indexOfLastItem - itemsPerPage;
	const currentItems = Array.isArray(results) ? results.slice(indexOfFirstItem, indexOfLastItem) : [];

	//Show video
	const videoRef = useRef(null);
	const [time, setTime] = useState("");
	const [inputMode, setInputMode] = useState("kis"); 


	const handleSeek = () => {
		if (videoRef.current) {
			const folderName = selectedImage.folder; 
			let fps = videoRef.current.fps; 
			if (!fps) { 
				fps = folderName.startsWith("Videos_L") && parseInt(folderName.slice(-2)) >= 13 ? 30 : 25; 
			}
			
			const parsedTime = parseFloat(time);
			if (isFinite(parsedTime)) {
				videoRef.current.currentTime = parsedTime / fps; 
			} else {
				console.error("Invalid time value:", time);
			}
		}
	};

	const handleInputChange = (e) => {
		setSearchValue(e.target.value);
	};

	const handleNextQueryChange = (index, value) => {
		const newNextQueries = [...nextQueries];
		newNextQueries[index] = value;
		setNextQueries(newNextQueries);
		// Removed the condition that disables OCR input based on next queries
		// setIsOcrDisabled(newNextQueries.some(q => q) || !value); 

		// Clear OCR description if any next query is entered
		if (value) {
			setOcrDescription(""); // Clear OCR description
		}
	};

	const addNextQuery = () => {
		setNextQueries([...nextQueries, ""]); // Add a new empty query
	};

	const removeNextQuery = (index) => {
		setNextQueries(nextQueries.filter((_, i) => i !== index));
	};

	const handleButtonSearch = async () => {
		setIsLoading(true);
		try {
			let response;

			if (inputType === "text") {
				const url = new URL(`${API_BASE_URL}/api/milvus/search`);
				if (searchValue) {
					url.searchParams.append("search_query", searchValue);
				}
				if (ocrDescription) {
					url.searchParams.append("ocr_filter", ocrDescription);
				}
	
				url.searchParams.append("use_expanded_prompt", useExpandedPrompt);

				// Add next queries to the URL
				if (nextQueries.length > 0) {
					nextQueries.forEach((nextQuery) => {
						if (nextQuery) {
							url.searchParams.append("next_queries", nextQuery);
						}
					});
				}

				if (searchValue || ocrDescription || nextQueries.some(q => q)) {
					response = await fetch(url);
				} else {
					throw new Error("Please provide at least one search criteria");
				}
			} else if (inputType === "file" && selectedFile) {
				const formData = new FormData();
				formData.append("image", selectedFile);
				const url = new URL(`${API_BASE_URL}/api/milvus/search_by_image`);
				if (ocrDescription) {
					url.searchParams.append("ocr_filter", ocrDescription);
				}
			
				response = await fetch(url, {
					method: "POST",
					body: formData,
				});
			} else {
				throw new Error("Please provide an image file or search query");
			}

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const data = await response.json();
			if (data.results && Array.isArray(data.results)) {
				setResults(data.results);
			} else {
				console.error("Unexpected data structure:", data);
				setResults([]);
			}
			setCurrentPage(1);
		} catch (error) {
			console.error("Error during search:", error);
			setResults([]);
		} finally {
			setIsLoading(false);
		}
	};

	const handleFileChange = (e) => {
		const file = e.target.files[0];
		setSelectedFile(file);
	};

	const totalPages = Math.ceil((Array.isArray(results) ? results.length : 0) / itemsPerPage);

	const handlePageClick = (pageNum) => {
		setCurrentPage(pageNum);
	};

	const handleImageClick = async (image) => {
		setSelectedImage(image);
		setShowModal(true);
		setShowVideo(false); // Hide video when selecting a new image

		// Call the API to fetch surrounding images
		await fetchSurroundingImages(image.file_path); // Pass the file path of the selected image
	};

	const fetchSurroundingImages = async (imagePath) => {
		setIsLoading(true);
		try {
			const response = await fetch(`${API_BASE_URL}/api/serve-images-around?filename=${encodeURIComponent(imagePath)}`); // Sử dụng biến môi trường
			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}
			const data = await response.json();
			if (data.surrounding_images && Array.isArray(data.surrounding_images)) {
				setSurroundingImages(data.surrounding_images); // Store surrounding images
			} else {
				console.error("Unexpected data structure:", data);
				setSurroundingImages([]);
			}
		} catch (error) {
			console.error("Error fetching surrounding images:", error);
		} finally {
			setIsLoading(false);
		}
	};

	const handleCloseModal = () => {
		setShowModal(false);
		setSelectedImage(null);
	};

	const handleSearchSimilar = async () => {
		if (selectedImage) {
			setIsLoading(true);
			try {
				const response = await fetch(`${API_BASE_URL}/api/search_similar?image_path=${encodeURIComponent(selectedImage.file_path)}&ocr_filter=${ocrDescription}&results=100`, {
					method: "GET",
				});

				if (!response.ok) {
					throw new Error(`HTTP error! status: ${response.status}`);
				}

				const data = await response.json();
				if (data.results && Array.isArray(data.results)) {
					setResults(data.results);
				} else {
					console.error("Unexpected data structure:", data);
					setResults([]);
				}

				setCurrentPage(1);
				setShowModal(false);
			} catch (error) {
				console.error("Error during similar image search:", error);
			} finally {
				setIsLoading(false);
			}
		}
	};

	const handleReset = () => {
		setInputType("text");
		setSearchValue("");
		setResults([]);
		setCurrentPage(1);
		setOcrDescription("");
		setSelectedFile(null);
		setSelectedImage(null);
		setNextQueries([""]); // Reset next queries
	};

	useEffect(() => {
		const handleClickOutside = (event) => {
			if (modalRef.current && !modalRef.current.contains(event.target)) {
				handleCloseModal();
			}
		};

		document.addEventListener("mousedown", handleClickOutside);
		return () => {
			document.removeEventListener("mousedown", handleClickOutside);
		};
	}, []);

	const handleExportCSV = async () => {
		if (results.length === 0) {
			message.error("No results to export");
			return;
		}

		try {
			const response = await fetch(`${API_BASE_URL}/api/export-to-csv`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(results.slice(0, 100)),
			});

			if (response.ok) {
				const blob = await response.blob();
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement("a");
				a.style.display = "none";
				a.href = url;
				a.download = "search_results.csv";
				document.body.appendChild(a);
				a.click();
				window.URL.revokeObjectURL(url);
			} else {
				throw new Error("Failed to export CSV");
			}
		} catch (error) {
			console.error("Error exporting CSV:", error);
			message.error("Failed to export CSV");
		}
	};

	// Add a button to close all next queries
	const closeAllNextQueries = () => {
		setNextQueries([""]); // Reset next queries
		setOcrDescription(""); // Clear OCR description
		setIsOcrDisabled(false); // Enable OCR input when closing all next queries
	};

	const handleSubmit = async () => {
		if (inputMode === "qa") {
			const number = parseInt(document.querySelector('input[placeholder="Number"]').value);
			const videos_ID = document.querySelector('input[placeholder="Videos_ID"]').value;
			const time = parseFloat(document.querySelector('input[placeholder="Time"]').value);

			try {
				const response = await fetch(`${API_BASE_URL}/api/submit-qa?number=${number}&videos_ID=${videos_ID}&time=${time}`, {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
					},
				});

				const data = await response.json();				
				if (data.status === true) { // Changed from == to ===
					if (data.submission === "WRONG") { // Changed from == to ===
						message.error(`Sai đáp án!\n${data.description}`);
					} else {
						message.success(`Nộp thành công!\n${data.submission}\n${data.description}`);
					}
				} else {
					message.error("Chưa nộp được! hoặc đã nộp trước đó!");
				}
			} catch (error) {
				console.error("Error submitting QA:", error);
				message.error("Failed to submit QA");
			}
		} else if (inputMode === "kis") {
			const videos_ID = document.querySelector('input[placeholder="Videos_ID"]').value;
			const start = parseInt(document.querySelector('input[placeholder="Start Time"]').value) || 0; // Default to 0 if NaN
			const end = parseInt(document.querySelector('input[placeholder="End Time"]').value) || 0; // Default to 0 if NaN

			// Ensure start and end are valid numbers
			if (isNaN(start) || isNaN(end)) {
				message.error("Start and End times must be valid numbers.");
				return;
			}

			try {
				const response = await fetch(`${API_BASE_URL}/api/submit-kis?videos_ID=${videos_ID}&start=${start}&end=${end}`, {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
					},
				});

				//Colab
				const data = await response.json();				
				if (data.status === true) { // Changed from == to ===
					if (data.submission === "WRONG") { // Changed from == to ===
						message.error(`Sai đáp án!\n${data.description}`);
					} else {
						message.success(`Nộp thành công!\n${data.submission}\n${data.description}`);
					}
				} else {
					message.error("Chưa nộp được! hoặc đã nộp trước đó!");
				}
			} catch (error) {
				console.error("Error submitting KIS:", error);
				message.error("Failed to submit KIS");
			}
		}
	};

	const handleKis = () => {
		setInputMode("kis"); // Set input mode to kis
	};

	const handleQA = () => {
		setInputMode("qa"); // Set input mode to QA
	};

	return (
		<div>
			<div className="flex flex-col h-screen">
				<div className="flex flex-1">
					{/* Search panel - 1/5 of the screen */}
					<div
						className="w-1/5 bg-slate-300 p-4 flex flex-col"
						style={{
							backgroundColor: "white",
						}}>
						<h1 className="text-4xl font-bold text-center mb-6 bg-gradient-to-r from-blue-500 to-teal-400 text-transparent bg-clip-text drop-shadow-lg font-sans tracking-wide">
							W1-Artemis
						</h1>
						<div className="flex justify-between items-center mb-4">
							<h2 className="text-2xl font-bold text-black">Your query</h2>
							<button
								onClick={handleReset}
								className="bg-gray-300 text-black px-3 py-1 rounded hover:bg-gray-400">
								Reset
							</button>
						</div>
						<select
							className="mb-4 p-2 border rounded text-black"
							value={inputType}
							onChange={(e) => setInputType(e.target.value)}>
							<option value="text">Search Text</option>
							<option value="file">Upload File</option>
						</select>
						{inputType === "text" ? (
							<textarea
								className="mb-4 p-2 border rounded resize-none text-black"
								type="search"
								placeholder="Search Anything..."
								onChange={handleInputChange}
								value={searchValue}
								style={{ height: 120, borderRadius: 10 }}
							/>
						) : (
							<input
								className="mb-4 p-2 border rounded text-black"
								type="file"
								onChange={handleFileChange}
							/>
						)}
						<div className="flex items-center mb-4"> {/* New div for the expand button */}
							<input
								type="checkbox"
								checked={useExpandedPrompt}
								onChange={(e) => setUseExpandedPrompt(e.target.checked)} // New line
								className="mr-2"
							/>
							<label>Use Expanded Prompt</label>
						</div>
						{/* Next Queries Section */}
						<div className="mb-4">
							<h3 className="text-lg font-bold">Next Queries</h3>
							{nextQueries.map((nextQuery, index) => (
								<div key={index} className="flex items-center mb-2">
									<Input
										className="mr-2"
										placeholder={`Next Query ${index + 1}`}
										value={nextQuery}
										onChange={(e) => handleNextQueryChange(index, e.target.value)}
									/>
									<Button onClick={() => removeNextQuery(index)} type="danger">
										Remove
									</Button>
								</div>
							))}
							<Button onClick={addNextQuery} type="dashed" style={{ width: "100%" }}>
								Add Next Query
							</Button>
						</div>
						<button
							onClick={handleButtonSearch}
							disabled={inputType === "text" ? (!searchValue && !ocrDescription) : !selectedFile}
							className="text-search-btn">
							Search
						</button>
						<Collapse defaultActiveKey={["1", "2"]} style={{ padding: 10, marginTop: 30 }}>
							<Panel header="OCR Filter" key="1" style={{ fontSize: 20, fontWeight: 500 }}>
								{/* New button to close all next queries */}
								<Button onClick={closeAllNextQueries} type="danger" className="mb-2">
									Close All Next Queries
								</Button>
								<textarea
									placeholder="Enter OCR description"
									value={ocrDescription}
									onChange={(e) => setOcrDescription(e.target.value)}
									className="mb-4 p-2 border rounded resize-none text-black"
									id="ocr-textarea"
									disabled={isOcrDisabled} // Disable OCR input based on state
								/>
							</Panel>
							{/* Removed Object Filter Panel */}
						</Collapse>
					</div>

					{/* Results panel - 4/5 of the screen */}
					<div className="w-4/5 bg-slate-100 p-4">
						{isLoading ? (
							<div className="flex justify-center items-center h-full">
								<Spin size="large" />
							</div>
						) : (
							Array.isArray(results) &&
							results.length > 0 && (
								<div>
									<div className="flex justify-between items-center mb-4">
										<h2 className="text-2xl font-bold text-black">Results: </h2>
										<div className="flex items-center">
											<Button
												onClick={handleExportCSV}
												className="mr-4 bg-green-500 text-white hover:bg-green-600"
											>
												Export to CSV
											</Button>
											<div className="flex">
												{[...Array(totalPages)].map((_, index) => (
													<button
														key={index}
														id="pagination-button"
														onClick={() => handlePageClick(index + 1)}
														className={`mx-1 px-3 py-1 rounded ${
															currentPage === index + 1
																? "bg-cyan-500 text-white"
																: "bg-gray-200 text-black"
														}`}>
														{index + 1}
													</button>
												))}
											</div>
										</div>
									</div>
									<div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
										{currentItems.map((image) => (
											<div
												key={image.id}
												className="cursor-pointer relative"
												onClick={() => handleImageClick(image)}>
												<img
													className="w-full h-40 object-cover rounded shadow-md"
													src={`${API_BASE_URL}/images/${image.file_path}`}
													alt={image.file}
												/>
												<div className="absolute inset-0 flex flex-col justify-end p-2">
													<div className="bg-black bg-opacity-40 p-1 rounded">
														<p className="text-white text-sm truncate">
															{image.frame} {image.file}
														</p>
													</div>
												</div>
											</div>
										))}
									</div>
								</div>
							)
						)}
					</div>
				</div>
			</div>
			{/* Modal for image details */}
			{showModal && selectedImage && (
				<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
					<div ref={modalRef} className="bg-white p-6 rounded-lg max-w-2xl w-full overflow-y-auto max-h-[100vh]">
						<div className="flex justify-between items-center mb-4">
							<h2 className="text-2xl font-bold text-black">{selectedImage.file}</h2>
						</div>
						{/* Image display */}
						{showVideo ? (
							<video
								ref={videoRef}
								className="w-full mb-4 rounded"
								controls
								preload="auto"
								muted
								crossOrigin="anonymous"
								autoPlay
								onLoadedMetadata={() => {
									const folderName = selectedImage.folder;
									const fps = folderName.startsWith("Videos_L") && parseInt(folderName.slice(-2)) >= 13 ? 30 : 25;
									videoRef.current.currentTime = selectedImage.frame / fps;
								}}
							>
								<source src={`${API_BASE_URL}/videos/${selectedImage.folder}/${selectedImage.VideosId}.mp4`} type="video/mp4" />
								Your browser does not support the video tag.
							</video>
						) : (
							<img
								src={`${API_BASE_URL}/images/${selectedImage.file_path}`}
								alt={selectedImage.file_path}
								className="w-full mb-4 rounded"
							/>
						)}
						<div className="flex gap-4">
							<p className="mb-2 text-black">
								<strong>Frame:</strong> {selectedImage.frame}
							</p>
							<p className="mb-2 text-black">
								<strong>VideoID:</strong> {selectedImage.VideosId}
							</p>
							<p className="mb-2 text-black">
								<strong>Time(ms):</strong> {selectedImage.time}
							</p>
							<p className="mb-2 text-black">
								<strong>Fps:</strong> {selectedImage.fps}
							</p>
						</div>
						<div className="flex justify-between items-center mb-4">
							
							<div className="flex gap-4">
								{inputMode === "kis" ? ( 
									<>
										<input
											type="text"
											defaultValue={selectedImage.VideosId}
											className="border-2 border-gray-300 bg-white rounded-lg text-sm focus:outline-none"
											placeholder="Videos_ID"
										/>
										<input
											type="number"
											defaultValue={selectedImage.time}
											className="border-2 border-gray-300 bg-white rounded-lg text-sm focus:outline-none"
											placeholder="Start Time"
										/>
										<input
											type="number"
											defaultValue={selectedImage.time} 
											className="border-2 border-gray-300 bg-white h-10 rounded-lg text-sm focus:outline-none"
											placeholder="End Time"
										/>
									</>
								) : (
									<>
										<input
											type="number"
											defaultValue={0} 
											className="border-2 border-gray-300 bg-white rounded-lg text-sm focus:outline-none"
											placeholder="Number"
										/>
										<input
											type="text"
											defaultValue={selectedImage.VideosId}
											className="border-2 border-gray-300 bg-white rounded-lg text-sm focus:outline-none"
											placeholder="Videos_ID"
										/>
										<input
											type="number"
											defaultValue={selectedImage.time} 
											className="border-2 border-gray-300 bg-white h-10 rounded-lg text-sm focus:outline-none"
											placeholder="Time"
										/>
									</>
								)}
							</div>
						</div>
						<div className="flex gap-4">
							<button
								onClick={handleKis}
								className="bg-blue-600 text-white w-20 px-2 py-2 rounded hover:bg-black">
								Kis
							</button>
							<button
								onClick={handleQA}
								className="bg-blue-600 text-white w-20 px-2 py-2 rounded hover:bg-black">
								QA
							</button>
							<button
								onClick={handleSubmit}
								className="bg-green-500 text-white w-20 px-2 py-2 rounded hover:bg-green-700">
								Submit
							</button>
						</div>
						
						<p className="mb-2 text-black">
							<strong>OCR Text:</strong> {selectedImage.ocr_text}
						</p>
						
						<button
							onClick={handleSearchSimilar}
							className="bg-blue-500 text-white px-2 py-2 rounded hover:bg-blue-600">
							Search Similar
						</button>
						<button
							onClick={() => setShowVideo(!showVideo)} 
							className="bg-green-500 text-white px-2 py-2 rounded hover:bg-green-600 ml-2">
							{showVideo ? "Frame" : "Video"}
						</button>
						<input
							type="text"
							value={time}
							onChange={(e) => setTime(e.target.value)} 
							placeholder="Enter frame"
							className="bg-white-500 text-black px-2 py-2 rounded"
						/>
						<button onClick={handleSeek} className="bg-amber-500 text-white px-2 py-2 rounded hover:bg-amber-600 ml-2">
							Move
						</button>

						{/* Display surrounding images */}
						<div className="mt-2 grid grid-cols-3 gap-1 overflow-y-auto max-h-44">
							{surroundingImages.map((img, index) => (
								<div key={index} onClick={() => setSelectedImage({ ...selectedImage, file_path: img })}> {/* Update selected image on click */}
									<img
										src={`${API_BASE_URL}/images/${img}`}
										alt={`Surrounding ${index + 1}`}
										className="object-cover rounded cursor-pointer"
									/>
								</div>
							))}
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export default Search;
					