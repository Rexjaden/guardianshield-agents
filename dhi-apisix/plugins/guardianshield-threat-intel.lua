-- GuardianShield Threat Intelligence Plugin for APISIX
-- Real-time threat detection and blocking

local core = require("apisix.core")
local http = require("resty.http")
local json = require("apisix.core.json")
local redis_new = require("resty.redis")
local ngx = ngx
local pairs = pairs
local type = type
local ipairs = ipairs
local tostring = tostring

local plugin_name = "guardianshield-threat-intel"

local schema = {
    type = "object",
    properties = {
        threat_intel_endpoint = {
            type = "string",
            description = "GuardianShield threat intelligence API endpoint",
            default = "http://threat-intel.guardianshield.svc.cluster.local:8080"
        },
        api_key = {
            type = "string",
            description = "API key for threat intelligence service"
        },
        cache_ttl = {
            type = "integer",
            minimum = 60,
            maximum = 86400,
            default = 3600,
            description = "Cache TTL in seconds"
        },
        redis_host = {
            type = "string",
            default = "redis.guardianshield.svc.cluster.local",
            description = "Redis host for caching"
        },
        redis_port = {
            type = "integer",
            minimum = 1,
            maximum = 65535,
            default = 6379,
            description = "Redis port"
        },
        redis_database = {
            type = "integer",
            minimum = 0,
            maximum = 15,
            default = 4,
            description = "Redis database number"
        },
        block_malicious_ips = {
            type = "boolean",
            default = true,
            description = "Block known malicious IPs"
        },
        block_suspicious_uas = {
            type = "boolean", 
            default = true,
            description = "Block suspicious user agents"
        },
        threat_score_threshold = {
            type = "integer",
            minimum = 1,
            maximum = 100,
            default = 70,
            description = "Threat score threshold for blocking"
        },
        enable_web3_checks = {
            type = "boolean",
            default = true,
            description = "Enable Web3-specific threat checks"
        },
        whitelist_ips = {
            type = "array",
            items = {
                type = "string"
            },
            description = "IP addresses to whitelist"
        }
    },
    required = {"api_key"}
}

local _M = {
    version = 1.0,
    priority = 8000,
    name = plugin_name,
    schema = schema,
}

-- Initialize Redis connection
local function init_redis(conf)
    local red = redis_new()
    red:set_timeout(1000) -- 1 second timeout
    
    local ok, err = red:connect(conf.redis_host, conf.redis_port)
    if not ok then
        core.log.error("failed to connect to redis: ", err)
        return nil, err
    end
    
    if conf.redis_database > 0 then
        local res, err = red:select(conf.redis_database)
        if not res then
            core.log.error("failed to select redis database: ", err)
            return nil, err
        end
    end
    
    return red
end

-- Check if IP is whitelisted
local function is_whitelisted_ip(ip, whitelist)
    if not whitelist then
        return false
    end
    
    for _, whitelisted_ip in ipairs(whitelist) do
        if ip == whitelisted_ip then
            return true
        end
    end
    return false
end

-- Get threat intelligence data from cache or API
local function get_threat_intel(conf, ip, user_agent)
    -- Check Redis cache first
    local red, err = init_redis(conf)
    if not red then
        core.log.error("Redis connection failed: ", err)
    else
        local cache_key = "threat_intel:" .. ip
        local cached_result, err = red:get(cache_key)
        if cached_result and cached_result ~= ngx.null then
            local data = json.decode(cached_result)
            if data then
                red:close()
                return data
            end
        end
        red:close()
    end
    
    -- Query threat intelligence API
    local httpc = http.new()
    httpc:set_timeout(5000) -- 5 second timeout
    
    local request_body = {
        ip = ip,
        user_agent = user_agent,
        timestamp = ngx.time(),
        source = "dhi-apisix"
    }
    
    local res, err = httpc:request_uri(conf.threat_intel_endpoint .. "/api/v1/check", {
        method = "POST",
        headers = {
            ["Content-Type"] = "application/json",
            ["Authorization"] = "Bearer " .. conf.api_key,
            ["X-API-Key"] = conf.api_key
        },
        body = json.encode(request_body),
        ssl_verify = false -- For internal services
    })
    
    if not res then
        core.log.error("threat intel API request failed: ", err)
        return {threat_score = 0, malicious = false}
    end
    
    if res.status ~= 200 then
        core.log.error("threat intel API returned status: ", res.status)
        return {threat_score = 0, malicious = false}
    end
    
    local threat_data = json.decode(res.body)
    if not threat_data then
        core.log.error("failed to decode threat intel response")
        return {threat_score = 0, malicious = false}
    end
    
    -- Cache the result
    local red, err = init_redis(conf)
    if red then
        local cache_key = "threat_intel:" .. ip
        red:setex(cache_key, conf.cache_ttl, json.encode(threat_data))
        red:close()
    end
    
    return threat_data
end

