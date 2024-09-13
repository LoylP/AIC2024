import React, { useState, useRef, useEffect } from "react";
import { Spin, Collapse, Select, Input, Button, message, Checkbox } from "antd";
import "./Search.css";

const { Panel } = Collapse;
const { Option } = Select;

const Search = () => {
	const [inputType, setInputType] = useState("text");
	const [searchValue, setSearchValue] = useState("");
	const [results, setResults] = useState([]);
	const [currentPage, setCurrentPage] = useState(1);
	const [ocrDescription, setOcrDescription] = useState("");
	const [selectedFile, setSelectedFile] = useState(null);
	const [selectedImage, setSelectedImage] = useState(null);
	const [showModal, setShowModal] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [objectFilters, setObjectFilters] = useState([{ class: "", value: "" }]);
	const [classes, setClasses] = useState([]); // New state for class options
	const modalRef = useRef(null);
	const [useExpandedPrompt, setUseExpandedPrompt] = useState(false);

	const itemsPerPage = 20;

	const indexOfLastItem = currentPage * itemsPerPage;
	const indexOfFirstItem = indexOfLastItem - itemsPerPage;
	const currentItems = Array.isArray(results) ? results.slice(indexOfFirstItem, indexOfLastItem) : [];

	useEffect(() => {
		// Fetch class options from unique_classes.json
		const fetchClasses = async () => {
			try {
				const response = await fetch("http://localhost:8000/api/get-all-objects/"); // Update with the correct path
				const data = await response.json();
				setClasses(data);
			} catch (error) {
				console.error("Error fetching class options:", error);
			}
		};

		fetchClasses();
	}, []);
	const handleInputChange = (e) => {
		setSearchValue(e.target.value);
	};

	const handleButtonSearch = async () => {
		setIsLoading(true);
		try {
			let response;
			// Construct the obj_filters parameter
			const objFiltersString = objectFilters
				.filter((filter) => filter.class && filter.value)
				.map((filter) => `${filter.class}=${filter.value}`)
				.join(",");

			if (inputType === "text") {
				const url = new URL("http://127.0.0.1:8000/api/milvus/search");
				if (searchValue) {
					url.searchParams.append("search_query", searchValue);
				}
				if (ocrDescription) {
					url.searchParams.append("ocr_filter", ocrDescription);
				}
				if (objFiltersString) {
					url.searchParams.append("obj_filters", objFiltersString);
				}
				url.searchParams.append("use_expanded_prompt", useExpandedPrompt);

				// Perform search even if only OCR filter is provided
				if (searchValue || ocrDescription || objFiltersString) {
					response = await fetch(url);
				} else {
					throw new Error("Please provide at least one search criteria");
				}
			} else if (inputType === "file" && selectedFile) {
				const formData = new FormData();
				formData.append("image", selectedFile);

				const url = new URL("http://127.0.0.1:8000/api/milvus/search_by_image");
				if (ocrDescription) {
					url.searchParams.append("ocr_filter", ocrDescription);
				}
				url.searchParams.append("results", "100");
				if (objFiltersString) {
					url.searchParams.append("obj_filters", objFiltersString);
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
				if (data.expanded_prompt) {
					console.log("Expanded prompt:", data.expanded_prompt);
				}
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

	const handleImageClick = (image) => {
		setSelectedImage(image);
		setShowModal(true);
	};

	const handleCloseModal = () => {
		setShowModal(false);
		setSelectedImage(null);
	};

	const handleSearchSimilar = async () => {
		if (selectedImage) {
			setIsLoading(true);
			try {
				const imageUrl = `http://127.0.0.1:8000/images/${selectedImage.file_path}`;
				
				// Construct the obj_filters parameter
				const objFiltersString = objectFilters
					.filter((filter) => filter.class && filter.value)
					.map((filter) => `${filter.class}=${filter.value}`)
					.join(",");

				const url = new URL("http://127.0.0.1:8000/api/milvus/search_by_image");
				url.searchParams.append("image_url", imageUrl);
				if (ocrDescription) {
					url.searchParams.append("ocr_filter", ocrDescription);
				}
				url.searchParams.append("results", "100");
				if (objFiltersString) {
					url.searchParams.append("obj_filters", objFiltersString);
				}

				const searchResponse = await fetch(url, {
					method: "POST",
				});

				if (!searchResponse.ok) {
					throw new Error(`HTTP error! status: ${searchResponse.status}`);
				}

				const data = await searchResponse.json();
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
		setObjectFilters([{ class: "", value: "" }]);
	};

	const addObjectFilter = () => {
		setObjectFilters([...objectFilters, { class: "", value: "" }]);
	};

	const removeObjectFilter = (index) => {
		setObjectFilters(objectFilters.filter((_, i) => i !== index));
	};

	const handleObjectFilterChange = (index, field, value) => {
		const newFilters = [...objectFilters];
		newFilters[index][field] = value;
		setObjectFilters(newFilters);
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
			const response = await fetch("http://127.0.0.1:8000/api/export-to-csv", {
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
						<Checkbox
							checked={useExpandedPrompt}
							onChange={(e) => setUseExpandedPrompt(e.target.checked)}
							className="mb-4 text-black"
						>
							Use Expanded Prompt
						</Checkbox>
						<button
							onClick={handleButtonSearch}
							disabled={inputType === "text" ? (!searchValue && !ocrDescription && objectFilters.every(f => !f.class && !f.value)) : !selectedFile}
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
							<Panel header="Object Filter" key="2" style={{ fontSize: 20, fontWeight: 500 }}>
								{objectFilters.map((filter, index) => (
									<div key={index} className="mb-4 flex items-center">
										<Select
											className="mr-2 w-full max-w-xs"
											placeholder="Select object class"
											style={{ width: 1000 }}
											showSearch
											value={filter.class}
											onChange={(value) => handleObjectFilterChange(index, "class", value)}>
											{classes.map((className, idx) => (
												<Option key={idx} value={className}>
													{className}
												</Option>
											))}
										</Select>
										<Input
											className="mr-2"
											placeholder="Filter value"
											value={filter.value}
											onChange={(e) => handleObjectFilterChange(index, "value", e.target.value)}
										/>
										<Button onClick={() => removeObjectFilter(index)} type="danger">
											Remove
										</Button>
									</div>
								))}
								<Button onClick={addObjectFilter} type="dashed" style={{ width: "100%" }}>
									Add Object Filter
								</Button>
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
													src={`http://127.0.0.1:8000/images/${image.file_path}`}
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
				<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
					<div ref={modalRef} className="bg-white p-6 rounded-lg max-w-3xl w-full">
						<div className="flex justify-between items-center mb-4">
							<h2 className="text-2xl font-bold text-black">{selectedImage.file}</h2>
							<button onClick={handleCloseModal} className="text-2xl text-black">
								&times;
							</button>
						</div>
						<img
							src={`http://127.0.0.1:8000/images/${selectedImage.file_path}`}
							alt={selectedImage.file_path}
							className="w-full mb-4 rounded"
						/>
						<p className="mb-2 text-black">
							<strong>Frame:</strong> {selectedImage.frame}
						</p>
						<p className="mb-2 text-black">
							<strong>File:</strong> {selectedImage.file_path}
						</p>
						<p className="mb-2 text-black">
							<strong>OCR Text:</strong> {selectedImage.ocr_text}
						</p>
						<button
							onClick={handleSearchSimilar}
							className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
							Search Similar Images
						</button>
					</div>
				</div>
			)}
		</div>
	);
};

export default Search;
