import React, { useState } from "react";

const Search = () => {
  const [inputType, setInputType] = useState("text");
  const [searchValue, setSearchValue] = useState("");
  const [results, setResults] = useState([]);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = results.slice(indexOfFirstItem, indexOfLastItem);

  const handleInputChange = (e) => {
    setSearchValue(e.target.value);
  };

  const handleButtonSearch = async () => {
    if (inputType === "file") {
      console.log("File selected");
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/search?search_query=${encodeURIComponent(
          searchValue
        )}`,
        {
          method: "GET",
          headers: {
            accept: "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();
      setResults(data);
      setCurrentPage(1);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    console.log(file);
  };

  const totalPages = Math.ceil(results.length / itemsPerPage);

  const handlePageClick = (pageNum) => {
    setCurrentPage(pageNum);
  };

  return (
    <div className="rounded-xl mx-5">
      <div className="mt-[2%] flex items-center justify-center text-black">
        <input
          className={`bg-gray-50 border rounded-l-lg border-gray-300 w-[50%] h-full indent-2 p-2.5 outline-none focus:border-blue-500 focus:ring-2 ${
            inputType === "file" ? "text-sm" : "text-lg"
          }`}
          type={inputType === "file" ? "file" : "search"}
          placeholder={
            inputType === "file" ? "Choose a file..." : "Search Anything..."
          }
          onChange={inputType === "file" ? handleFileChange : handleInputChange}
        />
        <button
          onClick={handleButtonSearch}
          disabled={inputType === "text" ? !searchValue : false}
          className={`bg-blue-800 px-6 py-2.5 text-white focus:ring-2 focus:ring-blue-300 disabled:bg-gray-400 rounded-r-lg ${
            inputType === "file" ? "text-xl" : ""
          }`}
        >
          Search
        </button>

        <select
          className="bg-gray-50 border border-gray-300 text-sm p-2.5 rounded-md ml-[10%]"
          value={inputType}
          onChange={(e) => setInputType(e.target.value)}
        >
          <option value="text">Search Text</option>
          <option value="file">Upload File</option>
        </select>
      </div>

      <div className="rounded-xl bg-slate-600 mx-[1%]">
        {results.length > 0 && (
          <div className="mt-4 mx-5">
            <h2 className="text-lg text-white font-bold">Search Results:</h2>
            <div className="flex items-center justify-end mb-2">
              {/* Page Numbers */}
              <div className="flex space-x-2">
                {[...Array(totalPages)].map((_, index) => {
                  const pageNum = index + 1;
                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageClick(pageNum)}
                      className={`px-3 py-1 rounded ${
                        currentPage === pageNum
                          ? "bg-blue-600 text-white"
                          : "bg-gray-300 text-black"
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {currentItems.map((image) => (
                <div key={image.id} className="relative">
                  <img
                    className="h-full w-full object-cover rounded-lg shadow-md"
                    src={`http://127.0.0.1:8000/images/${image.path}`}
                    alt={image.file}
                  />
                  {/* <div className="absolute inset-0 border-4 border-gray-400 rounded-lg pointer-events-none"></div> */}
                  <div className="absolute bottom-0 left-0  text-white p-2 rounded-b-lg flex">
                    <div className="mx-2 bg-black bg-opacity-40 hover:bg-opacity-100">
                      {image.frame}
                    </div>
                    <div className="bg-black bg-opacity-40 hover:bg-opacity-100">
                      {image.file}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Search;
