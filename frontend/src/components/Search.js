import React, { useState, useRef, useEffect } from "react";
import { Spin } from "antd";
import Header from "./Header";
import logo from "../static/logo.png";
import "./Search.css";
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
	const modalRef = useRef(null);

	const itemsPerPage = 20;

	const indexOfLastItem = currentPage * itemsPerPage;
	const indexOfFirstItem = indexOfLastItem - itemsPerPage;
	const currentItems = Array.isArray(results) ? results.slice(indexOfFirstItem, indexOfLastItem) : [];

	const handleInputChange = (e) => {
		setSearchValue(e.target.value);
	};

	const handleButtonSearch = async () => {
		setIsLoading(true); // Start loading
		try {
			let response;
			if (inputType === "text") {
				const url = new URL("http://127.0.0.1:8000/api/search");
				url.searchParams.append("search_query", searchValue);
				url.searchParams.append("ocr_filter", ocrDescription);
				url.searchParams.append("results", "100");

				response = await fetch(url);
			} else if (inputType === "file" && selectedFile) {
				const formData = new FormData();
				formData.append("image", selectedFile);

				const url = new URL("http://127.0.0.1:8000/api/search_by_image");
				url.searchParams.append("ocr_filter", ocrDescription);
				url.searchParams.append("results", "100");

				response = await fetch(url, {
					method: "POST",
					body: formData,
				});
			}
			const data = await response.json();
			setResults(Array.isArray(data) ? data : []);
			setCurrentPage(1);
		} catch (error) {
			console.error("Error during search:", error);
			setResults([]);
		} finally {
			setIsLoading(false); // End loading
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
			setIsLoading(true); // Start loading
			try {
				const url = new URL("http://127.0.0.1:8000/api/search_similar");
				url.searchParams.append("image_path", selectedImage.path);
				if (ocrDescription) {
					url.searchParams.append("ocr_filter", ocrDescription);
				}
				url.searchParams.append("results", "100");

				const response = await fetch(url);
				if (!response.ok) {
					throw new Error("Network response was not ok");
				}
				const data = await response.json();
				setResults(data);
				setCurrentPage(1);
				setShowModal(false);
			} catch (error) {
				console.error("Error during similar image search:", error);
			} finally {
				setIsLoading(false); // End loading
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

	return (
		<div>
			<div className="flex flex-col h-screen">
				<div className="flex flex-1 ">
					{/* Search panel - 1/5 of the screen */}
					<div className="w-1/5 bg-slate-300 p-4 flex flex-col" style={{ backgroundColor: "white" }}>
						<img
							src={logo}
							alt="logo"
							style={{
								maxWidth: 250,
								maxHeight: 250,
								padding: 10,
								justifyContent: "center",
								marginLeft: 30,
							}}
						/>
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
						<button
							onClick={handleButtonSearch}
							disabled={inputType === "text" ? !searchValue : !selectedFile}
							className="text-search-btn">
							Search
						</button>
						<h2 className="text-2xl font-bold text-black mt-4">OCR Filter</h2>
						<textarea
							placeholder="Enter OCR description"
							value={ocrDescription}
							onChange={(e) => setOcrDescription(e.target.value)}
							className="mb-4 p-2 border rounded resize-none text-black"
							id="ocr-textarea"
						/>
					</div>

					{/* Results panel - 4/5 of the screen */}
					<div className="w-4/5 bg-slate-100 p-4">
						{isLoading ? ( // Show loading spinner if loading
							<div className="flex justify-center items-center h-full">
								<Spin size="large" />
							</div>
						) : (
							Array.isArray(results) &&
							results.length > 0 && (
								<div>
									<div className="flex justify-between items-center mb-4">
										<h2 className="text-2xl font-bold text-black">Results: </h2>
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
									<div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
										{currentItems.map((image) => (
											<div
												key={image.id}
												className="cursor-pointer relative"
												onClick={() => handleImageClick(image)}>
												<img
													className="w-full h-40 object-cover rounded shadow-md"
													src={`http://127.0.0.1:8000/images/${image.path}`}
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
							src={`http://127.0.0.1:8000/images/${selectedImage.path}`}
							alt={selectedImage.file}
							className="w-full mb-4 rounded"
						/>
						<p className="mb-2 text-black">
							<strong>Frame:</strong> {selectedImage.frame}
						</p>
						<p className="mb-2 text-black">
							<strong>File:</strong> {selectedImage.file}
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
