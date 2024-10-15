import React, { useState, useRef, useEffect } from "react";
import { Spin, Collapse, Button, message } from "antd";
import "./Search.css";


const API_BASE_URL = "http://10.102.196.135:8080"

const { Panel } = Collapse;

const SearchExtra = () => {
	const [inputType, setInputType] = useState("text");
	const [searchValue, setSearchValue] = useState("");
	const [results, setResults] = useState([]);
	const [currentPage, setCurrentPage] = useState(1);
	const [ocrDescription, setOcrDescription] = useState("");
	const [selectedFile, setSelectedFile] = useState(null);
	const [selectedImage, setSelectedImage] = useState(null);
	const [showModal, setShowModal] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const modalRef = useRef(null);
	const [useExpandedPrompt, setUseExpandedPrompt] = useState(false);
	const [surroundingImages, setSurroundingImages] = useState([]); // New state for surrounding images

	const itemsPerPage = 25;

	const indexOfLastItem = currentPage * itemsPerPage;
	const indexOfFirstItem = indexOfLastItem - itemsPerPage;
	const currentItems = Array.isArray(results) ? results.slice(indexOfFirstItem, indexOfLastItem) : [];


	const handleInputChange = (e) => {
		setSearchValue(e.target.value);
	};

	const handleButtonSearch = async () => {
		setIsLoading(true);
		try {
			let response;

			if (inputType === "text") {
				const url = new URL(`${API_BASE_URL}/api/search`);
				if (searchValue) {
					url.searchParams.append("search_query", searchValue); // Updated parameter name
				}
				if (ocrDescription) {
					url.searchParams.append("ocr_filter", ocrDescription);
				}

				if (searchValue || ocrDescription) { 
					response = await fetch(url);
				} else {
					throw new Error("Please provide at least one search criteria");
				}
			} else if (inputType === "file" && selectedFile) {
				const formData = new FormData();
				formData.append("file", selectedFile); 
				const url = new URL(`${API_BASE_URL}/api/search/image`); 
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
			if (data && Array.isArray(data)) { // Adjusted to match the new response structure
				setResults(data);
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

		// Call the API to fetch surrounding images
		await fetchSurroundingImages(image.path); // Pass the file path of the selected image
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


	const handleReset = () => {
		setInputType("text");
		setSearchValue("");
		setResults([]);
		setCurrentPage(1);
		setOcrDescription("");
		setSelectedFile(null);
		setSelectedImage(null);
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
			const response = await fetch(`${API_BASE_URL}/api/export-to-csv`, { // Updated endpoint
				method: "POST", // Changed method to POST
				headers: {
					"Content-Type": "application/json", // Set content type to JSON
				},
				body: JSON.stringify(results), // Send the results as JSON
			});

			if (response.ok) {
				const blob = await response.blob();
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement("a");
				a.style.display = "none";
				a.href = url;
				a.download = "query.csv"; // Updated filename
				document.body.appendChild(a);
				a.click();
				window.URL.revokeObjectURL(url);
				message.success("CSV file exported successfully");
			} else {
				throw new Error("Failed to export CSV");
			}
		} catch (error) {
			console.error("Error exporting CSV:", error);
			message.error("Failed to export CSV");
		}
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
						<div className="flex items-center mb-4"> 
							<input
								type="checkbox"
								checked={useExpandedPrompt}
								onChange={(e) => setUseExpandedPrompt(e.target.checked)}
								className="mr-2"
							/>
							<label>Use Expanded Prompt</label>
						</div>
						<button
							onClick={handleButtonSearch}
							disabled={inputType === "text" ? (!searchValue && !ocrDescription) : !selectedFile}
							className="text-search-btn">
							Search
						</button>
						<Collapse defaultActiveKey={["1", "2"]} style={{ padding: 10, marginTop: 30 }}>
							<Panel header="OCR Filter" key="1" style={{ fontSize: 20, fontWeight: 500 }}>
								<textarea
									placeholder="Enter OCR description"
									value={ocrDescription}
									onChange={(e) => setOcrDescription(e.target.value)}
									className="mb-4 p-2 border rounded resize-none text-black"
									id="ocr-textarea"
								/>
							</Panel>
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
													src={`${API_BASE_URL}/images/${image.path}`}
													alt={image.path}
												/>
												<div className="absolute inset-0 flex flex-col justify-end p-2">
													<div className="bg-black bg-opacity-40 p-1 rounded">
														<p className="text-white text-sm truncate">
															{image.frame} {image.videos_ID}
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
					<div ref={modalRef} className="bg-white p-6 rounded-lg max-w-2xl w-full">
						<div className="flex justify-between items-center mb-4">
							<h2 className="text-2xl font-bold text-black">{selectedImage.path}</h2>
						</div>
						<img
							src={`${API_BASE_URL}/images/${selectedImage.path}`}
								alt={selectedImage.path}
								className="w-full mb-4 rounded"
							/>
						<div className="flex gap-4">
							<p className="mb-2 text-black">
								<strong>Frame:</strong> {selectedImage.frame}
							</p>
							<p className="mb-2 text-black">
									<strong>Videos ID:</strong> {selectedImage.videos_ID}
								</p>
						</div>
						
						<p className="mb-2 text-black">
							<strong>OCR Text:</strong> {selectedImage.ocr_text}
						</p>

						{/* Display surrounding images */}
						<div className="mt-2 grid grid-cols-3 gap-1 overflow-y-auto max-h-44">
							{surroundingImages.map((img, index) => (
								<div key={index} onClick={() => setSelectedImage({ ...selectedImage, path: img })}> {/* Update selected image on click */}
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

export default SearchExtra;
					