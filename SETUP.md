# Clinical Trial Assistant - Complete Setup Guide

## 🎯 Overview

This guide will help you set up both the backend (FastAPI) and frontend (Next.js) for the Clinical Trial Assistant.

## 📋 Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn
- MongoDB (optional, for session storage)

## 🔧 Backend Setup

### 1. Navigate to Backend Directory
```bash
cd agents_server
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create `.env` file in `agents_server/`:
```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# MongoDB (optional)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=clinical_agents

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=1
USE_PROXY=1
```

### 5. Start Backend Server
```bash
python app.py
```

Backend should now be running at `http://localhost:8000`

Check API documentation at: `http://localhost:8000/docs`

## 🎨 Frontend Setup

### 1. Navigate to Frontend Directory
```bash
cd client
```

### 2. Install Dependencies
```bash
npm install
```

This will install:
- Next.js 16
- React 19
- Tailwind CSS 4
- Heroicons
- React Markdown
- And more...

### 3. Configure Environment
The `.env.local` file is already created with:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If your backend runs on a different port, update this value.

### 4. Start Development Server
```bash
npm run dev
```

Frontend should now be running at `http://localhost:3000`

## 🚀 Quick Start (Both Servers)

Run both backend and frontend simultaneously:

### Terminal 1 - Backend
```bash
cd agents_server
source venv/bin/activate
python app.py
```

### Terminal 2 - Frontend
```bash
cd client
npm run dev
```

Then open `http://localhost:3000` in your browser.

## 🧪 Testing the Application

### 1. Health Check
```bash
# Test backend health
curl http://localhost:8000/health
```

### 2. Test Chat API
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are clinical trials?", "session_id": "test-123"}'
```

### 3. Access Frontend
Navigate to `http://localhost:3000` and:
1. You should see the welcome screen
2. Type a message like "What are enrollment criteria for diabetes trials?"
3. Watch the agents process your query
4. Review the response with agent badges

## 📁 Project Structure

```
ClinicalAgent/
├── agents_server/          # Backend (FastAPI)
│   ├── agents/             # AI Agents
│   │   ├── enrollment_agent.py
│   │   ├── efficacy_agent.py
│   │   ├── safety_agent.py
│   │   └── ...
│   ├── storage/            # Database integration
│   ├── datasets/           # Clinical trial data
│   ├── app.py              # FastAPI application
│   ├── chatbot.py          # Chatbot logic
│   └── requirements.txt    # Python dependencies
│
└── client/                 # Frontend (Next.js)
    ├── app/                # Next.js app router
    │   ├── chat/           # Chat page
    │   ├── layout.js       # Root layout
    │   └── page.js         # Home (redirects)
    ├── components/         # React components
    │   └── chat/           # Chat UI components
    ├── hooks/              # Custom React hooks
    ├── services/           # API services
    ├── utils/              # Utility functions
    └── package.json        # Node dependencies
```

## 🎯 Key Features

### Backend Features
- **Dynamic Agent Orchestration**: Automatically selects relevant agents
- **Multi-Agent System**: Enrollment, Efficacy, Safety, Reasoning agents
- **Session Management**: Track conversations
- **MongoDB Integration**: Persistent storage
- **FAISS Search**: Fast clinical trial lookup

### Frontend Features
- **Modern Chat UI**: ChatGPT-like interface
- **Session Management**: Create, switch, delete conversations
- **Dark Mode**: Full dark mode support
- **Responsive Design**: Mobile, tablet, desktop
- **Agent Visualization**: See which agents are working
- **Markdown Support**: Rich text formatting
- **Real-time Updates**: Live typing indicators

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/chat` | POST | Send message to agents |
| `/history/{session_id}` | GET | Get session history |
| `/replay/{session_id}` | GET | Replay session |

## 🛠️ Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Change port in .env
PORT=8001
```

**Missing dependencies:**
```bash
pip install --upgrade -r requirements.txt
```

**MongoDB connection error:**
```bash
# Start MongoDB or disable in code
# Set USE_PROXY=0 to disable MongoDB
```

### Frontend Issues

**Port already in use:**
```bash
PORT=3001 npm run dev
```

**API connection error:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Update .env.local if needed
NEXT_PUBLIC_API_URL=http://localhost:8001
```

**Dependencies installation error:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 🔐 Security Configuration

### Backend CORS
Already configured in `app.py` for local development:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variables
- Never commit `.env` or `.env.local` files
- Keep API keys secret
- Use environment-specific configurations

## 📊 Development Workflow

### 1. Backend Development
```bash
cd agents_server
# Edit agents or API
# Backend auto-reloads (RELOAD=1)
```

### 2. Frontend Development
```bash
cd client
# Edit components
# Hot reload is automatic
```

### 3. Testing
```bash
# Backend tests
cd agents_server
pytest

# Frontend (if configured)
cd client
npm test
```

## 🚀 Production Deployment

### Backend
```bash
# Build Docker image
docker build -t clinical-agents-backend .

# Or use gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
```bash
# Build for production
npm run build

# Start production server
npm start

# Or deploy to Vercel
vercel deploy
```

## 📈 Performance Tips

### Backend
- Use Redis for caching
- Enable connection pooling for MongoDB
- Use async/await throughout
- Optimize FAISS indices

### Frontend
- Enable Next.js image optimization
- Use lazy loading for components
- Implement virtual scrolling for long chats
- Cache API responses

## 🎓 Learning Resources

### Backend
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)

### Frontend
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [React Hooks](https://react.dev/reference/react)

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## 📞 Support

For issues:
1. Check troubleshooting section
2. Review API documentation at `/docs`
3. Check browser console for frontend errors
4. Review backend logs

## 🎉 Next Steps

After setup:
1. ✅ Test basic chat functionality
2. ✅ Try different agent queries
3. ✅ Create multiple sessions
4. ✅ Test dark mode
5. ✅ Try on mobile device
6. 🔧 Customize for your needs
7. 🚀 Deploy to production

---

Happy coding! 🎊
