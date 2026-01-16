# DHI-ClamAV Security API Server
# REST API interface for malware scanning and security services

import asyncio
import json
import logging
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, Optional
import mimetypes

from aiohttp import web, ClientSession, hdrs
from aiohttp.web_middlewares import cors_handler
from aiohttp_cors import setup as cors_setup, ResourceOptions
import aiofiles
from aiofiles import tempfile as aio_tempfile
from marshmallow import Schema, fields, ValidationError
import aiohttp_jinja2
import jinja2
from prometheus_client import generate_latest

from dhi_clamav_engine import DHIClamAVEngine, ScanResult, ThreatLevel, FileType

logger = logging.getLogger(__name__)

# Request/Response Schemas
class ScanFileSchema(Schema):
    scan_options = fields.Dict(missing={})
    auto_quarantine = fields.Bool(missing=True)
    notify_intelligence = fields.Bool(missing=True)

class ScanURLSchema(Schema):
    url = fields.Url(required=True)
    scan_options = fields.Dict(missing={})
    auto_quarantine = fields.Bool(missing=True)

class QuarantineActionSchema(Schema):
    action = fields.Str(required=True, validate=lambda x: x in ['restore', 'delete'])
    restore_path = fields.Str(missing=None, allow_none=True)

class BulkScanSchema(Schema):
    files = fields.List(fields.Str(), required=True, validate=lambda x: len(x) <= 100)
    scan_options = fields.Dict(missing={})

