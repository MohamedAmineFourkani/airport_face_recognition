# Airport Face Recognition System

> Advanced Computer Vision for Automated Passenger Verification at Security Checkpoints

## Overview

An AI-powered face recognition system designed for airport security environments. The system uses OpenCV-based computer vision algorithms to automatically verify passenger identities at security checkpoints, with real-time monitoring capabilities and a web-based dashboard.

## Features

- **Real-time Face Recognition**: Live video processing with bounding boxes and confidence scores
- **Traveler Registration**: Easy enrollment of authorized passengers with photo capture
- **Multi-Checkpoint Support**: Monitor multiple security gates simultaneously
- **Recognition Logging**: Complete audit trail of all recognition events
- **Dashboard Analytics**: Real-time statistics and system health monitoring
- **Web-based Interface**: Modern, responsive UI for security personnel
- **REST API**: Full API for integration with existing airport systems

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend language |
| Flask | Web framework |
| OpenCV | Face detection (Haar Cascade) & recognition (LBP + histograms) |
| SQLite | Database for logs & traveler data |
| Bootstrap 5 | Frontend UI framework |
| JavaScript | Client-side interactivity |

## Installation

### Prerequisites
- Python 3.8+
- Webcam (for live checkpoint monitoring)

### Setup (One Command)

```bash
# 1. Run setup (creates venv inside project folder + installs everything)
python setup.py

# 2. Start the application
python run.py
```

### Manual Setup

```bash
# Create virtual environment inside project folder
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

## Usage

### Start the Server

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Register a Traveler

1. Navigate to **Register** page
2. Fill in traveler details (Name, Passport ID, etc.)
3. Upload a clear frontal face photo
4. Click "Register Traveler"

### Live Monitoring

1. Go to **Checkpoint** page
2. Click **Start** to activate the camera
3. The system will automatically detect and recognize faces
4. Results appear in real-time with authorization status

### Manual Recognition

1. On the **Checkpoint** page, use the "Manual Image Recognition" section
2. Upload any image containing faces
3. Select the checkpoint location
4. Click "Recognize" to get results

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard |
| `/register` | GET/POST | Register new traveler |
| `/checkpoint` | GET | Live monitoring page |
| `/travelers` | GET | List all travelers |
| `/logs` | GET | Recognition logs |
| `/api/recognize` | POST | Recognize faces in image |
| `/api/stats` | GET | System statistics |
| `/api/traveler/<id>` | GET | Get traveler details |
| `/video_feed` | GET | Live MJPEG stream |
| `/api/camera/start` | GET | Start camera |
| `/api/camera/stop` | GET | Stop camera |

### Example API Usage

```python
import requests

# Recognize face from image
files = {'image': open('passenger.jpg', 'rb')}
data = {'checkpoint': 'CP-A1'}
response = requests.post('http://localhost:5000/api/recognize', files=files, data=data)
print(response.json())
```

## Project Structure

```
airport_face_recognition/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── airport_security.db         # SQLite database (auto-created)
├── face_encodings.pkl          # Saved face encodings (auto-created)
├── utils/
│   ├── __init__.py
│   ├── face_recognizer.py      # Face recognition engine
│   └── camera.py               # Camera handler
├── static/
│   ├── css/style.css           # Custom styles
│   ├── js/main.js              # Client-side scripts
│   └── uploads/                # Uploaded images
│       └── authorized_faces/   # Registered traveler photos
└── templates/
    ├── base.html               # Base layout
    ├── index.html              # Dashboard
    ├── register.html           # Traveler registration
    ├── checkpoint.html         # Live monitoring
    ├── travelers.html          # Traveler list
    └── logs.html               # Recognition logs
```

## Screenshots

### Dashboard
Real-time statistics, active checkpoints, and recent recognition logs.

![Dashboard Preview](https://raw.githubusercontent.com/MohamedAmineFourkani/airport_face_recognition/main/screenshots/preview_page.png)

### Checkpoint Monitor
Live video feed with face detection bounding boxes and authorization status.

### Traveler Registration
Form to register authorized travelers with photo upload and validation.

## Performance

- **Recognition Accuracy**: ~80-85% (OpenCV Haar Cascade + LBP histograms). For higher accuracy, consider upgrading to dlib/HOG, FaceNet, or DeepFace.
- **Processing Speed**: ~30 FPS on modern hardware (with frame skipping enabled)
- **Face Detection**: Real-time with Haar cascade
- **Database**: SQLite (easily migratable to PostgreSQL/MySQL)

## Security Considerations

- All face data is stored locally (no cloud upload)
- Encodings are saved as binary pickle files
- SQLite database for audit logs
- HTTPS recommended for production deployment


## License

MIT License - See [LICENSE](LICENSE) for details.

## Author

**Mohamed Amine Fourkani** - AI & Computer Vision Developer

---

> Built with Python, OpenCV, and Deep Learning for next-generation airport security.