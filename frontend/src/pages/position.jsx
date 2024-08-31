import React, { useState } from 'react';
import axios from 'axios';

const ObjectDetection = () => {
    const [image, setImage] = useState(null);
    const [boxes, setBoxes] = useState([]);

    const handleFileChange = (e) => {
        setImage(e.target.files[0]);
    };

    const handleDetect = async () => {
        const formData = new FormData();
        formData.append('file', image);

        const response = await axios.post('/api/detect/', formData);
        setBoxes(response.data.boxes);
    };

    return (
        <div>
            <input type="file" onChange={handleFileChange} />
            <button onClick={handleDetect}>Detect</button>
            <div>
                {/* Render the image and overlay boxes */}
                {boxes.map((box, index) => (
                    <div key={index} className="bounding-box" style={{
                        position: 'absolute',
                        top: box[1][1],
                        left: box[1][0],
                        width: box[1][2] - box[1][0],
                        height: box[1][3] - box[1][1],
                        border: '2px solid red'
                    }}></div>
                ))}
            </div>
        </div>
    );
};

export default ObjectDetection;
