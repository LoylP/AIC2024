document.getElementById("searchButton").addEventListener("click", function () {
  const searchTerm = document.getElementById("searchInput").value;
  if (searchTerm.trim() !== "") {
    const apiUrl = `/search?search_query=${searchTerm}`;
    fetch(apiUrl)
      .then((response) => response.json())
      .then((data) => {
        const resultsDiv = document.getElementById("results");
        resultsDiv.innerHTML = "";
        data.forEach((imageUrl) => {
          const img = document.createElement("img");
          img.src = imageUrl; // Sử dụng đường dẫn trả về từ API
          img.alt = imageUrl;
          resultsDiv.appendChild(img);
        });
      });
  }
});
