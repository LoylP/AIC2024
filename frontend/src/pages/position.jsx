// src/App.js
import React, { useState } from 'react';
import Canvas from '../components/Canvas';
import axios from 'axios';

const Position = () => {
    const [boxes, setBoxes] = useState([]);
    const [filteredImages, setFilteredImages] = useState([]);
    const [error, setError] = useState(null);

    const handleBoxDrawn = async (box) => {
        setBoxes([...boxes, box]);

        // Call the API to filter images based on bounding boxes
        try {
            const response = await axios.get('http://localhost:8000/api/search', {
                params: {
                    search_query: '', // Add search query if needed
                    obj_filters: [
                        `bbox_x=${Math.round(box.x)}`,
                        `bbox_y=${Math.round(box.y)}`,
                        `bbox_width=${Math.round(box.width)}`,
                        `bbox_height=${Math.round(box.height)}`
                    ],
                },
            });
            setFilteredImages(response.data);
            setError(null); // Reset error on successful fetch
        } catch (error) {
            console.error('Error fetching filtered images:', error);
            setError('Error fetching images. Please try again.');
        }
    };

    return (
        <div>
            <h1>Bounding Box Annotation</h1>
            <Canvas width={800} height={600} onBoxDrawn={handleBoxDrawn} />
            <div>
                <h2>Bounding Boxes</h2>
                <ul>
                    {boxes.map((box, index) => (
                        <li key={index}>
                            Box {index + 1}: x={box.x}, y={box.y}, width={box.width}, height={box.height}
                        </li>
                    ))}
                </ul>
            </div>
            <div>
                <h2>Filtered Images</h2>
                {error && <p style={{ color: 'red' }}>{error}</p>}
                <ul>
                    {filteredImages.map((image, index) => (
                        <li key={index}>
                            <img src={`/images/${image.file}`} alt={`Image file ${image.file}`} style={{ maxWidth: '200px' }} />
                            <p>{image.file}</p>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default Position;