class DHIClamAVAPIServer:
    """
    DHI-ClamAV API Server
    Provides REST API endpoints for malware scanning and security services
    """
    
    def __init__(self, clamav_engine: DHIClamAVEngine, config: Dict[str, Any]):
        self.clamav_engine = clamav_engine
        self.config = config
        
        # Create app with middleware
        self.app = web.Application(
            middlewares=[
                self._error_middleware,
                self._auth_middleware,
                self._rate_limit_middleware,
                self._metrics_middleware
            ],
            client_max_size=config.get('max_file_size', 100 * 1024 * 1024)  # 100MB
        )
        
        # Setup templates
        aiohttp_jinja2.setup(
            self.app,
            loader=jinja2.FileSystemLoader('templates')
        )
        
        self._setup_routes()
        self._setup_cors()
        
        # Request tracking
        self.active_scans = {}
        self.max_concurrent_scans = config.get('max_concurrent_scans', 50)
    
    def _setup_routes(self):
        """Setup API routes"""
        
        # Health and metrics
        self.app.router.add_get('/health', self._health_check)
        self.app.router.add_get('/metrics', self._metrics)
        self.app.router.add_get('/status', self._status)
        
        # File scanning endpoints
        self.app.router.add_post('/api/v1/scan/file', self._scan_file)
        self.app.router.add_post('/api/v1/scan/upload', self._scan_upload)
        self.app.router.add_post('/api/v1/scan/url', self._scan_url)
        self.app.router.add_post('/api/v1/scan/bulk', self._bulk_scan)
        self.app.router.add_get('/api/v1/scan/{scan_id}', self._get_scan_result)
        
        # Quarantine management
        self.app.router.add_get('/api/v1/quarantine', self._list_quarantine)
        self.app.router.add_get('/api/v1/quarantine/{quarantine_id}', self._get_quarantine_entry)
        self.app.router.add_post('/api/v1/quarantine/{quarantine_id}/action', self._quarantine_action)
        self.app.router.add_delete('/api/v1/quarantine/{quarantine_id}', self._delete_quarantine)
        
        # System management
        self.app.router.add_post('/api/v1/signatures/update', self._update_signatures)
        self.app.router.add_get('/api/v1/statistics', self._get_statistics)
        self.app.router.add_get('/api/v1/version', self._get_version)
        
        # Real-time scanning WebSocket
        self.app.router.add_get('/ws/scan', self._websocket_scan)
        
        # Admin endpoints
        self.app.router.add_get('/api/v1/admin/config', self._get_config)
        self.app.router.add_post('/api/v1/admin/config', self._update_config)
        self.app.router.add_post('/api/v1/admin/cache/clear', self._clear_cache)
        self.app.router.add_get('/api/v1/admin/logs', self._get_logs)
        
        # Web interface
        self.app.router.add_get('/', self._web_interface)
        self.app.router.add_get('/scan', self._web_scan_interface)
        self.app.router.add_get('/quarantine', self._web_quarantine_interface)
        
        # Static files
        self.app.router.add_static('/static', 'static')
        
        # API documentation
        self.app.router.add_get('/api/docs', self._api_documentation)
    
    def _setup_cors(self):
        """Setup CORS configuration"""
        cors_config = self.config.get('cors', {})
        
        cors = cors_setup(self.app, defaults={
            "*": ResourceOptions(
                allow_credentials=cors_config.get('allow_credentials', True),
                expose_headers="*",
                allow_headers="*",
                allow_methods=cors_config.get('allowed_methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
            )
        })
        
        # Add CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    @web.middleware
    async def _error_middleware(self, request, handler):
        """Global error handling middleware"""
        try:
            return await handler(request)
        except ValidationError as e:
            return web.json_response({
                'error': 'validation_error',
                'message': 'Request validation failed',
                'details': e.messages
            }, status=400)
        except web.HTTPException as e:
            raise
        except Exception as e:
            logger.error(f"Unhandled error in {request.path}: {e}", exc_info=True)
            return web.json_response({
                'error': 'internal_error',
                'message': 'Internal server error',
                'request_id': request.get('request_id', 'unknown')
            }, status=500)
    
    @web.middleware
    async def _auth_middleware(self, request, handler):
        """Authentication middleware"""
        
        # Skip auth for health, metrics, and docs
        if request.path in ['/health', '/metrics', '/status', '/api/docs', '/']:
            return await handler(request)
        
        # Extract API key
        api_key = request.headers.get('X-API-Key', '')
        auth_header = request.headers.get('Authorization', '')
        
        if not api_key and not auth_header.startswith('Bearer '):
            return web.json_response({
                'error': 'authentication_required',
                'message': 'API key or Bearer token required'
            }, status=401)
        
        # Simple API key validation (would integrate with DHI-Vault)
        if api_key and not api_key.startswith('dhi_'):
            return web.json_response({
                'error': 'invalid_api_key',
                'message': 'Invalid API key format'
            }, status=401)
        
        # Add auth info to request
        request['auth_info'] = {
            'api_key': api_key,
            'authenticated': True
        }
        
        return await handler(request)
    
    @web.middleware
    async def _rate_limit_middleware(self, request, handler):
        """Rate limiting middleware"""
        
        # Skip rate limiting for health checks
        if request.path in ['/health', '/metrics']:
            return await handler(request)
        
        # Check concurrent scans limit
        if len(self.active_scans) >= self.max_concurrent_scans:
            return web.json_response({
                'error': 'rate_limit_exceeded',
                'message': f'Maximum concurrent scans ({self.max_concurrent_scans}) exceeded',
                'active_scans': len(self.active_scans)
            }, status=429)
        
        return await handler(request)
    
    @web.middleware
    async def _metrics_middleware(self, request, handler):
        """Metrics collection middleware"""
        import time
        
        start_time = time.time()
        request_id = f"{int(start_time * 1000)}_{id(request)}"
        request['request_id'] = request_id
        
        try:
            response = await handler(request)
            status = response.status
        except web.HTTPException as e:
            status = e.status
            raise
        finally:
            duration = time.time() - start_time
            logger.info(f"Request {request_id}: {request.method} {request.path} - {status} ({duration:.3f}s)")
        
        return response
    
    # API Endpoints
    
    async def _health_check(self, request):
        """Health check endpoint"""
        health_status = await self.clamav_engine.health_check()
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        health_status.update({
            'active_scans': len(self.active_scans),
            'max_concurrent_scans': self.max_concurrent_scans
        })
        
        return web.json_response(health_status, status=status_code)
    
    async def _status(self, request):
        """Detailed status endpoint"""
        statistics = await self.clamav_engine.get_statistics()
        return web.json_response({
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': statistics,
            'active_scans': len(self.active_scans),
            'version': '1.0.0'
        })
    
    async def _metrics(self, request):
        """Prometheus metrics endpoint"""
        metrics = await self.clamav_engine.get_metrics()
        return web.Response(text=metrics, content_type='text/plain')
    
    async def _scan_file(self, request):
        """Scan file by path"""
        schema = ScanFileSchema()
        
        try:
            json_data = await request.json()
            data = schema.load(json_data)
        except Exception as e:
            raise ValidationError({'json': ['Invalid JSON data']})
        
        file_path = json_data.get('file_path')
        if not file_path:
            return web.json_response({
                'error': 'missing_parameter',
                'message': 'file_path parameter required'
            }, status=400)
        
        if not os.path.exists(file_path):
            return web.json_response({
                'error': 'file_not_found',
                'message': f'File not found: {file_path}'
            }, status=404)
        
        # Track scan
        scan_id = f"scan_{int(datetime.utcnow().timestamp())}_{id(request)}"
        self.active_scans[scan_id] = {
            'started_at': datetime.utcnow(),
            'file_path': file_path,
            'status': 'scanning'
        }
        
        try:
            result = await self.clamav_engine.scan_file(file_path, data['scan_options'])
            
            return web.json_response({
                'scan_id': result.scan_id,
                'file_path': result.file_path,
                'file_hash': result.file_hash,
                'file_size': result.file_size,
                'file_type': result.file_type,
                'scan_result': result.result.value,
                'threat_name': result.threat_name,
                'threat_level': result.threat_level.value,
                'scan_duration': result.scan_duration,
                'engine_version': result.engine_version,
                'signatures_version': result.signatures_version,
                'scan_time': result.scan_time.isoformat(),
                'additional_info': result.additional_info
            })
            
        finally:
            self.active_scans.pop(scan_id, None)
    
    async def _scan_upload(self, request):
        """Scan uploaded file"""
        reader = await request.multipart()
        
        file_field = await reader.next()
        if not file_field or file_field.name != 'file':
            return web.json_response({
                'error': 'missing_file',
                'message': 'File field required'
            }, status=400)
        
        filename = file_field.filename or 'uploaded_file'
        
        # Read file data
        file_data = b''
        while True:
            chunk = await file_field.read_chunk()
            if not chunk:
                break
            file_data += chunk
        
        # Track scan
        scan_id = f"upload_{int(datetime.utcnow().timestamp())}_{id(request)}"
        self.active_scans[scan_id] = {
            'started_at': datetime.utcnow(),
            'filename': filename,
            'size': len(file_data),
            'status': 'scanning'
        }
        
        try:
            result = await self.clamav_engine.scan_buffer(file_data, filename)
            
            response_data = {
                'scan_id': result.scan_id,
                'filename': filename,
                'file_hash': result.file_hash,
                'file_size': len(file_data),
                'file_type': result.file_type,
                'scan_result': result.result.value,
                'threat_name': result.threat_name,
                'threat_level': result.threat_level.value,
                'scan_duration': result.scan_duration,
                'engine_version': result.engine_version,
                'signatures_version': result.signatures_version,
                'scan_time': result.scan_time.isoformat()
            }
            
            # Include additional info for infected files
            if result.result in [ScanResult.INFECTED, ScanResult.SUSPICIOUS]:
                response_data['additional_info'] = result.additional_info
            
            return web.json_response(response_data)
            
        finally:
            self.active_scans.pop(scan_id, None)
    
    async def _scan_url(self, request):
        """Scan file from URL"""
        schema = ScanURLSchema()
        
        try:
            json_data = await request.json()
            data = schema.load(json_data)
        except Exception as e:
            raise ValidationError({'json': ['Invalid JSON data']})
        
        # Track scan
        scan_id = f"url_{int(datetime.utcnow().timestamp())}_{id(request)}"
        self.active_scans[scan_id] = {
            'started_at': datetime.utcnow(),
            'url': data['url'],
            'status': 'downloading'
        }
        
        try:
            self.active_scans[scan_id]['status'] = 'scanning'
            result = await self.clamav_engine.scan_url(data['url'])
            
            return web.json_response({
                'scan_id': result.scan_id,
                'url': data['url'],
                'file_hash': result.file_hash,
                'file_size': result.file_size,
                'file_type': result.file_type,
                'scan_result': result.result.value,
                'threat_name': result.threat_name,
                'threat_level': result.threat_level.value,
                'scan_duration': result.scan_duration,
                'scan_time': result.scan_time.isoformat()
            })
            
        except Exception as e:
            return web.json_response({
                'error': 'scan_failed',
                'message': str(e),
                'url': data['url']
            }, status=500)
            
        finally:
            self.active_scans.pop(scan_id, None)
    
    async def _bulk_scan(self, request):
        """Perform bulk file scanning"""
        schema = BulkScanSchema()
        
        try:
            json_data = await request.json()
            data = schema.load(json_data)
        except Exception as e:
            raise ValidationError({'json': ['Invalid JSON data']})
        
        # Track bulk scan
        scan_id = f"bulk_{int(datetime.utcnow().timestamp())}_{id(request)}"
        self.active_scans[scan_id] = {
            'started_at': datetime.utcnow(),
            'file_count': len(data['files']),
            'status': 'scanning'
        }
        
        try:
            results = []
            
            # Scan files concurrently (with limit)
            semaphore = asyncio.Semaphore(10)  # Max 10 concurrent scans
            
            async def scan_single_file(file_path):
                async with semaphore:
                    if os.path.exists(file_path):
                        try:
                            result = await self.clamav_engine.scan_file(file_path, data['scan_options'])
                            return {
                                'file_path': file_path,
                                'scan_id': result.scan_id,
                                'result': result.result.value,
                                'threat_name': result.threat_name,
                                'threat_level': result.threat_level.value,
                                'scan_duration': result.scan_duration
                            }
                        except Exception as e:
                            return {
                                'file_path': file_path,
                                'error': str(e),
                                'result': 'error'
                            }
                    else:
                        return {
                            'file_path': file_path,
                            'error': 'File not found',
                            'result': 'error'
                        }
            
            scan_tasks = [scan_single_file(file_path) for file_path in data['files']]
            results = await asyncio.gather(*scan_tasks, return_exceptions=True)
            
            # Process results
            summary = {
                'total_files': len(data['files']),
                'clean': sum(1 for r in results if isinstance(r, dict) and r.get('result') == 'clean'),
                'infected': sum(1 for r in results if isinstance(r, dict) and r.get('result') == 'infected'),
                'suspicious': sum(1 for r in results if isinstance(r, dict) and r.get('result') == 'suspicious'),
                'errors': sum(1 for r in results if isinstance(r, dict) and r.get('result') == 'error')
            }
            
            return web.json_response({
                'bulk_scan_id': scan_id,
                'summary': summary,
                'results': [r for r in results if isinstance(r, dict)],
                'scan_time': datetime.utcnow().isoformat()
            })
            
        finally:
            self.active_scans.pop(scan_id, None)
    
    async def _update_signatures(self, request):
        """Update virus signatures"""
        success = await self.clamav_engine.update_signatures()
        
        if success:
            return web.json_response({
                'message': 'Signatures updated successfully',
                'updated_at': datetime.utcnow().isoformat()
            })
        else:
            return web.json_response({
                'error': 'update_failed',
                'message': 'Failed to update signatures'
            }, status=500)
    
    async def _get_statistics(self, request):
        """Get scanning statistics"""
        stats = await self.clamav_engine.get_statistics()
        return web.json_response(stats)
    
    async def _websocket_scan(self, request):
        """WebSocket endpoint for real-time scanning"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        try:
            await ws.send_str(json.dumps({
                'type': 'connection',
                'message': 'Connected to DHI-ClamAV scanning service',
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            async for msg in ws:
                if msg.type == web.MsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        
                        if data.get('action') == 'scan_file':
                            file_path = data.get('file_path')
                            if file_path and os.path.exists(file_path):
                                result = await self.clamav_engine.scan_file(file_path)
                                
                                await ws.send_str(json.dumps({
                                    'type': 'scan_result',
                                    'scan_id': result.scan_id,
                                    'file_path': result.file_path,
                                    'result': result.result.value,
                                    'threat_name': result.threat_name,
                                    'scan_duration': result.scan_duration
                                }))
                            else:
                                await ws.send_str(json.dumps({
                                    'type': 'error',
                                    'message': 'File not found'
                                }))
                        
                        elif data.get('action') == 'get_status':
                            stats = await self.clamav_engine.get_statistics()
                            await ws.send_str(json.dumps({
                                'type': 'status',
                                'statistics': stats,
                                'active_scans': len(self.active_scans)
                            }))
                            
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({
                            'type': 'error',
                            'message': 'Invalid JSON'
                        }))
                elif msg.type == web.MsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        
        return ws
    
    # Web Interface Endpoints
    
    @aiohttp_jinja2.template('index.html')
    async def _web_interface(self, request):
        """Main web interface"""
        stats = await self.clamav_engine.get_statistics()
        return {
            'title': 'DHI-ClamAV Security Scanner',
            'statistics': stats,
            'active_scans': len(self.active_scans)
        }
    
    @aiohttp_jinja2.template('scan.html')
    async def _web_scan_interface(self, request):
        """File scanning web interface"""
        return {'title': 'File Scanner'}
    
    async def _api_documentation(self, request):
        """API documentation endpoint"""
        docs = {
            'title': 'DHI-ClamAV API Documentation',
            'version': '1.0.0',
            'description': 'Distributed HashiCorp Intelligence - ClamAV Security API',
            'base_url': f"http://{request.host}",
            'endpoints': {
                'scan_file': {
                    'method': 'POST',
                    'path': '/api/v1/scan/file',
                    'description': 'Scan file by path',
                    'auth_required': True,
                    'body': {
                        'file_path': 'string (required)',
                        'scan_options': 'object (optional)',
                        'auto_quarantine': 'boolean (optional, default: true)'
                    }
                },
                'scan_upload': {
                    'method': 'POST',
                    'path': '/api/v1/scan/upload',
                    'description': 'Scan uploaded file',
                    'auth_required': True,
                    'content_type': 'multipart/form-data',
                    'body': {
                        'file': 'file (required)'
                    }
                },
                'scan_url': {
                    'method': 'POST',
                    'path': '/api/v1/scan/url',
                    'description': 'Download and scan file from URL',
                    'auth_required': True,
                    'body': {
                        'url': 'string (required)',
                        'scan_options': 'object (optional)'
                    }
                },
                'bulk_scan': {
                    'method': 'POST',
                    'path': '/api/v1/scan/bulk',
                    'description': 'Scan multiple files',
                    'auth_required': True,
                    'body': {
                        'files': 'array of strings (required, max 100)',
                        'scan_options': 'object (optional)'
                    }
                }
            }
        }
        
        return web.json_response(docs)

async def create_app(config: Dict[str, Any]) -> web.Application:
    """Create and initialize the web application"""
    
    # Initialize ClamAV engine
    clamav_engine = DHIClamAVEngine(config)
    await clamav_engine.initialize()
    
    # Create API server
    api_server = DHIClamAVAPIServer(clamav_engine, config)
    
    return api_server.app

async def main():
    """Main server entry point"""
    config = {
        'clamd': {
            'host': 'localhost',
            'port': 3310
        },
        'redis': {
            'url': 'redis://redis.guardianshield.svc.cluster.local:6379',
            'database': 3
        },
        'server': {
            'host': '0.0.0.0',
            'port': 8080
        },
        'cors': {
            'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_credentials': True
        },
        'max_file_size': 100 * 1024 * 1024,  # 100MB
        'max_concurrent_scans': 50,
        'quarantine_dir': '/app/quarantine',
        'temp_dir': '/app/temp',
        'yara_rules_dir': '/app/yara_rules'
    }
    
    app = await create_app(config)
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(
        runner,
        host=config['server']['host'],
        port=config['server']['port']
    )
    
    await site.start()
    
    logger.info(f"DHI-ClamAV API server started on {config['server']['host']}:{config['server']['port']}")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())