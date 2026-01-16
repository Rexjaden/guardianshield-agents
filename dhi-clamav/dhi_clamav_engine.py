# DHI-ClamAV: Distributed HashiCorp Intelligence - ClamAV Security Engine
# Advanced malware detection and security scanning for GuardianShield

import asyncio
import json
import logging
import hashlib
import tempfile
import shutil
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import aiofiles
import aioredis
import clamd
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import psutil
import magic
import yara
import ssdeep
import pyclamd
from kubernetes import client as k8s_client, config as k8s_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScanResult(Enum):
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"
    SUSPICIOUS = "suspicious"
    QUARANTINED = "quarantined"

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FileType(Enum):
    EXECUTABLE = "executable"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    IMAGE = "image"
    SCRIPT = "script"
    UNKNOWN = "unknown"

@dataclass
class ScanMetadata:
    scan_id: str
    file_path: str
    file_hash: str
    file_size: int
    file_type: str
    scan_time: datetime
    scan_duration: float
    result: ScanResult
    threat_name: Optional[str]
    threat_level: ThreatLevel
    engine_version: str
    signatures_version: str
    additional_info: Dict[str, Any]

@dataclass
class QuarantineEntry:
    quarantine_id: str
    original_path: str
    quarantine_path: str
    file_hash: str
    threat_name: str
    quarantined_at: datetime
    metadata: Dict[str, Any]

