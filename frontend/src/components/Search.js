import React, { useState } from "react";

const Search = () => {
  const [inputType, setInputType] = useState("text");
  const [searchValue, setSearchValue] = useState("");

  const handleInputChange = (e) => {
    setSearchValue(e.target.value);
  };

  const handleButtonSearch = () => {
    console.log(inputType === "file" ? "File selected" : searchValue);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    console.log(file);
  };

  return (
    <div className="flex mx-[10%] items-center justify-center">
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
  );
};

export default Search;