-- Check for Web3-specific threats
local function check_web3_threats(uri, headers)
    local web3_patterns = {
        "eth_sendTransaction",
        "personal_unlockAccount", 
        "admin_addPeer",
        "metamask",
        "web3",
        "ethereum",
        "wallet",
        "private_key",
        "mnemonic",
        "seed_phrase"
    }
    
    -- Check URI
    for _, pattern in ipairs(web3_patterns) do
        if string.find(string.lower(uri), pattern) then
            return true, "Suspicious Web3 pattern in URI: " .. pattern
        end
    end
    
    -- Check headers
    for header_name, header_value in pairs(headers) do
        for _, pattern in ipairs(web3_patterns) do
            if string.find(string.lower(header_value), pattern) then
                return true, "Suspicious Web3 pattern in header: " .. pattern
            end
        end
    end
    
    return false, nil
end

-- Check for suspicious user agents
local function is_suspicious_user_agent(user_agent)
    if not user_agent then
        return false
    end
    
    local suspicious_patterns = {
        "sqlmap",
        "nikto",
        "nmap",
        "masscan",
        "zap",
        "gobuster",
        "dirb",
        "wfuzz",
        "burp",
        "metasploit",
        "exploit",
        "scanner",
        "bot.*malicious",
        "crawler.*malicious"
    }
    
    local lower_ua = string.lower(user_agent)
    for _, pattern in ipairs(suspicious_patterns) do
        if string.find(lower_ua, pattern) then
            return true, pattern
        end
    end
    
    return false, nil
end

function _M.check_schema(conf)
    local ok, err = core.schema.check(schema, conf)
    if not ok then
        return false, err
    end
    return true
end

function _M.access(conf, ctx)
    -- Get client IP
    local client_ip = core.request.get_remote_addr(ctx)
    if not client_ip then
        client_ip = ctx.var.remote_addr
    end
    
    -- Check if IP is whitelisted
    if is_whitelisted_ip(client_ip, conf.whitelist_ips) then
        return
    end
    
    -- Get headers and URI
    local headers = ngx.req.get_headers()
    local user_agent = headers["user-agent"]
    local uri = ctx.var.uri
    
    -- Check for suspicious user agent
    if conf.block_suspicious_uas then
        local is_suspicious, pattern = is_suspicious_user_agent(user_agent)
        if is_suspicious then
            core.log.warn("Blocking suspicious user agent: ", user_agent, " (pattern: ", pattern, ")")
            return 403, {
                error = "Suspicious user agent detected",
                code = "THREAT_DETECTED_UA",
                request_id = ctx.var.request_id
            }
        end
    end
    
    -- Check for Web3-specific threats
    if conf.enable_web3_checks then
        local is_web3_threat, reason = check_web3_threats(uri, headers)
        if is_web3_threat then
            core.log.warn("Blocking Web3 threat from IP: ", client_ip, " - ", reason)
            return 403, {
                error = "Web3 security threat detected",
                code = "THREAT_DETECTED_WEB3",
                reason = reason,
                request_id = ctx.var.request_id
            }
        end
    end
    
    -- Get threat intelligence data
    if conf.block_malicious_ips then
        local threat_data = get_threat_intel(conf, client_ip, user_agent)
        
        if threat_data.malicious or 
           (threat_data.threat_score and threat_data.threat_score >= conf.threat_score_threshold) then
            
            -- Log the threat
            core.log.warn("Blocking malicious IP: ", client_ip, 
                         " (threat score: ", threat_data.threat_score or 0, 
                         ", reason: ", threat_data.reason or "unknown", ")")
            
            -- Block the request
            return 403, {
                error = "Access denied - malicious activity detected",
                code = "THREAT_DETECTED_IP",
                threat_score = threat_data.threat_score,
                reason = threat_data.reason,
                request_id = ctx.var.request_id
            }
        end
        
        -- Add threat score to request headers for downstream services
        if threat_data.threat_score and threat_data.threat_score > 0 then
            core.request.set_header(ctx, "X-Threat-Score", tostring(threat_data.threat_score))
            core.request.set_header(ctx, "X-Threat-Source", "guardianshield-threat-intel")
        end
    end
end

function _M.header_filter(conf, ctx)
    -- Add security headers
    local headers = {
        ["X-Content-Type-Options"] = "nosniff",
        ["X-Frame-Options"] = "DENY", 
        ["X-XSS-Protection"] = "1; mode=block",
        ["Referrer-Policy"] = "strict-origin-when-cross-origin",
        ["X-GuardianShield-Protected"] = "true"
    }
    
    for name, value in pairs(headers) do
        core.response.set_header(name, value)
    end
end

function _M.log(conf, ctx)
    -- Log threat detection events
    local client_ip = core.request.get_remote_addr(ctx) or ctx.var.remote_addr
    local threat_score = ctx.var.http_x_threat_score
    
    if threat_score and tonumber(threat_score) > 30 then
        local log_data = {
            timestamp = ngx.time(),
            client_ip = client_ip,
            user_agent = ctx.var.http_user_agent,
            uri = ctx.var.uri,
            method = ctx.var.request_method,
            threat_score = tonumber(threat_score),
            status = ctx.var.status,
            request_id = ctx.var.request_id,
            plugin = plugin_name
        }
        
        core.log.warn("Threat detected: ", json.encode(log_data))
    end
end

return _M