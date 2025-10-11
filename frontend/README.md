# GuardianShield Frontend Dashboard

A modern, responsive web-based admin dashboard for monitoring and controlling GuardianShield autonomous agents.

## 🚀 Features

- **Real-time Monitoring**: Live agent status, threat detection, and system metrics
- **Agent Management**: Start, stop, configure, and evolve agents remotely
- **Threat Intelligence**: Visual threat dashboard with severity tracking
- **Analytics & Charts**: Performance metrics and trend analysis
- **WebSocket Integration**: Real-time updates without page refresh
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Dark Theme**: Professional cybersecurity-focused UI

## 📁 Structure

```
frontend/
├── index.html          # Main dashboard page
├── css/
│   ├── dashboard.css   # Main styles and layout
│   └── components.css  # Component-specific styles
├── js/
│   ├── dashboard.js    # Core dashboard functionality
│   ├── agents.js       # Agent management
│   ├── websocket.js    # Real-time WebSocket connection
│   ├── threats.js      # Threat monitoring
│   └── analytics.js    # Charts and analytics
└── assets/
    └── [images/icons]  # Static assets
```

## 🛠️ Technologies

- **Frontend**: HTML5, CSS3 (CSS Grid/Flexbox), Vanilla JavaScript
- **Charts**: Chart.js for data visualization
- **Icons**: Font Awesome
- **Fonts**: Inter (Google Fonts)
- **Real-time**: WebSocket API
- **Backend**: FastAPI with WebSocket support

## 🔧 Setup

1. **Start the API Server**:
   ```bash
   python api_server.py
   ```

2. **Access Dashboard**:
   - Open browser to: http://localhost:8000
   - Dashboard loads automatically

3. **Real-time Features**:
   - WebSocket connection establishes automatically
   - Live updates for agent status, threats, and metrics

## 🎮 Usage

### Navigation
- **Dashboard**: Overview with stats and real-time activity
- **Agents**: Manage individual agents (start/stop/configure)
- **Threats**: Monitor threat detection and analysis
- **Analytics**: Performance charts and trend analysis
- **Logs**: System logs with filtering and search
- **Settings**: Configure system parameters

### Agent Management
- **Start/Stop**: Control agent execution
- **Configure**: Adjust autonomy levels and parameters
- **Evolve**: Trigger manual evolution cycles
- **Monitor**: View real-time performance metrics

### Real-time Features
- Live agent status updates
- Threat detection notifications
- Performance metric streaming
- System log monitoring
- WebSocket connection status

### Emergency Controls
- **Emergency Stop**: Immediately halt all agents
- **System Alerts**: High-priority notifications
- **Connection Monitoring**: WebSocket health status

## 🔌 API Endpoints

The dashboard connects to these API endpoints:

- `GET /` - Serve dashboard
- `GET /api/agents` - List all agents
- `POST /api/agents/{id}/start` - Start agent
- `POST /api/agents/{id}/stop` - Stop agent
- `PUT /api/agents/{id}/config` - Update configuration
- `POST /api/agents/{id}/evolve` - Trigger evolution
- `POST /api/emergency-stop` - Emergency stop all
- `WS /ws/dashboard` - WebSocket for real-time updates

## 📱 Responsive Design

The dashboard is fully responsive:

- **Desktop**: Full sidebar navigation, multi-column layouts
- **Tablet**: Adaptive grid layouts, touch-friendly controls
- **Mobile**: Collapsible sidebar, single-column layouts

## 🎨 Customization

### Theme Colors
Edit CSS variables in `dashboard.css`:
```css
:root {
    --primary-color: #3b82f6;    /* Main brand color */
    --bg-primary: #0f172a;       /* Background */
    --text-primary: #f1f5f9;     /* Text color */
    /* ... more variables */
}
```

### Adding Components
1. Add HTML structure to `index.html`
2. Style in `components.css`
3. Add functionality to appropriate JS file
4. Connect to WebSocket events if needed

## 🔒 Security

- **HTTPS Ready**: Works with SSL certificates
- **Input Validation**: All form inputs validated
- **Error Handling**: Graceful error states
- **Connection Security**: WebSocket over WSS for production

## 🚀 Production Deployment

1. **Environment Setup**:
   ```bash
   # Install dependencies
   pip install fastapi uvicorn websockets
   
   # Set production variables
   export ENVIRONMENT=production
   ```

2. **SSL Configuration**:
   - Update WebSocket URLs to use `wss://`
   - Configure reverse proxy (nginx/Apache)
   - Enable HTTPS for all endpoints

3. **Performance**:
   - Enable gzip compression
   - Minify CSS/JS for production
   - Configure CDN for static assets

## 📊 Monitoring

The dashboard provides comprehensive monitoring:

- **System Health**: CPU, memory, disk usage
- **Agent Performance**: Accuracy, response times, evolution progress
- **Threat Intelligence**: Detection rates, severity distribution
- **Real-time Logs**: Filterable system logs with search

## 🔧 Development

### Adding New Features
1. Create HTML structure in appropriate section
2. Add styles to `components.css`
3. Implement functionality in relevant JS module
4. Add API endpoints to `api_server.py`
5. Test WebSocket integration

### Debugging
- Browser DevTools for frontend debugging
- WebSocket connection status in console
- Network tab for API call monitoring
- Server logs for backend issues

## 🤝 Contributing

When adding new features:
1. Follow existing code structure
2. Maintain responsive design principles
3. Add appropriate error handling
4. Update documentation
5. Test on multiple devices/browsers

## 📄 License

Part of the GuardianShield project - see main LICENSE file.