class DHIClamAVEngine:
    """
    DHI-ClamAV Security Engine
    Advanced malware detection and file scanning system for GuardianShield
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.clamd_client = None
        self.redis_client = None
        self.k8s_client = None
        
        # Directories
        self.quarantine_dir = Path(config.get('quarantine_dir', '/app/quarantine'))
        self.temp_dir = Path(config.get('temp_dir', '/app/temp'))
        self.yara_rules_dir = Path(config.get('yara_rules_dir', '/app/yara_rules'))
        
        # Create directories
        for directory in [self.quarantine_dir, self.temp_dir, self.yara_rules_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # YARA rules
        self.yara_rules = None
        
        # Metrics
        self.scans_total = Counter(
            'dhi_clamav_scans_total',
            'Total number of scans performed',
            ['result', 'file_type']
        )
        self.scan_duration = Histogram(
            'dhi_clamav_scan_duration_seconds',
            'Time spent scanning files'
        )
        self.threats_detected = Counter(
            'dhi_clamav_threats_detected_total',
            'Total threats detected',
            ['threat_level', 'threat_type']
        )
        self.quarantined_files = Gauge(
            'dhi_clamav_quarantined_files_total',
            'Number of files in quarantine'
        )
        self.signature_age = Gauge(
            'dhi_clamav_signature_age_hours',
            'Age of virus signatures in hours'
        )
        
        # Cache for scan results
        self.scan_cache = {}
        self.cache_ttl = config.get('cache_ttl', 3600)  # 1 hour
        
    async def initialize(self):
        """Initialize ClamAV engine and connections"""
        try:
            await self._init_clamd()
            await self._init_redis()
            await self._init_kubernetes()
            await self._load_yara_rules()
            await self._update_metrics()
            
            logger.info("DHI-ClamAV engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DHI-ClamAV: {e}")
            raise
    
    async def _init_clamd(self):
        """Initialize ClamAV daemon connection"""
        clamd_config = self.config.get('clamd', {})
        
        try:
            # Try socket connection first
            if clamd_config.get('socket'):
                self.clamd_client = clamd.ClamdUnixSocket(clamd_config['socket'])
            else:
                # Fall back to network connection
                host = clamd_config.get('host', 'localhost')
                port = clamd_config.get('port', 3310)
                self.clamd_client = clamd.ClamdNetworkSocket(host, port)
            
            # Test connection
            version = self.clamd_client.version()
            logger.info(f"Connected to ClamAV: {version}")
            
        except Exception as e:
            logger.error(f"Failed to connect to ClamAV daemon: {e}")
            raise
    
    async def _init_redis(self):
        """Initialize Redis connection for caching"""
        redis_config = self.config.get('redis', {})
        
        try:
            self.redis_client = await aioredis.from_url(
                redis_config.get('url', 'redis://redis.guardianshield.svc.cluster.local:6379'),
                encoding='utf-8',
                decode_responses=True,
                db=redis_config.get('database', 3)
            )
            
            await self.redis_client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - Continuing without cache")
            self.redis_client = None
    
    async def _init_kubernetes(self):
        """Initialize Kubernetes client"""
        try:
            k8s_config.load_incluster_config()
            self.k8s_client = k8s_client.ApiClient()
            logger.info("Kubernetes client initialized")
        except:
            logger.warning("Failed to initialize Kubernetes client - running outside cluster")
    
    async def _load_yara_rules(self):
        """Load YARA rules for advanced threat detection"""
        try:
            yara_files = list(self.yara_rules_dir.glob('*.yar')) + list(self.yara_rules_dir.glob('*.yara'))
            
            if yara_files:
                rules_dict = {}
                for rule_file in yara_files:
                    rules_dict[rule_file.stem] = str(rule_file)
                
                self.yara_rules = yara.compile(filepaths=rules_dict)
                logger.info(f"Loaded {len(yara_files)} YARA rule files")
            else:
                logger.warning("No YARA rules found")
                
        except Exception as e:
            logger.error(f"Failed to load YARA rules: {e}")
    
    async def scan_file(
        self,
        file_path: str,
        scan_options: Dict[str, Any] = None
    ) -> ScanMetadata:
        """
        Scan a file for malware and threats
        
        Args:
            file_path: Path to file to scan
            scan_options: Additional scan options
            
        Returns:
            ScanMetadata with scan results
        """
        start_time = time.time()
        scan_id = hashlib.md5(f"{file_path}_{start_time}".encode()).hexdigest()[:16]
        
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return self._create_error_result(scan_id, file_path, "File not found")
            
            # Get file metadata
            file_stats = os.stat(file_path)
            file_hash = await self._calculate_file_hash(file_path)
            file_type = await self._detect_file_type(file_path)
            
            # Check cache first
            if self.redis_client:
                cached_result = await self._get_cached_result(file_hash)
                if cached_result:
                    logger.debug(f"Cache hit for file {file_hash}")
                    return cached_result
            
            # Perform ClamAV scan
            clamav_result = await self._clamav_scan(file_path)
            
            # Perform YARA scan
            yara_result = await self._yara_scan(file_path)
            
            # Perform fuzzy hash analysis
            fuzzy_result = await self._fuzzy_hash_analysis(file_path)
            
            # Combine results
            scan_result = await self._analyze_scan_results(
                clamav_result, yara_result, fuzzy_result
            )
            
            scan_duration = time.time() - start_time
            
            # Create metadata
            metadata = ScanMetadata(
                scan_id=scan_id,
                file_path=file_path,
                file_hash=file_hash,
                file_size=file_stats.st_size,
                file_type=file_type.value,
                scan_time=datetime.utcnow(),
                scan_duration=scan_duration,
                result=scan_result['result'],
                threat_name=scan_result.get('threat_name'),
                threat_level=scan_result['threat_level'],
                engine_version=self.clamd_client.version(),
                signatures_version=await self._get_signatures_version(),
                additional_info={
                    'clamav_result': clamav_result,
                    'yara_matches': yara_result,
                    'fuzzy_hash': fuzzy_result,
                    'file_magic': magic.from_file(file_path)
                }
            )
            
            # Update metrics
            self.scans_total.labels(
                result=metadata.result.value,
                file_type=metadata.file_type
            ).inc()
            self.scan_duration.observe(scan_duration)
            
            if metadata.result == ScanResult.INFECTED:
                self.threats_detected.labels(
                    threat_level=metadata.threat_level.value,
                    threat_type=metadata.threat_name or 'unknown'
                ).inc()
                
                # Auto-quarantine if configured
                if self.config.get('auto_quarantine', True):
                    await self._quarantine_file(file_path, metadata)
            
            # Cache result
            if self.redis_client:
                await self._cache_scan_result(file_hash, metadata)
            
            # Send to threat intelligence
            await self._send_to_threat_intelligence(metadata)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Scan error for {file_path}: {e}")
            scan_duration = time.time() - start_time
            return self._create_error_result(scan_id, file_path, str(e), scan_duration)
    
    async def scan_buffer(self, data: bytes, filename: str = "buffer") -> ScanMetadata:
        """
        Scan data buffer for malware
        
        Args:
            data: Data to scan
            filename: Optional filename for context
            
        Returns:
            ScanMetadata with scan results
        """
        # Write buffer to temporary file
        temp_file = self.temp_dir / f"scan_{int(time.time())}_{filename}"
        
        try:
            async with aiofiles.open(temp_file, 'wb') as f:
                await f.write(data)
            
            result = await self.scan_file(str(temp_file))
            result.file_path = filename  # Update to original filename
            
            return result
            
        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()
    
    async def scan_url(self, url: str) -> ScanMetadata:
        """
        Download and scan file from URL
        
        Args:
            url: URL to download and scan
            
        Returns:
            ScanMetadata with scan results
        """
        import aiohttp
        
        temp_file = self.temp_dir / f"url_scan_{int(time.time())}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download URL: {response.status}")
                    
                    async with aiofiles.open(temp_file, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
            
            result = await self.scan_file(str(temp_file))
            result.file_path = url  # Update to URL
            
            return result
            
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    async def quarantine_file(self, file_path: str, metadata: ScanMetadata) -> QuarantineEntry:
        """
        Quarantine infected file
        
        Args:
            file_path: Path to infected file
            metadata: Scan metadata
            
        Returns:
            QuarantineEntry with quarantine information
        """
        return await self._quarantine_file(file_path, metadata)
    
    async def restore_from_quarantine(self, quarantine_id: str, restore_path: str) -> bool:
        """
        Restore file from quarantine
        
        Args:
            quarantine_id: Quarantine entry ID
            restore_path: Path to restore file to
            
        Returns:
            True if restored successfully
        """
        try:
            # Load quarantine entry
            entry = await self._load_quarantine_entry(quarantine_id)
            if not entry:
                return False
            
            # Copy file back
            shutil.copy2(entry.quarantine_path, restore_path)
            
            # Remove from quarantine
            await self._remove_from_quarantine(quarantine_id)
            
            logger.info(f"Restored file from quarantine: {quarantine_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from quarantine: {e}")
            return False
    
    async def update_signatures(self) -> bool:
        """
        Update virus signatures
        
        Returns:
            True if updated successfully
        """
        try:
            # Use freshclam to update signatures
            import subprocess
            
            result = await asyncio.create_subprocess_exec(
                'freshclam',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                logger.info("Virus signatures updated successfully")
                await self._update_metrics()
                return True
            else:
                logger.error(f"Failed to update signatures: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Signature update failed: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get scanning statistics
        
        Returns:
            Dictionary with statistics
        """
        try:
            # Get quarantine count
            quarantine_files = len(list(self.quarantine_dir.glob('*')))
            
            # Get system resources
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage(str(self.temp_dir.parent))
            
            # Get signature info
            signatures_version = await self._get_signatures_version()
            
            return {
                'engine_status': 'running',
                'signatures_version': signatures_version,
                'quarantine_files': quarantine_files,
                'temp_files': len(list(self.temp_dir.glob('*'))),
                'yara_rules': len(list(self.yara_rules_dir.glob('*.y*'))) if self.yara_rules_dir.exists() else 0,
                'system': {
                    'memory_usage': memory_info.percent,
                    'memory_available': memory_info.available,
                    'disk_usage': disk_info.percent,
                    'disk_free': disk_info.free
                },
                'cache': {
                    'enabled': self.redis_client is not None,
                    'ttl': self.cache_ttl
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {'error': str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Health status dictionary
        """
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Check ClamAV daemon
        try:
            version = self.clamd_client.version()
            health['services']['clamd'] = {
                'status': 'healthy',
                'version': version
            }
        except Exception as e:
            health['services']['clamd'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['status'] = 'degraded'
        
        # Check Redis
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health['services']['redis'] = {'status': 'healthy'}
            except Exception as e:
                health['services']['redis'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        
        # Check disk space
        try:
            disk_usage = psutil.disk_usage(str(self.temp_dir.parent))
            if disk_usage.percent > 90:
                health['services']['disk'] = {
                    'status': 'warning',
                    'usage_percent': disk_usage.percent
                }
                health['status'] = 'degraded'
            else:
                health['services']['disk'] = {
                    'status': 'healthy',
                    'usage_percent': disk_usage.percent
                }
        except Exception as e:
            health['services']['disk'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        return health
    
    async def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        return generate_latest()
    
    # Private helper methods
    
    async def _clamav_scan(self, file_path: str) -> Dict[str, Any]:
        """Perform ClamAV scan"""
        try:
            result = self.clamd_client.scan(file_path)
            
            if result is None:
                return {'status': 'clean', 'threat': None}
            
            for path, (status, threat) in result.items():
                if status == 'FOUND':
                    return {'status': 'infected', 'threat': threat}
                elif status == 'ERROR':
                    return {'status': 'error', 'error': threat}
            
            return {'status': 'clean', 'threat': None}
            
        except Exception as e:
            logger.error(f"ClamAV scan error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _yara_scan(self, file_path: str) -> List[Dict[str, Any]]:
        """Perform YARA scan"""
        if not self.yara_rules:
            return []
        
        try:
            matches = self.yara_rules.match(file_path)
            return [
                {
                    'rule': match.rule,
                    'namespace': match.namespace,
                    'tags': match.tags,
                    'strings': [(s.offset, s.identifier, s.instances) for s in match.strings]
                }
                for match in matches
            ]
        except Exception as e:
            logger.error(f"YARA scan error: {e}")
            return []
    
    async def _fuzzy_hash_analysis(self, file_path: str) -> Dict[str, Any]:
        """Perform fuzzy hash analysis"""
        try:
            fuzzy_hash = ssdeep.hash_from_file(file_path)
            return {
                'fuzzy_hash': fuzzy_hash,
                'suspicious': False  # Would compare against known bad hashes
            }
        except Exception as e:
            logger.debug(f"Fuzzy hash analysis failed: {e}")
            return {}
    
    async def _analyze_scan_results(
        self, 
        clamav_result: Dict[str, Any], 
        yara_result: List[Dict[str, Any]], 
        fuzzy_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze combined scan results"""
        
        # Start with clean result
        result = {
            'result': ScanResult.CLEAN,
            'threat_level': ThreatLevel.LOW,
            'threat_name': None
        }
        
        # Check ClamAV result
        if clamav_result.get('status') == 'infected':
            result.update({
                'result': ScanResult.INFECTED,
                'threat_level': ThreatLevel.HIGH,
                'threat_name': clamav_result.get('threat')
            })
            return result
        
        # Check YARA matches
        if yara_result:
            high_risk_rules = [m for m in yara_result if 'malware' in m.get('tags', [])]
            if high_risk_rules:
                result.update({
                    'result': ScanResult.SUSPICIOUS,
                    'threat_level': ThreatLevel.MEDIUM,
                    'threat_name': f"YARA: {high_risk_rules[0]['rule']}"
                })
            else:
                result.update({
                    'result': ScanResult.SUSPICIOUS,
                    'threat_level': ThreatLevel.LOW,
                    'threat_name': f"YARA: {yara_result[0]['rule']}"
                })
        
        # Check fuzzy hash
        if fuzzy_result.get('suspicious'):
            if result['result'] == ScanResult.CLEAN:
                result.update({
                    'result': ScanResult.SUSPICIOUS,
                    'threat_level': ThreatLevel.LOW
                })
        
        return result
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    async def _detect_file_type(self, file_path: str) -> FileType:
        """Detect file type"""
        try:
            mime_type = magic.from_file(file_path, mime=True)
            
            if mime_type.startswith('application/x-executable'):
                return FileType.EXECUTABLE
            elif mime_type.startswith('application/'):
                if 'zip' in mime_type or 'tar' in mime_type:
                    return FileType.ARCHIVE
                else:
                    return FileType.DOCUMENT
            elif mime_type.startswith('text/'):
                return FileType.SCRIPT
            elif mime_type.startswith('image/'):
                return FileType.IMAGE
            else:
                return FileType.UNKNOWN
                
        except Exception:
            return FileType.UNKNOWN
    
    async def _quarantine_file(self, file_path: str, metadata: ScanMetadata) -> QuarantineEntry:
        """Move file to quarantine"""
        quarantine_id = hashlib.md5(f"{file_path}_{metadata.scan_time}".encode()).hexdigest()
        quarantine_path = self.quarantine_dir / f"{quarantine_id}.quarantine"
        
        try:
            # Copy file to quarantine (don't move to preserve original)
            shutil.copy2(file_path, quarantine_path)
            
            # Create quarantine entry
            entry = QuarantineEntry(
                quarantine_id=quarantine_id,
                original_path=file_path,
                quarantine_path=str(quarantine_path),
                file_hash=metadata.file_hash,
                threat_name=metadata.threat_name or 'Unknown',
                quarantined_at=datetime.utcnow(),
                metadata={
                    'scan_id': metadata.scan_id,
                    'threat_level': metadata.threat_level.value,
                    'file_size': metadata.file_size
                }
            )
            
            # Store quarantine info
            await self._store_quarantine_entry(entry)
            
            # Update metrics
            self.quarantined_files.inc()
            
            logger.info(f"File quarantined: {file_path} -> {quarantine_id}")
            return entry
            
        except Exception as e:
            logger.error(f"Failed to quarantine file: {e}")
            raise
    
    def _create_error_result(
        self, 
        scan_id: str, 
        file_path: str, 
        error_msg: str, 
        scan_duration: float = 0.0
    ) -> ScanMetadata:
        """Create error scan result"""
        return ScanMetadata(
            scan_id=scan_id,
            file_path=file_path,
            file_hash="",
            file_size=0,
            file_type=FileType.UNKNOWN.value,
            scan_time=datetime.utcnow(),
            scan_duration=scan_duration,
            result=ScanResult.ERROR,
            threat_name=None,
            threat_level=ThreatLevel.LOW,
            engine_version="",
            signatures_version="",
            additional_info={'error': error_msg}
        )
    
    async def _get_signatures_version(self) -> str:
        """Get virus signatures version"""
        try:
            version = self.clamd_client.version()
            # Extract version info from ClamAV response
            lines = version.split('\n')
            for line in lines:
                if 'ClamAV' in line:
                    return line.strip()
            return version
        except Exception:
            return "unknown"
    
    async def _update_metrics(self):
        """Update signature age and other metrics"""
        try:
            # Update signature age (simplified)
            self.signature_age.set(24)  # Would calculate actual age
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    async def _send_to_threat_intelligence(self, metadata: ScanMetadata):
        """Send scan results to threat intelligence system"""
        if metadata.result in [ScanResult.INFECTED, ScanResult.SUSPICIOUS]:
            # Would integrate with GuardianShield threat intelligence agents
            logger.info(f"Threat detected, notifying intelligence system: {metadata.threat_name}")

if __name__ == "__main__":
    config = {
        'clamd': {
            'host': 'localhost',
            'port': 3310
        },
        'redis': {
            'url': 'redis://redis.guardianshield.svc.cluster.local:6379',
            'database': 3
        },
        'quarantine_dir': '/app/quarantine',
        'temp_dir': '/app/temp',
        'yara_rules_dir': '/app/yara_rules',
        'auto_quarantine': True,
        'cache_ttl': 3600
    }
    
    async def main():
        engine = DHIClamAVEngine(config)
        await engine.initialize()
        
        # Example scan
        test_file = "/tmp/test_file.txt"
        if os.path.exists(test_file):
            result = await engine.scan_file(test_file)
            print(f"Scan result: {result.result.value}")
        
        # Health check
        health = await engine.health_check()
        print(f"Health: {health['status']}")
    
    asyncio.run(main())