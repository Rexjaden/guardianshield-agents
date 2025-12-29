const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

/**
 * GuardianShield Frontend Server
 * Serves the token sale frontend with Web3 integration
 */
class FrontendServer {
    constructor(options = {}) {
        this.port = options.port || 3000;
        this.host = options.host || 'localhost';
        this.frontendDir = path.join(__dirname, '..', 'frontend');
        this.app = express();
        
        this.setupMiddleware();
        this.setupRoutes();
        this.setupAPI();
    }
    
    setupMiddleware() {
        // Enable CORS for Web3 interactions
        this.app.use(cors({
            origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
            credentials: true
        }));
        
        // Parse JSON bodies
        this.app.use(express.json());
        
        // Serve static files
        this.app.use('/js', express.static(path.join(this.frontendDir, 'js')));
        this.app.use('/css', express.static(path.join(this.frontendDir, 'css')));
        this.app.use('/images', express.static(path.join(this.frontendDir, 'images')));
        this.app.use('/assets', express.static(path.join(this.frontendDir, 'assets')));
    }
    
    setupRoutes() {
        // Main token sale page
        this.app.get('/', (req, res) => {
            const htmlPath = path.join(this.frontendDir, 'token-sale-frontend.html');
            if (fs.existsSync(htmlPath)) {
                res.sendFile(htmlPath);
            } else {
                res.status(404).send('Frontend not found. Please run deployment first.');
            }
        });
        
        // Alternative routes
        this.app.get('/token-sale', (req, res) => {
            res.redirect('/');
        });
        
        this.app.get('/sale', (req, res) => {
            res.redirect('/');
        });
        
        // Admin dashboard (if exists)
        this.app.get('/admin', (req, res) => {
            const adminPath = path.join(this.frontendDir, 'admin-dashboard.html');
            if (fs.existsSync(adminPath)) {
                res.sendFile(adminPath);
            } else {
                res.redirect('/');
            }
        });
        
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                timestamp: new Date().toISOString(),
                server: 'GuardianShield Frontend Server'
            });
        });
    }
    
    setupAPI() {
        // API routes for contract information
        this.app.get('/api/config', (req, res) => {
            try {
                const configPath = path.join(this.frontendDir, 'js', 'config.js');
                if (fs.existsSync(configPath)) {
                    // Read and parse the config file
                    const configContent = fs.readFileSync(configPath, 'utf8');
                    
                    // Extract the configuration object (basic parsing)
                    const configMatch = configContent.match(/const GuardianConfig = ({[\\s\\S]*?});/);
                    if (configMatch) {
                        // Return config info (simplified)
                        res.json({
                            available: true,
                            lastUpdated: fs.statSync(configPath).mtime,
                            hasContracts: configContent.includes('0x') && !configContent.includes('0x0000000000000000000000000000000000000000')
                        });
                    } else {
                        res.json({ available: false, error: 'Config format invalid' });
                    }
                } else {
                    res.json({ available: false, error: 'Config not found' });
                }
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });
        
        // API to get deployment information
        this.app.get('/api/deployment', (req, res) => {
            try {
                const deploymentFiles = fs.readdirSync('.')
                    .filter(f => f.startsWith('deployment-') && f.endsWith('.json'))
                    .sort()
                    .reverse();
                
                if (deploymentFiles.length === 0) {
                    return res.json({ available: false, error: 'No deployments found' });
                }
                
                const latestFile = deploymentFiles[0];
                const deployment = JSON.parse(fs.readFileSync(latestFile, 'utf8'));
                
                res.json({
                    available: true,
                    deployment: {
                        network: deployment.network,
                        chainId: deployment.chainId,
                        timestamp: deployment.timestamp,
                        contracts: deployment.contracts,
                        oracleEnabled: deployment.configuration.oracleEnabled
                    }
                });
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });
        
        // API for wallet connection status
        this.app.get('/api/status', (req, res) => {
            res.json({
                server: 'GuardianShield Frontend Server',
                version: '1.0.0',
                features: {
                    tokenSale: true,
                    chainlinkIntegration: true,
                    multiWalletSupport: true,
                    realTimePricing: true
                },
                timestamp: new Date().toISOString()
            });
        });
    }
    
    start() {
        return new Promise((resolve, reject) => {
            this.server = this.app.listen(this.port, this.host, (error) => {
                if (error) {
                    reject(error);
                } else {
                    console.log('🚀 GuardianShield Frontend Server Started');
                    console.log('=' .repeat(50));
                    console.log(`🌐 Server: http://${this.host}:${this.port}`);
                    console.log(`📁 Frontend Directory: ${this.frontendDir}`);
                    console.log(`⏰ Started: ${new Date().toISOString()}`);
                    console.log('');
                    console.log('📋 Available Routes:');
                    console.log('   💰 Token Sale: http://localhost:3000/');
                    console.log('   ⚙️  API Config: http://localhost:3000/api/config');
                    console.log('   📊 API Status: http://localhost:3000/api/status');
                    console.log('   🏥 Health Check: http://localhost:3000/health');
                    console.log('');
                    console.log('✨ Features:');
                    console.log('   🔗 Chainlink Price Integration');
                    console.log('   💳 Multi-Wallet Support (MetaMask, WalletConnect, etc.)');
                    console.log('   📈 Real-time Token Sales');
                    console.log('   🛣️  Comprehensive Roadmap');
                    console.log('   📱 Responsive Design');
                    console.log('');
                    console.log('🎯 Ready for token sales! Connect your wallet to get started.');
                    resolve(this.server);
                }
            });
        });
    }
    
    stop() {
        return new Promise((resolve) => {
            if (this.server) {
                this.server.close(() => {
                    console.log('🛑 Frontend server stopped');
                    resolve();
                });
            } else {
                resolve();
            }
        });
    }
}

// CLI usage
if (require.main === module) {
    const server = new FrontendServer({
        port: process.env.PORT || 3000,
        host: process.env.HOST || 'localhost'
    });
    
    server.start()
        .then(() => {
            // Graceful shutdown
            process.on('SIGTERM', () => {
                console.log('\\nShutting down server...');
                server.stop().then(() => process.exit(0));
            });
            
            process.on('SIGINT', () => {
                console.log('\\nShutting down server...');
                server.stop().then(() => process.exit(0));
            });
        })
        .catch(error => {
            console.error('❌ Failed to start server:', error);
            process.exit(1);
        });
}

module.exports = FrontendServer;